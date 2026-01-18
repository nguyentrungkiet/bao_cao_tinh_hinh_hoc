from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from config import TIMEZONE

# Mapping lịch học cho từng lớp
# Cấu trúc: {class: {"weekdays": [list of weekday numbers], "time": "time_range", "schedule_text": "description"}}
# weekday numbers: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday

CLASS_SCHEDULES: Dict[str, Dict] = {
    "6.1": {
        "weekdays": [0, 2],  # Thứ 2 và Thứ 4
        "time": "18:00 - 19:30",
        "schedule_text": "Thứ 2 và Thứ 4, 18:00 - 19:30"
    },
    "6.2": {
        "weekdays": [0, 2],  # Thứ 2 và Thứ 4
        "time": "18:00 - 19:30",
        "schedule_text": "Thứ 2 và Thứ 4, 18:00 - 19:30"
    },
    "7.1": {
        "weekdays": [1, 3],  # Thứ 3 và Thứ 5
        "time": "18:00 - 19:30",
        "schedule_text": "Thứ 3 và Thứ 5, 18:00 - 19:30"
    },
    "7.2": {
        "weekdays": [5, 6],  # Thứ 7 và Chủ nhật
        "time": "16:30 - 18:00",
        "schedule_text": "Thứ 7 và Chủ nhật, 16:30 - 18:00"
    },
    "8.1": {
        "weekdays": [0, 2],  # Thứ 2 và Thứ 4
        "time": "19:30 - 21:00",
        "schedule_text": "Thứ 2 và Thứ 4, 19:30 - 21:00"
    },
    "8.2": {
        "weekdays": [5, 6],  # Thứ 7 và Chủ nhật
        "time": "15:00 - 16:30",
        "schedule_text": "Thứ 7 và Chủ nhật, 15:00 - 16:30"
    },
    "9.1": {
        "weekdays": [1, 3],  # Thứ 3 và Thứ 5
        "time": "19:30 - 21:00",
        "schedule_text": "Thứ 3 và Thứ 5, 19:30 - 21:00"
    },
    "9.2": {
        "weekdays": [5, 6],  # Thứ 7 và Chủ nhật
        "time": "18:00 - 19:30",
        "schedule_text": "Thứ 7 và Chủ nhật, 18:00 - 19:30"
    },
}

# Mapping số thứ tự thứ sang tên tiếng Việt
WEEKDAY_NAMES = {
    0: "Thứ 2",
    1: "Thứ 3", 
    2: "Thứ 4",
    3: "Thứ 5",
    4: "Thứ 6",
    5: "Thứ 7",
    6: "Chủ nhật"
}

def get_class_schedule(class_name: str) -> Dict:
    """Lấy thông tin lịch học của lớp"""
    return CLASS_SCHEDULES.get(class_name, {})

def get_weekday_name(weekday: int) -> str:
    """Chuyển số thứ tự thứ sang tên tiếng Việt"""
    return WEEKDAY_NAMES.get(weekday, f"Thứ {weekday + 1}")

def validate_class_date(class_name: str, date_input: str) -> Tuple[bool, Optional[datetime], str]:
    """
    Validate ngày đã nhập có đúng thứ theo lịch lớp không
    
    Args:
        class_name: Tên lớp
        date_input: Chuỗi ngày theo format dd/mm/yyyy
        
    Returns:
        Tuple[bool, Optional[datetime], str]: (is_valid, parsed_date, error_message)
    """
    try:
        # Parse ngày
        parsed_date = datetime.strptime(date_input.strip(), "%d/%m/%Y")
        parsed_date = TIMEZONE.localize(parsed_date)
        
        # Lấy lịch học của lớp
        schedule = get_class_schedule(class_name)
        if not schedule:
            return False, None, f"Không tìm thấy lịch học cho lớp {class_name}"
        
        # Kiểm tra thứ
        weekday = parsed_date.weekday()
        valid_weekdays = schedule["weekdays"]
        
        if weekday not in valid_weekdays:
            valid_weekday_names = [get_weekday_name(wd) for wd in valid_weekdays]
            return False, None, f"Lớp {class_name} chỉ học vào {', '.join(valid_weekday_names)}. Ngày {date_input} là {get_weekday_name(weekday)}."
            
        return True, parsed_date, ""
        
    except ValueError:
        return False, None, "Định dạng ngày không đúng. Vui lòng nhập theo format dd/mm/yyyy"

def get_latest_session_date(class_name: str) -> Optional[datetime]:
    """
    Tính buổi học gần nhất trong quá khứ theo lịch của lớp
    
    Args:
        class_name: Tên lớp
        
    Returns:
        Optional[datetime]: Ngày buổi học gần nhất, None nếu không tìm thấy
    """
    schedule = get_class_schedule(class_name)
    if not schedule:
        return None
    
    now = datetime.now(TIMEZONE)
    valid_weekdays = schedule["weekdays"]
    
    # Tìm buổi học gần nhất trong quá khứ
    for days_back in range(1, 15):  # Tìm trong vòng 2 tuần gần nhất
        check_date = now - timedelta(days=days_back)
        if check_date.weekday() in valid_weekdays:
            return check_date
    
    return None

def format_session_date(date: datetime) -> str:
    """
    Format ngày buổi học theo định dạng Vietnamese
    
    Args:
        date: Datetime object
        
    Returns:
        str: Formatted date string "Thứ X, ngày dd/mm/yyyy"
    """
    weekday_name = get_weekday_name(date.weekday())
    date_str = date.strftime("%d/%m/%Y")
    return f"{weekday_name}, ngày {date_str}"

def get_class_time_range(class_name: str) -> str:
    """
    Lấy khung giờ học của lớp
    
    Args:
        class_name: Tên lớp
        
    Returns:
        str: Khung giờ học, ví dụ "18:00 - 19:30"
    """
    schedule = get_class_schedule(class_name)
    return schedule.get("time", "")

def get_class_schedule_text(class_name: str) -> str:
    """
    Lấy mô tả lịch học đầy đủ của lớp
    
    Args:
        class_name: Tên lớp
        
    Returns:
        str: Mô tả lịch học, ví dụ "Thứ 2 và Thứ 4, 18:00 - 19:30"
    """
    schedule = get_class_schedule(class_name)
    return schedule.get("schedule_text", "")

def calculate_lateness_days(session_date: datetime) -> int:
    """
    Tính số ngày trễ hạn
    
    Args:
        session_date: Ngày buổi học
        
    Returns:
        int: Số ngày trễ hạn (0 nếu không trễ)
    """
    now = datetime.now(TIMEZONE)
    
    # Chỉ so sánh ngày, không quan tâm giờ
    session_day = session_date.date()
    today = now.date()
    
    lateness_days = (today - session_day).days
    return max(0, lateness_days)