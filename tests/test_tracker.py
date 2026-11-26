import json
import os
import shutil
import sys
from email.utils import format_datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests import fixtures as F  # noqa: E402
from tracker import collect_feeds, collect_kq, collect_x, common  # noqa: E402
from tracker.classify import classify, detect_members, member_patterns  # noqa: E402
from tracker.dates import extract_events  # noqa: E402

CFG = common.load_config()
PATS = member_patterns(CFG["members"])


class Resp:
    def __init__(self, text=None, js=None, status=200):
        self.text = text if text is not None else json.dumps(js)
        self._js = js
        self.status_code = status
        self.ok = status < 400

    def json(self):
        return self._js if self._js is not None else json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class FakeHTTP:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(url)
        if url.endswith("/tag/NOTICE"):
            return Resp(F.kq_list_html())
        if "/_next/data/" in url:
            oid = url.rsplit("/", 1)[1].replace(".json", "")
            return Resp(js=F.kq_detail(oid))
        if "youtube.com/feeds" in url:
            return Resp(F.YT_XML)
        if "news.google.com" in url:
            return Resp(F.news_xml(format_datetime(common.now_utc())))
        if url.endswith("/users/by"):
            return Resp(js=F.X_USERS)
        if "/tweets" in url:
            return Resp(js=F.x_timeline(url.split("/users/")[1].split("/")[0]))
        raise AssertionError(url)

    def post(self, *a, **k):
        return Resp(js={})


def test_kq_parse():
    items = collect_kq.collect(CFG, FakeHTTP(), set(), log=lambda *_: None)
    assert len(items) == len(F.KQ_ITEMS)
    t = next(i for i in items if "Ticket" in i["title"])
    assert "NAVER ARENA" in t["text"]
    assert t["url"].endswith("/contents/6ae94a808d38027a8d6b8b65")
    # khong doc lai bai da co
    assert collect_kq.collect(CFG, FakeHTTP(), {f"kq:{i['id']}" for i in F.KQ_ITEMS}, log=lambda *_: None) == []


def test_kq_html_fallback():
    class H(FakeHTTP):
        def get(self, url, params=None, headers=None, timeout=None):
            if "/_next/data/" in url:
                return Resp(js={"pageProps": {"__N_REDIRECT": "/"}})
            if "/contents/" in url:
                oid = url.rsplit("/", 1)[1]
                nd = {"props": F.kq_detail(oid)}
                return Resp(f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(nd)}</script>')
            return super().get(url, params, headers, timeout)
    items = collect_kq.collect(CFG, H(), set(), log=lambda *_: None)
    assert all(i["text"] for i in items)


def test_objectid_time():
    assert collect_kq.objectid_time("6ac915ceb899027df4664814").strftime("%Y-%m-%d") == "2026-10-09"


@pytest.mark.parametrize("title,cat", [
    ("ATEEZ(에이티즈) Drip (IÖN Ver.) 발매 안내", "release"),
    ("2027 ATEEZ WORLD TOUR [ZERO TO ALL] IN INCHEON Ticket Sales Announcement", "tour"),
    ("2027 ATEEZ WORLD TOUR [ZERO TO ALL] Tour Announcement", "tour"),
    ("ATEEZ HONGJOONG KBS2 'Music Bank' Appearance Update", "schedule"),
    ("ATEEZ 'VR CONCERT BOX' 예약 판매 안내", "merch"),
    ("ATEEZ(에이티즈) 공개방송 공통 유의사항 안내(261111 ver.)", "schedule"),
    ("Notice Regarding the Protection of ATEEZ and Legal Action Against Malicious Posts", "official"),
    ("ATEEZ HONGJOONG Health Status and Schedule Update", "official"),
    ("ATEEZ 8th Anniversary PHOTOBOOK Blue Drift 예약 판매 안내", "merch"),
    ("Pre-save/add 'GOLDEN HOUR : Part.6'", "release"),
    ("[OFFICIAL MD 판매 안내] 2026 ATEEZ FANMEETING", "merch"),
])
def test_classify_kq_titles(title, cat):
    assert classify({"source": "kq", "title": title, "text": "Melon ▶ melon.com"}) == cat


def test_classify_x_and_news():
    assert classify({"source": "x", "title": "UP debuts at #1 on Billboard 200", "text": ""}) == "charts"
    assert classify({"source": "x", "title": "Throwback to 2019 when Mingi said", "text": ""}) == "funfact"
    assert classify({"source": "x", "title": "SAN Instagram story update", "text": ""}) == "sns"
    assert classify({"source": "youtube", "title": "[WANTEEZ] EP.99", "text": ""}) == "video"


def test_members():
    assert detect_members("산(ATEEZ) <나인 투 식스>", PATS) == ["San"]
    assert detect_members("Trip to San Francisco", PATS) == []
    assert set(detect_members("HONGJOONG and WOOYOUNG", PATS)) == {"Hongjoong", "Wooyoung"}
    assert detect_members("민기(ATEEZ) OST", PATS) == ["Mingi"]


def test_events_from_ticket_notice():
    text = common.html_to_text(F.KQ_BODIES["6ae94a808d38027a8d6b8b65"])
    evs = extract_events(text, "Ticket")
    labels = {e["label"] for e in evs}
    assert "Global Membership Presale" in labels
    pre = next(e for e in evs if e["label"] == "Global Membership Presale")
    assert pre["start"] == "2026-12-07T11:00:00Z" and pre["end"] == "2026-12-07T14:59:00Z"
    gen = next(e for e in evs if e["label"].startswith("General Sale"))
    assert gen["start"] == "2026-12-08T11:00:00Z"
    assert any(e["start"] == "2027-01-22T10:00:00Z" for e in evs)


def test_youtube_and_news():
    yt = collect_feeds.collect_youtube(CFG, FakeHTTP(), set(), log=lambda *_: None)
    assert [i["id"] for i in yt] == ["yt:abc123", "yt:def456"] and yt[0]["images"]
    news = collect_feeds.collect_news(CFG, FakeHTTP(), set(), log=lambda *_: None)
    titles = [n["title"] for n in news]
    assert "ATEEZ tops Billboard 200 again" in titles
    assert not any("Old story" in t for t in titles)
    assert len([t for t in titles if "Billboard" in t]) == 1  # gop trung giua cac truy van


def test_x(monkeypatch):
    monkeypatch.setenv("X_BEARER_TOKEN", "t")
    cfg = json.loads(json.dumps(CFG))
    cfg["x"]["accounts"] = [{"username": "ATEEZofficial", "tier": "official"},
                            {"username": "kqent", "tier": "official", "only_ateez": True},
                            {"username": "ATEEZUD", "tier": "fan"}]
    from tracker.classify import is_about_group
    state = {}
    items = collect_x.collect(cfg, FakeHTTP(), state, log=lambda *_: None,
                              about_group=lambda t: is_about_group(t, cfg, PATS))
    ids = [i["id"] for i in items]
    assert "x:2001" not in ids and "x:2002" in ids  # kqent: chi giu bai ve ATEEZ
    off = next(i for i in items if i["id"] == "x:1001")
    assert off["images"] == ["https://pbs.twimg.com/media/a.jpg"] and "t.co" not in off["text"]
    assert state["x_since"]["ATEEZofficial"] == "1001"


def test_full_run(tmp_path, monkeypatch):
    """Chay tron mot luot voi HTTP gia, ghi vao thu muc tam."""
    root = tmp_path / "repo"
    shutil.copytree(common.ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__", "docs"))
    os.makedirs(root / "docs" / "data")
    from tracker import run
    monkeypatch.setattr(run, "ITEMS_PATH", str(root / "docs/data/items.json"))
    monkeypatch.setattr(run, "DATA_DIR", str(root / "docs/data"))
    monkeypatch.setattr(run, "STATE_PATH", str(root / "state.json"))
    monkeypatch.setattr(run, "session", lambda: FakeHTTP())
    monkeypatch.setenv("X_BEARER_TOKEN", "t")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DISCORD_WEBHOOK", raising=False)
    monkeypatch.setattr(sys, "argv", ["run", "--sources", "kq,youtube,news,x"])
    run.main()
    data = json.load(open(root / "docs/data/items.json", encoding="utf-8"))
    assert len(data["items"]) >= 10
    evs = json.load(open(root / "docs/data/events.json", encoding="utf-8"))["events"]
    assert any(e["label"] == "Global Membership Presale" for e in evs)
    # chay lai: khong nhan doi
    run.main()
    assert len(json.load(open(root / "docs/data/items.json", encoding="utf-8"))["items"]) == len(data["items"])


def test_similar_titles():
    from tracker.run import similar
    assert similar("Wooyoung's birthday post passes 270,000 likes",
                   "Wooyoung Turns 27 as His Birthday Post Passes 270,000 Likes")
    assert not similar("ATEEZ tops Hanteo weekly trend chart", "ATEEZ tops Circle chart")
    assert not similar("UP passes 10 million views", "UP passes 20 million views")


def test_image_dedupe():
    from PIL import Image, ImageDraw
    from tracker.images import dedupe_images, dhash
    def pic(seed):
        im = Image.new("RGB", (200, 260), "white"); d = ImageDraw.Draw(im)
        for k in range(6):
            x0, y0 = (seed * 37 + k * 29) % 120, (seed * 53 + k * 41) % 160
            d.rectangle([x0, y0, x0 + 30 + k * 10, y0 + 40 + k * 12], fill=(k * 40, 80, 200 - k * 30))
        return im
    import random
    rnd = random.Random(7)
    noise = Image.new("L", (200, 260)); noise.putdata([rnd.randint(0, 255) for _ in range(200 * 260)])
    a, b = dhash(pic(1)), dhash(noise)
    a2 = dhash(pic(1).resize((150, 195)))  # cung anh, kich thuoc khac
    story = {"id": "x:1", "source": "x", "tier": "fan", "images": ["u1"], "img_hash": [a], "members": ["San"],
             "summary_en": "San posted a new Instagram story.", "text": "#CHOISAN instagram story", "published": "2026-11-26T11:51:00Z"}
    detail = {"id": "x:2", "source": "x", "tier": "fan", "images": ["u2", "u3"], "img_hash": [a2, a2], "members": ["San", "Wooyoung"],
              "summary_en": "San posted a photo with Wooyoung under the hashtags #OURLOVESHINEFORWOOYOUNG as part of the birthday celebration.",
              "text": "SAN with WOOYOUNG", "published": "2026-11-26T11:48:00Z"}
    other = {"id": "x:3", "source": "x", "tier": "fan", "images": ["u4"], "img_hash": [b], "members": [], "text": "x", "published": "2026-11-26T10:00:00Z"}
    out = dedupe_images([story, detail, other], log=lambda *_: None)
    ids = [i["id"] for i in out]
    assert ids == ["x:2", "x:3"]
    assert out[0]["images"] == ["u2"]  # anh lap trong cung mot tin cung bi bo
