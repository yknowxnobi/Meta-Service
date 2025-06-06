import os
import asyncio
import requests
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.error import TelegramError, Forbidden, BadRequest

# Conversation states
WAITING_USERNAME = 1

# User states
user_states = {}

async def check_subscription(user_id, context, channel_id):
    """Check if user is subscribed to the channel"""
    try:
        print(f"DEBUG: Checking subscription for user {user_id} in channel {channel_id}")
        
        # Clean channel_id format
        if channel_id.startswith('@'):
            channel_id = channel_id[1:]
        
        # Try to get chat member
        member = await context.bot.get_chat_member(f"@{channel_id}", user_id)
        print(f"DEBUG: Member status: {member.status}")
        
        # Valid subscription statuses
        valid_statuses = ['member', 'administrator', 'creator']
        is_subscribed = member.status in valid_statuses
        
        print(f"DEBUG: Is subscribed: {is_subscribed}")
        return is_subscribed
        
    except Forbidden as e:
        print(f"DEBUG: Forbidden error - Bot not admin or channel private: {e}")
        # If bot doesn't have admin rights, assume user is subscribed
        return True
        
    except BadRequest as e:
        print(f"DEBUG: BadRequest error: {e}")
        error_str = str(e).lower()
        if "chat not found" in error_str or "user not found" in error_str:
            return False
        return True
        
    except TelegramError as e:
        print(f"DEBUG: Telegram error: {e}")
        return True
        
    except Exception as e:
        print(f"DEBUG: Unexpected error checking subscription: {e}")
        return True

async def meth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /meth command"""
    user_id = update.effective_user.id
    channel_id = os.getenv('CHANNEL_ID', '@meta_server')
    
    print(f"DEBUG: Meth command called by user {user_id}")
    print(f"DEBUG: Channel ID from env: {channel_id}")
    
    # Check subscription
    is_subscribed = await check_subscription(user_id, context, channel_id)
    print(f"DEBUG: Subscription check result: {is_subscribed}")
    
    if not is_subscribed:
        # Clean channel name for URL
        channel_name = channel_id.replace('@', '') if channel_id.startswith('@') else channel_id
        
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_name}")],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_fsub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ **Please join our channel first to use this feature.**\n\n"
            f"Channel: @{channel_name}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # If subscribed, proceed with username request
    await update.message.reply_text(
        '🎯 **Instagram Meth Analyzer**\n\n'
        '📝 Please send your target username without @\n\n'
        '⚠️ *Please send only real targets*',
        parse_mode='Markdown'
    )
    
    user_states[user_id] = {'waiting_for': 'username'}
    return WAITING_USERNAME

async def handle_username_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle username input"""
    user_id = update.effective_user.id
    username = update.message.text.strip().replace('@', '')
    
    print(f"DEBUG: Username input received from user {user_id}: {username}")
    
    if user_id not in user_states:
        print(f"DEBUG: User {user_id} not in user_states")
        return ConversationHandler.END
    
    # Validate username format
    if not username or len(username) < 3:
        await update.message.reply_text(
            '❌ **Please enter a valid Instagram username (at least 3 characters).**',
            parse_mode='Markdown'
        )
        return WAITING_USERNAME
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        '🔍 **Verifying username...**',
        parse_mode='Markdown'
    )
    
    try:
        # Verify username with timeout
        api_url = os.getenv('IG_INFO_API', 'https://ig-info-drsudo.vercel.app')
        
        # Use asyncio.wait_for for proper timeout handling
        async def verify_username():
            response = requests.get(f"{api_url}/api/ig?user={username}", timeout=10)
            return response
        
        try:
            response = await asyncio.wait_for(verify_username(), timeout=15)
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                '⏱️ **Request timed out!**\n\nPlease try again with the Instagram username.',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        if response.status_code != 200:
            await processing_msg.edit_text(
                '❌ **Something went wrong while verifying the username.**\n\n'
                'Please try again with a valid Instagram username.',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        data = response.json()
        
        if not data.get('success'):
            await processing_msg.edit_text(
                '❌ **Invalid Instagram username or account not found.**\n\n'
                'Please try again with a valid username.',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Show confirmation
        info_text = f"""
🔍 **Is this the correct user?**

• **Username:** {data.get('username', 'N/A')}
• **Nickname:** {data.get('nickname', 'N/A')}
• **Followers:** {data.get('followers', 'N/A'):,}
• **Following:** {data.get('following', 'N/A'):,}
• **Created At:** {data.get('account_created', 'N/A')}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("Yes ✅", callback_data=f"confirm_yes_{username}"),
                InlineKeyboardButton("No ❌", callback_data="confirm_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(info_text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Request error: {e}")
        await processing_msg.edit_text(
            '❌ **Network error occurred.**\n\nPlease try again later.',
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        await processing_msg.edit_text(
            '❌ **Something went wrong.**\n\nPlease try again.',
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Clean up user state
    if user_id in user_states:
        del user_states[user_id]
    
    return ConversationHandler.END

async def handle_meth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for meth feature"""
    query = update.callback_query
    await query.answer()
    
    print(f"DEBUG: Callback received: {query.data}")
    
    if query.data == "check_fsub":
        user_id = query.from_user.id
        channel_id = os.getenv('CHANNEL_ID', '@meta_server')
        
        print(f"DEBUG: Re-checking subscription for callback user {user_id}")
        
        # Add a small delay to allow for subscription to be processed
        await asyncio.sleep(1)
        
        is_subscribed = await check_subscription(user_id, context, channel_id)
        print(f"DEBUG: Callback subscription result: {is_subscribed}")
        
        if is_subscribed:
            await query.edit_message_text(
                '✅ **Subscription verified!**\n\n'
                'Now use /meth command to proceed with analysis.',
                parse_mode='Markdown'
            )
        else:
            # Clean channel name for display
            channel_name = channel_id.replace('@', '') if channel_id.startswith('@') else channel_id
            
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_name}")],
                [InlineKeyboardButton("✅ Check Again", callback_data="check_fsub")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f'❌ **Please join @{channel_name} first.**\n\n'
                'After joining, click "Check Again" button.',
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        return
    
    if query.data.startswith('confirm_yes_'):
        username = query.data.replace('confirm_yes_', '')
        await process_meth_analysis(query, context, username)
    
    elif query.data == 'confirm_no':
        await query.edit_message_text(
            '❌ **Cancelled.**\n\n'
            'Use /meth command again to start over.',
            parse_mode='Markdown'
        )

async def process_meth_analysis(query, context, username):
    """Process meth analysis with loading animation"""
    print(f"DEBUG: Processing analysis for username: {username}")
    
    # Show confirmation
    await query.edit_message_text(
        f'✅ **Confirmed IG:** @{username}\n\n🔄 Starting analysis...',
        parse_mode='Markdown'
    )
    
    await asyncio.sleep(2)
    
    # Delete confirmation and show loading
    try:
        await query.message.delete()
    except:
        pass  # Ignore if message can't be deleted
    
    loading_msg = await context.bot.send_message(
        query.message.chat_id,
        '🔄 **Processing... Please wait.**',
        parse_mode='Markdown'
    )
    
    # Loading animation
    try:
        for i in range(10, 101, 10):
            bar = '▒' * (i // 10) + '░' * (10 - i // 10)
            await loading_msg.edit_text(
                f'🔄 **Processing... {i}%**\n\n[{bar}]',
                parse_mode='Markdown'
            )
            await asyncio.sleep(random.uniform(0.5, 1.0))
    except:
        pass  # Continue even if loading animation fails
    
    # Generate random categories
    categories = [
        'Nudity¹', 'Nudity²', 'Nudity³', 'Nudity⁴', 'Hate', 'Scam', 'Terrorism',
        'Vio¹', 'Vio²', 'Vio³', 'Vio⁴', 'Sale Illegal [High Risk Drugs]',
        'Sale Illegal [Other Drugs]', 'Firearms', 'Endangered Animal',
        'Bully_Me', 'Self_Injury', 'Self [Eating Disorder]', 'Spam', 'Problem'
    ]
    
    count = random.randint(2, 4)
    picked = random.sample(categories, count)
    
    result = '\n'.join([f'➥ {random.randint(1, 5)}x {cat}' for cat in picked])
    
    final_text = f"""
*Username : @{username}*

**Suggested Reports for Your Target:**

```
{result}
```

⚠️ **Note:** *This method is based on available data and may not be fully accurate.*

💡 **Tip:** Use /meth command again for another analysis.
    """
    
    keyboard = [
        [InlineKeyboardButton("👨‍💻 Contact Developer", url="tg://openmessage?user_id=7863546766")],
        [InlineKeyboardButton("🔄 New Analysis", callback_data="new_analysis")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await loading_msg.edit_text(final_text, parse_mode='Markdown', reply_markup=reply_markup)
    except:
        # If edit fails, send new message
        try:
            await loading_msg.delete()
        except:
            pass
        await context.bot.send_message(
            query.message.chat_id,
            final_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_new_analysis_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new analysis callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "new_analysis":
        await query.edit_message_text(
            '🎯 **Ready for new analysis!**\n\n'
            'Use /meth command to start a new Instagram analysis.',
            parse_mode='Markdown'
        )

def setup_meth_commands(app, admin_id, channel_id):
    """Setup meth analysis commands"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("meth", meth_command)],
        states={
            WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_meth_callback))
    app.add_handler(CallbackQueryHandler(handle_new_analysis_callback))
    
    print("✅ Meth analyzer commands loaded")
    print(f"✅ Channel ID configured: {channel_id}")
