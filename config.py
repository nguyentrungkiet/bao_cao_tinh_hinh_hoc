import os
from typing import Dict
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Timezone
TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")

# Telegram Bot Token (from environment)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables. Please set it in .env file")

# Danh sách lớp
CLASSES = ["6.1", "6.2", "7.1", "7.2", "8.1", "8.2", "9.1", "9.2"]

# Mapping chat_id group cho từng lớp (supergroup format: -100XXXXXXXXX)
GROUP_CHAT_IDS: Dict[str, int] = {
    "6.1": -1003286311559,
    "6.2": -1003587354816,
    "7.1": -1003581175482,
    "7.2": -1003566374831,
    "8.1": -1003567115873,
    "8.2": -1003469126307,
    "9.1": -1003577772497,
    "9.2": -1003564597640,
}

# Google Sheets settings
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1rq1DDObItEtFeyyghv-Do-hPvYB_mwaTWihTJ8lfQCk/edit?resourcekey=&gid=767173574#gid=767173574"
GOOGLE_SHEET_ID = "1rq1DDObItEtFeyyghv-Do-hPvYB_mwaTWihTJ8lfQCk"
SHEET_NAME = "Thống kê điểm"
DOCUMENTS_SHEET_NAME = "Thống kê tài liệu"
CREDENTIALS_FILE = "credentials.json"

# Conversation states
class States:
    # Report flow states
    REPORT_CLASS_SELECTION = 0
    REPORT_DATE_SELECTION = 1
    REPORT_DATE_INPUT = 2
    REPORT_CONTENT_INPUT = 3
    REPORT_CONFIRMATION = 4
    
    # Score flow states
    SCORE_CLASS_SELECTION = 10
    SCORE_INPUT = 11
    SCORE_CONFIRMATION = 12

    # Document flow states
    DOC_CLASS_SELECTION = 20
    DOC_ACTION_SELECTION = 21
    DOC_CHAPTER_SELECTION = 22
    DOC_UPDATE_INPUT = 23

# Menu options
MENU_REPORT = "📋 Báo cáo tình hình học"
MENU_SCORE = "💯 Nhập điểm kiểm tra"
MENU_DOCUMENTS = "📚 Thống kê tài liệu"

# Callback data patterns
CALLBACK_REPORT = "report"
CALLBACK_SCORE = "score"
CALLBACK_DOCUMENTS = "documents"
CALLBACK_CLASS_PREFIX = "class_"
CALLBACK_DATE_USE = "date_use"
CALLBACK_DATE_CUSTOM = "date_custom"
CALLBACK_CONFIRM_SEND = "confirm_send"
CALLBACK_EDIT_AGAIN = "edit_again"
CALLBACK_CANCEL = "cancel"

# Default values for report fields
REPORT_DEFAULTS = {
    "absent": 0,
    "no_homework": 0,
    "missing_homework": 0,
    "missing_tools": 0,
    "detention": 0,
    "reminder": 0,
    "fee_collection": 0,
    "lesson_content": "Không có",
    "homework_assigned": "Không có",
    "documents_distributed": 0
}