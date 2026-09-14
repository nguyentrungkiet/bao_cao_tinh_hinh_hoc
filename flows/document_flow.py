import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CLASSES, States, 
    CALLBACK_CLASS_PREFIX, CALLBACK_CANCEL
)
from sheets_client import SheetsClient
from utils.chart_generator import generate_document_chart

logger = logging.getLogger(__name__)

class DocumentFlow:
    """ConversationHandler cho chức năng thống kê tài liệu"""
    
    def __init__(self):
        self.sheets_client = SheetsClient()

    async def start_document_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow thống kê tài liệu - chọn lớp (từ callback query)"""
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
            "📚 **Thống kê tài liệu**\n\nVui lòng chọn lớp:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.DOC_CLASS_SELECTION

    async def start_document_flow_from_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow thống kê tài liệu - chọn lớp (từ message/keyboard button)"""
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
            "📚 **Thống kê tài liệu**\n\nVui lòng chọn lớp:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return States.DOC_CLASS_SELECTION

    async def _show_document_status(self, update_obj, context: ContextTypes.DEFAULT_TYPE, selected_class: str, message: str = ""):
        # Lấy data tài liệu theo khối (ví dụ: 6.1 -> 6, 7.2 -> 7)
        base_class = selected_class.split('.')[0]
        
        # Lấy data tài liệu cho lớp
        docs = self.sheets_client.get_document_data(base_class)
        context.user_data["docs"] = docs
        
        if not docs:
            text = f"📚 **Thống kê tài liệu - Khối {base_class}**\n\nKhông có dữ liệu tài liệu cho khối này."
            keyboard = [[InlineKeyboardButton("❌ Thoát", callback_data=CALLBACK_CANCEL)]]
        else:
            text = f"📚 **Thống kê tài liệu - Khối {base_class}**\n\n"
            if message:
                text += f"_{message}_\n\n"
            text += "📖 **Chương** | 📦 **Số lượng còn**\n"
            text += "-" * 30 + "\n"
            for doc in docs:
                text += f"Chương {doc['chapter']} | {doc['remaining']}\n"
                
            keyboard = [
                [InlineKeyboardButton("🔄 Cập nhật số lượng", callback_data="doc_update")],
                [InlineKeyboardButton("📊 Xem biểu đồ", callback_data="doc_chart")],
                [InlineKeyboardButton("❌ Thoát", callback_data=CALLBACK_CANCEL)]
            ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update_obj, 'edit_message_text'):
            await update_obj.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update_obj.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_class_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý chọn lớp và hiển thị tình hình tài liệu"""
        query = update.callback_query
        await query.answer()
        
        if query.data == CALLBACK_CANCEL:
            await query.edit_message_text("❌ Đã hủy thống kê tài liệu.")
            return ConversationHandler.END
            
        selected_class = query.data[len(CALLBACK_CLASS_PREFIX):]
        context.user_data["selected_class"] = selected_class
        
        await self._show_document_status(query, context, selected_class)
        return States.DOC_ACTION_SELECTION

    async def handle_action_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý chọn hành động (cập nhật, xem biểu đồ, hay hủy)"""
        query = update.callback_query
        await query.answer()
        
        if query.data == CALLBACK_CANCEL:
            await query.edit_message_text("❌ Đã thoát thống kê tài liệu.")
            return ConversationHandler.END
            
        if query.data == "doc_chart":
            docs = context.user_data.get("docs", [])
            base_class = context.user_data["selected_class"].split('.')[0]
            if docs:
                # Gửi ảnh biểu đồ
                chart_buf = generate_document_chart(base_class, docs)
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=chart_buf,
                    caption=f"📊 Biểu đồ thống kê tài liệu Khối {base_class}"
                )
            # Không return ConversationHandler.END để người dùng vẫn có thể click các nút ở menu hiện tại
            return States.DOC_ACTION_SELECTION
            
        if query.data == "doc_update":
            docs = context.user_data.get("docs", [])
            if not docs:
                await self._show_document_status(query, context, context.user_data["selected_class"], "Không có chương nào để cập nhật.")
                return States.DOC_ACTION_SELECTION
                
            keyboard = []
            for doc in docs:
                keyboard.append([InlineKeyboardButton(f"Chương {doc['chapter']}", callback_data=f"chap_{doc['row']}")])
                
            keyboard.append([InlineKeyboardButton("🔙 Trở lại", callback_data="doc_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            base_class = context.user_data["selected_class"].split('.')[0]
            await query.edit_message_text(
                f"🔄 **Cập nhật số lượng tài liệu - Khối {base_class}**\n\nChọn chương bạn muốn cập nhật:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return States.DOC_CHAPTER_SELECTION
            
        return States.DOC_ACTION_SELECTION

    async def handle_chapter_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý chọn chương cần cập nhật"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "doc_back":
            await self._show_document_status(query, context, context.user_data["selected_class"])
            return States.DOC_ACTION_SELECTION
            
        if query.data.startswith("chap_"):
            row = int(query.data[5:])
            context.user_data["update_row"] = row
            
            # Find chapter name for display
            docs = context.user_data.get("docs", [])
            chapter = next((d['chapter'] for d in docs if d['row'] == row), "Unknown")
            context.user_data["update_chapter"] = chapter
            
            base_class = context.user_data["selected_class"].split('.')[0]
            await query.edit_message_text(
                f"📝 **Cập nhật số lượng - Khối {base_class}**\n\n"
                f"Chương: {chapter}\n"
                f"Vui lòng nhập số lượng tài liệu còn lại (chỉ nhập số):",
                parse_mode='Markdown'
            )
            return States.DOC_UPDATE_INPUT
            
        return States.DOC_CHAPTER_SELECTION

    async def handle_update_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý số lượng mới"""
        text = update.message.text.strip()
        
        if not text.isdigit():
            await update.message.reply_text(
                "❌ Vui lòng chỉ nhập số nguyên hợp lệ.\nNhập lại số lượng:",
            )
            return States.DOC_UPDATE_INPUT
            
        new_count = int(text)
        row = context.user_data.get("update_row")
        
        if row:
            success = self.sheets_client.update_document_count(row, new_count)
            if success:
                message = f"✅ Đã cập nhật Chương {context.user_data.get('update_chapter')} thành {new_count} tài liệu."
            else:
                message = "❌ Cập nhật thất bại. Vui lòng thử lại sau."
        else:
            message = "❌ Lỗi: Không tìm thấy dòng cần cập nhật."
            
        await self._show_document_status(update.message, context, context.user_data["selected_class"], message)
        return States.DOC_ACTION_SELECTION

    async def cancel_document_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hủy thống kê tài liệu"""
        await update.message.reply_text("❌ Đã hủy thống kê tài liệu.")
        return ConversationHandler.END
