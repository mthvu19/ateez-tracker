"""Phan dung chung: cau hinh, HTTP, thoi gian, doc/ghi du lieu."""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "docs", "data")
ITEMS_PATH = os.path.join(DATA_DIR, "items.json")
STATE_PATH = os.path.join(ROOT, "state.json")

KST = timezone(timedelta(hours=9))
VN = timezone(timedelta(hours=7))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")


def load_config():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(s):
    """Doc ISO 8601; chuoi khong co mui gio duoc hieu la gio KST."""
    if not s:
        return None
    try:
        d = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=KST)
    return d


def session():
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
    return s


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


class _Text(HTMLParser):
    BLOCK = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag in ("td", "th"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(html):
    p = _Text()
    p.feed(html or "")
    text = "".join(p.parts).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    out = []
    for ln in lines:
        if ln or (out and out[-1]):
            out.append(ln)
    return "\n".join(out).strip()


def clip(text, n):
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"
