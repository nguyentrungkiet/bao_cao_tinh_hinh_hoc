# Quick Fix Guide - Lỗi "No module named 'dotenv'"

## Nguyên nhân
- Chưa cài đặt các thư viện cần thiết
- Chưa kích hoạt virtual environment

## Cách sửa

### Bước 1: Tạo virtual environment (nếu chưa có)
```powershell
cd C:\bao_cao_tinh_hinh_hoc
python -m venv .venv
```

### Bước 2: Kích hoạt virtual environment
```powershell
.\.venv\Scripts\Activate.ps1
```

**Lưu ý**: Nếu gặp lỗi ExecutionPolicy, chạy lệnh này trước (với quyền Administrator):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Bước 3: Cài đặt dependencies
```powershell
pip install -r requirements.txt
```

### Bước 4: Chạy bot
```powershell
python main.py
```

## Hoặc sử dụng script tự động

Chạy PowerShell với quyền Administrator:
```powershell
cd C:\bao_cao_tinh_hinh_hoc
powershell -ExecutionPolicy Bypass -File setup_vps.ps1
```

Script này sẽ tự động:
- Kiểm tra Python
- Tạo virtual environment
- Cài đặt tất cả dependencies
- Kiểm tra các file cấu hình

## Kiểm tra xem đã cài đặt thành công chưa

```powershell
# Kích hoạt virtual environment
.\.venv\Scripts\Activate.ps1

# Kiểm tra các package đã cài
pip list

# Bạn sẽ thấy: python-dotenv, python-telegram-bot, gspread, etc.
```

## Sau khi fix lỗi

1. **Tạo/sửa file .env**:
```env
TELEGRAM_BOT_TOKEN=your_actual_bot_token
GOOGLE_SHEET_ID=your_actual_sheet_id
```

2. **Copy file credentials.json** vào thư mục `C:\bao_cao_tinh_hinh_hoc`

3. **Chạy bot**:
```powershell
python main.py
```

4. **Cài đặt như Windows Service** (để tự động chạy khi khởi động):
```powershell
# Download NSSM từ https://nssm.cc/download
# Copy nssm.exe (win64) vào C:\bao_cao_tinh_hinh_hoc
powershell -ExecutionPolicy Bypass -File setup_service.ps1 -Action install
```
