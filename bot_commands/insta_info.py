import os
import requests
import time
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
        
        # Debug: Print the API response to see what we're getting
        print(f"API Response: {data}")
        
        # Extract data from API response
        user_id = data.get('id2', 'N/A')
        username_display = data.get('username', 'N/A')
        nickname = data.get('nickname', 'N/A')
        followers = data.get('followers', 0)
        following = data.get('following', 0)
        posts = data.get('posts', 0)
        private_status = data.get('private', False)
        verified_status = data.get('verified', False)
        account_created = data.get('account_created', 'N/A')
        
        # Format numbers with commas
        followers_formatted = f"{followers:,}" if isinstance(followers, int) else str(followers)
        following_formatted = f"{following:,}" if isinstance(following, int) else str(following)
        posts_formatted = f"{posts:,}" if isinstance(posts, int) else str(posts)
        
        # Format private status
        private_text = "Yes" if private_status else "No"
        
        # Format verification status
        verified_text = "✅ Verified" if verified_status else "❌ Not Verified"
        
        # Format creation year
        creation_year = str(account_created) if account_created != 'N/A' and account_created is not None else 'N/A'
        
        # Create the formatted message exactly like web response
        message = f"""🔍 **Instagram User Details**
━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **User:** `{username_display}`
📛 **Name:** `{nickname}`
🆔 **ID:** `{user_id}`
{verified_text}
🔒 **Private:** `{private_text}`
👥 **Followers:** `{followers_formatted}`
🔄 **Following:** `{following_formatted}`
📸 **Posts:** `{posts_formatted}`
📅 **Created In:** `{creation_year}`

━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        await loading_msg.edit_text(message, parse_mode='Markdown')
        
    except requests.exceptions.Timeout:
        await update.message.reply_text('⏱️ Request timeout. Please try again.')
    except requests.exceptions.RequestException:
        await update.message.reply_text('🚨 Network error occurred. Please try again.')
    except Exception as e:
        print(f"Error in insta_command: {e}")
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
        # Record start time
        start_time = time.time()
        
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
        
        # Calculate time taken
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        # Get user's display name
        user_name = update.effective_user.first_name or update.effective_user.username or "Unknown User"
        
        # Parse response to extract email if available
        associated_email = "Not Available"
        try:
            if response.status_code == 200:
                response_data = response.json()
                # Try to extract email from response (this depends on Instagram's response format)
                if 'email' in response_data:
                    email = response_data['email']
                    # Mask email like w*******u@gmail.com
                    if '@' in email:
                        local, domain = email.split('@', 1)
                        if len(local) > 2:
                            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
                            associated_email = f"{masked_local}@{domain}"
                        else:
                            associated_email = f"**@{domain}"
                    else:
                        associated_email = email
        except:
            pass
        
        # Format response in the requested style
        if response.status_code == 200:
            result_text = f"""
•𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱 𝗥𝗲𝘀𝗲𝘁 𝗟𝗶𝗻𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!

≭ 𝗘𝗺𝗮𝗶𝗹 𝗔𝘀𝘀𝗼𝗰𝗶𝗮𝘁𝗲𝗱: `{associated_email}`
≭ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗕𝘆: `{user_name}`
≭ 𝗕𝗼𝘁 𝗕𝘆 / 𝗗𝗲𝘃: @meta_server
≭ 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻: `{time_taken}` 𝘀𝗲𝗰𝗼𝗻𝗱𝘀
            """
        else:
            result_text = f"""
•𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱 𝗥𝗲𝘀𝗲𝘁 𝗙𝗮𝗶𝗹𝗲𝗱!

≭ 𝗧𝗮𝗿𝗴𝗲𝘁: `{email_or_username}`
≭ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗕𝘆: `{user_name}`
≭ 𝗕𝗼𝘁 𝗕𝘆 / 𝗗𝗲𝘃: @meta_server
≭ 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻: `{time_taken}` 𝘀𝗲𝗰𝗼𝗻𝗱𝘀
≭ 𝗘𝗿𝗿𝗼𝗿: `{response.status_code}`
            """
        
        await processing_msg.edit_text(result_text, parse_mode='Markdown')
        
    except Exception as e:
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        error_text = f"""
•𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱 𝗥𝗲𝘀𝗲𝘁 𝗙𝗮𝗶𝗹𝗲𝗱!

≭ 𝗧𝗮𝗿𝗴𝗲𝘁: `{email_or_username}`
≭ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗕𝘆: `{user_name}`
≭ 𝗕𝗼𝘁 𝗕𝘆 / 𝗗𝗲𝘃: @meta_server
≭ 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻: `{time_taken}` 𝘀𝗲𝗰𝗼𝗻𝗱𝘀
≭ 𝗘𝗿𝗿𝗼𝗿: `{str(e)}`
        """
        
        await processing_msg.edit_text(error_text, parse_mode='Markdown')
    
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
