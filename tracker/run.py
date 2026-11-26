"""Chay mot luot cap nhat.
    python -m tracker.run --sources kq,youtube,news
    python -m tracker.run --sources x
"""
import argparse
import os
import re
from datetime import timedelta

from . import collect_feeds, collect_kq, collect_x
from .classify import CATEGORIES, classify, detect_members, is_about_group, member_patterns
from .common import (DATA_DIR, ITEMS_PATH, STATE_PATH, KST, iso, load_config, now_utc,
                     parse_iso, read_json, session, write_json)
from .dates import extract_events
from .enrich_ai import enrich
from .images import annotate, dedupe_images
from .notify import build_lines, send


def prepare(item, pats):
    item["category"] = classify(item)
    item["members"] = detect_members(f"{item['title']}\n{item['text']}", pats)
    if item["tier"] == "official" and item["source"] in ("kq", "x"):
        item["events"] = extract_events(item["text"], item["title"])
    else:
        item.setdefault("events", [])
    return item


STOP = set("a an the and or of to in on at for with as by from his her their its is are was were be has have after new "
           "over into about up out this that than more ateez's".split())


def _tokens(text):
    text = re.sub(r"(\d)[,.](\d{3})", r"\1\2", (text or "").lower())  # 270,000 -> 270000
    text = re.sub(r"'s\b|’s\b", "", text)
    return {w for w in re.findall(r"[a-z0-9가-힣]+", text) if w not in STOP and len(w) > 1}


def similar(a, b):
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    na, nb = {w for w in ta if w.isdigit()}, {w for w in tb if w.isdigit()}
    if na and nb and not (na & nb):
        return False  # so lieu khac nhau -> tin khac nhau
    return len(ta & tb) / len(ta | tb) >= 0.6


def dedupe_news(items, days=3):
    """Cung mot su kien nhieu bao dang (tieu de gan giong) -> giu 1 tin (moi nhat)."""
    kept, out = [], []
    for it in items:
        if it.get("source") == "news":
            title = it.get("title_en") or it.get("title", "")
            ts = parse_iso(it.get("published"))
            dup = False
            for k in kept:
                kts = parse_iso(k.get("published"))
                if ts and kts and abs((ts - kts).total_seconds()) > days * 86400:
                    continue
                if similar(title, k.get("title_en") or k.get("title", "")):
                    dup = True
                    break
            if dup:
                continue
            kept.append(it)
        out.append(it)
    return out


def build_events(items, now):
    """Gom moc thoi gian tu moi tin -> docs/data/events.json."""
    out, seen = [], set()
    lo = now - timedelta(days=45)
    for it in items:
        for e in it.get("events") or []:
            start = parse_iso(e.get("start"))
            end = parse_iso(e.get("end")) if e.get("end") else None
            if not start or (end or start) < lo:
                continue
            key = (e.get("label"), e.get("start"), e.get("end"))
            if key in seen:
                continue
            seen.add(key)
            k = start.astimezone(KST)
            has_time = bool(e.get("has_time", True)) and not (k.hour == 0 and k.minute == 0)
            e = {**e, "start": iso(start), "end": iso(end) if end else None, "has_time": has_time}
            out.append({**e, "item_id": it["id"], "title": it.get("title_en") or it["title"],
                        "url": it["url"], "category": it.get("category"), "members": it.get("members", [])})
    out.sort(key=lambda e: e["start"])
    return out


def due_reminders(events, state, now):
    sent = set(state.setdefault("reminded", []))
    out = []
    for e in events:
        when = e.get("end") or e["start"]
        d = parse_iso(when)
        if not d or not (now <= d <= now + timedelta(hours=24)):
            continue
        key = f"{e['item_id']}|{e['label']}|{when}"
        if key in sent:
            continue
        sent.add(key)
        out.append({**e, "when": when})
    state["reminded"] = sorted(sent)[-500:]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="kq,youtube,news")
    ap.add_argument("--no-notify", action="store_true")
    ap.add_argument("--reprocess", action="store_true",
                    help="cho AI xu ly lai cac tin cu chua duoc tom tat/dich")
    args = ap.parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    cfg = load_config()
    pats = member_patterns(cfg["members"])
    state = read_json(STATE_PATH, {})
    store = read_json(ITEMS_PATH, {"items": []})
    items = store.get("items", [])
    # bai KQ chua co noi dung -> lay lai
    retry = {i["id"] for i in items if i["source"] == "kq" and not i.get("text")}
    if retry:
        items = [i for i in items if i["id"] not in retry]
    known = {i["id"] for i in items}
    had_source = {i["source"] for i in items}  # nguon lan dau chay -> khong bao Discord tran lan
    http = session()
    now = now_utc()
    meta = read_json(os.path.join(DATA_DIR, "meta.json"), {"sources": {}})

    new = []
    for src in sources:
        try:
            if src == "kq":
                got = collect_kq.collect(cfg, http, known)
            elif src == "youtube":
                got = collect_feeds.collect_youtube(cfg, http, known)
            elif src == "news":
                got = collect_feeds.collect_news(cfg, http, known)
                got = [g for g in got if is_about_group(f"{g['title']} {g['text']}", cfg, pats)]
            elif src == "x":
                got = collect_x.collect(cfg, http, state,
                                        about_group=lambda t: is_about_group(t, cfg, pats))
            else:
                print(f"Nguon khong ro: {src}")
                continue
            meta["sources"][src] = {"ok": True, "at": iso(now), "new": len(got)}
        except Exception as e:  # noqa: BLE001
            print(f"[{src}] LOI: {e}")
            meta["sources"][src] = {"ok": False, "at": iso(now), "error": str(e)[:300]}
            got = []
        for g in got:
            if g["id"] in known:
                continue
            known.add(g["id"])
            new.append(prepare(g, pats))

    today = now.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")
    enrich(new, cfg, today, http)
    if args.reprocess:
        old = [i for i in items if i.get("ai") != "en"]
        print(f"[ai] xu ly lai {len(old)} tin cu")
        enrich(old, cfg, today, http, limit=len(old))
        for it in old:
            it["category_label"] = CATEGORIES.get(it["category"], it["category"])
    for it in new:
        it["category_label"] = CATEGORIES.get(it["category"], it["category"])
        it.pop("category_hint", None)
        it["fetched"] = iso(now)

    # tinh lai moc thoi gian cho tin cu (luat trich ngay co the da duoc cai tien)
    for it in items:
        if not it.get("ai") and it.get("tier") == "official" and it.get("source") in ("kq", "x"):
            it["events"] = extract_events(it.get("text", ""), it.get("title", ""))
    items = new + items
    items.sort(key=lambda i: i.get("published") or "", reverse=True)
    items = dedupe_news(items)
    try:
        annotate(items, http)
        items = dedupe_images(items)
    except Exception as e:  # noqa: BLE001
        print(f"[img] loi: {e}")
    items = items[: cfg.get("keep_items", 2000)]
    events = build_events(items, now)

    write_json(ITEMS_PATH, {"updated": iso(now), "items": items})
    write_json(os.path.join(DATA_DIR, "events.json"), {"updated": iso(now), "events": events})
    meta["updated"] = iso(now)
    meta["counts"] = {"items": len(items), "events": len(events)}
    write_json(os.path.join(DATA_DIR, "meta.json"), meta)

    reminders = due_reminders(events, state, now)
    write_json(STATE_PATH, state)
    print(f"Xong: {len(new)} tin moi, {len(items)} tin tong, {len(events)} moc thoi gian, {len(reminders)} nhac han")
    if not args.no_notify:
        try:
            fresh = [i for i in new if i["source"] in had_source]
            send(build_lines(fresh, reminders), http)
        except Exception as e:  # noqa: BLE001
            print(f"[discord] loi: {e}")


if __name__ == "__main__":
    main()
