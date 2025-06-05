import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all modules
from bot_commands.insta_info import setup_insta_commands
from bot_commands.meth_analyzer import setup_meth_commands
from bot_commands.report_tool import setup_report_commands
from bot_commands.session_manager import setup_session_commands
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.admin_id = int(os.getenv('ADMIN_ID', '0'))
        self.channel_id = os.getenv('CHANNEL_ID', '@meta_service')
        
        if not self.token:
            print("❌ BOT_TOKEN not found in environment variables!")
            sys.exit(1)
        
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command handlers"""
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Setup feature-specific handlers
        setup_insta_commands(self.app, self.admin_id, self.channel_id)
        setup_meth_commands(self.app, self.admin_id, self.channel_id)
        setup_report_commands(self.app, self.admin_id, self.channel_id)
        setup_session_commands(self.app, self.admin_id, self.channel_id)
        
        print("✅ All handlers setup complete!")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        
        # Notify admin about new user
        if self.admin_id and user.id != self.admin_id:
            try:
                await context.bot.send_message(
                    self.admin_id,
                    f"🆕 New user started bot:\n\n"
                    f"• Name: {user.first_name or 'N/A'}\n"
                    f"• Username: @{user.username or 'N/A'}\n"
                    f"• ID: <code>{user.id}</code>",
                    parse_mode='HTML'
                )
            except:
                pass
        
        welcome_text = f"""
🚀 **Welcome {user.first_name or 'User'}!**

🤖 **Multi-Feature Instagram Bot**

**Available Commands:**
• `/insta` - Get Instagram user details
• `/meth` - Instagram analysis tool
• `/report` - Instagram report tool  
• `/session` - Get Instagram session ID
• `/help` - Show this help message

**Choose your feature and get started!**
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup={
                'inline_keyboard': [
                    [{'text': '📢 Updates', 'url': f'https://t.me/{self.channel_id.replace("@", "")}'}],
                    [{'text': '💬 Support', 'url': 'https://t.me/offchats'}]
                ]
            }
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
📚 **Available Commands:**

🔍 **Instagram Info:**
• `/insta <username>` - Get user details & creation year

🎯 **Meth Analysis:**
• `/meth` - Advanced Instagram analysis

📊 **Report Tool:**
• `/report` - Instagram report automation

🔐 **Session Manager:**
• `/session` - Get Instagram session ID

❓ **Help:**
• `/help` - Show this message
• `/start` - Restart the bot

**Note:** Some features require channel subscription.
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup={
                'inline_keyboard': [
                    [{'text': '📢 Channel', 'url': f'https://t.me/{self.channel_id.replace("@", "")}'}],
                    [{'text': '💬 Support', 'url': 'https://t.me/nobi_shops'}]
                ]
            }
        )
    
    def run(self):
        """Run the bot"""
        print(f"🚀 Starting Telegram Bot...")
        print(f"📢 Channel: {self.channel_id}")
        print(f"👑 Admin ID: {self.admin_id}")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
