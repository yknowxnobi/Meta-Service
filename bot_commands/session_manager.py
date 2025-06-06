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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
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
        start_time = time.time()
        processing_msg = await update.message.reply_text(
            '🔄 **Processing login request...**\n\n'
            '⏳ Please wait while we generate your session ID.\n'
            '🔄 This may take up to 30 seconds...',
            parse_mode='Markdown'
        )
        
        # Process login with new method
        result = await instagram_login_v3(username, password)
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
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
• Don't use this session simultaneously in multiple places

≭ **Bot By / Dev:** @luciInVain
≭ **Time Taken:** `{time_taken}` seconds"""
            
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
• Try using different network/VPN

💡 **Common Issues:**
• Recently created accounts may not work
• Accounts with recent suspicious activity
• Rate limiting from Instagram

≭ **Bot By / Dev:** @luciInVain
≭ **Time Taken:** `{time_taken}` seconds"""
            
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

async def instagram_login_v3(username, password):
    """Latest Instagram login method 2025"""
    try:
        session = requests.Session()
        
        # Use mobile user agent for better success rate
        user_agent = "Instagram 276.0.0.18.119 Android (33/13; 420dpi; 1080x2340; samsung; SM-G991B; o1s; exynos2100; en_US; 458229237)"
        
        # Set mobile headers
        session.headers.update({
            "User-Agent": user_agent,
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        })
        
        print("🔄 Step 1: Getting Instagram mobile page...")
        
        # Get Instagram mobile page
        try:
            resp = session.get("https://www.instagram.com/", timeout=15)
            if resp.status_code != 200:
                return {"success": False, "error": f"Failed to load page (Status: {resp.status_code})"}
        except Exception as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
        
        # Extract necessary data from page
        csrf_token = None
        rollout_hash = None
        
        # Get CSRF token from cookies
        for cookie in session.cookies:
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value
                break
        
        # Extract rollout hash from page source
        try:
            import re
            rollout_match = re.search(r'"rollout_hash":"([^"]+)"', resp.text)
            if rollout_match:
                rollout_hash = rollout_match.group(1)
        except:
            rollout_hash = "c3b14f1ba957"  # fallback
        
        if not csrf_token:
            return {"success": False, "error": "Could not get CSRF token"}
        
        print(f"🔐 CSRF Token: {csrf_token[:10]}...")
        print(f"🎲 Rollout Hash: {rollout_hash}")
        
        await asyncio.sleep(random.uniform(1, 2))
        
        # Prepare login data with mobile format
        timestamp = int(time.time())
        
        # Use simple password format for mobile
        login_data = {
            "username": username,
            "password": password,
            "queryParams": "{}",
            "optIntoOneTap": "false"
        }
        
        # Update headers for login
        session.headers.update({
            "X-CSRFToken": csrf_token,
            "X-Instagram-AJAX": rollout_hash,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Origin": "https://www.instagram.com"
        })
        
        print("📤 Step 2: Sending login request...")
        
        # Send login request
        try:
            login_url = "https://www.instagram.com/accounts/login/ajax/"
            login_response = session.post(login_url, data=login_data, timeout=20)
            
            print(f"📊 Login response status: {login_response.status_code}")
            
            if login_response.status_code != 200:
                return {"success": False, "error": f"Login failed (Status: {login_response.status_code})"}
                
        except Exception as e:
            return {"success": False, "error": f"Request error: {str(e)}"}
        
        # Parse JSON response
        try:
            response_data = login_response.json()
            print(f"📥 Response data: {response_data}")
        except:
            print("❌ Failed to parse JSON response")
            return {"success": False, "error": "Invalid response from Instagram"}
        
        # Check response status
        if response_data.get("authenticated") == True:
            # Success - extract session ID
            session_id = None
            for cookie in session.cookies:
                if cookie.name == 'sessionid':
                    session_id = cookie.value
                    break
            
            if session_id:
                print("✅ Login successful - Session ID obtained!")
                return {"success": True, "session_id": session_id}
            else:
                return {"success": False, "error": "Login successful but no session ID found"}
        
        elif response_data.get("two_factor_required"):
            return {"success": False, "error": "2FA enabled - Please disable temporarily"}
        
        elif response_data.get("checkpoint_url"):
            return {"success": False, "error": "Account verification required - Check email/SMS"}
        
        elif "Please wait a few minutes" in str(response_data):
            return {"success": False, "error": "Rate limited - Wait 15-30 minutes"}
        
        elif "The username you entered doesn't appear to belong" in str(response_data):
            return {"success": False, "error": "Username not found"}
        
        elif "Sorry, your password was incorrect" in str(response_data):
            return {"success": False, "error": "Incorrect password"}
        
        else:
            # Extract error message
            error_msg = "Unknown error"
            if "message" in response_data:
                error_msg = response_data["message"]
            elif "errors" in response_data:
                if "error" in response_data["errors"]:
                    error_msg = response_data["errors"]["error"]
            
            return {"success": False, "error": f"Login failed: {error_msg}"}
            
    except Exception as e:
        print(f"🚨 Exception in login: {e}")
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

# Test function
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
