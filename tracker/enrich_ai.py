"""Tuy chon: neu co ANTHROPIC_API_KEY thi dung Claude de
- tom tat + dich tieu de/noi dung sang tieng Viet
- phan loai lai, nhan dien thanh vien
- trich moc thoi gian (deadline, ngay dien...) chuan hon luat.
Khong co key -> bo qua, trang van chay voi phan loai bang luat."""
import json
import os

from .classify import CATEGORIES

API = "https://api.anthropic.com/v1/messages"

PROMPT = """Bạn xử lý tin tức về nhóm nhạc K-pop ATEEZ cho một trang theo dõi cá nhân của fan người Việt.
Thành viên: Hongjoong, Seonghwa, Yunho, Yeosang, San, Mingi, Wooyoung, Jongho.
Loại tin hợp lệ (dùng đúng mã): {cats}
- funfact: chuyện cũ fan đào lại, TMI, trích phỏng vấn trước đây.
- sns: cập nhật mạng xã hội của thành viên/nhóm (story, post IG, Weverse, TOKTOQ...).

Với MỖI tin dưới đây, trả về một object JSON:
{{"id": "<giữ nguyên id>", "category": "<mã>", "members": ["<tên tiếng Anh>"...] (rỗng nếu cả nhóm hoặc không rõ),
 "title_vi": "<tiêu đề ngắn bằng tiếng Việt, tối đa 90 ký tự>",
 "summary_vi": "<tóm tắt 1-2 câu tiếng Việt, giữ nguyên tên riêng/tên bài hát; nêu ngày giờ quan trọng nếu có>",
 "events": [{{"label": "<tên mốc, tiếng Việt, ngắn>", "start": "<ISO 8601 có múi giờ>", "end": "<ISO hoặc null>"}}]}}
"events" chỉ gồm các mốc trong TƯƠNG LAI hoặc đang diễn ra được nêu rõ trong tin (hạn đăng ký, mở bán vé, presale, phát hành, lịch diễn, lên sóng...). Giờ không ghi múi giờ thì hiểu là KST (+09:00). Không bịa mốc.
Ngày hiện tại: {today}.
Chỉ trả về một mảng JSON, không thêm chữ nào khác.

TIN:
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
    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        payload = [{"id": it["id"], "nguon": f"{it['account']} ({it['platform']})", "tieu_de": it["title"],
                    "noi_dung": it["text"][:2500], "ngay_dang": it["published"]} for it in batch]
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
            log(f"[ai] loi: {e}")
            continue
        for it in batch:
            o = res.get(it["id"])
            if not o:
                continue
            if o.get("category") in CATEGORIES and not it.get("category_hint"):
                it["category"] = o["category"]
            if isinstance(o.get("members"), list):
                it["members"] = [m for m in o["members"] if isinstance(m, str)][:8]
            for k in ("title_vi", "summary_vi"):
                if o.get(k):
                    it[k] = str(o[k])[:400]
            evs = [e for e in (o.get("events") or []) if isinstance(e, dict) and e.get("start")]
            if evs:
                it["events"] = [{"label": str(e.get("label", ""))[:90], "start": e["start"],
                                 "end": e.get("end"), "has_time": "T" in e["start"]} for e in evs][:12]
            it["ai"] = True
            done += 1
    log(f"[ai] da xu ly {done}/{len(todo)} tin")
    return done
