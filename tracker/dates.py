"""Trich moc thoi gian (deadline, ngay dien...) tu than bai thong bao chinh thuc.
Mac dinh hieu la gio KST. Bo qua dong ghi mui gio My (EDT/EST/PDT...)."""
import re
from datetime import datetime

from .common import KST, iso

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
MON3 = {k[:3]: v for k, v in MONTHS.items()}

EN = re.compile(
    r"(?P<mon>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
    r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>20\d\d)"
    r"(?:\s*\([A-Za-z]{2,4}\.?\))?"
    r"(?:\s*[,\-–]?\s*(?:at\s*)?(?P<h>\d{1,2})(?::(?P<mi>\d{2}))?\s*(?P<ap>AM|PM|am|pm))?")
KO = re.compile(
    r"(?P<y>20\d\d)\s*년\s*(?P<mo>\d{1,2})\s*월\s*(?P<d>\d{1,2})\s*일(?:\s*\([^)]{1,3}\))?"
    r"(?:\s*(?P<ampm>오전|오후)?\s*(?P<h>\d{1,2})(?:\s*시|:(?P<mi>\d{2})|(?=\s*(?:AM|PM)))(?:\s*(?P<mi2>\d{1,2})\s*분)?)?"
    r"(?:\s*(?P<ap>AM|PM))?")
KO_NY = re.compile(
    r"(?<![\d년])(?<!년 )(?P<mo>\d{1,2})\s*월\s*(?P<d>\d{1,2})\s*일(?:\s*\([^)]{1,3}\))?"
    r"(?:\s*(?P<ampm>오전|오후)?\s*(?P<h>\d{1,2})(?:\s*시|:(?P<mi>\d{2})|(?=\s*(?:AM|PM)))(?:\s*(?P<mi2>\d{1,2})\s*분)?)?"
    r"(?:\s*(?P<ap>AM|PM))?")
DOT = re.compile(
    r"(?P<y>20\d\d)\s*[.\-/]\s*(?P<mo>\d{1,2})\s*[.\-/]\s*(?P<d>\d{1,2})\.?(?:\s*\([^)]{1,3}\))?"
    r"(?:\s*(?P<h>\d{1,2}):(?P<mi>\d{2}))?(?:\s*(?P<ap>AM|PM))?")
US_TZ = re.compile(r"\b(EDT|EST|ET|PDT|PST|PT|CDT|CST|BST|CET|CEST)\b")
END_TIME = re.compile(r"^\s*[–~\-]\s*(?P<h>\d{1,2}):(?P<mi>\d{2})\s*(?P<ap>AM|PM)?")


def _mk(y, mo, d, h=None, mi=None, ap=None, ampm=None):
    try:
        y, mo, d = int(y), int(mo), int(d)
        hour = int(h) if h else None
        minute = int(mi) if mi else 0
        if hour is not None:
            if (ap and ap.upper() == "PM") or ampm == "오후":
                if hour < 12:
                    hour += 12
            if ((ap and ap.upper() == "AM") or ampm == "오전") and hour == 12:
                hour = 0
        has_time = hour is not None
        dt = datetime(y, mo, d, hour or 0, minute, tzinfo=KST)
        if not has_time:
            dt = dt.replace(hour=23, minute=59)
        return dt, has_time
    except (ValueError, TypeError):
        return None, False


def find_datetimes(line):
    """Tra ve list (vi tri, datetime, co_gio) theo thu tu xuat hien."""
    found = []
    for m in EN.finditer(line):
        mon = MON3[m.group("mon")[:3].lower()]
        dt, ht = _mk(m.group("y"), mon, m.group("d"), m.group("h"), m.group("mi"), m.group("ap"))
        if dt:
            found.append((m.start(), m.end(), dt, ht))
    for m in KO.finditer(line):
        dt, ht = _mk(m.group("y"), m.group("mo"), m.group("d"), m.group("h"),
                     m.group("mi") or m.group("mi2"), m.group("ap"), m.group("ampm"))
        if dt:
            found.append((m.start(), m.end(), dt, ht))
    for m in DOT.finditer(line):
        if any(s <= m.start() < e for s, e, _, _ in found):
            continue
        dt, ht = _mk(m.group("y"), m.group("mo"), m.group("d"), m.group("h"), m.group("mi"), m.group("ap"))
        if dt:
            found.append((m.start(), m.end(), dt, ht))
    found.sort(key=lambda x: x[0])
    # "~ 11월 25일 ..." khong ghi nam: lay nam cua moc dung truoc
    if found:
        for m in KO_NY.finditer(line):
            if any(s_ <= m.start() < e_ for s_, e_, _, _ in found):
                continue
            prev = [f for f in found if f[0] < m.start()]
            if not prev:
                continue
            y = prev[-1][2].year + (1 if int(m.group("mo")) < prev[-1][2].month else 0)
            dt, ht = _mk(y, m.group("mo"), m.group("d"), m.group("h"),
                         m.group("mi") or m.group("mi2"), m.group("ap"), m.group("ampm"))
            if dt:
                found.append((m.start(), m.end(), dt, ht))
        found.sort(key=lambda x: x[0])
    keep = []
    for s_, e_, dt, ht in found:
        if US_TZ.search(line[e_:e_ + 12]):
            continue
        keep.append((s_, e_, dt, ht))
    return keep


def _label(line, spans):
    text = line
    for s, e, _, _ in sorted(spans, key=lambda x: -x[0]):
        text = text[:s] + " " + text[e:]
    text = re.sub(r"\((KST|Mon|Tue|Wed|Thu|Fri|Sat|Sun|월|화|수|목|금|토|일)\)", "", text)
    text = re.sub(r"[\s:：~\-–—|·,]+$", "", text)
    text = re.sub(r"^[\s\-–•*※▶■☑️✔]+", "", text)
    text = re.sub(r"\s\*.*$", "", text)  # bo ghi chu "*1일 1회..."
    text = re.sub(r"\s{2,}", " ", text).strip(" :-–~")
    return text[:90]


def extract_events(text, title=""):
    events = []
    seen = set()
    last_label = ""
    for raw in (text or "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        spans = find_datetimes(line)
        if not spans:
            if len(line) < 80 and not US_TZ.search(line):
                last_label = _label(line, []).strip("[]【】 ")
            continue
        same_day_end = None
        if len(spans) == 1:
            m = END_TIME.match(line[spans[0][1]:])
            if m:
                d0 = spans[0][2]
                h = int(m.group("h")) + (12 if m.group("ap") and m.group("ap").upper() == "PM" and int(m.group("h")) < 12 else 0)
                same_day_end = d0.replace(hour=h % 24, minute=int(m.group("mi")))
                s0, e0, d0_, ht0 = spans[0]
                spans = [(s0, e0 + m.end(), d0_, ht0)]
        prefix = _label(line[:spans[0][0]], [])
        label = prefix if len(prefix) >= 2 else (_label(line, spans) or last_label or title)
        start = spans[0][2]
        end = spans[1][2] if len(spans) > 1 and spans[1][2] > start else same_day_end
        key = (label, start, end)
        if key in seen:
            continue
        seen.add(key)
        events.append({
            "label": label,
            "start": iso(start),
            "end": iso(end) if end else None,
            "has_time": spans[0][3],
        })
    return events
