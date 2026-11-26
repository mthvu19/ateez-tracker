"""Tuy chon: neu co ANTHROPIC_API_KEY thi dung Claude de
- tom tat + dich tieu de/noi dung sang tieng Viet
- phan loai lai, nhan dien thanh vien
- trich moc thoi gian (deadline, ngay dien...) chuan hon luat.
Khong co key -> bo qua, trang van chay voi phan loai bang luat."""
import json
import os

from .classify import CATEGORIES
from .common import iso, parse_iso

API = "https://api.anthropic.com/v1/messages"

PROMPT = """You process news about the K-pop group ATEEZ for a fan's personal tracking page.
Members: Hongjoong, Seonghwa, Yunho, Yeosang, San, Mingi, Wooyoung, Jongho.
Valid categories (use the exact code): {cats}
- funfact: throwbacks dug up by fans, TMI, quotes from past interviews.
- sns: social media updates by members/the group (IG story/post, Weverse, TOKTOQ...).

For EACH item below return one JSON object:
{{"id": "<keep the id>", "category": "<code>", "members": ["<English name>"...] (empty if whole group or unclear),
 "title_en": "<short, natural English headline, max 90 characters>",
 "summary_en": "<1-2 sentence English summary; keep proper nouns and song titles as written; mention key dates/times if any>",
 "events": [{{"label": "<short English name of the milestone>", "start": "<ISO 8601 with timezone>", "end": "<ISO or null>"}}]}}
"events" only lists FUTURE or ongoing milestones stated explicitly in the item (registration deadlines, ticket opening, presale, release, show dates, broadcast...). Times without a timezone are KST (+09:00). Date-only milestones use T00:00:00+09:00. Never invent milestones.
Write in plain, natural English like a K-pop news account, not a literal translation. Do not use markdown.
Current date: {today}.
Return only a JSON array, nothing else. Make sure strings are valid JSON (escape double quotes).

ITEMS:
{items}"""


def enrich(items, cfg, today, http, log=print, limit=None):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        log("[ai] khong co ANTHROPIC_API_KEY -> bo qua")
        return 0
    if not items:
        return 0
    todo = items[: limit or cfg.get("ai_max_items_per_run", 40)]
    done = 0
    queue = [todo[i:i + 10] for i in range(0, len(todo), 10)]
    while queue:
        batch = queue.pop(0)
        payload = [{"id": it["id"], "source": f"{it['account']} ({it['platform']})", "title": it["title"],
                    "text": it["text"][:2500], "published": it["published"]} for it in batch]
        body = {
            "model": cfg.get("ai_model", "claude-haiku-5-5"),
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": PROMPT.format(
                cats=", ".join(CATEGORIES), today=today, items=json.dumps(payload, ensure_ascii=False))}],
        }
        try:
            r = http.post(API, json=body, timeout=120, headers={
                "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            if r.status_code >= 400:
                log(f"[ai] HTTP {r.status_code}: {r.text[:300]}")
                continue
            text = "".join(b.get("text", "") for b in r.json().get("content", []))
            text = text[text.find("["): text.rfind("]") + 1]
            res = {o["id"]: o for o in json.loads(text)}
        except Exception as e:  # noqa: BLE001
            if len(batch) > 1:
                log(f"[ai] loi ({e}) -> chia nho {len(batch)} tin de thu lai")
                half = len(batch) // 2
                queue += [batch[:half], batch[half:]]
            else:
                log(f"[ai] loi tin {batch[0]['id']}: {e}")
            continue
        for it in batch:
            o = res.get(it["id"])
            if not o:
                continue
            if o.get("category") in CATEGORIES and not it.get("category_hint"):
                it["category"] = o["category"]
            if isinstance(o.get("members"), list):
                canon = {m["en"].lower(): m["en"] for m in cfg["members"]}
                it["members"] = [canon[m.lower()] for m in o["members"] if isinstance(m, str) and m.lower() in canon]
            for k in ("title_vi", "summary_vi"):
                it.pop(k, None)
            for k in ("title_en", "summary_en"):
                if o.get(k):
                    it[k] = str(o[k])[:400]
            evs = []
            for e in o.get("events") or []:
                st = parse_iso(e.get("start")) if isinstance(e, dict) else None
                if not st:
                    continue
                en = parse_iso(e.get("end"))
                evs.append({"label": str(e.get("label", ""))[:90], "start": iso(st),
                            "end": iso(en) if en and en > st else None, "has_time": "T" in str(e["start"])})
            if evs or "events" in o:
                it["events"] = evs[:12]
            it["ai"] = "en"
            done += 1
    log(f"[ai] da xu ly {done}/{len(todo)} tin")
    return done
