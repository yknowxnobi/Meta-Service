import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Test function to check if bot is working
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to check bot responsiveness"""
    print(f"TEST: Bot is working! User: {update.effective_user.id}")
    await update.message.reply_text("✅ Bot is working! Instagram commands loaded.")

async def simple_insta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple insta command for testing"""
    print(f"SIMPLE INSTA: Command received from {update.effective_user.id}")
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a username: /insta username")
        return
    
    await update.message.reply_text(f"🔄 Testing with username: {context.args[0]}")

def main():
    # Your bot token
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    
    print("Starting test bot...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add test handlers
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("insta", simple_insta))
    
    print("Handlers added. Starting polling...")
    
    # Start the bot
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
