[English](README.md) | **Tiếng Việt**

<p align="center">
  <img src="https://img.shields.io/badge/🤖_100%25_AI_Developed-7C3AED?style=for-the-badge" alt="100% AI Developed" />
  <img src="https://img.shields.io/badge/✨_100%25_AI_Generated-00D4AA?style=for-the-badge" alt="100% AI Generated" />
</p>

# AI Daily News 🤖

Hệ thống tự động tổng hợp tin tức AI mỗi ngày, xuất bản dưới dạng trang tĩnh trên GitHub Pages.
Giao diện song ngữ Việt / Anh, lấy tin từ các nguồn tiếng Anh và tiếng Việt.

**Trang web:** https://linhfishCR7.github.io/ai-daily-news/

## Tính năng

- Lấy tin AI từ các nguồn RSS tiếng Anh và tiếng Việt
- Lọc đúng chủ đề AI, chỉ giữ tin trong 48 giờ gần nhất, loại tin trùng
- Phân loại: Tin nổi bật, Sản phẩm mới, Gọi vốn & M&A, Nghiên cứu, Thị trường & Chính sách, Tin khác
- Tạo bản tin HTML kiểu báo giấy (dễ chụp màn hình trên điện thoại)
- Lưu mọi số cũ trong `archive/`, có trang lưu trữ (lịch nhiệt, dòng thời gian, tìm kiếm)
- PWA cài được lên màn hình chính, xem được khi offline
- Tự chạy mỗi ngày lúc **07:00 giờ Việt Nam** (00:00 UTC) bằng GitHub Actions

## Cách hoạt động

```
GitHub Actions (cron hằng ngày)
  └─ scripts/fetch_news.py  → data/categorized_news.json
  └─ scripts/generate.py    → lưu index.html cũ vào archive/YYYYMMDD.html
                            → tạo index.html mới
                            → tạo lại data/archive_manifest.json
  └─ git commit & push      → GitHub Pages phục vụ trang
```

Nếu không nguồn nào trả về tin, `fetch_news.py` báo lỗi và workflow dừng lại,
nên bản tin hôm trước vẫn giữ nguyên thay vì đăng dữ liệu giả.

## Cấu trúc dự án

```
ai-daily-news/
├── index.html                 # Bản tin hôm nay (trang chủ, được tạo tự động)
├── archive/                   # Các số cũ, mỗi ngày một file (tự động)
├── data/
│   ├── categorized_news.json  # Tin hôm nay đã phân loại (tự động)
│   └── archive_manifest.json  # Danh mục các số cho trang lưu trữ (tự động)
├── assets/style.css           # Giao diện
├── icons/                     # Icon ứng dụng (scripts/make_icons.py)
├── manifest.webmanifest       # PWA manifest
├── sw.js                      # Service worker
├── scripts/
│   ├── fetch_news.py          # Lấy, lọc, bỏ trùng và phân loại tin
│   ├── generate.py            # Tạo HTML, lưu trữ, tạo manifest
│   ├── send_feishu.py         # Gửi Feishu (tùy chọn, đang tắt, xem SETUP.md)
│   ├── serve.py               # Server xem thử trong mạng LAN
│   ├── make_icons.py          # Tạo icon
│   └── run.sh                 # Chạy toàn bộ quy trình trên máy
└── .github/workflows/daily.yml
```

## Nguồn tin

| Tiếng Anh | Tiếng Việt (lọc theo chủ đề AI) |
|---|---|
| TechCrunch (AI) | VnExpress (Khoa học - Công nghệ) |
| The Verge (AI) | Tuổi Trẻ (Nhịp sống số) |
| VentureBeat (AI, qua Google News) | Dân trí (Công nghệ) |
| OpenAI News | GenK |
| Google DeepMind Blog | |
| Google AI Blog | |
| Hacker News (AI/LLM/GPT, từ 20 điểm) | |

Danh sách nguồn nằm trong `NEWS_SOURCES` ở [scripts/fetch_news.py](scripts/fetch_news.py).

## Chạy trên máy

```bash
pip install -r scripts/requirements.txt
cd scripts
python fetch_news.py
python generate.py
python serve.py        # mở http://localhost:8000/
```

## Tự triển khai bản riêng

1. Fork repository này
2. Bật GitHub Actions và GitHub Pages (deploy từ nhánh `main`, thư mục gốc)
3. Sửa URL trang trong README và `SITE_URL` trong `scripts/send_feishu.py`
4. Workflow chạy mỗi ngày; có thể chạy tay tại **Actions → Run workflow**

## Giấy phép

MIT
