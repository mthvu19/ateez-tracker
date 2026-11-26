"""X API v2 (tra phi theo so bai doc). Chi doc timeline cua cac tai khoan trong config.
Bo retweet va reply. Moi tai khoan toi da `max_per_account` bai moi luot."""
import os

from .common import clip, iso, parse_iso

API = "https://api.x.com/2"


def _auth():
    tok = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not tok:
        raise RuntimeError("Thieu X_BEARER_TOKEN")
    return {"Authorization": f"Bearer {tok}"}


def resolve_users(http, usernames, cache, log=print):
    """User lookup ton phi -> luu id vao state de chi tra 1 lan."""
    missing = [u for u in usernames if u.lower() not in cache]
    if missing:
        r = http.get(f"{API}/users/by", headers=_auth(), timeout=30,
                     params={"usernames": ",".join(missing)})
        r.raise_for_status()
        for u in r.json().get("data", []):
            cache[u["username"].lower()] = u["id"]
        log(f"[x] tra cuu id cho {len(missing)} tai khoan")
    return cache


def parse_timeline(js, acct):
    media = {m["media_key"]: m for m in (js.get("includes") or {}).get("media", [])}
    out = []
    for t in js.get("data", []) or []:
        text = ((t.get("note_tweet") or {}).get("text")) or t.get("text", "")
        imgs = []
        for k in (t.get("attachments") or {}).get("media_keys", []):
            m = media.get(k) or {}
            u = m.get("url") or m.get("preview_image_url")
            if u:
                imgs.append(u)
        # bo cac link t.co o cuoi (link anh)
        clean = text
        for u in (t.get("entities") or {}).get("urls", []) or []:
            if u.get("media_key") or "/photo/" in (u.get("expanded_url") or "") or "/video/" in (u.get("expanded_url") or ""):
                clean = clean.replace(u.get("url", ""), "")
            elif u.get("url") and u.get("expanded_url"):
                clean = clean.replace(u["url"], u["expanded_url"])
        clean = clean.strip()
        first = clean.split("\n", 1)[0]
        out.append({
            "id": f"x:{t['id']}",
            "source": "x",
            "platform": "X",
            "account": "@" + acct["username"],
            "tier": acct.get("tier", "fan"),
            "url": f"https://x.com/{acct['username']}/status/{t['id']}",
            "title": clip(first, 140),
            "text": clip(clean, 2000),
            "images": imgs,
            "published": iso(parse_iso(t["created_at"])) if t.get("created_at") else None,
            "category_hint": acct.get("category"),
        })
    return out


def collect(cfg, http, state, log=print, about_group=None):
    xcfg = cfg["x"]
    accts = xcfg["accounts"]
    ids = resolve_users(http, [a["username"] for a in accts], state.setdefault("x_user_ids", {}), log)
    since = state.setdefault("x_since", {})
    out, read = [], 0
    for a in accts:
        uid = ids.get(a["username"].lower())
        if not uid:
            log(f"[x] khong tim thay @{a['username']}")
            continue
        params = {
            "max_results": max(5, xcfg["max_per_account"] if a["username"] in since else xcfg["first_run_max"]),
            "exclude": "retweets,replies",
            "tweet.fields": "created_at,entities,attachments,note_tweet",
            "expansions": "attachments.media_keys",
            "media.fields": "url,preview_image_url,type",
        }
        if since.get(a["username"]):
            params["since_id"] = since[a["username"]]
        try:
            r = http.get(f"{API}/users/{uid}/tweets", headers=_auth(), params=params, timeout=30)
            if r.status_code == 402 or r.status_code == 429:
                log(f"[x] @{a['username']}: HTTP {r.status_code} (het credit / qua gioi han) -> dung")
                break
            r.raise_for_status()
            js = r.json()
        except Exception as e:  # noqa: BLE001
            log(f"[x] loi @{a['username']}: {e}")
            continue
        items = parse_timeline(js, a)
        read += len(items)
        if js.get("meta", {}).get("newest_id"):
            since[a["username"]] = js["meta"]["newest_id"]
        if a.get("only_ateez") and about_group:
            items = [i for i in items if about_group(i["text"])]
        log(f"[x] @{a['username']}: doc {len(js.get('data') or [])} bai, giu {len(items)}")
        out += items
    log(f"[x] tong so bai doc (tinh phi): {read} ~ ${read * 0.005:.2f}")
    state["x_reads_total"] = state.get("x_reads_total", 0) + read
    return out
