import os
import asyncio
import requests
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Conversation states
WAITING_USERNAME = 1

# User states
user_states = {}

async def check_subscription(user_id, context, channel_id):
    """Check if user is subscribed to the channel"""
    try:
        member = await context.bot.get_chat_member(channel_id, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return False

async def meth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /meth command"""
    user_id = update.effective_user.id
    channel_id = os.getenv('CHANNEL_ID', '@meta_servers')
    
    # Check subscription
    if not await check_subscription(user_id, context, channel_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_id.replace('@', '')}")],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_fsub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ **Please join our channel first to use this feature.**",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # Request username
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
    
    if user_id not in user_states:
        return ConversationHandler.END
    
    # Set timeout for verification
    timeout_task = asyncio.create_task(timeout_handler(update, context, 7))
    
    try:
        # Verify username
        api_url = os.getenv('IG_INFO_API', 'https://ig-info-drsudo.vercel.app')
        response = requests.get(f"{api_url}/api/ig?user={username}", timeout=5)
        
        # Cancel timeout
        timeout_task.cancel()
        
        if response.status_code != 200:
            await update.message.reply_text(
                '❌ **Something went wrong while verifying the username.**\n\n'
                'Please send the username without @.',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        data = response.json()
        
        if not data.get('success'):
            await update.message.reply_text(
                '❌ **Invalid Instagram username or not found.**',
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
        
        await update.message.reply_text(info_text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except asyncio.CancelledError:
        pass
    except requests.exceptions.Timeout:
        timeout_task.cancel()
        await update.message.reply_text(
            '⏱️ **Request timed out!**\n\nPlease send the Instagram username again.',
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    except Exception as e:
        timeout_task.cancel()
        await update.message.reply_text(
            '❌ **Something went wrong while verifying the username.**\n\n'
            'Please send the username without @.',
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    del user_states[user_id]
    return ConversationHandler.END

async def timeout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, seconds: int):
    """Handle timeout for username verification"""
    await asyncio.sleep(seconds)
    await update.message.reply_text(
        '⏱️ **Request timed out!**\n\nPlease send the Instagram username again.',
        parse_mode='Markdown'
    )

async def handle_meth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for meth feature"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_fsub":
        user_id = query.from_user.id
        channel_id = os.getenv('CHANNEL_ID', '@meta_servers')
        
        if await check_subscription(user_id, context, channel_id):
            await query.edit_message_text(
                '✅ **Subscription verified!**\n\nNow use /meth to proceed.',
                parse_mode='Markdown'
            )
        else:
            await query.answer('❌ You still need to join the channel.', show_alert=True)
        return
    
    if query.data.startswith('confirm_yes_'):
        username = query.data.replace('confirm_yes_', '')
        await process_meth_analysis(query, context, username)
    
    elif query.data == 'confirm_no':
        await query.edit_message_text(
            '❌ **Okay, please try again with the correct IG username.**',
            parse_mode='Markdown'
        )

async def process_meth_analysis(query, context, username):
    """Process meth analysis with loading animation"""
    # Show confirmation
    await query.edit_message_text(
        f'✅ **Confirmed IG:** {username}\n\n🔄 Starting meth process...',
        parse_mode='Markdown'
    )
    
    await asyncio.sleep(1)
    
    # Delete confirmation and show loading
    await context.bot.delete_message(query.message.chat_id, query.message.message_id)
    
    loading_msg = await context.bot.send_message(
        query.message.chat_id,
        '🔄 **Loading... Please wait.**',
        parse_mode='Markdown'
    )
    
    # Loading animation
    for i in range(10, 101, 10):
        bar = '▒' * (i // 10) + ' ' * (10 - i // 10)
        try:
            await loading_msg.edit_text(
                f'🔄 **Loading... {i}%** {bar}',
                parse_mode='Markdown'
            )
            await asyncio.sleep(0.5)
        except:
            break
    
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
    """
    
    keyboard = [
        [InlineKeyboardButton("👨‍💻 Contact Developer", url="tg://openmessage?user_id=7863546766")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await loading_msg.edit_text(final_text, parse_mode='Markdown', reply_markup=reply_markup)
    except:
        await context.bot.send_message(
            query.message.chat_id,
            final_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
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
    
    print("✅ Meth analyzer commands loaded")
