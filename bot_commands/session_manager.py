import os
import requests
import time
import asyncio
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Conversation states
WAITING_USERNAME, WAITING_PASSWORD = range(2)

# User states for session management
session_states = {}

async def session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /session command"""
    try:
        user_id = update.effective_user.id
        channel_id = os.getenv('CHANNEL_ID', '@meta_services')
        
        print(f"📥 Session command received from user: {user_id}")
        
        # Check subscription
        try:
            member = await context.bot.get_chat_member(channel_id, user_id)
            print(f"👤 User membership status: {member.status}")
            
            if member.status in ['left', 'kicked']:
                keyboard = [
                    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_id.replace('@', '')}")],
                    [InlineKeyboardButton("✅ I Joined", callback_data="check_session_sub")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "⚠️ **Please join our channel first to use this feature.**",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
        except Exception as e:
            print(f"❌ Error checking subscription: {e}")
            # Continue anyway if channel check fails
            pass
        
        await update.message.reply_text(
            '🔐 **Instagram Session Manager**\n\n'
            '👤 Please enter your Instagram username:\n\n'
            '⚠️ *Your credentials are processed securely and not stored*',
            parse_mode='Markdown'
        )
        
        session_states[user_id] = {}
        print(f"✅ Session state initialized for user: {user_id}")
        return WAITING_USERNAME
        
    except Exception as e:
        print(f"🚨 Error in session_command: {e}")
        await update.message.reply_text(
            '❌ **An error occurred. Please try again later.**',
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def handle_session_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle username input for session"""
    try:
        user_id = update.effective_user.id
        username = update.message.text.strip()
        
        print(f"📝 Username received from user {user_id}: {username}")
        
        if user_id not in session_states:
            print(f"❌ No session state found for user: {user_id}")
            await update.message.reply_text(
                '❌ **Session expired. Please start again with /session**',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        session_states[user_id]['username'] = username
        
        # Delete the username message for security
        try:
            await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
        except Exception as e:
            print(f"⚠️ Could not delete username message: {e}")
        
        await update.message.reply_text(
            f'✅ **Username:** `{username}`\n\n'
            '🔒 Now please enter your Instagram password:\n\n'
            '⚠️ *Your password will be deleted immediately after processing*',
            parse_mode='Markdown'
        )
        
        return WAITING_PASSWORD
        
    except Exception as e:
        print(f"🚨 Error in handle_session_username: {e}")
        await update.message.reply_text(
            '❌ **An error occurred. Please try again.**',
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def handle_session_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password input and generate session"""
    try:
        user_id = update.effective_user.id
        password = update.message.text.strip()
        
        print(f"🔐 Password received from user: {user_id}")
        
        if user_id not in session_states:
            print(f"❌ No session state found for user: {user_id}")
            await update.message.reply_text(
                '❌ **Session expired. Please start again with /session**',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        username = session_states[user_id]['username']
        
        # Delete the password message immediately
        try:
            await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
        except Exception as e:
            print(f"⚠️ Could not delete password message: {e}")
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            '🔄 **Processing login request...**\n\n'
            '⏳ Please wait while we generate your session ID.',
            parse_mode='Markdown'
        )
        
        # Process login
        session_id = await instagram_login(username, password)
        
        if session_id:
            success_text = f"""✅ **Session Generated Successfully!**

👤 **Username:** `{username}`
🔑 **Session ID:** `{session_id}`

📋 **How to use:**
1. Copy the session ID above
2. Use it in your Instagram automation tools
3. Keep it secure and don't share with others

⚠️ **Important:** Session IDs can expire. Generate a new one if needed."""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Generate New", callback_data="new_session")],
                [InlineKeyboardButton("👨‍💻 Support", url="tg://openmessage?user_id=7863546766")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(success_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            error_text = f"""❌ **Login Failed**

👤 **Username:** `{username}`
🚨 **Error:** Invalid credentials or account locked

🔧 **Troubleshooting:**
• Check your username and password
• Make sure your account is not locked
• Try again after some time
• Disable 2FA temporarily if enabled"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="retry_session")],
                [InlineKeyboardButton("👨‍💻 Support", url="tg://openmessage?user_id=7863546766")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(error_text, parse_mode='Markdown', reply_markup=reply_markup)
        
        # Clear session state
        if user_id in session_states:
            del session_states[user_id]
        
        return ConversationHandler.END
        
    except Exception as e:
        print(f"🚨 Error in handle_session_password: {e}")
        await update.message.reply_text(
            '❌ **An error occurred during processing. Please try again.**',
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def instagram_login(username, password):
    """Login to Instagram and get session ID"""
    try:
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Accept-Language": "en-US,en;q=0.9"
        })
        
        # Step 1: Get CSRF token
        print("🔄 Getting CSRF Token...")
        resp = session.get("https://www.instagram.com/accounts/login/", timeout=10)
        
        # Extract CSRF token from cookies
        csrf_token = session.cookies.get('csrftoken')
        
        if not csrf_token:
            print("❌ CSRF token not found.")
            return None
        
        print(f"🔐 CSRF Token: {csrf_token}")
        
        # Step 2: Login
        enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}"
        
        payload = {
            "username": username,
            "enc_password": enc_password,
            "queryParams": "{}",
            "optIntoOneTap": "false"
        }
        
        session.headers.update({
            "X-CSRFToken": csrf_token,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        print("📤 Sending login request...")
        login_resp = session.post(
            "https://www.instagram.com/api/v1/web/accounts/login/ajax/",
            data=payload,
            timeout=15
        )
        
        data = login_resp.json()
        print("📥 Response:", data)
        
        if data.get("authenticated"):
            session_id = session.cookies.get("sessionid")
            print("✅ Login successful!")
            print("🔑 Session ID:", session_id)
            return session_id
        else:
            print("❌ Login failed:", data.get("message", "Unknown error"))
            return None
            
    except requests.exceptions.Timeout:
        print("⏱️ Request timeout")
        return None
    except Exception as e:
        print(f"🚨 Login error: {e}")
        return None

async def handle_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for session feature"""
    try:
        query = update.callback_query
        await query.answer()
        
        print(f"🔄 Callback received: {query.data}")
        
        if query.data == "check_session_sub":
            user_id = query.from_user.id
            channel_id = os.getenv('CHANNEL_ID', '@meta_services')
            
            try:
                member = await context.bot.get_chat_member(channel_id, user_id)
                if member.status not in ['left', 'kicked']:
                    await query.edit_message_text(
                        '✅ **Subscription verified!**\n\nNow use /session to proceed.',
                        parse_mode='Markdown'
                    )
                else:
                    await query.answer('❌ You still need to join the channel.', show_alert=True)
            except Exception as e:
                print(f"❌ Error checking subscription: {e}")
                await query.answer('❌ Error checking subscription.', show_alert=True)
            return
        
        elif query.data == "new_session":
            await query.edit_message_text(
                '🔄 **Generate New Session**\n\nUse /session command to start the process again.',
                parse_mode='Markdown'
            )
        
        elif query.data == "retry_session":
            await query.edit_message_text(
                '🔄 **Retry Session Generation**\n\nUse /session command to try again.',
                parse_mode='Markdown'
            )
            
    except Exception as e:
        print(f"🚨 Error in handle_session_callback: {e}")

async def cancel_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the session conversation"""
    user_id = update.effective_user.id
    if user_id in session_states:
        del session_states[user_id]
    
    await update.message.reply_text(
        '❌ **Session generation cancelled.**',
        parse_mode='Markdown'
    )
    return ConversationHandler.END

def setup_session_commands(app, admin_id=None, channel_id=None):
    """Setup session manager commands"""
    try:
        # Create conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("session", session_command)],
            states={
                WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_session_username)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_session_password)],
            },
            fallbacks=[CommandHandler("cancel", cancel_session)],
            per_message=False,
            per_chat=True,
            per_user=True,
        )
        
        # Add handlers
        app.add_handler(conv_handler)
        app.add_handler(CallbackQueryHandler(handle_session_callback))
        
        print("✅ Session manager commands loaded successfully")
        
    except Exception as e:
        print(f"🚨 Error setting up session commands: {e}")

# Test function to verify bot is working
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to verify bot is responding"""
    await update.message.reply_text(
        '✅ **Bot is working!**\n\nUse /session to start the session generation process.',
        parse_mode='Markdown'
    )

def setup_test_command(app):
    """Setup test command"""
    app.add_handler(CommandHandler("test", test_command))
