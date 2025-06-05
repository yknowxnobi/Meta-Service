import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Conversation states
WAITING_RESET_INPUT = range(1)

# Global variables for reset requests
reset_states = {}

async def insta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /insta command for user details"""
    try:
        # Get username from command
        if not context.args:
            await update.message.reply_text(
                '❌ Please provide an Instagram username.\n\n'
                '**Usage:** `/insta username`\n\n'
                '**Example:** `/insta cristiano`',
                parse_mode='Markdown'
            )
            return
        
        username = context.args[0].replace('@', '')
        
        # Show loading message
        loading_msg = await update.message.reply_text('🔄 Fetching user details...')
        
        # Fetch user details
        api_url = os.getenv('NEXTCOUNTS_API', 'https://api-v2.nextcounts.com')
        response = requests.get(f"{api_url}/api/instagram/user/{username}", timeout=10)
        
        if response.status_code != 200:
            await loading_msg.edit_text('❌ Failed to fetch user details. Please try again.')
            return
        
        data = response.json()
        user_id = data.get('id2', 'N/A')
        
        # Fetch account creation year
        creation_year = 'N/A'
        try:
            gojo_url = os.getenv('GOJOAPI_URL', 'https://gojoapi.pythonanywhere.com')
            creation_response = requests.get(
                f"{gojo_url}/get-year",
                params={'Id': user_id},
                timeout=5
            )
            if creation_response.status_code == 200:
                creation_year = creation_response.json().get('year', 'N/A')
        except:
            creation_year = 'Could not fetch'
        
        # Format message
        message = f"""
🔍 **Instagram User Details**
━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **User:** {data.get('username', 'N/A')}
📛 **Name:** {data.get('nickname', 'N/A')}
🆔 **ID:** {user_id}
🔒 **Private:** {'Yes' if data.get('private') else 'No'}
👥 **Followers:** {data.get('followers', 'N/A'):,} 
🔄 **Following:** {data.get('following', 'N/A'):,}
📸 **Posts:** {data.get('posts', 'N/A'):,}
📅 **Created In:** {creation_year}

━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        await loading_msg.edit_text(message, parse_mode='Markdown')
        
    except requests.exceptions.Timeout:
        await update.message.reply_text('⏱️ Request timeout. Please try again.')
    except requests.exceptions.RequestException:
        await update.message.reply_text('🚨 Network error occurred. Please try again.')
    except Exception as e:
        await update.message.reply_text(f'🚨 An error occurred: {str(e)}')

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command for password reset"""
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        '🔄 **Password Reset Mode Activated**\n\n'
        '📝 Please send your Instagram username or email to proceed with the reset.\n\n'
        '**Note:** This will send a reset link to the associated email.',
        parse_mode='Markdown'
    )
    
    reset_states[user_id] = True
    return WAITING_RESET_INPUT

async def handle_reset_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for reset requests"""
    user_id = update.effective_user.id
    
    if user_id not in reset_states:
        return ConversationHandler.END
    
    email_or_username = update.message.text.strip()
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        f'🔄 **Processing reset request for:** `{email_or_username}`',
        parse_mode='Markdown'
    )
    
    try:
        # Send reset request
        recovery_url = os.getenv('IG_RECOVERY_URL', 'https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/')
        
        payload = f"email_or_username={email_or_username}&flow=fxcal"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36',
            'X-CSRFToken': 'BbJnjd.Jnw20VyXU0qSsHLV',
            'X-IG-App-ID': '1217981644879628'
        }
        
        response = requests.post(recovery_url, data=payload, headers=headers, timeout=10)
        
        # Format response
        result_text = f"""
📬 **Reset Request Result:**

**Target:** `{email_or_username}`
**Status:** {"✅ Sent" if response.status_code == 200 else "❌ Failed"}
**Response:** `{response.text[:200]}...`
        """
        
        await processing_msg.edit_text(result_text, parse_mode='Markdown')
        
    except Exception as e:
        await processing_msg.edit_text(f'🚨 **Error:** {str(e)}', parse_mode='Markdown')
    
    # Clean up
    if user_id in reset_states:
        del reset_states[user_id]
    
    return ConversationHandler.END

def setup_insta_commands(app, admin_id, channel_id):
    """Setup Instagram info commands"""
    
    # Basic insta command
    app.add_handler(CommandHandler("insta", insta_command))
    
    # Reset conversation handler
    reset_handler = ConversationHandler(
        entry_points=[CommandHandler('reset', reset_command)],
        states={
            WAITING_RESET_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reset_input)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    app.add_handler(reset_handler)
    
    print("✅ Instagram info commands loaded")
