# 🎓 Bot Thống Kê Điểm - Telegram Bot

Bot Telegram hỗ trợ trợ giảng trong việc báo cáo tình hình học và nhập điểm kiểm tra hàng loạt vào Google Sheets.

## ✨ Tính Năng Chính

### 📋 Báo Cáo Tình Hình Học
- Chọn lớp và ngày buổi học
- Nhập nội dung báo cáo theo format tự do
- Bot tự động parse và format theo mẫu chuẩn
- Gửi báo cáo vào group Telegram của lớp
- Tự động tính số ngày trễ hạn

### 💯 Nhập Điểm Kiểm Tra
- Nhập điểm hàng loạt từ text block
- Tự động tìm học sinh trong Google Sheets
- Batch update điểm vào sheet
- Xử lý fuzzy matching tên tiếng Việt
- Báo cáo chi tiết kết quả xử lý

## 🚀 Cài Đặt

### Yêu Cầu Hệ Thống
- Python 3.11 trở lên
- Telegram Bot Token
- Google Service Account credentials

### 1. Cài Đặt Dependencies

```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu Hình Environment Variables

Tạo file `.env` ở thư mục root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### 3. Cấu Hình Google Sheets

1. **Tạo Google Service Account:**
   - Truy cập [Google Cloud Console](https://console.cloud.google.com/)
   - Tạo project mới hoặc chọn project có sẵn
   - Enable Google Sheets API và Google Drive API
   - Tạo Service Account và download credentials.json

2. **Đặt file credentials.json:**
   ```bash
   # File đã có sẵn trong project, cần cập nhật với credentials thật
   # QUAN TRỌNG: KHÔNG commit file này lên public repo!
   ```

3. **Chia sẻ Google Sheet:**
   - Mở Google Sheet cần quản lý
   - Chia sẻ với email của Service Account (có trong credentials.json)
   - Cấp quyền "Editor"

### 4. Cấu Hình Telegram Bot

1. **Tạo Bot với BotFather:**
   - Chat với [@BotFather](https://t.me/botfather)
   - Tạo bot mới: `/newbot`
   - Lấy token và thêm vào file `.env`

2. **Thêm Bot vào Groups:**
   - Thêm bot vào các group lớp học
   - Cấp quyền "Send Messages"
   - Lấy chat_id của groups (có thể dùng bot khác hoặc API)

## 🏃‍♂️ Chạy Bot

### Chạy Bot Thông Thường

```bash
# Chạy bot
python main.py
```

### Chạy Bot với Auto-Reload (Khuyến Nghị Khi Phát Triển)

```bash
# Bot sẽ tự động restart khi có thay đổi file .py
python run_with_autoreload.py
```

**Lợi ích của Auto-Reload:**
- ✅ Tự động restart bot khi save file Python
- ✅ Không cần dừng và chạy lại thủ công
- ✅ Tiết kiệm thời gian khi đang phát triển/sửa lỗi
- ✅ Thay đổi code được áp dụng ngay lập tức

Bot sẽ bắt đầu hoạt động và hiển thị log. Nhấn Ctrl+C để dừng.

## 📖 Hướng Dẫn Sử Dụng

### Lệnh Cơ Bản
- `/start` - Bắt đầu sử dụng bot
- `/menu` - Hiển thị menu chính  
- `/help` - Xem hướng dẫn chi tiết
- `/cancel` - Hủy thao tác hiện tại

### Báo Cáo Tình Hình Học

1. **Chọn `/menu` → "📋 Báo cáo tình hình học"**
2. **Chọn lớp từ danh sách**
3. **Chọn ngày:**
   - "Dùng ngày đề xuất" (buổi học gần nhất)
   - "Nhập ngày khác" theo format dd/mm/yyyy
4. **Nhập nội dung báo cáo:**
   ```
   Vắng: 2 (Thảo, Diệp)
   Không làm bài tập: 1 (Nam)
   Thiếu bài tập: 3 (Dũng, Trung, Hân) - thiếu BTVN bài 3
   Nội dung bài học:
   Chữa bài tập 1, 2
   Học bài mới: Phương trình bậc nhất
   Bài tập về nhà:
   Làm bài 5, 6, 7 trang 25
   ```
5. **Xem preview và xác nhận gửi**

### Nhập Điểm Kiểm Tra

1. **Chọn `/menu` → "💯 Nhập điểm kiểm tra"**
2. **Chọn lớp từ danh sách**
3. **Dán block điểm:**
   ```
   💯Điểm bài kiểm tra ngày 🗓️17/01/2026 :
   Trung 0
   Trí Dũng 9
   Phương Nam 8.75
   Quang Dũng 9.5
   ```
4. **Bot tự động xử lý và báo cáo kết quả**

## 📊 Cấu Trúc Dữ Liệu

### Lịch Học
```python
# Lớp 6.1, 6.2: Thứ 2 và Thứ 4, 18:00-19:30
# Lớp 7.1: Thứ 3 và Thứ 5, 18:00-19:30  
# Lớp 7.2: Thứ 7 và Chủ nhật, 16:30-18:00
# Lớp 8.1: Thứ 2 và Thứ 4, 19:30-21:00
# Lớp 8.2: Thứ 7 và Chủ nhật, 15:00-16:30
# Lớp 9.1: Thứ 3 và Thứ 5, 19:30-21:00
# Lớp 9.2: Thứ 7 và Chủ nhật, 18:00-19:30
```

### Google Sheet Format
| STT | Họ và tên | Lớp | Điểm 1 (17/01) | Điểm 2 (24/01) | ... |
|-----|-----------|-----|----------------|----------------|-----|
| 1   | Nguyễn A  | 6.1 | 8.5            | 9.0            | ... |
| 2   | Trần B    | 6.1 | 7.0            | 8.5            | ... |

## ⚙️ Cấu Hình

### Chỉnh Sửa Lịch Học
Sửa file `schedule.py` để thay đổi lịch học các lớp.

### Thêm/Sửa Lớp
Sửa file `config.py`:
```python
CLASSES = ["6.1", "6.2", "7.1", "7.2", "8.1", "8.2", "9.1", "9.2"]

GROUP_CHAT_IDS = {
    "6.1": -4500167226,
    # Thêm chat_id group mới...
}
```

### Thay Đổi Google Sheet
Sửa `GOOGLE_SHEET_ID` trong `config.py`.

## 🔒 Bảo Mật

### ⚠️ QUAN TRỌNG - KHÔNG BAO GIỜ:
- Commit file `credentials.json` lên public repository
- Chia sẻ Telegram Bot Token
- Để lộ chat_id của groups

### ✅ Thực Hành Tốt:
- Sử dụng file `.env` cho sensitive data
- Thêm `credentials.json` vào `.gitignore`
- Định kỳ rotate credentials
- Giới hạn quyền Service Account

## 🛠️ Troubleshooting

### Bot không gửi được báo cáo vào group
- Kiểm tra bot đã được add vào group chưa
- Kiểm tra bot có quyền "Send Messages"
- Kiểm tra chat_id group có đúng không

### Lỗi Google Sheets API
- Kiểm tra credentials.json có hợp lệ không
- Kiểm tra Service Account có quyền truy cập sheet không  
- Kiểm tra Google Sheets API đã được enable chưa

### Bot không phản hồi
- Kiểm tra TELEGRAM_BOT_TOKEN có đúng không
- Kiểm tra kết nối internet
- Xem logs để debug

## 📁 Cấu Trúc Project

```
📦 thong-ke-diem/
├── 📄 main.py              # Entry point
├── 📄 config.py            # Cấu hình chung
├── 📄 schedule.py          # Quản lý lịch học
├── 📄 sheets_client.py     # Google Sheets client  
├── 📄 requirements.txt     # Dependencies
├── 📄 credentials.json     # Google credentials (KHÔNG commit)
├── 📄 .env                 # Environment variables (KHÔNG commit)
├── 📂 flows/
│   ├── 📄 report_flow.py   # Flow báo cáo
│   └── 📄 score_flow.py    # Flow nhập điểm
├── 📂 parsers/
│   ├── 📄 report_parser.py # Parse nội dung báo cáo
│   └── 📄 scores_parser.py # Parse block điểm
└── 📂 utils/
    └── 📄 text.py          # Text processing utilities
```

## 📝 Logs

Bot tự động log các hoạt động quan trọng:
- Khởi động/tắt bot
- Gửi báo cáo thành công/thất bại
- Xử lý điểm hàng loạt
- Lỗi API calls

## 🤝 Đóng Góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push branch  
5. Tạo Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết chi tiết.

## 📞 Hỗ Trợ

Có vấn đề hoặc góp ý? Tạo issue trên GitHub hoặc liên hệ admin.

---

**⚠️ LƯU Ý:** Đây là bot nội bộ, vui lòng không chia sẻ credentials hoặc thông tin nhạy cảm!