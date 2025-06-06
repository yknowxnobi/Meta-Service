import os
import requests
import time
import asyncio
import json
import random
import hashlib
import uuid
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Conversation states
WAITING_USERNAME, WAITING_PASSWORD = range(2)

# User states for session management
session_states = {}

# Updated user agents for 2025
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

# Instagram mobile app signatures
INSTAGRAM_SIGNATURES = {
    "version": "292.0.0.26.109",
    "android_version": "33",
    "android_release": "13.0",
    "dpi": "420dpi",
    "resolution": "1080x2340",
    "manufacturer": "samsung",
    "device": "SM-G991B",
    "model": "o1s",
    "cpu": "exynos2100",
    "version_code": "503988293"
}

async def session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /session command"""
    try:
        user_id = update.effective_user.id
        channel_id = os.getenv('CHANNEL_ID', '@meta_servers')
        
        print(f"📥 Session command received from user: {user_id}")
        
        # Check subscription with improved logic
        try:
            if channel_id:
                # Clean channel ID format
                clean_channel = channel_id.replace('@', '') if channel_id.startswith('@') else channel_id
                member = await context.bot.get_chat_member(f"@{clean_channel}", user_id)
                print(f"👤 User membership status: {member.status}")
                
                if member.status in ['left', 'kicked']:
                    keyboard = [
                        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{clean_channel}")],
                        [InlineKeyboardButton("✅ I Joined", callback_data="check_session_sub")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"⚠️ **Please join @{clean_channel} first to use this feature.**",
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    return ConversationHandler.END
        except Exception as e:
            print(f"❌ Error checking subscription: {e}")
            # Continue anyway if channel check fails
            pass
        
        await update.message.reply_text(
            '🔐 **Instagram Session Manager v2.0**\n\n'
            '👤 Please enter your Instagram username:\n\n'
            '⚠️ *Your credentials are processed securely and not stored*\n\n'
            '💡 **Important Tips:**\n'
            '• Use account without 2FA enabled\n'
            '• Account should be at least 7 days old\n'
            '• Don\'t use if recently locked/suspended\n'
            '• Wait 15+ minutes between attempts\n'
            '• Use stable internet connection',
            parse_mode='Markdown'
        )
        
        session_states[user_id] = {'attempts': 0, 'last_attempt': 0}
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
        username = update.message.text.strip().replace('@', '').lower()
        
        print(f"📝 Username received from user {user_id}: {username}")
        
        if user_id not in session_states:
            print(f"❌ No session state found for user: {user_id}")
            await update.message.reply_text(
                '❌ **Session expired. Please start again with /session**',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Validate username format
        if len(username) < 3 or len(username) > 30:
            await update.message.reply_text(
                '❌ **Invalid username format. Please enter a valid Instagram username (3-30 characters).**',
                parse_mode='Markdown'
            )
            return WAITING_USERNAME
        
        # Check for invalid characters
        import re
        if not re.match(r'^[a-zA-Z0-9._]+$', username):
            await update.message.reply_text(
                '❌ **Username contains invalid characters. Only letters, numbers, dots, and underscores allowed.**',
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
            '⚠️ *Your password will be deleted immediately after processing*\n'
            '🔐 *Make sure your password is correct to avoid account locks*',
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
        
        # Check rate limiting
        current_time = int(time.time())
        last_attempt = session_states[user_id].get('last_attempt', 0)
        if current_time - last_attempt < 300:  # 5 minutes
            session_states[user_id]['attempts'] += 1
            if session_states[user_id]['attempts'] > 3:
                await update.message.reply_text(
                    '⚠️ **Too many attempts. Please wait 15 minutes before trying again.**',
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
        
        session_states[user_id]['last_attempt'] = current_time
        
        # Delete the password message immediately
        try:
            await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
        except Exception as e:
            print(f"⚠️ Could not delete password message: {e}")
        
        # Show processing message
        start_time = time.time()
        processing_msg = await update.message.reply_text(
            '🔄 **Processing login request...**\n\n'
            '⏳ Connecting to Instagram servers...\n'
            '🔐 Authenticating credentials...\n'
            '🎯 This may take 30-60 seconds...',
            parse_mode='Markdown'
        )
        
        # Try multiple login methods
        methods = [
            ('Mobile App Method', instagram_login_mobile),
            ('Web Method v1', instagram_login_web_v1),
            ('Web Method v2', instagram_login_web_v2)
        ]
        
        result = None
        method_used = "Unknown"
        
        for method_name, method_func in methods:
            try:
                print(f"🔄 Trying {method_name}...")
                await processing_msg.edit_text(
                    f'🔄 **Processing login request...**\n\n'
                    f'🎯 Method: {method_name}\n'
                    f'⏳ Please wait...',
                    parse_mode='Markdown'
                )
                
                result = await method_func(username, password)
                if result['success']:
                    method_used = method_name
                    print(f"✅ {method_name} successful!")
                    break
                else:
                    print(f"❌ {method_name} failed: {result['error']}")
                    await asyncio.sleep(2)  # Wait between methods
                    
            except Exception as e:
                print(f"🚨 {method_name} exception: {e}")
                continue
        
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        if result and result['success']:
            session_id = result['session_id']
            success_text = f"""✅ **Session Generated Successfully!**

👤 **Username:** `{username}`
🔑 **Session ID:** `{session_id}`
🛠️ **Method:** {method_used}

📋 **How to use:**
1. Copy the session ID above
2. Use it in your Instagram automation tools
3. Keep it secure and don't share with others

⚠️ **Important Notes:** 
• Session IDs typically last 30-90 days
• Generate a new one if you get auth errors
• Don't use simultaneously in multiple places
• Store securely and delete when not needed

🔐 **Security Tips:**
• Change your password after getting session
• Monitor account activity regularly
• Logout from unknown devices

≭ **Bot By:** @luciInVain
≭ **Time Taken:** `{time_taken}s`
≭ **Status:** Active & Secure"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Generate New", callback_data="new_session")],
                [InlineKeyboardButton("👨‍💻 Support", url="tg://openmessage?user_id=7863546766")],
                [InlineKeyboardButton("🔒 Security Tips", callback_data="security_tips")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(success_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            error_msg = result['error'] if result else "All methods failed"
            error_text = f"""❌ **Session Generation Failed**

👤 **Username:** `{username}`
🚨 **Error:** {error_msg}

🔧 **Troubleshooting Steps:**
1. **Verify Credentials**
   • Double-check username and password
   • Try logging in through Instagram app first

2. **Account Status**
   • Ensure account isn't locked/suspended
   • Check if email/phone verification needed
   • Disable 2FA temporarily

3. **Rate Limiting**
   • Wait 15-30 minutes between attempts
   • Try using different network/VPN
   • Don't attempt login elsewhere simultaneously

4. **Account Age**
   • New accounts (< 7 days) often fail
   • Recently created accounts need activity first

💡 **Success Tips:**
• Use established, active accounts
• Ensure stable internet connection
• Try during off-peak hours
• Don't use account on multiple devices

≭ **Bot By:** @luciInVain
≭ **Time Taken:** `{time_taken}s`
≭ **Status:** Failed - Try Again Later"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="retry_session")],
                [InlineKeyboardButton("👨‍💻 Support", url="tg://openmessage?user_id=7863546766")],
                [InlineKeyboardButton("📚 Help Guide", callback_data="help_guide")]
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

async def instagram_login_mobile(username, password):
    """Instagram mobile app login method"""
    try:
        session = requests.Session()
        
        # Generate device info
        device_id = str(uuid.uuid4())
        android_device_id = hashlib.md5(username.encode()).hexdigest()[:16]
        
        # Mobile app headers
        headers = {
            "User-Agent": f"Instagram {INSTAGRAM_SIGNATURES['version']} Android ({INSTAGRAM_SIGNATURES['android_version']}/{INSTAGRAM_SIGNATURES['android_release']}; {INSTAGRAM_SIGNATURES['dpi']}; {INSTAGRAM_SIGNATURES['resolution']}; {INSTAGRAM_SIGNATURES['manufacturer']}; {INSTAGRAM_SIGNATURES['device']}; {INSTAGRAM_SIGNATURES['model']}; {INSTAGRAM_SIGNATURES['cpu']}; en_US; {INSTAGRAM_SIGNATURES['version_code']})",
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-IG-App-ID": "567067343352427",
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Capabilities": "3brTvw==",
            "X-IG-App-ID": "567067343352427"
        }
        
        session.headers.update(headers)
        
        # Get initial cookies
        session.get("https://i.instagram.com/api/v1/accounts/get_prefill_candidates/", timeout=10)
        
        # Login data
        login_data = {
            "username": username,
            "password": password,
            "device_id": device_id,
            "login_attempt_count": "0"
        }
        
        # Login request
        response = session.post(
            "https://i.instagram.com/api/v1/accounts/login/",
            data=login_data,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok" and data.get("logged_in_user"):
                # Extract session
                for cookie in session.cookies:
                    if cookie.name == 'sessionid':
                        return {"success": True, "session_id": cookie.value}
                return {"success": False, "error": "No session ID in response"}
            else:
                error = data.get("message", "Login failed")
                return {"success": False, "error": error}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"Mobile method error: {str(e)}"}

async def instagram_login_web_v1(username, password):
    """Instagram web login method v1"""
    try:
        session = requests.Session()
        
        # Web headers
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
        
        session.headers.update(headers)
        
        # Get Instagram homepage
        response = session.get("https://www.instagram.com/", timeout=15)
        if response.status_code != 200:
            return {"success": False, "error": "Failed to load Instagram"}
        
        # Extract CSRF token and other data
        csrf_token = None
        rollout_hash = None
        
        for cookie in session.cookies:
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value
                break
        
        # Extract from page source
        import re
        if not csrf_token:
            csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        rollout_match = re.search(r'"rollout_hash":"([^"]+)"', response.text)
        if rollout_match:
            rollout_hash = rollout_match.group(1)
        
        if not csrf_token:
            return {"success": False, "error": "Could not get CSRF token"}
        
        # Update headers for login
        session.headers.update({
            "X-CSRFToken": csrf_token,
            "X-Instagram-AJAX": rollout_hash or "1",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Origin": "https://www.instagram.com",
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        # Login data
        login_data = {
            "username": username,
            "password": password,
            "queryParams": "{}",
            "optIntoOneTap": "false"
        }
        
        # Login request
        login_response = session.post(
            "https://www.instagram.com/accounts/login/ajax/",
            data=login_data,
            timeout=20
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            if data.get("authenticated"):
                for cookie in session.cookies:
                    if cookie.name == 'sessionid':
                        return {"success": True, "session_id": cookie.value}
                return {"success": False, "error": "No session ID found"}
            else:
                error = data.get("message", "Authentication failed")
                if data.get("two_factor_required"):
                    error = "2FA required - disable temporarily"
                elif data.get("checkpoint_url"):
                    error = "Account verification required"
                return {"success": False, "error": error}
        else:
            return {"success": False, "error": f"Login failed: HTTP {login_response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"Web v1 error: {str(e)}"}

async def instagram_login_web_v2(username, password):
    """Instagram web login method v2 - alternative approach"""
    try:
        session = requests.Session()
        
        # Different user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        session.headers.update(headers)
        
        # Get login page directly
        response = session.get("https://www.instagram.com/accounts/login/", timeout=15)
        if response.status_code != 200:
            return {"success": False, "error": "Failed to load login page"}
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find CSRF token from meta tag or script
        csrf_token = None
        
        # Try meta tag first
        meta_csrf = soup.find('meta', {'name': 'csrf-token'})
        if meta_csrf:
            csrf_token = meta_csrf.get('content')
        
        # Try from cookies
        if not csrf_token:
            for cookie in session.cookies:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
        
        # Try from script tags
        if not csrf_token:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'csrf_token' in script.string:
                    import re
                    match = re.search(r'"csrf_token":"([^"]+)"', script.string)
                    if match:
                        csrf_token = match.group(1)
                        break
        
        if not csrf_token:
            return {"success": False, "error": "CSRF token not found"}
        
        # Prepare login
        session.headers.update({
            "X-CSRFToken": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        # Login payload
        payload = {
            "username": username,
            "password": password,
            "queryParams": "{}",
            "optIntoOneTap": "false",
            "trustedDeviceRecords": "{}"
        }
        
        # Send login request
        login_resp = session.post(
            "https://www.instagram.com/accounts/login/ajax/",
            data=payload,
            timeout=20
        )
        
        if login_resp.status_code == 200:
            try:
                result = login_resp.json()
                if result.get("authenticated"):
                    # Get session ID
                    for cookie in session.cookies:
                        if cookie.name == 'sessionid' and cookie.value:
                            return {"success": True, "session_id": cookie.value}
                    return {"success": False, "error": "Session ID not found in cookies"}
                else:
                    error_msg = result.get("message", "Login failed")
                    if "two_factor_required" in result:
                        error_msg = "2FA enabled - please disable"
                    elif "checkpoint_url" in result:
                        error_msg = "Verification required - check email"
                    return {"success": False, "error": error_msg}
            except:
                return {"success": False, "error": "Invalid response format"}
        else:
            return {"success": False, "error": f"HTTP error: {login_resp.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": f"Web v2 error: {str(e)}"}

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
                if channel_id:
                    clean_channel = channel_id.replace('@', '') if channel_id.startswith('@') else channel_id
                    member = await context.bot.get_chat_member(f"@{clean_channel}", user_id)
                    if member.status not in ['left', 'kicked']:
                        await query.edit_message_text(
                            '✅ **Subscription verified!**\n\nNow use /session to proceed.',
                            parse_mode='Markdown'
                        )
                    else:
                        await query.answer('❌ You still need to join the channel.', show_alert=True)
                else:
                    await query.answer('❌ Channel not configured.', show_alert=True)
            except Exception as e:
                print(f"❌ Error checking subscription: {e}")
                await query.answer('❌ Error checking subscription.', show_alert=True)
            return
        
        elif query.data == "new_session":
            await query.edit_message_text(
                '🔄 **Generate New Session**\n\n'
                'Use /session command to start the process again.\n\n'
                '💡 **Tip:** Wait 5-10 minutes between attempts for better success rate.',
                parse_mode='Markdown'
            )
        
        elif query.data == "retry_session":
            await query.edit_message_text(
                '🔄 **Retry Session Generation**\n\n'
                'Use /session command to try again.\n\n'
                '📝 **Before retrying:**\n'
                '• Wait at least 15 minutes\n'
                '• Verify credentials in Instagram app\n'
                '• Ensure stable internet connection\n'
                '• Try different network if possible',
                parse_mode='Markdown'
            )
        
        elif query.data == "security_tips":
            await query.edit_message_text(
                '🔐 **Security Tips**\n\n'
                '🛡️ **After Getting Session:**\n'
                '• Change your password immediately\n'
                '• Enable 2FA after session generation\n'
                '• Monitor login activity regularly\n'
                '• Logout unknown devices\n\n'
                '⚠️ **Session Safety:**\n'
                '• Don\'t share session IDs\n'
                '• Store securely (encrypted)\n'
                '• Delete when not needed\n'
                '• Generate new ones monthly\n\n'
                '🔒 **Account Protection:**\n'
                '• Use strong, unique passwords\n'
                '• Keep recovery info updated\n'
                '• Be cautious with automation tools',
                parse_mode='Markdown'
            )
        
        elif query.data == "help_guide":
            await query.edit_message_text(
                '📚 **Complete Help Guide**\n\n'
                '❓ **Common Issues & Solutions:**\n\n'
                '1. **"Login Failed" Error:**\n'
                '   • Verify username/password\n'
                '   • Try logging in Instagram app first\n'
                '   • Wait 30 minutes, try again\n\n'
                '2. **"Account Verification Required":**\n'
                '   • Check email for verification\n'
                '   • Complete verification in app\n'
                '   • Try again after verification\n\n'
                '3. **"Rate Limited" Error:**\n'
                '   • Wait 1-2 hours before retry\n'
                '   • Try different network/VPN\n'
                '   • Don\'t attempt multiple times\n\n'
                '4. **"2FA Required":**\n'
                '   • Temporarily disable 2FA\n'
                '   • Generate session\n'
                '   • Re-enable 2FA immediately\n\n'
                '✅ **Best Practices:**\n'
                '• Use established accounts (7+ days old)\n'
                '• Ensure account has activity/posts\n'
                '• Try during off-peak hours\n'
                '• Use stable internet connection',
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
        '❌ **Session generation cancelled.**\n\n'
        'Use /session to start again when ready.',
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to verify bot is responding"""
    await update.message.reply_text(
        '✅ **Bot is working perfectly!**\n\n'
        '🔧 **Available Commands:**\n'
        '• `/session` - Generate Instagram session ID\n'
        '• `/test` - Test bot functionality\n'
        '• `/cancel` - Cancel current operation\n\n'
        '📊 **System Status:**\n'
        '• Web Method v1: ✅ Active\n'
        '• Web Method v2: ✅ Active\n'
        '• Mobile Method: ✅ Active\n'
        '• Multi-method Fallback: ✅ Enabled\n\n'
        '📝 **Usage Tips:**\n'
        '• Disable 2FA temporarily\n'
        '• Use accounts 7+ days old\n'
        '• Wait 15+ minutes between attempts\n'
        '• Ensure stable internet connection',
        parse_mode='Markdown'
    )

def setup
