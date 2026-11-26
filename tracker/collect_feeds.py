"""YouTube (RSS kenh) va bao chi (Google News RSS)."""
import re
import xml.etree.ElementTree as ET
from datetime import timedelta
from email.utils import parsedate_to_datetime

from .common import clip, html_to_text, iso, now_utc, parse_iso

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


def parse_youtube(xml_text, ch):
    root = ET.fromstring(xml_text)
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", default="", namespaces=NS)
        title = e.findtext("a:title", default="", namespaces=NS)
        pub = e.findtext("a:published", default="", namespaces=NS)
        group = e.find("media:group", NS)
        desc, thumb = "", None
        if group is not None:
            desc = group.findtext("media:description", default="", namespaces=NS)
            t = group.find("media:thumbnail", NS)
            thumb = t.get("url") if t is not None else None
        link = e.find("a:link", NS)
        url = link.get("href") if link is not None else f"https://www.youtube.com/watch?v={vid}"
        out.append({
            "id": f"yt:{vid}",
            "source": "youtube",
            "platform": "YouTube",
            "account": ch["name"],
            "tier": ch.get("tier", "official"),
            "url": url,
            "title": title,
            "text": clip(desc, 1500),
            "images": [thumb] if thumb else [],
            "published": iso(parse_iso(pub)) if pub else iso(now_utc()),
        })
    return out


def _norm_title(t):
    t = re.sub(r"\s+-\s+[^-]+$", "", t or "")  # bo " - Ten bao" o cuoi
    return re.sub(r"\W+", "", t.lower())[:80]


def parse_news(xml_text, max_n, max_age_days=3):
    root = ET.fromstring(xml_text)
    out = []
    cutoff = now_utc() - timedelta(days=max_age_days)
    for it in root.iter("item"):
        title = it.findtext("title", default="")
        link = it.findtext("link", default="")
        pub = it.findtext("pubDate", default="")
        src = it.find("source")
        try:
            dt = parsedate_to_datetime(pub)
        except (TypeError, ValueError):
            dt = now_utc()
        if dt < cutoff:
            continue
        outlet = src.text if src is not None and src.text else ""
        clean_title = re.sub(r"\s+-\s+" + re.escape(outlet) + r"$", "", title) if outlet else title
        out.append({
            "id": "news:" + _norm_title(title),
            "source": "news",
            "platform": "News",
            "account": outlet,
            "tier": "news",
            "url": link,
            "title": clean_title,
            "text": clip(html_to_text(it.findtext("description", default="")), 600),
            "images": [],
            "published": iso(dt),
        })
        if len(out) >= max_n:
            break
    return out


def collect_youtube(cfg, http, known_ids, log=print):
    out = []
    for ch in cfg["youtube"]:
        try:
            r = http.get("https://www.youtube.com/feeds/videos.xml",
                         params={"channel_id": ch["channel_id"]}, timeout=30)
            r.raise_for_status()
            items = [i for i in parse_youtube(r.text, ch) if i["id"] not in known_ids]
            log(f"[youtube] {ch['name']}: {len(items)} video moi")
            out += items
        except Exception as e:  # noqa: BLE001
            log(f"[youtube] loi {ch['name']}: {e}")
    return out


def collect_news(cfg, http, known_ids, log=print):
    out, seen = [], set(known_ids)
    for q in cfg["news"]:
        try:
            r = http.get("https://news.google.com/rss/search", timeout=30,
                         params={"q": q["q"], "hl": q["hl"], "gl": q["gl"], "ceid": q["ceid"]})
            r.raise_for_status()
            items = parse_news(r.text, cfg.get("news_max_per_query", 25))
            new = []
            for i in items:
                if i["id"] in seen:
                    continue
                seen.add(i["id"])
                new.append(i)
            log(f"[news] {q['q']} ({q['hl']}): {len(new)} bai moi")
            out += new
        except Exception as e:  # noqa: BLE001
            log(f"[news] loi {q['q']}: {e}")
    return out
