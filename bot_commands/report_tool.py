import os
import requests
import random
import time
from string import ascii_letters, digits
from faker import Faker
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Conversation states
WAITING_TARGET_USER, WAITING_TARGET_NAME = range(2)

# User states for report tool
report_states = {}

fake = Faker()

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    user_id = update.effective_user.id
    channel_id = os.getenv('CHANNEL_ID', '@meta_servers')
    
    # Check subscription
    try:
        member = await context.bot.get_chat_member(channel_id, user_id)
        if member.status in ['left', 'kicked']:
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_id.replace('@', '')}")],
                [InlineKeyboardButton("✅ I Joined", callback_data="check_report_sub")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⚠️ **Please join our channel first to use this feature.**",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return ConversationHandler.END
    except:
        await update.message.reply_text(
            '❌ **Unable to verify your subscription. Try again later.**',
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Request target username
    await update.message.reply_text(
        '📊 **Instagram Report Tool**\n\n'
        '👤 Please enter the target Instagram username (without @):\n\n'
        '⚠️ *Use responsibly and only for legitimate purposes*',
        parse_mode='Markdown'
    )
    
    report_states[user_id] = {}
    return WAITING_TARGET_USER

async def handle_target_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target username input"""
    user_id = update.effective_user.id
    target_user = update.message.text.strip().replace('@', '')
    
    if user_id not in report_states:
        return ConversationHandler.END
    
    report_states[user_id]['target_user'] = target_user
    
    await update.message.reply_text(
        f'✅ **Target Username:** `{target_user}`\n\n'
        '📝 Now please enter the target\'s display name:',
        parse_mode='Markdown'
    )
    
    return WAITING_TARGET_NAME

async def handle_target_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target name input and start reporting"""
    user_id = update.effective_user.id
    target_name = update.message.text.strip()
    
    if user_id not in report_states:
        return ConversationHandler.END
    
    report_states[user_id]['target_name'] = target_name
    target_user = report_states[user_id]['target_user']
    
    # Show confirmation
    confirm_text = f"""
📋 **Report Configuration:**

👤 **Username:** `{target_user}`
📛 **Name:** `{target_name}`

🚀 **Ready to start reporting?**
    """
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Start Reporting", callback_data=f"start_report_{user_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_report")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(confirm_text, parse_mode='Markdown', reply_markup=reply_markup)
    return ConversationHandler.END

async def handle_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for report feature"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_report_sub":
        user_id = query.from_user.id
        channel_id = os.getenv('CHANNEL_ID', '@meta_servers')
        
        try:
            member = await context.bot.get_chat_member(channel_id, user_id)
            if member.status not in ['left', 'kicked']:
                await query.edit_message_text(
                    '✅ **Subscription verified!**\n\nNow use /report to proceed.',
                    parse_mode='Markdown'
                )
            else:
                await query.answer('❌ You still need to join the channel.', show_alert=True)
        except:
            await query.answer('❌ Error checking subscription.', show_alert=True)
        return
    
    if query.data.startswith('start_report_'):
        user_id = int(query.data.replace('start_report_', ''))
        if user_id in report_states:
            await start_instagram_reporting(query, context, report_states[user_id])
            del report_states[user_id]
    
    elif query.data == 'cancel_report':
        await query.edit_message_text(
            '❌ **Report cancelled.**',
            parse_mode='Markdown'
        )

async def start_instagram_reporting(query, context, report_data):
    """Start the Instagram reporting process"""
    target_user = report_data['target_user']
    target_name = report_data['target_name']
    
    await query.edit_message_text(
        f'🚀 **Starting Instagram Report Tool**\n\n'
        f'🎯 **Target:** `{target_user}`\n'
        f'📊 **Processing reports...**',
        parse_mode='Markdown'
    )
    
    # Report counter
    successful_reports = 0
    failed_reports = 0
    total_attempts = 10  # Limit attempts
    
    status_msg = await context.bot.send_message(
        query.message.chat_id,
        '📊 **Report Status:**\n\n'
        '✅ Successful: 0\n'
        '❌ Failed: 0\n'
        '🔄 Progress: 0%',
        parse_mode='Markdown'
    )  # FIXED: Added missing closing parenthesis
    
    # Simulate reporting process
    for i in range(total_attempts):
        try:
            # Simulate delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Random success/fail (for demo)
            if random.choice([True, False, True]):  # 2/3 success rate
                successful_reports += 1
            else:
                failed_reports += 1
            
            # Update progress
            progress = int(((i + 1) / total_attempts) * 100)
            
            try:
                await status_msg.edit_text(
                    f'📊 **Report Status:**\n\n'
                    f'✅ Successful: {successful_reports}\n'
                    f'❌ Failed: {failed_reports}\n'
                    f'🔄 Progress: {progress}%',
                    parse_mode='Markdown'
                )
            except:
                pass  # Ignore edit errors
                
        except Exception as e:
            failed_reports += 1
    
    # Final status
    final_text = f"""
🏁 **Report Process Complete!**

📊 **Final Results:**
✅ **Successful Reports:** {successful_reports}
❌ **Failed Reports:** {failed_reports}
📈 **Success Rate:** {int((successful_reports/total_attempts)*100)}%

🎯 **Target:** `{target_user}`
⏰ **Completed:** {time.strftime('%H:%M:%S')}

⚠️ **Note:** This is a demonstration. Actual reporting depends on various factors.
    """
    
    try:
        await status_msg.edit_text(final_text, parse_mode='Markdown')
    except:
        await context.bot.send_message(
            query.message.chat_id,
            final_text,
            parse_mode='Markdown'
        )

def setup_report_commands(app, admin_id, channel_id):
    """Setup report-related handlers"""
    
    # Conversation handler for report process
    report_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_command)],
        states={
            WAITING_TARGET_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_target_username)],
            WAITING_TARGET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_target_name)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    # Add handlers
    app.add_handler(report_handler)
    app.add_handler(CallbackQueryHandler(handle_report_callback))
    
    print("✅ Report commands setup complete!")
