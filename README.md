# ATEEZ Tracker

Trang theo dõi tin ATEEZ cá nhân: gom thông báo chính thức, lịch, release, concert, chart… về một chỗ.

- **Trang web:** `https://mthvu19.github.io/ateez-tracker/` (sau khi bật GitHub Pages)
- **Tự cập nhật** bằng GitHub Actions, không cần máy tính bật.

## Nguồn dữ liệu

| Nguồn | Tần suất | Chi phí |
|---|---|---|
| KQ Web – ateez.kqent.com (tag NOTICE) | 1 giờ/lần | Miễn phí |
| YouTube – kênh ATEEZ (RSS) | 1 giờ/lần | Miễn phí |
| Báo – Google News (ATEEZ / 에이티즈, tiếng Anh, Hàn, Việt) | 1 giờ/lần | Miễn phí |
| X – @ATEEZofficial, @ATEEZofficialjp, @kqent (chỉ giữ bài về ATEEZ), @ATEEZstaff, @ATEEZUD, @1024updates, @ateez_charts | 10:00 và 18:00 giờ VN | ~0,005 USD/bài đọc |

Muốn thêm hoặc bớt nguồn thì sửa `config.json`.

## Cài đặt (làm 1 lần)

1. **Tạo repo** `ateez-tracker` trên GitHub rồi đẩy toàn bộ thư mục này lên nhánh `main`.
2. **Bật GitHub Pages:** Settings → Pages → *Deploy from a branch* → `main` / `/docs`.
3. **Thêm secrets** (Settings → Secrets and variables → Actions → *New repository secret*):

   | Secret | Bắt buộc? | Dùng để |
   |---|---|---|
   | `X_BEARER_TOKEN` | Có (để lấy tin X) | Bearer Token trong X Developer Console |
   | `DISCORD_WEBHOOK` | Không | Gửi tin chính thức mới và nhắc hạn trong 24 giờ lên Discord. Có thể dùng chung webhook với Fansign Radar hoặc tạo kênh mới |
   | `ANTHROPIC_API_KEY` | Không | Tóm tắt và dịch tiếng Việt, phân loại và trích mốc thời gian chính xác hơn. Không có key thì trang vẫn chạy, chỉ hiện tiêu đề/đoạn trích gốc |

4. **Chạy lần đầu:** tab Actions → *Update (KQ Web, YouTube, News)* → *Run workflow*. Sau đó chạy *Update X* nếu đã có token.

### X API: giữ chi phí thấp
- Mua credit trong developer.x.com, **không bật auto-recharge**, đặt **spending limit** (ví dụ 10 USD/tháng).
- Mỗi tài khoản lấy tối đa 20 bài mới/lượt, bỏ retweet và reply (`config.json → x.max_per_account`).
- Mỗi lượt chạy in ra log số bài đã đọc và chi phí ước tính.

## Fun Facts thủ công

Thêm vào `docs/data/funfacts.json`:

```json
{"facts": [
  {"kind": "Throwback", "text": "Nội dung…", "meta": "Mingi · 2019", "url": "https://…", "members": ["Mingi"]}
]}
```

`kind` gợi ý: `Throwback`, `TMI`, `Interview`. Ngoài ra, bài của tài khoản fan được nhận là throwback/TMI sẽ tự xuất hiện ở mục Fun Facts.

## Cấu trúc

```
config.json              danh sách nguồn, thành viên
tracker/                 code thu thập (Python)
  collect_kq.py          KQ Web (JSON nội bộ của trang)
  collect_feeds.py       YouTube RSS, Google News RSS
  collect_x.py           X API v2
  classify.py            phân loại tin + nhận diện thành viên (luật, miễn phí)
  dates.py               trích mốc thời gian trong thông báo (giờ KST)
  enrich_ai.py           (tuỳ chọn) Claude: tóm tắt tiếng Việt, phân loại, mốc thời gian
  notify.py              Discord
  run.py                 chạy một lượt
docs/                    trang web (GitHub Pages)
  data/items.json        tin đã thu thập
  data/events.json       các mốc thời gian (Highlight, Calendar, Upcoming)
state.json               trạng thái (since_id của X, nhắc hạn đã gửi)
tests/                   kiểm thử với dữ liệu mẫu: python -m pytest
```

## Lưu ý
- Repo public thì dữ liệu trong `docs/data` cũng công khai (đều là tin công khai). Trang có `noindex` nên không lên Google. Secrets luôn được giữ kín.
- GitHub tự tắt lịch chạy nếu repo không có hoạt động 60 ngày. Các commit dữ liệu tự động giữ repo luôn hoạt động.
- Nếu ô *Sources* trên trang báo lỗi KQ Web liên tục, có thể trang KQ đang chặn máy chủ GitHub. Khi đó báo lại để đổi cách lấy.
