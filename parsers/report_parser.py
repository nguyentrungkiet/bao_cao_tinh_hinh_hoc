from typing import Dict, Optional
from utils.text import fuzzy_match_field_name, parse_count_and_description, clean_multiline_text
from config import REPORT_DEFAULTS

class ReportParser:
    """Parser để chuyển đổi free text thành structured report data"""
    
    def __init__(self):
        # Mapping các tên field trong tiếng Việt
        self.field_mappings = {
            "vắng": "absent",
            "không làm bài tập": "no_homework", 
            "thiếu bài tập": "missing_homework",
            "thiếu dụng cụ học tập": "missing_tools",
            "chép phạt": "detention",
            "nhắc nhở trong giờ học": "reminder",
            "đóng tiền mất tài liệu": "fee_collection",
            "nội dung bài học": "lesson_content",
            "bài tập về nhà": "homework_assigned",
            "tài liệu đã phát": "documents_distributed"
        }
        
        # Reverse mapping
        self.field_names = list(self.field_mappings.keys())

    def parse_report_content(self, content: str) -> Dict:
        """
        Parse free text content thành structured report data
        
        Args:
            content: Nội dung báo cáo do trợ giảng nhập
            
        Returns:
            Dict: Structured report data
        """
        # Khởi tạo với giá trị mặc định
        result = REPORT_DEFAULTS.copy()
        
        if not content:
            return result
        
        # Chia content thành các dòng
        lines = content.strip().split('\n')
        
        current_field = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Kiểm tra xem dòng này có phải là field label không
            field_name = self._extract_field_name(line)
            
            if field_name:
                # Lưu content của field trước đó (nếu có)
                if current_field:
                    self._save_field_content(result, current_field, current_content)
                
                # Bắt đầu field mới
                current_field = field_name
                current_content = []
                
                # Xử lý content ngay trong dòng này (phần sau dấu :)
                content_part = self._extract_field_content(line)
                if content_part:
                    current_content.append(content_part)
            else:
                # Dòng này là content của field hiện tại
                if current_field:
                    current_content.append(line)
        
        # Lưu field cuối cùng
        if current_field:
            self._save_field_content(result, current_field, current_content)
        
        return result

    def _extract_field_name(self, line: str) -> Optional[str]:
        """
        Trích xuất tên field từ dòng text
        
        Args:
            line: Dòng text
            
        Returns:
            Optional[str]: Tên field đã normalize, None nếu không phải field line
        """
        # Kiểm tra pattern "Field Name:" 
        if ':' in line:
            potential_field = line.split(':', 1)[0].strip()
            
            # Fuzzy match với danh sách field hợp lệ
            matched_field = fuzzy_match_field_name(potential_field, self.field_names)
            return matched_field
        
        return None

    def _extract_field_content(self, line: str) -> str:
        """
        Trích xuất content từ dòng field (phần sau dấu :)
        
        Args:
            line: Dòng text có format "Field: content"
            
        Returns:
            str: Content part
        """
        if ':' in line:
            return line.split(':', 1)[1].strip()
        return ""

    def _save_field_content(self, result: Dict, field_name: str, content_lines: list):
        """
        Lưu content đã parse vào result dict
        
        Args:
            result: Dict kết quả
            field_name: Tên field
            content_lines: Danh sách dòng content
        """
        if not field_name or field_name not in self.field_mappings:
            return
        
        field_key = self.field_mappings[field_name]
        content_text = '\n'.join(content_lines).strip()
        
        # Xử lý theo loại field
        if field_key in ["lesson_content", "homework_assigned"]:
            # Multiline fields
            result[field_key] = clean_multiline_text(content_text) if content_text else "Không có"
        
        elif field_key == "documents_distributed":
            # Field số lượng đơn giản
            count, description = parse_count_and_description(content_text)
            result[field_key] = count
            if description:
                result[f"{field_key}_desc"] = description
        
        else:
            # Các field số lượng khác (có thể có description)
            count, description = parse_count_and_description(content_text)
            result[field_key] = count
            
            # Lưu description nếu có
            if description:
                result[f"{field_key}_desc"] = description

    def generate_report_preview(self, report_data: Dict, class_name: str, 
                              session_date_str: str, time_range: str, 
                              lateness_days: int = 0) -> str:
        """
        Tạo preview báo cáo theo format mẫu
        
        Args:
            report_data: Data báo cáo đã parse
            class_name: Tên lớp
            session_date_str: Ngày buổi học (format: "Thứ X, ngày dd/mm/yyyy")
            time_range: Khung giờ học
            lateness_days: Số ngày trễ hạn
            
        Returns:
            str: Báo cáo theo format mẫu
        """
        # Helper function để format field với description
        def format_field_with_desc(count: int, desc: str = "") -> str:
            if desc:
                return f"{count} ( {desc} )"
            return str(count)
        
        # Tạo content báo cáo
        absent_str = format_field_with_desc(
            report_data.get("absent", 0), 
            report_data.get("absent_desc", "")
        )
        
        no_homework_str = format_field_with_desc(
            report_data.get("no_homework", 0), 
            report_data.get("no_homework_desc", "")
        )
        
        missing_homework_str = format_field_with_desc(
            report_data.get("missing_homework", 0), 
            report_data.get("missing_homework_desc", "")
        )
        
        missing_tools_str = format_field_with_desc(
            report_data.get("missing_tools", 0), 
            report_data.get("missing_tools_desc", "")
        )
        
        detention_str = format_field_with_desc(
            report_data.get("detention", 0), 
            report_data.get("detention_desc", "")
        )
        
        reminder_str = format_field_with_desc(
            report_data.get("reminder", 0), 
            report_data.get("reminder_desc", "")
        )
        
        fee_collection_str = format_field_with_desc(
            report_data.get("fee_collection", 0), 
            report_data.get("fee_collection_desc", "")
        )
        
        # Tài liệu đã phát: chỉ hiển thị description, không có số count và ngoặc
        documents_desc = report_data.get("documents_distributed_desc", "")
        if documents_desc:
            documents_str = documents_desc
        else:
            # Nếu không có description, hiển thị số count hoặc "Không có"
            count = report_data.get("documents_distributed", 0)
            documents_str = str(count) if count > 0 else "Không có"
        
        # Tạo báo cáo theo format mẫu
        report = f"""🏫 Lớp: {class_name} | ⏰ {time_range}
📅 {session_date_str}
Vắng: {absent_str}
Không làm bài tập: {no_homework_str}
- Thiếu bài tập : {missing_homework_str}
Thiếu dụng cụ học tập: {missing_tools_str}
Chép phạt: {detention_str}
Nhắc nhở trong giờ học: {reminder_str}
💰 Đóng tiền mất tài liệu: {fee_collection_str}
📚 Nội dung bài học:
{report_data.get("lesson_content", "Không có")}
🏠 Bài tập về nhà:
{report_data.get("homework_assigned", "Không có")}
📄 Tài liệu đã phát : {documents_str}"""
        
        # Thêm dòng báo trễ nếu cần
        if lateness_days > 0:
            report += f"\n⏰ Trợ giảng báo trễ: {lateness_days} ngày"
        
        return report

    def generate_input_guide(self) -> str:
        """
        Tạo hướng dẫn format input cho trợ giảng
        
        Returns:
            str: Hướng dẫn format
        """
        guide = """📋 Vui lòng nhập nội dung báo cáo theo format sau:

**Có thể sử dụng các nhãn (không bắt buộc đầy đủ):**

Vắng: (số lượng + danh sách)
Không làm bài tập: (số lượng + danh sách)  
Thiếu bài tập: (số lượng + ghi chú)
Thiếu dụng cụ học tập: (số lượng + mô tả)
Chép phạt: (số lượng + danh sách)
Nhắc nhở trong giờ học: (số lượng + nội dung)
Đóng tiền mất tài liệu: (số lượng + danh sách)
Nội dung bài học:
(nhiều dòng)
Bài tập về nhà:
(nhiều dòng)
Tài liệu đã phát: (số lượng + mô tả)

**Ví dụ:**
Vắng: 2 (Thảo, Diệp)
Thiếu bài tập: 3 (Dũng, Trung, Hân) - thiếu BTVN bài 3
Nội dung bài học:
Chữa bài tập 1, 2
Học bài mới: Phương trình bậc nhất
Bài tập về nhà:
Làm bài 5, 6, 7 trang 25

*Lưu ý: Có thể viết tắt hoặc gõ sai chính tả một chút, bot sẽ tự hiểu.*"""
        
        return guide