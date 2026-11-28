"""Gom cac tin noi ve cung mot su kien (vd. nhieu bao cung dua tin tour chau Au) thanh mot "chu de".
Moi item co truong `topic`; thong tin chu de luu o docs/data/topics.json.
Can ANTHROPIC_API_KEY; khong co key thi moi tin la mot chu de rieng."""
import hashlib
import json
import os
from datetime import timedelta

from .common import parse_iso

API = "https://api.anthropic.com/v1/messages"
WINDOW_DAYS = 5

PROMPT = """You group K-pop news items about ATEEZ into stories, for a personal news tracker.
Two items belong to the same story when they report the SAME specific announcement, event, achievement or post
(e.g. several outlets covering the same tour announcement, or two fan accounts reposting the same Instagram story).
Different songs, different charts, different shows or different dates are different stories, even if similar.

EXISTING STORIES (from the last few days):
{topics}

NEW ITEMS:
{items}

For each new item return {{"id": "<item id>", "story": "<existing story id, or a new label like NEW1, NEW2...>"}}.
New items that belong together share the same NEW label. For each NEW label also return one object
{{"new": "<label>", "title": "<short neutral English headline for the whole story, max 90 chars>"}}.
Return only a JSON array with all these objects, nothing else."""


def _tid(seed):
    return "t" + hashlib.sha1(seed.encode()).hexdigest()[:10]


def _call(http, key, model, prompt):
    r = http.post(API, timeout=120, json={"model": model, "max_tokens": 4000,
                                          "messages": [{"role": "user", "content": prompt}]},
                  headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    text = "".join(b.get("text", "") for b in r.json().get("content", []))
    return json.loads(text[text.find("["): text.rfind("]") + 1])


def recent_topics(items, topics, now):
    lo = now - timedelta(days=WINDOW_DAYS)
    seen = {}
    for it in items:
        t = it.get("topic")
        d = parse_iso(it.get("published"))
        if t and d and d >= lo and t in topics:
            seen[t] = topics[t]["title"]
    return seen


def assign(items, todo, topics, cfg, http, now, log=print):
    """Gan `topic` cho cac tin trong `todo` (danh sach dict trong `items`), cap nhat `topics`."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    todo = [i for i in todo if not i.get("topic")]
    if not todo:
        return 0
    if not key:
        for it in todo:
            it["topic"] = _tid(it["id"])
            topics[it["topic"]] = {"title": it.get("title_en") or it["title"]}
        return 0
    done = 0
    todo.sort(key=lambda i: i.get("published") or "")
    for k in range(0, len(todo), 25):
        batch = todo[k:k + 25]
        known = recent_topics(items, topics, parse_iso(batch[-1].get("published")) or now)
        prompt = PROMPT.format(
            topics=json.dumps([{"id": t, "title": title} for t, title in known.items()], ensure_ascii=False),
            items=json.dumps([{"id": i["id"], "title": i.get("title_en") or i["title"],
                               "summary": (i.get("summary_en") or i.get("text", ""))[:300],
                               "date": (i.get("published") or "")[:10]} for i in batch], ensure_ascii=False))
        try:
            res = _call(http, key, cfg.get("ai_model", "claude-haiku-5-5"), prompt)
        except Exception as e:  # noqa: BLE001
            log(f"[topic] loi: {e}")
            continue
        labels = {o["new"]: o.get("title", "") for o in res if isinstance(o, dict) and o.get("new")}
        new_ids = {}
        for o in res:
            if not isinstance(o, dict) or "id" not in o:
                continue
            it = next((i for i in batch if i["id"] == o["id"]), None)
            if not it:
                continue
            story = str(o.get("story", ""))
            if story in known:
                it["topic"] = story
            else:
                if story not in new_ids:
                    new_ids[story] = _tid(it["id"])
                    topics[new_ids[story]] = {"title": labels.get(story) or it.get("title_en") or it["title"]}
                it["topic"] = new_ids[story]
            done += 1
        for it in batch:  # tin AI bo sot -> chu de rieng
            if not it.get("topic"):
                it["topic"] = _tid(it["id"])
                topics[it["topic"]] = {"title": it.get("title_en") or it["title"]}
    log(f"[topic] gan chu de cho {done}/{len(todo)} tin")
    return done


def finalize(items, topics):
    """Tinh lai thong tin hien thi cho moi chu de; bo chu de khong con tin."""
    groups = {}
    for it in items:
        if it.get("topic"):
            groups.setdefault(it["topic"], []).append(it)
    out = {}
    for t, its in groups.items():
        latest = max((i.get("published") or "" for i in its), default="")
        out[t] = {"title": (topics.get(t) or {}).get("title") or its[0].get("title_en") or its[0]["title"],
                  "count": len(its), "latest": latest}
    return out
