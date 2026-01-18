import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CLASSES, TIMEZONE, States, 
    CALLBACK_CLASS_PREFIX, CALLBACK_CANCEL
)
from parsers.scores_parser import ScoresParser
from sheets_client import SheetsClient

logger = logging.getLogger(__name__)

class ScoreFlow:
    """ConversationHandler cho chức năng nhập điểm kiểm tra hàng loạt"""
    
    def __init__(self):
        self.parser = ScoresParser()
        self.sheets_client = SheetsClient()

    async def start_score_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow nhập điểm - chọn lớp (từ callback query)"""
        query = update.callback_query
        await query.answer()
        
        # Tạo keyboard chọn lớp
        keyboard = []
        for i in range(0, len(CLASSES), 2):
            row = []
            row.append(InlineKeyboardButton(
                CLASSES[i], 
                callback_data=f"{CALLBACK_CLASS_PREFIX}{CLASSES[i]}"
            ))
            if i + 1 < len(CLASSES):
                row.append(InlineKeyboardButton(
                    CLASSES[i + 1], 
                    callback_data=f"{CALLBACK_CLASS_PREFIX}{CLASSES[i + 1]}"
                ))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Hủy", callback_data=CALLBACK_CANCEL)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💯 **Nhập điểm kiểm tra hàng loạt**\n\nVui lòng chọn lớp:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.SCORE_CLASS_SELECTION
    
    async def start_score_input_from_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow nhập điểm - chọn lớp (từ message/keyboard button)"""
        # Tạo keyboard chọn lớp
        keyboard = []
        for i in range(0, len(CLASSES), 2):
            row = []
            row.append(InlineKeyboardButton(
                CLASSES[i], 
                callback_data=f"{CALLBACK_CLASS_PREFIX}{CLASSES[i]}"
            ))
            if i + 1 < len(CLASSES):
                row.append(InlineKeyboardButton(
                    CLASSES[i + 1], 
                    callback_data=f"{CALLBACK_CLASS_PREFIX}{CLASSES[i + 1]}"
                ))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Hủy", callback_data=CALLBACK_CANCEL)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💯 **Nhập điểm kiểm tra hàng loạt**\n\nVui lòng chọn lớp:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.SCORE_CLASS_SELECTION

    async def handle_class_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý chọn lớp và yêu cầu nhập điểm"""
        query = update.callback_query
        await query.answer()
        
        if query.data == CALLBACK_CANCEL:
            await query.edit_message_text("❌ Đã hủy nhập điểm.")
            return ConversationHandler.END
        
        # Lấy lớp đã chọn
        if not query.data.startswith(CALLBACK_CLASS_PREFIX):
            await query.edit_message_text("❌ Lỗi chọn lớp. Vui lòng thử lại.")
            return ConversationHandler.END
        
        selected_class = query.data[len(CALLBACK_CLASS_PREFIX):]
        if selected_class not in CLASSES:
            await query.edit_message_text("❌ Lớp không hợp lệ. Vui lòng thử lại.")
            return ConversationHandler.END
        
        # Lưu lớp đã chọn
        context.user_data["selected_class"] = selected_class
        
        # Yêu cầu nhập block điểm
        example_text = """💯Điểm bài kiểm tra ngày 🗓️17/01/2026 :
Trung 0
Trí Dũng 9
Phương Nam 8.75
Quang Dũng 9.5"""
        
        await query.edit_message_text(
            f"💯 **Nhập điểm hàng loạt**\n\n"
            f"**Lớp:** {selected_class}\n\n"
            f"📝 **Hướng dẫn:**\n"
            f"- Dòng đầu có thể chứa ngày kiểm tra (không bắt buộc)\n"
            f"- Các dòng tiếp theo: `<tên> <điểm>`\n"
            f"- Điểm từ 0-10, có thể số thập phân\n\n"
            f"**Ví dụ:**\n```\n{example_text}\n```\n\n"
            f"Dán block điểm vào đây:\n"
            f"_Gõ /cancel để hủy_",
            parse_mode='Markdown'
        )
        
        return States.SCORE_INPUT

    async def handle_score_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý input block điểm và process"""
        content = update.message.text.strip()
        
        if not content:
            await update.message.reply_text(
                "❌ Nội dung trống. Vui lòng dán block điểm.\n"
                "_Gõ /cancel để hủy_",
                parse_mode='Markdown'
            )
            return States.SCORE_INPUT
        
        selected_class = context.user_data["selected_class"]
        
        # Hiển thị loading message
        loading_msg = await update.message.reply_text(
            "⏳ Đang xử lý điểm...\n"
            "- Parse dữ liệu\n"
            "- Kết nối Google Sheets\n"
            "- Tìm học sinh\n"
            "- Ghi điểm hàng loạt"
        )
        
        try:
            # Parse block điểm
            test_date, valid_entries, error_lines = self.parser.parse_scores_block(content)
            
            if not valid_entries and error_lines:
                await loading_msg.edit_text(
                    f"❌ **Không thể xử lý block điểm**\n\n"
                    f"**Lỗi:**\n" + "\n".join(error_lines[:5]) + "\n\n"
                    f"Vui lòng kiểm tra định dạng và thử lại.\n"
                    f"_Gõ /cancel để hủy_"
                )
                return States.SCORE_INPUT
            
            if not valid_entries:
                await loading_msg.edit_text(
                    "❌ Không tìm thấy dữ liệu điểm hợp lệ.\n"
                    "Vui lòng kiểm tra định dạng và thử lại.\n"
                    "_Gõ /cancel để hủy_"
                )
                return States.SCORE_INPUT
            
            # Lấy dữ liệu học sinh từ Google Sheets
            await loading_msg.edit_text(
                "⏳ Đang tải dữ liệu học sinh từ Google Sheets..."
            )
            
            sheet_students = self.sheets_client.get_student_data()
            
            if not sheet_students:
                await loading_msg.edit_text(
                    "❌ Không thể tải dữ liệu từ Google Sheets.\n"
                    "Vui lòng kiểm tra kết nối và thử lại.\n"
                    "_Gõ /cancel để hủy_"
                )
                return States.SCORE_INPUT
            
            # Match students
            await loading_msg.edit_text(
                "⏳ Đang tìm kiếm học sinh trong danh sách..."
            )
            
            match_result = self.parser.match_students_with_sheet_data(
                valid_entries, sheet_students, selected_class
            )
            
            # Log matching results for debug
            logger.info(f"Match result: matched={len(match_result['matched'])}, "
                       f"not_found={len(match_result['not_found'])}, "
                       f"ambiguous={len(match_result['ambiguous'])}")
            
            if match_result["not_found"]:
                logger.info(f"Not found students: {[e.name_raw for e in match_result['not_found']]}")
            
            # Chuẩn bị batch updates (tự động tìm ô trống)
            batch_updates = []
            test_date_short = test_date.split("/")[:-1]  # dd/mm only
            test_date_short = "/".join(test_date_short)
            
            for match_item in match_result["matched"]:
                entry = match_item["entry"]
                student = match_item["student"]
                
                # Tìm cột trống tiếp theo (luôn tìm ô trống)
                col = self.sheets_client.find_next_empty_score_column(student["row"])
                
                # Chuẩn bị update
                batch_updates.append({
                    "row": student["row"],
                    "col": col,
                    "score": entry.score,
                    "name": student["name"]
                })
            
            # Ghi điểm vào Google Sheets
            if batch_updates:
                await loading_msg.edit_text(
                    f"⏳ Đang ghi {len(batch_updates)} điểm vào Google Sheets..."
                )
                
                # Tạo/cập nhật headers cho các cột điểm
                for update_item in batch_updates:
                    self.sheets_client.get_or_create_score_header(
                        update_item["col"], test_date_short
                    )
                
                # Batch update scores
                success_count, batch_errors = self.sheets_client.batch_update_scores(batch_updates)
                
                # Cập nhật error_lines nếu có lỗi từ batch update
                if batch_errors:
                    error_lines.extend(batch_errors)
            
            # Tạo summary
            summary = self.parser.generate_batch_summary(match_result, error_lines)
            
            try:
                await loading_msg.edit_text(
                    f"✅ **Hoàn thành xử lý điểm!**\n\n"
                    f"**Lớp:** {selected_class}\n"
                    f"**Ngày kiểm tra:** {test_date}\n\n"
                    f"{summary}\n\n"
                    f"🎉 Cảm ơn bạn đã sử dụng bot!",
                    parse_mode='Markdown'
                )
            except Exception as msg_error:
                logger.error(f"Error sending summary message: {msg_error}")
                # Thử gửi dạng plain text nếu Markdown fail
                try:
                    await loading_msg.edit_text(
                        f"✅ Hoàn thành xử lý điểm!\n\n"
                        f"Lớp: {selected_class}\n"
                        f"Ngày kiểm tra: {test_date}\n\n"
                        f"{summary}\n\n"
                        f"🎉 Cảm ơn bạn đã sử dụng bot!"
                    )
                except Exception as plain_error:
                    logger.error(f"Error sending plain text: {plain_error}")
                    await update.message.reply_text(
                        f"✅ Hoàn thành!\nĐã xử lý {len(valid_entries)} entries, "
                        f"ghi được {len(batch_updates)} điểm."
                    )
            
            logger.info(f"Score input completed for class {selected_class}, "
                       f"processed {len(valid_entries)} entries, "
                       f"updated {len(batch_updates)} records")
            
        except Exception as e:
            logger.error(f"Error processing score input: {e}")
            await loading_msg.edit_text(
                f"❌ **Lỗi xử lý điểm**\n\n"
                f"Đã xảy ra lỗi trong quá trình xử lý:\n"
                f"`{str(e)}`\n\n"
                f"Vui lòng thử lại sau hoặc liên hệ admin."
            )
        
        return ConversationHandler.END

    async def cancel_score_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hủy nhập điểm"""
        await update.message.reply_text("❌ Đã hủy nhập điểm.")
        return ConversationHandler.END