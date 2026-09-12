import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List, Tuple, Optional, Any
import logging
from config import GOOGLE_SHEET_ID, SHEET_NAME, CREDENTIALS_FILE
from utils.text import normalize_name

logger = logging.getLogger(__name__)

class SheetsClient:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Sheets client"""
        try:
            # Setup credentials
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                CREDENTIALS_FILE, 
                scopes=scopes
            )
            
            # Create client
            self.client = gspread.authorize(credentials)
            
            # Open spreadsheet
            self.spreadsheet = self.client.open_by_key(GOOGLE_SHEET_ID)
            self.worksheet = self.spreadsheet.worksheet(SHEET_NAME)
            
            try:
                from config import DOCUMENTS_SHEET_NAME
                self.doc_worksheet = self.spreadsheet.worksheet(DOCUMENTS_SHEET_NAME)
            except Exception as e:
                logger.warning(f"Could not open documents worksheet {DOCUMENTS_SHEET_NAME}: {e}")
                self.doc_worksheet = None
            
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise

    def get_student_data(self) -> List[Dict]:
        """
        Lấy toàn bộ data học sinh từ sheet
        
        Returns:
            List[Dict]: Danh sách học sinh với thông tin [row, name, class, name_normalized]
        """
        try:
            # Lấy toàn bộ data
            all_values = self.worksheet.get_all_values()
            
            if len(all_values) < 2:  # Không có data ngoài header
                return []
            
            students = []
            
            # Skip header (row 1), bắt đầu từ row 2
            for row_idx, row_data in enumerate(all_values[1:], start=2):
                if len(row_data) >= 3:  # STT, Họ và tên, Lớp
                    name = row_data[1].strip() if len(row_data) > 1 else ""
                    class_name = row_data[2].strip() if len(row_data) > 2 else ""
                    
                    if name:  # Chỉ lấy những dòng có tên
                        students.append({
                            "row": row_idx,
                            "name": name,
                            "class": class_name,
                            "name_normalized": normalize_name(name)
                        })
            
            logger.info(f"Retrieved {len(students)} students from sheet")
            return students
            
        except Exception as e:
            logger.error(f"Failed to get student data: {e}")
            raise

    def find_student_rows(self, name_input: str, class_filter: Optional[str] = None) -> List[Dict]:
        """
        Tìm học sinh theo tên (fuzzy match)
        
        Args:
            name_input: Tên cần tìm
            class_filter: Lớp để filter (optional)
            
        Returns:
            List[Dict]: Danh sách học sinh match
        """
        students = self.get_student_data()
        normalized_input = normalize_name(name_input)
        
        matches = []
        
        for student in students:
            # Match theo tên normalize
            if normalized_input in student["name_normalized"] or student["name_normalized"] in normalized_input:
                # Apply class filter nếu có
                if class_filter is None or student["class"] == class_filter:
                    matches.append(student)
        
        return matches

    def check_existing_scores(self, row: int, col: int) -> Optional[float]:
        """
        Kiểm tra xem ô điểm đã có giá trị chưa
        
        Args:
            row: Số dòng
            col: Số cột
            
        Returns:
            Optional[float]: Điểm hiện có (nếu có), hoặc None
        """
        try:
            cell_value = self.worksheet.cell(row, col).value
            if cell_value and cell_value.strip():
                try:
                    return float(cell_value.strip())
                except ValueError:
                    return None
            return None
        except Exception as e:
            logger.error(f"Error checking existing score at row {row}, col {col}: {e}")
            return None

    def find_next_empty_score_column(self, row: int) -> int:
        """
        Tìm cột trống tiếp theo để ghi điểm cho học sinh
        
        Args:
            row: Row number của học sinh
            
        Returns:
            int: Column number (1-based) của cột trống tiếp theo
        """
        try:
            # Lấy toàn bộ data của row
            row_values = self.worksheet.row_values(row)
            
            # Bắt đầu từ cột D (index 3, column 4)
            start_col = 4
            
            # Tìm cột trống đầu tiên từ cột D trở đi
            for col_idx in range(start_col, len(row_values) + 2):  # +2 để có thêm cột mới
                if col_idx > len(row_values) or not row_values[col_idx - 1].strip():
                    return col_idx
            
            # Nếu không tìm thấy, return cột tiếp theo
            return len(row_values) + 1
            
        except Exception as e:
            logger.error(f"Failed to find next empty column for row {row}: {e}")
            return 4  # Default to column D

    def get_or_create_score_header(self, col: int, test_date: str) -> str:
        """
        Lấy hoặc tạo header cho cột điểm
        
        Args:
            col: Column number (1-based)
            test_date: Ngày kiểm tra (dd/mm format)
            
        Returns:
            str: Header text
        """
        try:
            # Kiểm tra header hiện tại
            current_header = self.worksheet.cell(1, col).value
            
            if current_header and current_header.strip():
                return current_header.strip()
            
            # Tạo header mới
            # Đếm số cột điểm hiện có để tạo số thứ tự
            existing_headers = self.worksheet.row_values(1)
            score_count = 0
            
            for header in existing_headers[3:]:  # Bắt đầu từ cột D
                if header and header.strip():
                    score_count += 1
            
            new_header = f"Điểm {score_count + 1} ({test_date})"
            
            # Ghi header mới
            self.worksheet.update_cell(1, col, new_header)
            logger.info(f"Created new score header: {new_header} at column {col}")
            
            return new_header
            
        except Exception as e:
            logger.error(f"Failed to get/create header for column {col}: {e}")
            return f"Điểm ({test_date})"

    def batch_update_scores(self, updates: List[Dict]) -> Tuple[int, List[str]]:
        """
        Batch update điểm cho nhiều học sinh
        
        Args:
            updates: List các update có format:
                    [{"row": int, "col": int, "score": float, "name": str}, ...]
                    
        Returns:
            Tuple[int, List[str]]: (số update thành công, danh sách lỗi)
        """
        try:
            if not updates:
                return 0, []
            
            # Chuẩn bị batch update
            batch_updates = []
            
            for update in updates:
                row = update["row"]
                col = update["col"]
                score = update["score"]
                
                # Convert to A1 notation
                cell_range = f"{self._col_number_to_letter(col)}{row}"
                batch_updates.append({
                    "range": cell_range,
                    "values": [[score]]
                })
            
            # Thực hiện batch update
            self.worksheet.batch_update(batch_updates)
            
            logger.info(f"Successfully updated {len(updates)} scores")
            return len(updates), []
            
        except Exception as e:
            logger.error(f"Failed to batch update scores: {e}")
            return 0, [f"Lỗi batch update: {str(e)}"]

    def _col_number_to_letter(self, col_num: int) -> str:
        """
        Convert column number to letter (1 -> A, 2 -> B, etc.)
        
        Args:
            col_num: Column number (1-based)
            
        Returns:
            str: Column letter
        """
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(col_num % 26 + ord('A')) + result
            col_num //= 26
        return result

    def record_score_entry(self, student_name: str, class_name: str, score: float, test_date: str) -> Tuple[bool, str]:
        """
        Ghi điểm cho một học sinh
        
        Args:
            student_name: Tên học sinh
            class_name: Lớp
            score: Điểm số
            test_date: Ngày kiểm tra (dd/mm format)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Tìm học sinh
            matches = self.find_student_rows(student_name, class_name)
            
            if not matches:
                return False, f"Không tìm thấy học sinh '{student_name}' trong lớp {class_name}"
            
            if len(matches) > 1:
                return False, f"Tìm thấy nhiều học sinh trùng tên '{student_name}' trong lớp {class_name}"
            
            student = matches[0]
            row = student["row"]
            
            # Tìm cột trống tiếp theo
            col = self.find_next_empty_score_column(row)
            
            # Tạo/lấy header
            self.get_or_create_score_header(col, test_date)
            
            # Ghi điểm
            self.worksheet.update_cell(row, col, score)
            
            logger.info(f"Recorded score {score} for {student_name} at row {row}, col {col}")
            return True, f"Đã ghi điểm {score} cho {student['name']}"
            
        except Exception as e:
            logger.error(f"Failed to record score for {student_name}: {e}")
            return False, f"Lỗi khi ghi điểm cho {student_name}: {str(e)}"

    def get_document_data(self, class_name: str) -> List[Dict]:
        """
        Lấy thông tin tài liệu cho một lớp
        
        Args:
            class_name: Lớp cần lấy thông tin
            
        Returns:
            List[Dict]: Danh sách tài liệu với thông tin [row, chapter, remaining]
        """
        if not self.doc_worksheet:
            return []
            
        try:
            # Lấy toàn bộ data
            all_values = self.doc_worksheet.get_all_values()
            
            if len(all_values) < 2:
                return []
            
            docs = []
            
            # Skip header, columns: Lớp (A), Chương (B), Số lượng còn (C)
            for row_idx, row_data in enumerate(all_values[1:], start=2):
                if len(row_data) >= 3:
                    row_class = row_data[0].strip()
                    if row_class == class_name:
                        chapter = row_data[1].strip()
                        try:
                            remaining = int(row_data[2].strip() or 0)
                        except ValueError:
                            remaining = 0
                            
                        docs.append({
                            "row": row_idx,
                            "chapter": chapter,
                            "remaining": remaining
                        })
            
            return docs
            
        except Exception as e:
            logger.error(f"Failed to get document data for class {class_name}: {e}")
            return []

    def update_document_count(self, row: int, new_count: int) -> bool:
        """
        Cập nhật số lượng tài liệu
        
        Args:
            row: Dòng cần update
            new_count: Số lượng mới
            
        Returns:
            bool: Success status
        """
        if not self.doc_worksheet:
            return False
            
        try:
            # Cột C (3) là Số lượng còn
            self.doc_worksheet.update_cell(row, 3, new_count)
            logger.info(f"Updated document count at row {row} to {new_count}")
            return True
        except Exception as e:
            logger.error(f"Failed to update document count at row {row}: {e}")
            return False