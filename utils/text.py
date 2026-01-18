import re
import unicodedata
from typing import Optional, List, Tuple

def remove_accents(text: str) -> str:
    """
    Bỏ dấu tiếng Việt khỏi text
    
    Args:
        text: Chuỗi có dấu
        
    Returns:
        str: Chuỗi không dấu
    """
    # Normalize unicode và bỏ các ký tự combining
    nfd = unicodedata.normalize('NFD', text)
    without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return without_accents

def normalize_name(name: str) -> str:
    """
    Normalize tên để so khớp: lowercase, bỏ dấu, loại bỏ khoảng trắng thừa
    
    Args:
        name: Tên gốc
        
    Returns:
        str: Tên đã normalize
    """
    if not name:
        return ""
    
    # Lowercase và strip
    name = name.strip().lower()
    
    # Bỏ dấu
    name = remove_accents(name)
    
    # Chuẩn hóa khoảng trắng (thay multiple spaces thành single space)
    name = re.sub(r'\s+', ' ', name)
    
    return name

def parse_number_from_text(text: str) -> Optional[float]:
    """
    Trích xuất số từ text
    
    Args:
        text: Chuỗi text chứa số
        
    Returns:
        Optional[float]: Số đã parse, None nếu không tìm thấy
    """
    if not text:
        return None
    
    # Tìm số đầu tiên trong text (bao gồm số thập phân)
    match = re.search(r'\d+(?:\.\d+)?', text.strip())
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def parse_count_and_description(text: str) -> Tuple[int, str]:
    """
    Parse text có dạng "số (mô tả)" hoặc "số; mô tả" hoặc "mô tả có chứa số"
    
    Args:
        text: Text để parse, ví dụ "2 (Thảo, Diệp)", "0", "bài 6. Xác suất..."
        
    Returns:
        Tuple[int, str]: (số lượng, mô tả)
    """
    if not text:
        return 0, ""
    
    text = text.strip()
    
    # Tìm số đầu tiên
    number = parse_number_from_text(text)
    count = int(number) if number is not None else 0
    
    # Tìm mô tả trong ngoặc hoặc sau dấu ;
    description = ""
    
    # Pattern cho mô tả trong ngoặc đơn
    paren_match = re.search(r'\((.*?)\)', text)
    if paren_match:
        description = paren_match.group(1).strip()
    else:
        # Pattern cho mô tả sau dấu ;
        semicolon_match = re.search(r';\s*(.+)', text)
        if semicolon_match:
            description = semicolon_match.group(1).strip()
        else:
            # Nếu không có pattern đặc biệt:
            # - Nếu text BẮT ĐẦU bằng số: lấy phần sau số làm description
            # - Nếu text KHÔNG bắt đầu bằng số: lấy TOÀN BỘ text làm description
            if re.match(r'^\d+(?:\.\d+)?', text):
                # Text bắt đầu bằng số: bỏ số và khoảng trắng đầu
                remaining = re.sub(r'^\d+(?:\.\d+)?\s*', '', text).strip()
                if remaining:
                    description = remaining
            else:
                # Text KHÔNG bắt đầu bằng số (VD: "bài 6. Xác suất...")
                # → Lấy toàn bộ text làm description
                description = text
    
    return count, description

def fuzzy_match_field_name(input_name: str, valid_fields: List[str]) -> Optional[str]:
    """
    Tìm field name gần giống nhất với input (fuzzy matching)
    
    Args:
        input_name: Tên field người dùng nhập
        valid_fields: Danh sách tên field hợp lệ
        
    Returns:
        Optional[str]: Field name match được, None nếu không tìm thấy
    """
    if not input_name or not valid_fields:
        return None
    
    normalized_input = normalize_name(input_name)
    
    # Exact match trước
    for field in valid_fields:
        if normalized_input == normalize_name(field):
            return field
    
    # Fuzzy match: kiểm tra xem input có chứa hoặc được chứa trong field nào không
    for field in valid_fields:
        normalized_field = normalize_name(field)
        
        # Input chứa field hoặc ngược lại
        if normalized_input in normalized_field or normalized_field in normalized_input:
            return field
    
    # Tìm theo từ khóa chính
    keyword_mappings = {
        "vang": ["vắng", "absent"],
        "khong lam bai tap": ["không làm bài tập", "no homework"],
        "thieu bai tap": ["thiếu bài tập", "missing homework"],
        "thieu dung cu": ["thiếu dụng cụ", "missing tools"],
        "chep phat": ["chép phạt", "detention"],
        "nhac nho": ["nhắc nhở", "reminder"],
        "dong tien": ["đóng tiền", "fee collection"],
        "noi dung": ["nội dung bài học", "lesson content"],
        "bai tap": ["bài tập về nhà", "homework assigned"],
        "tai lieu": ["tài liệu", "documents distributed"]
    }
    
    for keyword, targets in keyword_mappings.items():
        if keyword in normalized_input:
            for field in valid_fields:
                normalized_field = normalize_name(field)
                for target in targets:
                    if normalize_name(target) in normalized_field:
                        return field
    
    return None

def clean_multiline_text(text: str) -> str:
    """
    Clean và format multiline text
    
    Args:
        text: Text gốc
        
    Returns:
        str: Text đã clean
    """
    if not text:
        return ""
    
    # Split lines và clean từng line
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:  # Bỏ qua dòng trống
            cleaned_lines.append(line)
    
    # Join lại với newline
    result = '\n'.join(cleaned_lines)
    return result if result else "Không có"

def extract_date_from_text(text: str) -> Optional[str]:
    """
    Trích xuất ngày từ text theo format dd/mm/yyyy
    
    Args:
        text: Text chứa ngày
        
    Returns:
        Optional[str]: Ngày theo format dd/mm/yyyy, None nếu không tìm thấy
    """
    if not text:
        return None
    
    # Pattern cho ngày theo format dd/mm/yyyy
    date_pattern = r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'
    match = re.search(date_pattern, text)
    
    if match:
        day, month, year = match.groups()
        # Format lại để đảm bảo có 2 chữ số cho ngày và tháng
        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
    
    return None

def is_valid_score(score_text: str) -> Tuple[bool, Optional[float], str]:
    """
    Validate điểm số
    
    Args:
        score_text: Text chứa điểm
        
    Returns:
        Tuple[bool, Optional[float], str]: (is_valid, parsed_score, error_message)
    """
    if not score_text:
        return False, None, "Điểm không được để trống"
    
    try:
        score = float(score_text.strip())
        if 0 <= score <= 10:
            return True, score, ""
        else:
            return False, None, f"Điểm phải trong khoảng 0-10, nhận được: {score}"
    except ValueError:
        return False, None, f"Điểm không hợp lệ: {score_text}"