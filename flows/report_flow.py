import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CLASSES, GROUP_CHAT_IDS, TIMEZONE, States, 
    CALLBACK_CLASS_PREFIX, CALLBACK_DATE_USE, CALLBACK_DATE_CUSTOM,
    CALLBACK_CONFIRM_SEND, CALLBACK_EDIT_AGAIN, CALLBACK_CANCEL
)
from schedule import (
    get_latest_session_date, format_session_date, validate_class_date,
    get_class_time_range, calculate_lateness_days
)
from parsers.report_parser import ReportParser

logger = logging.getLogger(__name__)

class ReportFlow:
    """ConversationHandler cho chức năng báo cáo tình hình học"""
    
    def __init__(self):
        self.parser = ReportParser()

    async def start_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow báo cáo - chọn lớp (từ callback query)"""
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
            "📋 **Báo cáo tình hình học**\n\nVui lòng chọn lớp:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.REPORT_CLASS_SELECTION
    
    async def start_report_from_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow báo cáo - chọn lớp (từ message/keyboard button)"""
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
            "📋 **Báo cáo tình hình học**\n\nVui lòng chọn lớp:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.REPORT_CLASS_SELECTION

    async def handle_class_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý chọn lớp và đề xuất ngày"""
        query = update.callback_query
        await query.answer()
        
        if query.data == CALLBACK_CANCEL:
            await query.edit_message_text("❌ Đã hủy báo cáo.")
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
        
        # Tính buổi học gần nhất
        latest_date = get_latest_session_date(selected_class)
        
        if not latest_date:
            await query.edit_message_text(
                f"❌ Không tìm thấy buổi học gần đây cho lớp {selected_class}. "
                "Vui lòng liên hệ admin."
            )
            return ConversationHandler.END
        
        # Format ngày đề xuất
        suggested_date_str = format_session_date(latest_date)
        context.user_data["suggested_date"] = latest_date
        
        # Tạo keyboard chọn ngày
        keyboard = [
            [InlineKeyboardButton("✅ Dùng ngày đề xuất", callback_data=CALLBACK_DATE_USE)],
            [InlineKeyboardButton("📅 Nhập ngày khác", callback_data=CALLBACK_DATE_CUSTOM)],
            [InlineKeyboardButton("❌ Hủy", callback_data=CALLBACK_CANCEL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📅 **Chọn buổi học cần báo cáo**\n\n"
            f"Lớp: **{selected_class}**\n"
            f"Buổi học gần nhất: **{suggested_date_str}**\n\n"
            f"Chọn một trong các tùy chọn:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.REPORT_DATE_SELECTION

    async def handle_date_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý chọn ngày báo cáo"""
        query = update.callback_query
        await query.answer()
        
        if query.data == CALLBACK_CANCEL:
            await query.edit_message_text("❌ Đã hủy báo cáo.")
            return ConversationHandler.END
        
        selected_class = context.user_data["selected_class"]
        
        if query.data == CALLBACK_DATE_USE:
            # Dùng ngày đề xuất
            session_date = context.user_data["suggested_date"]
            context.user_data["session_date"] = session_date
            
            # Chuyển đến nhập nội dung
            return await self._request_report_content(update, context, selected_class, session_date)
        
        elif query.data == CALLBACK_DATE_CUSTOM:
            # Yêu cầu nhập ngày khác
            await query.edit_message_text(
                f"📅 **Nhập ngày buổi học**\n\n"
                f"Lớp: **{selected_class}**\n"
                f"Vui lòng nhập ngày theo định dạng **dd/mm/yyyy**\n\n"
                f"Ví dụ: 15/01/2026\n\n"
                f"_Gõ /cancel để hủy_",
                parse_mode='Markdown'
            )
            return States.REPORT_DATE_INPUT
        
        await query.edit_message_text("❌ Lựa chọn không hợp lệ.")
        return ConversationHandler.END

    async def handle_custom_date_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý input ngày tùy chọn"""
        date_input = update.message.text.strip()
        selected_class = context.user_data["selected_class"]
        
        # Validate ngày
        is_valid, parsed_date, error_message = validate_class_date(selected_class, date_input)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ **Lỗi nhập ngày:**\n{error_message}\n\n"
                f"Vui lòng nhập lại theo định dạng **dd/mm/yyyy**\n"
                f"_Gõ /cancel để hủy_",
                parse_mode='Markdown'
            )
            return States.REPORT_DATE_INPUT
        
        # Lưu ngày đã chọn
        context.user_data["session_date"] = parsed_date
        
        # Chuyển đến nhập nội dung
        return await self._request_report_content(update, context, selected_class, parsed_date)

    async def _request_report_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    class_name: str, session_date: datetime):
        """Yêu cầu nhập nội dung báo cáo"""
        session_date_str = format_session_date(session_date)
        
        # Gửi hướng dẫn input
        guide_text = self.parser.generate_input_guide()
        
        message_text = (
            f"📝 **Nhập nội dung báo cáo**\n\n"
            f"**Lớp:** {class_name}\n"
            f"**Buổi học:** {session_date_str}\n\n"
            f"{guide_text}\n\n"
            f"_Gõ /cancel để hủy_"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text, 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                message_text, 
                parse_mode='Markdown'
            )
        
        return States.REPORT_CONTENT_INPUT

    async def handle_content_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý nội dung báo cáo và tạo preview"""
        content = update.message.text.strip()
        
        if not content:
            await update.message.reply_text(
                "❌ Nội dung trống. Vui lòng nhập nội dung báo cáo.\n"
                "_Gõ /cancel để hủy_",
                parse_mode='Markdown'
            )
            return States.REPORT_CONTENT_INPUT
        
        # Parse nội dung
        report_data = self.parser.parse_report_content(content)
        
        # Lấy thông tin đã lưu
        selected_class = context.user_data["selected_class"]
        session_date = context.user_data["session_date"]
        
        # Tính thông tin cho báo cáo
        session_date_str = format_session_date(session_date)
        time_range = get_class_time_range(selected_class)
        lateness_days = calculate_lateness_days(session_date)
        
        # Tạo preview
        preview_report = self.parser.generate_report_preview(
            report_data, selected_class, session_date_str, 
            time_range, lateness_days
        )
        
        # Lưu data để gửi sau
        context.user_data["report_preview"] = preview_report
        context.user_data["report_data"] = report_data
        
        # Tạo keyboard xác nhận
        keyboard = [
            [InlineKeyboardButton("✅ Xác nhận gửi", callback_data=CALLBACK_CONFIRM_SEND)],
            [InlineKeyboardButton("✏️ Sửa lại", callback_data=CALLBACK_EDIT_AGAIN)],
            [InlineKeyboardButton("❌ Hủy", callback_data=CALLBACK_CANCEL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📋 **Preview báo cáo:**\n\n"
            f"```\n{preview_report}\n```\n\n"
            f"Xác nhận gửi báo cáo này vào nhóm lớp?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.REPORT_CONFIRMATION

    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý xác nhận gửi báo cáo"""
        query = update.callback_query
        await query.answer()
        
        if query.data == CALLBACK_CANCEL:
            await query.edit_message_text("❌ Đã hủy báo cáo.")
            return ConversationHandler.END
        
        elif query.data == CALLBACK_EDIT_AGAIN:
            # Quay lại nhập nội dung
            selected_class = context.user_data["selected_class"]
            session_date = context.user_data["session_date"]
            return await self._request_report_content(update, context, selected_class, session_date)
        
        elif query.data == CALLBACK_CONFIRM_SEND:
            # Gửi báo cáo
            return await self._send_report_to_group(update, context)
        
        await query.edit_message_text("❌ Lựa chọn không hợp lệ.")
        return ConversationHandler.END

    async def _send_report_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gửi báo cáo vào group của lớp"""
        try:
            selected_class = context.user_data["selected_class"]
            report_preview = context.user_data["report_preview"]
            
            # Lấy chat_id của group
            group_chat_id = GROUP_CHAT_IDS.get(selected_class)
            if not group_chat_id:
                await update.callback_query.edit_message_text(
                    f"❌ Không tìm thấy group chat cho lớp {selected_class}. "
                    "Vui lòng liên hệ admin."
                )
                return ConversationHandler.END
            
            # Gửi báo cáo vào group
            await context.bot.send_message(
                chat_id=group_chat_id,
                text=report_preview,
                parse_mode='Markdown'
            )
            
            # Thông báo thành công cho trợ giảng
            await update.callback_query.edit_message_text(
                f"✅ **Đã gửi báo cáo thành công!**\n\n"
                f"Báo cáo đã được gửi vào nhóm lớp **{selected_class}**.\n\n"
                f"Cảm ơn bạn đã sử dụng bot! 🎉"
            )
            
            logger.info(f"Report sent successfully to group {group_chat_id} for class {selected_class}")
            
        except Exception as e:
            logger.error(f"Failed to send report to group: {e}")
            
            await update.callback_query.edit_message_text(
                f"❌ **Lỗi gửi báo cáo**\n\n"
                f"Không thể gửi báo cáo vào nhóm lớp {selected_class}.\n"
                f"Có thể bot chưa được thêm vào group hoặc không có quyền gửi tin nhắn.\n\n"
                f"Vui lòng liên hệ admin để được hỗ trợ."
            )
        
        return ConversationHandler.END

    async def cancel_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hủy báo cáo"""
        await update.message.reply_text("❌ Đã hủy báo cáo.")
        return ConversationHandler.END