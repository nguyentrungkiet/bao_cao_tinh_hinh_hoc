import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler, ContextTypes
)

from config import (
    TELEGRAM_BOT_TOKEN, MENU_REPORT, MENU_SCORE, 
    CALLBACK_REPORT, CALLBACK_SCORE, CALLBACK_CANCEL, States
)
from flows.report_flow import ReportFlow
from flows.score_flow import ScoreFlow

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Telegram Bot class"""
    
    def __init__(self):
        self.report_flow = ReportFlow()
        self.score_flow = ScoreFlow()
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""🎓 **Chào mừng {user.first_name}!**

🤖 **Bot Thống Kê Điểm**
Hỗ trợ trợ giảng trong việc:
📋 Báo cáo tình hình học 
💯 Nhập điểm kiểm tra hàng loạt

Chọn chức năng từ menu bên dưới:"""
        
        await self.show_main_menu(update, context, welcome_text)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command - show main menu"""
        await self.show_main_menu(update, context, "📋 **Menu Chính**\n\nChọn chức năng:")
    
    def get_main_keyboard(self):
        """Tạo keyboard cố định với các nút chính"""
        keyboard = [
            [KeyboardButton("📋 Báo cáo"), KeyboardButton("💯 Nhập điểm")],
            [KeyboardButton("ℹ️ Hướng dẫn"), KeyboardButton("📱 Menu")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🔧 **Hướng Dẫn Sử Dụng Bot**

**📋 Báo Cáo Tình Hình Học:**
1. Chọn lớp từ danh sách
2. Chọn ngày buổi học (đề xuất hoặc nhập thủ công)
3. Nhập nội dung báo cáo tự do
4. Bot tự động format và gửi vào group lớp

**💯 Nhập Điểm Kiểm Tra:**
1. Chọn lớp từ danh sách  
2. Dán block điểm theo format:
   ```
   💯Điểm bài kiểm tra ngày 🗓️17/01/2026:
   Tên học sinh 1  8.5
   Tên học sinh 2  9.0
   ```
3. Bot tự động nhập vào Google Sheets

**🎯 Lệnh Cơ Bản:**
/start - Bắt đầu sử dụng
/menu - Hiển thị menu chính
/help - Xem hướng dẫn
/cancel - Hủy thao tác hiện tại

**💡 Mẹo:**
- Có thể gõ sai chính tả, bot sẽ tự hiểu
- Điểm từ 0-10, có thể số thập phân  
- Bot tự động tính ngày trễ hạn

Có vấn đề? Liên hệ admin! 📞"""
        
        keyboard = [[InlineKeyboardButton("🔙 Về Menu", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Show main menu with inline keyboard"""
        keyboard = [
            [InlineKeyboardButton(MENU_REPORT, callback_data=CALLBACK_REPORT)],
            [InlineKeyboardButton(MENU_SCORE, callback_data=CALLBACK_SCORE)],
            [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Keyboard cố định
        persistent_keyboard = self.get_main_keyboard()
        
        if update.message:
            await update.message.reply_text(
                message_text, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            # Gửi keyboard cố định
            await update.message.reply_text(
                "👇 Sử dụng menu bên dưới:",
                reply_markup=persistent_keyboard
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                message_text, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "menu":
            await self.show_main_menu(update, context, "📋 **Menu Chính**\n\nChọn chức năng:")
        elif query.data == "help":
            help_text = """🔧 **Hướng Dẫn Sử Dụng Bot**

**📋 Báo Cáo Tình Hình Học:**
1. Chọn lớp → 2. Chọn ngày → 3. Nhập nội dung → 4. Xác nhận gửi

**💯 Nhập Điểm Kiểm Tra:**
1. Chọn lớp → 2. Dán block điểm → 3. Bot tự động xử lý

**🎯 Các Lệnh:**
/start, /menu, /help, /cancel

**💡 Có thể gõ sai chính tả, bot sẽ tự hiểu!**"""
            
            keyboard = [[InlineKeyboardButton("🔙 Về Menu", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                help_text, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            "❓ Lệnh không được nhận diện.\n\n"
            "Sử dụng /menu để xem các chức năng có sẵn."
        )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log errors caused by Updates."""
        logger.error(f'Update {update} caused error {context.error}')
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Đã xảy ra lỗi. Vui lòng thử lại hoặc liên hệ admin."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    def setup_handlers(self):
        """Setup all handlers for the bot"""
        # Basic command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Report flow conversation handler
        report_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.report_flow.start_report, 
                    pattern=f"^{CALLBACK_REPORT}$"
                ),
                MessageHandler(
                    filters.Regex("^📋 Báo cáo$"),
                    self.report_flow.start_report_from_message
                )
            ],
            states={
                States.REPORT_CLASS_SELECTION: [
                    CallbackQueryHandler(self.report_flow.handle_class_selection)
                ],
                States.REPORT_DATE_SELECTION: [
                    CallbackQueryHandler(self.report_flow.handle_date_selection)
                ],
                States.REPORT_DATE_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_flow.handle_custom_date_input)
                ],
                States.REPORT_CONTENT_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_flow.handle_content_input)
                ],
                States.REPORT_CONFIRMATION: [
                    CallbackQueryHandler(self.report_flow.handle_confirmation)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.report_flow.cancel_report)],
            conversation_timeout=1800,  # 30 minutes timeout
        )
        
        # Score flow conversation handler  
        score_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.score_flow.start_score_input, 
                    pattern=f"^{CALLBACK_SCORE}$"
                ),
                MessageHandler(
                    filters.Regex("^💯 Nhập điểm$"),
                    self.score_flow.start_score_input_from_message
                )
            ],
            states={
                States.SCORE_CLASS_SELECTION: [
                    CallbackQueryHandler(self.score_flow.handle_class_selection)
                ],
                States.SCORE_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.score_flow.handle_score_input)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.score_flow.cancel_score_input)],
            conversation_timeout=1800,  # 30 minutes timeout
        )
        
        # Add conversation handlers
        self.application.add_handler(report_conv_handler)
        self.application.add_handler(score_conv_handler)
        
        # Main menu callback handler (for non-conversation callbacks)
        self.application.add_handler(CallbackQueryHandler(self.handle_main_menu_callback))
        
        # Handler cho các nút còn lại từ keyboard cố định (Hướng dẫn, Menu)
        self.application.add_handler(MessageHandler(
            filters.Regex("^(ℹ️ Hướng dẫn|📱 Menu)$"), 
            self.handle_other_keyboard_buttons
        ))
        
        # Unknown command handler
        self.application.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def handle_other_keyboard_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý các nút khác từ keyboard (không phải conversation flows)"""
        text = update.message.text
        
        if text == "ℹ️ Hướng dẫn":
            await self.help_command(update, context)
        elif text == "📱 Menu":
            await self.menu_command(update, context)

    def run(self):
        """Run the bot"""
        # Start bot
        logger.info("🚀 Bot đang khởi động...")
        logger.info("📋 Chức năng báo cáo: ✅")
        logger.info("💯 Chức năng nhập điểm: ✅")
        logger.info("🔗 Google Sheets integration: ✅")
        logger.info("⏰ Timezone: Asia/Ho_Chi_Minh")
        logger.info("📱 Bot sẵn sàng nhận tin nhắn!")
        
        # Create application
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Run bot
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function"""
    try:
        bot = TelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot đã được dừng bởi người dùng")
    except Exception as e:
        logger.error(f"❌ Lỗi khi chạy bot: {e}")
        raise

if __name__ == "__main__":
    # Fix for Windows + Python 3.14 event loop issue
    import sys
    import asyncio
    
    if sys.platform == 'win32':
        # For Python 3.14+, create a new event loop explicitly
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # Create new event loop if none exists or if closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    
    main()