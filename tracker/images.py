"""Gop anh trung: cung mot anh do nhieu tai khoan dang lai (URL khac nhau).
Dung dHash 64-bit (anh thu nho 9x8 muc xam) -> so sanh khoang cach Hamming."""
from io import BytesIO

from .common import parse_iso

THRESHOLD = 6  # <= 6/64 bit khac nhau -> coi la cung anh


def dhash(img):
    g = img.convert("L").resize((9, 8))
    px = list(g.getdata())
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (1 if px[row * 9 + col] > px[row * 9 + col + 1] else 0)
    return f"{bits:016x}"


def hamming(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def same(a, b):
    return a is not None and b is not None and hamming(a, b) <= THRESHOLD


def _small(url):
    if "pbs.twimg.com/media/" in url and "?" not in url:
        return url + "?name=small"
    return url


def fetch_hash(http, url):
    from PIL import Image
    r = http.get(_small(url), timeout=20)
    r.raise_for_status()
    return dhash(Image.open(BytesIO(r.content)))


def annotate(items, http, log=print):
    """Tinh hash cho anh cua cac tin chua co (luu vao item['img_hash'], cung thu tu voi images)."""
    n = 0
    for it in items:
        imgs = it.get("images") or []
        if not imgs or it.get("source") == "youtube" or len(it.get("img_hash") or []) == len(imgs):
            continue
        hs = []
        for u in imgs:
            try:
                hs.append(fetch_hash(http, u))
            except Exception:  # noqa: BLE001
                hs.append(None)
        it["img_hash"] = hs
        n += 1
    if n:
        log(f"[img] tinh hash anh cho {n} tin")


def _dedupe_within(it):
    imgs, hs = it.get("images") or [], it.get("img_hash") or []
    if len(hs) != len(imgs):
        return
    keep_i, keep_h = [], []
    for u, h in zip(imgs, hs):
        if h is not None and any(same(h, k) for k in keep_h):
            continue
        keep_i.append(u)
        keep_h.append(h)
    it["images"], it["img_hash"] = keep_i, keep_h


def _score(it):
    """Uu tien tin co caption chi tiet hon, nhieu thanh vien hon, nguon chinh thuc."""
    text = (it.get("summary_en") or "") + " " + (it.get("text") or "")
    return (len(it.get("members") or []) * 40 + len(text)
            + (200 if it.get("tier") == "official" else 0))


def _covers(a, b):
    """Moi anh cua a deu co trong b."""
    return all(any(same(x, y) for y in b) for x in a)


def dedupe_images(items, days=3, log=print):
    """Hai tin co cung bo anh (mot ben chua tron ben kia) trong `days` ngay -> giu tin tot hon."""
    for it in items:
        _dedupe_within(it)
    cand = [it for it in items if it.get("img_hash") and all(h is not None for h in it["img_hash"])
            and it.get("source") != "youtube"]
    groups = []
    for it in cand:
        ts = parse_iso(it.get("published"))
        for g in groups:
            ref = g[0]
            rts = parse_iso(ref.get("published"))
            if ts and rts and abs((ts - rts).total_seconds()) > days * 86400:
                continue
            if any(_covers(it["img_hash"], o["img_hash"]) or _covers(o["img_hash"], it["img_hash"]) for o in g):
                g.append(it)
                break
        else:
            groups.append([it])
    drop = set()
    for g in groups:
        if len(g) > 1:
            best = max(g, key=_score)
            drop |= {id(o) for o in g if o is not best}
    if drop:
        log(f"[img] bo {len(drop)} tin trung anh")
    return [it for it in items if id(it) not in drop]
