"""Du lieu mau cho test (mo phong phan hoi cua cac nguon)."""
import json

KQ_ITEMS = [
    {"id": "6b03a69e00027c0e6d14274b", "title": "ATEEZ(에이티즈) Drip (IÖN Ver.) 발매 안내", "publishedAt": "2026-11-23T05:00:00Z"},
    {"id": "6afd2e2dccee951db8944613", "title": "산(ATEEZ) <나인 투 식스 - Not Like Lovin Me> 음원 발매 안내", "publishedAt": "2026-11-18T09:00:00Z"},
    {"id": "6ae94a808d38027a8d6b8b65", "title": "2027 ATEEZ WORLD TOUR [ZERO TO ALL] IN INCHEON Ticket Sales Announcement", "publishedAt": "2026-11-03T02:44:00Z"},
    {"id": "6ae4517b1f4e424aa8b92617", "title": "ATEEZ HONGJOONG KBS2 'Music Bank' Appearance Update", "publishedAt": "2026-10-30T06:00:00Z"},
    {"id": "6ace4dd972022d1e98d3fbcc", "title": "ATEEZ 'VR CONCERT BOX' 예약 판매 안내", "publishedAt": "2026-10-14T03:00:00Z"},
    {"id": "6adf21ad92e3571155a044a6", "title": "ATEEZ(에이티즈) 공개방송 공통 유의사항 안내(261111 ver.)", "publishedAt": "2026-10-26T03:00:00Z"},
    {"id": "6a5e402b90a3af4ff75295bb", "title": "Notice Regarding the Protection of ATEEZ and Legal Action Against Malicious Posts", "publishedAt": "2026-07-21T03:00:00Z"},
]

KQ_BODIES = {
    "6b03a69e00027c0e6d14274b": "<p>안녕하세요.</p><p>KQ엔터테인먼트입니다.</p><p>금일(23일) 오후 2시에 ATEEZ(에이티즈) Drip (IÖN Ver.) 앨범이 전 음원 사이트에 공개되었습니다.</p><p>Melon ▶ melon.com</p>",
    "6afd2e2dccee951db8944613": "<p>금일 (18일) 오후 6시, 산이 참여한 SBS 수, 목 드라마 ‘나인 투 식스'의 OST 'Not Like Lovin Me'가 전 음원 사이트에 공개되었습니다.</p>",
    "6ae94a808d38027a8d6b8b65": (
        "<p>We would like to announce the ticket opening for 2027 ATEEZ WORLD TOUR [ZERO TO ALL] IN INCHEON.</p>"
        "<p>[Concert Overview]</p><p>- Performance Dates &amp; Times:</p>"
        "<p>January 22, 2027 (Fri) - 7:00 PM</p><p>January 23, 2027 (Sat) - 5:00 PM</p><p>January 24, 2027 (Sun) - 4:00 PM</p>"
        "<p>- Venue: NAVER ARENA at INSPIRE</p>"
        "<p>- Domestic &amp; Global Membership Survey Period: November 23, 2026 (Mon), 7:00 PM – November 30, 2026 (Mon), 11:59 PM (KST)</p>"
        "<p>- Global Membership Verification Period: December 1, 2026 (Tue), 2:00 PM – December 7, 2026 (Mon), 11:59 PM (KST)</p>"
        "<p>- Global Membership Presale: December 7, 2026 (Mon), 8:00 PM – 11:59 PM (KST)</p>"
        "<p>- General Sale: Opens December 8, 2026 (Tue), at 8:00 PM (KST)</p>"),
    "6ae4517b1f4e424aa8b92617": "<p>HONGJOONG was originally scheduled to appear on the show today but is unfortunately unable to participate due to health reasons.</p>",
    "6ace4dd972022d1e98d3fbcc": "<p>[발매 정보 안내]</p><p>- PRE-ORDER DATE (KST) : 2026.10.14 (수) 12:00 ~ 2026.10.20 (화) 23:59</p><p>- RELEASE DATE (KST) : 2027.02.17 (수)</p>",
    "6adf21ad92e3571155a044a6": "<p>ATEEZ [GOLDEN HOUR : Part.6] 전곡 개별곡 구매 내역서 (멜론) 확인</p><p>2026년 10월 7일 오후 11시 59분(KST)까지 ATINY 멤버십에 가입한 회원만</p>",
    "6a5e402b90a3af4ff75295bb": "<p>We continuously monitor the spread of false information.</p>",
}


def kq_list_html():
    nd = {"buildId": "BUILD123", "props": {"pageProps": {"data": {"items": KQ_ITEMS}}}}
    return f'<html><body><script id="__NEXT_DATA__" type="application/json">{json.dumps(nd)}</script></body></html>'


def kq_detail(oid):
    t = next(i["title"] for i in KQ_ITEMS if i["id"] == oid)
    return {"pageProps": {"contents": {"title": t, "body": KQ_BODIES[oid]}}}


YT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
 <entry>
  <yt:videoId>abc123</yt:videoId>
  <title>ATEEZ(에이티즈) - 'UP' Official MV</title>
  <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
  <published>2026-11-13T05:00:00+00:00</published>
  <media:group><media:thumbnail url="https://i.ytimg.com/vi/abc123/hqdefault.jpg" width="480" height="360"/><media:description>ATEEZ 15th mini album</media:description></media:group>
 </entry>
 <entry>
  <yt:videoId>def456</yt:videoId>
  <title>[WANTEEZ] EP.99 행복한 하루</title>
  <link rel="alternate" href="https://www.youtube.com/watch?v=def456"/>
  <published>2026-11-25T09:00:00+00:00</published>
  <media:group><media:thumbnail url="https://i.ytimg.com/vi/def456/hqdefault.jpg" width="480" height="360"/><media:description>Wooyoung Yunho</media:description></media:group>
 </entry>
</feed>"""


def news_xml(now_rfc):
    return f"""<?xml version="1.0"?><rss><channel>
<item><title>ATEEZ tops Billboard 200 again - Billboard</title><link>https://news.google.com/a1</link><pubDate>{now_rfc}</pubDate><source url="https://billboard.com">Billboard</source><description>ATEEZ ...</description></item>
<item><title>Some unrelated story about San Francisco - CNN</title><link>https://news.google.com/a2</link><pubDate>{now_rfc}</pubDate><source url="https://cnn.com">CNN</source></item>
<item><title>Old story - X</title><link>https://news.google.com/a3</link><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate></item>
</channel></rss>"""


X_USERS = {"data": [{"id": "1", "username": "ATEEZofficial"}, {"id": "2", "username": "kqent"},
                    {"id": "3", "username": "ATEEZUD"}]}


def x_timeline(uid):
    if uid == "1":
        return {"data": [{"id": "1001", "created_at": "2026-11-25T10:00:00.000Z",
                          "text": "[📸] 2026 ATEEZ SEASON'S GREETINGS Preview #ATEEZ https://t.co/img1",
                          "entities": {"urls": [{"url": "https://t.co/img1", "expanded_url": "https://x.com/ATEEZofficial/status/1001/photo/1", "media_key": "3_1"}]},
                          "attachments": {"media_keys": ["3_1"]}}],
                "includes": {"media": [{"media_key": "3_1", "type": "photo", "url": "https://pbs.twimg.com/media/a.jpg"}]},
                "meta": {"newest_id": "1001"}}
    if uid == "2":
        return {"data": [
            {"id": "2001", "created_at": "2026-11-25T08:00:00.000Z", "text": "xikers new single out now"},
            {"id": "2002", "created_at": "2026-11-25T09:00:00.000Z", "text": "ATEEZ(에이티즈) 2026 MAMA 출연 안내"}],
                "meta": {"newest_id": "2002"}}
    return {"data": [{"id": "3001", "created_at": "2026-11-25T11:00:00.000Z",
                      "text": "SAN Instagram story update 🐯 #ATEEZ #에이티즈 https://t.co/p",
                      "entities": {"urls": [{"url": "https://t.co/p", "expanded_url": "https://x.com/ATEEZUD/status/3001/photo/1"}]},
                      "attachments": {"media_keys": ["3_9"]}}],
            "includes": {"media": [{"media_key": "3_9", "type": "photo", "url": "https://pbs.twimg.com/media/b.jpg"}]},
            "meta": {"newest_id": "3001"}}
