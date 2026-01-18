import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from utils.text import extract_date_from_text, is_valid_score, normalize_name
from config import TIMEZONE

class ScoreEntry:
    """Class để lưu thông tin một entry điểm"""
    def __init__(self, name_raw: str, name_normalized: str, score: float, original_line: str):
        self.name_raw = name_raw
        self.name_normalized = name_normalized
        self.score = score
        self.original_line = original_line

class ScoresParser:
    """Parser để chuyển đổi block text điểm thành structured data"""
    
    def __init__(self):
        pass

    def parse_scores_block(self, content: str) -> Tuple[Optional[str], List[ScoreEntry], List[str]]:
        """
        Parse block text điểm thành structured data
        
        Args:
            content: Block text điểm do trợ giảng nhập
            
        Returns:
            Tuple[Optional[str], List[ScoreEntry], List[str]]: 
                - test_date: Ngày kiểm tra (dd/mm/yyyy hoặc None)
                - valid_entries: Danh sách entries hợp lệ
                - error_lines: Danh sách dòng lỗi
        """
        if not content:
            return None, [], ["Nội dung trống"]
        
        lines = content.strip().split('\n')
        test_date = None
        valid_entries = []
        error_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip các dòng header/tiêu đề tự động
            if self._is_header_line(line):
                # Nếu là dòng đầu, cố gắng extract ngày
                if i == 0 or not test_date:
                    date_in_line = self._extract_test_date_from_header(line)
                    if date_in_line:
                        test_date = date_in_line
                continue
            
            # Parse dòng điểm
            entry, error = self._parse_score_line(line)
            if entry:
                valid_entries.append(entry)
            elif error:
                error_lines.append(f"Dòng {i+1}: {error}")
        
        # Nếu không tìm thấy ngày trong header, dùng ngày hiện tại
        if not test_date:
            today = datetime.now(TIMEZONE)
            test_date = today.strftime("%d/%m/%Y")
        
        return test_date, valid_entries, error_lines
    
    def _is_header_line(self, line: str) -> bool:
        """
        Kiểm tra xem dòng có phải là header/tiêu đề không
        
        Args:
            line: Dòng text
            
        Returns:
            bool: True nếu là header
        """
        line_lower = line.lower()
        
        # Check keywords thường xuất hiện trong header
        header_keywords = [
            'điểm bài kiểm tra',
            'bài kiểm tra',
            'kiểm tra ngày',
            'kiem tra',
            'test date',
            'ngày kiểm tra',
            'ngay kiem tra'
        ]
        
        if any(keyword in line_lower for keyword in header_keywords):
            return True
        
        # Check nếu dòng bắt đầu bằng emoji thường dùng cho tiêu đề
        header_emojis = ['💯', '📝', '📋', '✏️', '🎯', '📊']
        if any(line.startswith(emoji) for emoji in header_emojis):
            return True
        
        # Check nếu dòng chỉ chứa ngày tháng và dấu hai chấm (không có tên người)
        # VD: "14/01/2026 :" hoặc "Ngày 14/01/2026:"
        if ':' in line and re.search(r'\d{1,2}/\d{1,2}/\d{4}', line):
            # Kiểm tra xem có tên người và điểm không
            if not self._contains_name_and_score(line):
                return True
        
        return False
    
    def _contains_name_and_score(self, line: str) -> bool:
        """
        Kiểm tra xem dòng có chứa cả tên và điểm không
        
        Args:
            line: Dòng text
            
        Returns:
            bool: True nếu có tên và điểm
        """
        # Pattern: tên (ít nhất 2 chữ cái) + khoảng trắng + điểm
        pattern = r'[a-zA-ZÀ-ỹ]{2,}.*\s+\d+(?:\.\d+)?$'
        return bool(re.search(pattern, line))

    def _extract_test_date_from_header(self, line: str) -> Optional[str]:
        """
        Trích xuất ngày kiểm tra từ header line
        
        Args:
            line: Dòng header
            
        Returns:
            Optional[str]: Ngày kiểm tra (dd/mm/yyyy) hoặc None
        """
        return extract_date_from_text(line)

    def _contains_score_data(self, line: str) -> bool:
        """
        Kiểm tra xem dòng có chứa data điểm không
        
        Args:
            line: Dòng text
            
        Returns:
            bool: True nếu có data điểm
        """
        # Tìm pattern "tên số"
        pattern = r'\w+\s+\d+(?:\.\d+)?'
        return bool(re.search(pattern, line))

    def _parse_score_line(self, line: str) -> Tuple[Optional[ScoreEntry], Optional[str]]:
        """
        Parse một dòng điểm
        
        Args:
            line: Dòng text có format "<tên> <điểm>"
            
        Returns:
            Tuple[Optional[ScoreEntry], Optional[str]]: (entry, error_message)
        """
        # Bỏ qua dòng chỉ chứa emoji hoặc ký tự đặc biệt
        if re.match(r'^[^\w\s]*$', line):
            return None, None
        
        # Tìm điểm ở cuối dòng
        # Pattern: tên (có thể có nhiều từ) + khoảng trắng + điểm
        pattern = r'^(.+?)\s+(\d+(?:\.\d+)?)$'
        match = re.match(pattern, line.strip())
        
        if not match:
            return None, f"Không thể parse: '{line}'"
        
        name_raw = match.group(1).strip()
        score_text = match.group(2).strip()
        
        # Validate tên
        if not name_raw:
            return None, f"Tên trống: '{line}'"
        
        # Validate điểm
        is_valid, score_value, score_error = is_valid_score(score_text)
        if not is_valid:
            return None, f"{score_error} trong dòng: '{line}'"
        
        # Tạo entry
        name_normalized = normalize_name(name_raw)
        entry = ScoreEntry(
            name_raw=name_raw,
            name_normalized=name_normalized,
            score=score_value,
            original_line=line
        )
        
        return entry, None

    def match_students_with_sheet_data(self, entries: List[ScoreEntry], 
                                     sheet_students: List[Dict], 
                                     target_class: str) -> Dict:
        """
        Match entries với data từ Google Sheet
        
        Args:
            entries: Danh sách ScoreEntry
            sheet_students: Danh sách học sinh từ sheet
            target_class: Lớp đang xử lý (VD: "6.2", "7.1")
            
        Returns:
            Dict: {
                "matched": [{"entry": ScoreEntry, "student": Dict}],
                "not_found": [ScoreEntry],
                "ambiguous": [{"entry": ScoreEntry, "candidates": [Dict]}]
            }
        """
        result = {
            "matched": [],
            "not_found": [],
            "ambiguous": []
        }
        
        # Extract grade number from target_class (VD: "6.2" -> "6", "7.1" -> "7")
        target_grade = target_class.split(".")[0] if "." in target_class else target_class
        
        for entry in entries:
            candidates = []
            
            # Tìm tất cả match theo tên
            for student in sheet_students:
                if self._names_match(entry.name_normalized, student["name_normalized"]):
                    candidates.append(student)
            
            if not candidates:
                # Không tìm thấy match nào
                result["not_found"].append(entry)
            
            elif len(candidates) == 1:
                # Tìm thấy duy nhất 1 match
                student = candidates[0]
                # So sánh grade number (VD: "6" với "6" từ "6.2")
                student_grade = student["class"].split(".")[0] if "." in student["class"] else student["class"]
                if student_grade == target_grade:
                    result["matched"].append({"entry": entry, "student": student})
                else:
                    result["not_found"].append(entry)
            
            else:
                # Có nhiều match, filter theo grade number
                class_filtered = []
                for s in candidates:
                    s_grade = s["class"].split(".")[0] if "." in s["class"] else s["class"]
                    if s_grade == target_grade:
                        class_filtered.append(s)
                
                if len(class_filtered) == 1:
                    # Sau khi filter theo lớp còn 1
                    result["matched"].append({"entry": entry, "student": class_filtered[0]})
                elif len(class_filtered) == 0:
                    # Filter theo lớp không còn ai
                    result["not_found"].append(entry)
                else:
                    # Vẫn còn nhiều match sau khi filter theo lớp
                    result["ambiguous"].append({"entry": entry, "candidates": class_filtered})
        
        return result

    def _names_match(self, name1_norm: str, name2_norm: str) -> bool:
        """
        Kiểm tra 2 tên có match không (fuzzy)
        
        Args:
            name1_norm: Tên 1 đã normalize (tên ngắn từ input)
            name2_norm: Tên 2 đã normalize (tên đầy đủ từ sheet)
            
        Returns:
            bool: True nếu match
        """
        if not name1_norm or not name2_norm:
            return False
        
        # Exact match
        if name1_norm == name2_norm:
            return True
        
        # Substring match: "kim ngan" in "vu hoang kim ngan"
        if name1_norm in name2_norm or name2_norm in name1_norm:
            return True
        
        # Token matching: tất cả các từ trong tên ngắn phải có trong tên dài
        # VD: "Kim Ngân" -> ["kim", "ngan"] -> check trong "vu hoang kim ngan"
        tokens1 = name1_norm.split()
        tokens2 = name2_norm.split()
        
        # Nếu tên ngắn hơn, check xem tất cả tokens có trong tên dài không
        if len(tokens1) <= len(tokens2):
            # Tất cả tokens của name1 phải có trong name2
            if all(token in tokens2 for token in tokens1):
                return True
        else:
            # Tên 1 dài hơn tên 2, check ngược lại
            if all(token in tokens1 for token in tokens2):
                return True
        
        # Partial token match: ít nhất 2 tokens giống nhau (với tên >= 2 tokens)
        if len(tokens1) >= 2 and len(tokens2) >= 2:
            common_tokens = set(tokens1) & set(tokens2)
            if len(common_tokens) >= 2:
                return True
        
        return False

    def generate_batch_summary(self, match_result: Dict, error_lines: List[str]) -> str:
        """
        Tạo summary cho kết quả batch process
        
        Args:
            match_result: Kết quả matching
            error_lines: Danh sách dòng lỗi
            
        Returns:
            str: Summary message
        """
        matched_count = len(match_result["matched"])
        not_found_count = len(match_result["not_found"])
        ambiguous_count = len(match_result["ambiguous"])
        error_count = len(error_lines)
        
        summary = f"📊 **Kết quả xử lý điểm:**\n\n"
        
        if matched_count > 0:
            summary += f"✅ **Đã nhập thành công:** {matched_count} học sinh\n"
        
        if not_found_count > 0:
            summary += f"❓ **Không tìm thấy:** {not_found_count} học sinh\n"
            for entry in match_result["not_found"]:
                summary += f"  - {entry.name_raw}\n"
        
        if ambiguous_count > 0:
            summary += f"⚠️ **Trùng tên/không xác định:** {ambiguous_count} học sinh\n"
            for item in match_result["ambiguous"]:
                entry = item["entry"]
                candidates = item["candidates"]
                summary += f"  - {entry.name_raw} (tìm thấy {len(candidates)} ứng viên)\n"
        
        if error_count > 0:
            summary += f"❌ **Dòng lỗi:** {error_count}\n"
            for error in error_lines[:5]:  # Chỉ hiện 5 lỗi đầu
                summary += f"  - {error}\n"
            if error_count > 5:
                summary += f"  - ... và {error_count - 5} lỗi khác\n"
        
        # Hướng dẫn xử lý
        if not_found_count > 0 or ambiguous_count > 0:
            summary += f"\n💡 **Hướng dẫn:**\n"
            if not_found_count > 0:
                summary += "- Kiểm tra chính tả tên học sinh\n"
            if ambiguous_count > 0:
                summary += "- Gõ họ tên đầy đủ hơn để phân biệt\n"
            summary += "- Dán lại chỉ những dòng cần sửa"
        
        return summary