"""Phan loai tin bang luat (mien phi). Neu co ANTHROPIC_API_KEY, enrich_ai.py se ghi de ket qua."""
import re

CATEGORIES = {
    "schedule": "Schedule",
    "release": "Release",
    "tour": "Concert/Tour",
    "merch": "Album/Merch",
    "charts": "Charts & Records",
    "sns": "SNS",
    "video": "Video",
    "press": "Press",
    "official": "Official Announcement",
    "funfact": "Fun Facts",
}

# Thu tu quan trong: luat dau tien khop se thang.
RULES = [
    ("official", r"health|건강|부상|injur|legal action|법적|malicious|악성|cancell?ation|취소|hiatus|apolog|사과"),
    ("funfact", r"throwback|#?onthisday|\btmi\b|years ago|년 전|fun fact|recall(ed|s)|flashback|#tbt"),
    ("tour", r"ticket|티켓|presale|선예매|예매"),
    ("merch", r"pre-?order|예약 ?판매|\bmd\b|merch|photobook|포토북|dvd|playcode|membership kit|kit 판매|판매 안내|goods|굿즈|season'?s greetings|시즌 ?그리팅|concert box"),
    ("tour", r"world tour|\btour\b|concert|콘서트|투어|fan ?meeting|팬미팅|atiny zone|encore|setlist|soundcheck|arena|stadium|dome"),
    ("charts", r"chart|차트|billboard|빌보드|hanteo|한터|oricon|오리콘|\B#1\b|1위|no\. ?1|\brecords?\b|신기록|certif|first win|1st win"),
    ("release", r"발매|release|\bmv\b|m/v|music video|teaser|티저|\bost\b|comeback|컴백|tracklist|트랙리스트|concept photo|콘셉트|pre-?save|remix|single|album|앨범|highlight medley|spoiler"),
    ("schedule", r"appearance|출연|schedule|스케줄|방송|music bank|뮤직뱅크|inkigayo|인기가요|m ?countdown|엠카|show champion|쇼챔|music core|음악중심|the show|radio|라디오|airport|공항|출국|입국|fansign|팬사인|broadcast|공개방송|\blive\b|라이브|variety|예능|interview|인터뷰|magazine|화보|pictorial"),
    ("charts", r"spotify|melon|멜론|streams|million views|누적"),
    ("sns", r"instagram|insta|story|스토리|weverse|toktoq|톡톡|bubble|버블|tiktok|틱톡|threads|selca|셀카"),
]
_COMPILED = [(c, re.compile(p, re.I)) for c, p in RULES]


def classify(item):
    """Tra ve ma loai tin cho item (dict co title/text/source/account)."""
    if item.get("category_hint"):
        return item["category_hint"]
    if item.get("source") == "kq":
        blob = item.get("title", "")  # tieu de KQ rat co quy luat; than bai co link Melon... gay nhieu
    else:
        blob = f"{item.get('title', '')}\n{item.get('text', '')[:600]}"
    for cat, rx in _COMPILED:
        if rx.search(blob):
            return cat
    src = item.get("source")
    if src == "youtube":
        return "video"
    if src == "news":
        return "press"
    if src == "x":
        return "sns"
    return "official"


def member_patterns(members):
    pats = []
    for m in members:
        en, ko = m["en"], m["ko"]
        if en == "San":
            en_rx = r"\bSAN\b|\bSan\b(?! (?:Francisco|Diego|Jose|Antonio|Juan))|#San\b"
            ko_rx = r"산\s*\(|#산\b|(?<![가-힣])산(?=이|은|의|과|\s*\(ATEEZ)"
        else:
            en_rx = rf"\b{en}\b"
            ko_rx = re.escape(ko)
        pats.append((en, re.compile(f"(?:{en_rx})|(?:{ko_rx})", re.I if en != "San" else 0)))
    return pats


def detect_members(text, pats):
    found = [name for name, rx in pats if rx.search(text or "")]
    return found


def is_about_group(text, cfg, pats):
    t = text or ""
    if any(k.lower() in t.lower() for k in cfg["group_keywords"]):
        return True
    return bool(detect_members(t, pats))
