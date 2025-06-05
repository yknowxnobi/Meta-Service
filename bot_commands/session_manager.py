import os
import requests
import time
import asyncio
import json
import random
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Conversation states
WAITING_USERNAME, WAITING_PASSWORD = range(2)

# User states for session management
session_states = {}

# User agents pool for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

async def session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /session command"""
    try:
        user_id = update.effective_user.id
        channel_id = os.getenv('CHANNEL_ID', '@meta_servers')
        
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
            '⚠️ *Your credentials are processed securely and not stored*\n'
            '💡 **Tips for success:**\n'
            '• Use account without 2FA enabled\n'
            '• Ensure account is not recently created\n'
            '• Don\'t use if account was recently locked',
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
        username = update.message.text.strip().replace('@', '')
        
        print(f"📝 Username received from user {user_id}: {username}")
        
        if user_id not in session_states:
            print(f"❌ No session state found for user: {user_id}")
            await update.message.reply_text(
                '❌ **Session expired. Please start again with /session**',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Validate username
        if len(username) < 3 or len(username) > 30:
            await update.message.reply_text(
                '❌ **Invalid username format. Please enter a valid Instagram username.**',
                parse_mode='Markdown'
            )
            return WAITING_USERNAME
        
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
            '⏳ Please wait while we generate your session ID.\n'
            '🔄 This may take up to 30 seconds...',
            parse_mode='Markdown'
        )
        
        # Process login with improved method
        result = await instagram_login_improved(username, password)
        
        if result['success']:
            session_id = result['session_id']
            success_text = f"""✅ **Session Generated Successfully!**

👤 **Username:** `{username}`
🔑 **Session ID:** `{session_id}`

📋 **How to use:**
1. Copy the session ID above
2. Use it in your Instagram automation tools
3. Keep it secure and don't share with others

⚠️ **Important:** 
• Session IDs can expire after some time
• Generate a new one if you get authentication errors
• Don't use this session simultaneously in multiple places"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Generate New", callback_data="new_session")],
                [InlineKeyboardButton("👨‍💻 Support", url="tg://openmessage?user_id=7863546766")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(success_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            error_text = f"""❌ **Login Failed**

👤 **Username:** `{username}`
🚨 **Error:** {result['error']}

🔧 **Troubleshooting:**
• Verify your username and password are correct
• Make sure 2FA is disabled temporarily
• Wait 10-15 minutes if you tried multiple times
• Check if account requires phone/email verification
• Use a different IP/network if possible

💡 **Common Issues:**
• Recently created accounts may not work
• Accounts with recent suspicious activity
• Using VPN/Proxy might cause issues"""
            
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

async def instagram_login_improved(username, password):
    """Improved Instagram login with better error handling"""
    try:
        session = requests.Session()
        
        # Random user agent
        user_agent = random.choice(USER_AGENTS)
        
        # Enhanced headers
        session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        })
        
        print("🔄 Step 1: Getting Instagram login page...")
        
        # Step 1: Get initial page to establish session
        try:
            resp = session.get("https://www.instagram.com/", timeout=15)
            if resp.status_code != 200:
                return {"success": False, "error": f"Failed to load Instagram (Status: {resp.status_code})"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        
        # Small delay to mimic human behavior
        await asyncio.sleep(random.uniform(1, 3))
        
        print("🔄 Step 2: Getting login page...")
        
        # Step 2: Get login page
        try:
            login_resp = session.get("https://www.instagram.com/accounts/login/", timeout=15)
            if login_resp.status_code != 200:
                return {"success": False, "error": f"Failed to load login page (Status: {login_resp.status_code})"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Login page error: {str(e)}"}
        
        # Extract CSRF token
        csrf_token = session.cookies.get('csrftoken')
        if not csrf_token:
            # Try to extract from HTML
            try:
                soup = BeautifulSoup(login_resp.text, 'html.parser')
                csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
            except:
                pass
        
        if not csrf_token:
            return {"success": False, "error": "Could not obtain CSRF token"}
        
        print(f"🔐 CSRF Token obtained: {csrf_token[:10]}...")
        
        # Small delay
        await asyncio.sleep(random.uniform(2, 4))
        
        # Step 3: Prepare login data
        timestamp = int(time.time())
        enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}"
        
        # More comprehensive login payload
        login_data = {
            "username": username,
            "enc_password": enc_password,
            "queryParams": "{}",
            "optIntoOneTap": "false",
            "trustedDeviceRecords": "{}",
            "stopDeletionNonce": "",
            "queryParams": "{}"
        }
        
        # Update headers for login request
        session.headers.update({
            "X-CSRFToken": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Origin": "https://www.instagram.com"
        })
        
        print("📤 Step 3: Sending login request...")
        
        # Step 4: Send login request
        try:
            login_response = session.post(
                "https://www.instagram.com/api/v1/web/accounts/login/ajax/",
                data=login_data,
                timeout=20
            )
            
            if login_response.status_code != 200:
                return {"success": False, "error": f"Login request failed (Status: {login_response.status_code})"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Login request error: {str(e)}"}
        
        # Parse response
        try:
            response_data = login_response.json()
            print(f"📥 Login response: {response_data}")
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid response from Instagram"}
        
        # Check login result
        if response_data.get("authenticated"):
            session_id = session.cookies.get("sessionid")
            if session_id:
                print("✅ Login successful!")
                return {"success": True, "session_id": session_id}
            else:
                return {"success": False, "error": "Login succeeded but no session ID found"}
        
        elif response_data.get("two_factor_required"):
            return {"success": False, "error": "2FA is enabled. Please disable it temporarily"}
        
        elif response_data.get("checkpoint_url"):
            return {"success": False, "error": "Account verification required. Check your email/phone"}
        
        elif "Please wait a few minutes" in str(response_data):
            return {"success": False, "error": "Rate limited. Please wait 15-30 minutes"}
        
        elif "incorrect" in str(response_data).lower():
            return {"success": False, "error": "Incorrect username or password"}
        
        else:
            error_msg = response_data.get("message", "Unknown login error")
            return {"success": False, "error": f"Login failed: {error_msg}"}
            
    except Exception as e:
        print(f"🚨 Login exception: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

async def handle_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for session feature"""
    try:
        query = update.callback_query
        await query.answer()
        
        print(f"🔄 Callback received: {query.data}")
        
        if query.data == "check_session_sub":
            user_id = query.from_user.id
            channel_id = os.getenv('CHANNEL_ID', '@meta_servers')
            
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
                '🔄 **Retry Session Generation**\n\nUse /session command to try again with different credentials or after waiting.',
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

# Test function with more detailed info
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to verify bot is responding"""
    await update.message.reply_text(
        '✅ **Bot is working perfectly!**\n\n'
        '🔧 **Available Commands:**\n'
        '• `/session` - Generate Instagram session ID\n'
        '• `/test` - Test bot functionality\n'
        '• `/cancel` - Cancel current operation\n\n'
        '📝 **Usage Tips:**\n'
        '• Make sure 2FA is disabled\n'
        '• Use established accounts (not new ones)\n'
        '• Wait if you get rate limited',
        parse_mode='Markdown'
    )

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

def setup_test_command(app):
    """Setup test command"""
    app.add_handler(CommandHandler("test", test_command))
