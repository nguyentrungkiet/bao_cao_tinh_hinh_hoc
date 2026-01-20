# Hướng dẫn Deploy lên VPS Windows

## Yêu cầu hệ thống
- Windows Server hoặc Windows 10/11
- Python 3.8 trở lên
- Git
- Quyền Administrator

## Các bước cài đặt

### 1. Cài đặt Python
- Download Python từ: https://www.python.org/downloads/
- Chọn "Add Python to PATH" khi cài đặt
- Kiểm tra: `python --version`

### 2. Cài đặt Git
- Download Git từ: https://git-scm.com/download/win
- Kiểm tra: `git --version`

### 3. Clone project từ GitHub
```powershell
cd C:\
git clone https://github.com/nguyentrungkiet/bao_cao_tinh_hinh_hoc.git
cd bao_cao_tinh_hinh_hoc
```

### 4. Tạo virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Lưu ý**: Nếu gặp lỗi execution policy, chạy PowerShell với quyền Administrator và chạy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. Cài đặt dependencies
```powershell
pip install -r requirements.txt
```

### 6. Cấu hình file .env
Tạo file `.env` trong thư mục gốc với nội dung:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_SHEET_ID=your_sheet_id_here
```

### 7. Đặt file credentials.json
Copy file `credentials.json` (Google Service Account) vào thư mục gốc của project.

### 8. Chạy bot
```powershell
python main.py
```

## Chạy bot tự động khi khởi động VPS

### Cách 1: Sử dụng Task Scheduler
1. Mở Task Scheduler (`taskschd.msc`)
2. Chọn "Create Task"
3. General tab:
   - Name: "Telegram Score Bot"
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"
4. Triggers tab:
   - New > Begin the task: "At startup"
5. Actions tab:
   - New > Action: "Start a program"
   - Program/script: `C:\bao_cao_tinh_hinh_hoc\start_bot.bat`
6. Conditions tab:
   - Uncheck "Start the task only if the computer is on AC power"
7. Settings tab:
   - Check "If the task fails, restart every: 1 minute"

### Cách 2: Sử dụng NSSM (Non-Sucking Service Manager)
1. Download NSSM: https://nssm.cc/download
2. Giải nén và copy nssm.exe vào thư mục project
3. Mở PowerShell với quyền Administrator:
```powershell
cd C:\bao_cao_tinh_hinh_hoc
.\nssm.exe install TelegramScoreBot "C:\bao_cao_tinh_hinh_hoc\.venv\Scripts\python.exe" "C:\bao_cao_tinh_hinh_hoc\main.py"
.\nssm.exe set TelegramScoreBot AppDirectory "C:\bao_cao_tinh_hinh_hoc"
.\nssm.exe start TelegramScoreBot
```

## Quản lý Service với NSSM
```powershell
# Xem trạng thái
.\nssm.exe status TelegramScoreBot

# Dừng service
.\nssm.exe stop TelegramScoreBot

# Khởi động service
.\nssm.exe start TelegramScoreBot

# Restart service
.\nssm.exe restart TelegramScoreBot

# Xóa service
.\nssm.exe remove TelegramScoreBot confirm
```

## Cập nhật code mới
```powershell
cd C:\bao_cao_tinh_hinh_hoc

# Dừng bot (nếu đang chạy)
# Nếu dùng NSSM:
.\nssm.exe stop TelegramScoreBot

# Pull code mới
git pull origin main

# Cài đặt dependencies mới (nếu có)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Khởi động lại bot
# Nếu dùng NSSM:
.\nssm.exe start TelegramScoreBot
```

## Xem logs
- Nếu dùng NSSM, logs sẽ được lưu tại thư mục project
- Có thể cấu hình log file trong NSSM:
```powershell
.\nssm.exe set TelegramScoreBot AppStdout "C:\bao_cao_tinh_hinh_hoc\logs\output.log"
.\nssm.exe set TelegramScoreBot AppStderr "C:\bao_cao_tinh_hinh_hoc\logs\error.log"
```

## Kiểm tra bot đang chạy
```powershell
# Xem process Python
Get-Process python

# Hoặc với NSSM
.\nssm.exe status TelegramScoreBot
```

## Troubleshooting

### Bot không kết nối được Telegram
- Kiểm tra internet connection
- Kiểm tra TELEGRAM_BOT_TOKEN trong file .env
- Kiểm tra firewall không block port 443

### Bot không kết nối được Google Sheets
- Kiểm tra file credentials.json có đúng định dạng
- Kiểm tra GOOGLE_SHEET_ID trong file .env
- Kiểm tra Service Account có quyền truy cập Google Sheet

### Lỗi Permission
- Chạy PowerShell/CMD với quyền Administrator
- Kiểm tra execution policy: `Get-ExecutionPolicy`

### Bot bị crash
- Xem logs để tìm lỗi
- Kiểm tra dependencies đã cài đầy đủ
- Restart service
