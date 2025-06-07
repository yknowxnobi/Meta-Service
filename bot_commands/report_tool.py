import os
import requests
import random
import time
import asyncio
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
    print(f"DEBUG: /report command received from user {update.effective_user.id}")
    user_id = update.effective_user.id
    
    # Request target username directly (no subscription check)
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
    print(f"DEBUG: Target username received from user {update.effective_user.id}")
    user_id = update.effective_user.id
    target_user = update.message.text.strip().replace('@', '')
    
    if user_id not in report_states:
        print(f"DEBUG: User {user_id} not in report_states")
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
    print(f"DEBUG: Target name received from user {update.effective_user.id}")
    user_id = update.effective_user.id
    target_name = update.message.text.strip()
    
    if user_id not in report_states:
        print(f"DEBUG: User {user_id} not in report_states")
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
    print(f"DEBUG: Callback received: {query.data} from user {query.from_user.id}")
    
    try:
        await query.answer()
        
        if query.data.startswith('start_report_'):
            user_id = int(query.data.replace('start_report_', ''))
            print(f"DEBUG: Starting report for user {user_id}")
            
            if user_id in report_states:
                await start_instagram_reporting(query, context, report_states[user_id])
                # Clean up state after starting
                del report_states[user_id]
            else:
                print(f"DEBUG: User {user_id} not found in report_states")
                await query.edit_message_text(
                    '❌ **Session expired. Please start over with /report**',
                    parse_mode='Markdown'
                )
        
        elif query.data == 'cancel_report':
            print("DEBUG: Report cancelled")
            await query.edit_message_text(
                '❌ **Report cancelled.**',
                parse_mode='Markdown'
            )
            # Clean up any states
            user_id = query.from_user.id
            if user_id in report_states:
                del report_states[user_id]
    
    except Exception as e:
        print(f"ERROR in callback handler: {e}")
        try:
            await query.answer("❌ Error processing request")
        except:
            pass

async def start_instagram_reporting(query, context, report_data):
    """Start the Instagram reporting process"""
    target_user = report_data['target_user']
    target_name = report_data['target_name']
    
    print(f"DEBUG: Starting reporting process for {target_user}")
    
    try:
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
        )
        
        # Simulate reporting process
        for i in range(total_attempts):
            try:
                # Simulate delay
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Random success/fail (for demo)
                if random.choice([True, False, True]):  # 2/3 success rate
                    successful_reports += 1
                    print(f"DEBUG: Report {i+1} successful")
                else:
                    failed_reports += 1
                    print(f"DEBUG: Report {i+1} failed")
                
                # Update progress every 2 reports to avoid rate limits
                if (i + 1) % 2 == 0 or i == total_attempts - 1:
                    progress = int(((i + 1) / total_attempts) * 100)
                    
                    try:
                        await status_msg.edit_text(
                            f'📊 **Report Status:**\n\n'
                            f'✅ Successful: {successful_reports}\n'
                            f'❌ Failed: {failed_reports}\n'
                            f'🔄 Progress: {progress}%\n'
                            f'⏳ Processing... ({i+1}/{total_attempts})',
                            parse_mode='Markdown'
                        )
                    except Exception as edit_error:
                        print(f"DEBUG: Edit error: {edit_error}")
                        pass  # Ignore edit errors
                        
            except Exception as e:
                print(f"DEBUG: Error in report loop: {e}")
                failed_reports += 1
        
        # Final status
        final_text = f"""
🏁 **Report Process Complete!**

📊 **Final Results:**
✅ **Successful Reports:** {successful_reports}
❌ **Failed Reports:** {failed_reports}
📈 **Success Rate:** {int((successful_reports/total_attempts)*100)}%

🎯 **Target:** `{target_user}`
📛 **Name:** `{target_name}`
⏰ **Completed:** {time.strftime('%H:%M:%S')}

⚠️ **Note:** This is a demonstration. Actual reporting depends on various factors.
        """
        
        try:
            await status_msg.edit_text(final_text, parse_mode='Markdown')
            print("DEBUG: Report process completed successfully")
        except Exception as final_error:
            print(f"DEBUG: Final edit error: {final_error}")
            await context.bot.send_message(
                query.message.chat_id,
                final_text,
                parse_mode='Markdown'
            )
    
    except Exception as e:
        print(f"ERROR in start_instagram_reporting: {e}")
        try:
            await context.bot.send_message(
                query.message.chat_id,
                f'❌ **Error starting report process:** {str(e)}',
                parse_mode='Markdown'
            )
        except:
            pass

async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the report process"""
    user_id = update.effective_user.id
    if user_id in report_states:
        del report_states[user_id]
    
    await update.message.reply_text('❌ Report process cancelled.')
    return ConversationHandler.END

def setup_report_commands(app, admin_id, channel_id):
    """Setup report-related handlers"""
    
    print("DEBUG: Setting up report commands...")
    
    # Conversation handler for report process
    report_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_command)],
        states={
            WAITING_TARGET_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_target_username)],
            WAITING_TARGET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_target_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel_report)]
    )
    
    # Add handlers
    app.add_handler(report_handler)
    print("DEBUG: Added report conversation handler")
    
    # Add callback handler with specific pattern to avoid conflicts
    app.add_handler(CallbackQueryHandler(
        handle_report_callback, 
        pattern=r'^(start_report_|cancel_report).*'
    ))
    print("DEBUG: Added report callback handler")
    
    print("✅ Report commands setup complete!")
