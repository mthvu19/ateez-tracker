"""Thong bao chinh thuc tren ateez.kqent.com (nen tang b.stage, Next.js).
Danh sach: JSON __NEXT_DATA__ trong HTML trang /tag/NOTICE.
Than bai: /_next/data/{buildId}/ko/contents/{id}.json -> pageProps.contents.body"""
import json
import re
from datetime import datetime, timezone

from .common import clip, html_to_text, iso

NEXT_RX = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def objectid_time(oid):
    try:
        return datetime.fromtimestamp(int(oid[:8], 16), tz=timezone.utc)
    except (ValueError, TypeError):
        return None


def parse_list_html(html):
    m = NEXT_RX.search(html)
    if not m:
        raise RuntimeError("Khong tim thay __NEXT_DATA__ tren trang NOTICE")
    nd = json.loads(m.group(1))
    items = (((nd.get("props") or {}).get("pageProps") or {}).get("data") or {}).get("items") or []
    return nd.get("buildId"), items


def parse_detail(js):
    c = (js.get("pageProps") or {}).get("contents") or {}
    return c.get("title"), c.get("body") or ""


def to_item(meta, body_html, base):
    oid = meta["id"]
    pub = meta.get("publishedAt") or meta.get("createdAt")
    try:
        published = iso(datetime.fromisoformat(pub.replace("Z", "+00:00"))) if pub else None
    except ValueError:
        published = None
    if not published:
        t = objectid_time(oid)
        published = iso(t) if t else None
    text = html_to_text(body_html)
    return {
        "id": f"kq:{oid}",
        "source": "kq",
        "platform": "KQ Web",
        "account": "ateez.kqent.com",
        "tier": "official",
        "url": f"{base}/contents/{oid}",
        "title": meta.get("title") or "",
        "text": clip(text, 6000),
        "images": [],
        "published": published,
    }


def collect(cfg, http, known_ids, log=print):
    base = cfg["kq"]["base"]
    r = http.get(cfg["kq"]["list_url"], timeout=30)
    r.raise_for_status()
    build_id, metas = parse_list_html(r.text)
    log(f"[kq] {len(metas)} thong bao tren trang, buildId={build_id}")
    out = []
    for meta in metas:
        oid = meta.get("id")
        if not oid or f"kq:{oid}" in known_ids:
            continue
        body = ""
        try:
            d = http.get(f"{base}/_next/data/{build_id}/ko/contents/{oid}.json",
                         params={"id": oid}, timeout=30)
            d.raise_for_status()
            _, body = parse_detail(d.json())
        except Exception as e:  # noqa: BLE001
            log(f"[kq] loi doc bai {oid}: {e}")
        out.append(to_item(meta, body, base))
    log(f"[kq] {len(out)} thong bao moi")
    return out
