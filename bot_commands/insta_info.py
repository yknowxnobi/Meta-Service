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
        
        # Add headers to make request more reliable
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(f"{api_url}/api/instagram/user/{username}", headers=headers, timeout=15)
        
        if response.status_code != 200:
            await loading_msg.edit_text(f'❌ Failed to fetch user details. Status: {response.status_code}. Please try again.')
            return
        
        data = response.json()
        
        # Map the response to match your desired format
        formatted_data = {
            "account_created": data.get('account_created', 'N/A'),
            "avatar": data.get('avatar', data.get('userBanner', 'N/A')),
            "biography": data.get('biography', 'N/A'),
            "followers": data.get('followers', 0),
            "following": data.get('following', 0),
            "id": data.get('id', data.get('username', 'N/A')),
            "id2": data.get('id2', data.get('user_id', 'N/A')),
            "meta_status": str(data.get('meta_status', 'False')),
            "nickname": data.get('nickname', data.get('full_name', 'N/A')),
            "posts": data.get('posts', 0),
            "private": data.get('private', False),
            "success": True,
            "userBanner": data.get('userBanner', data.get('avatar', 'N/A')),
            "username": data.get('username', 'N/A'),
            "verified": data.get('verified', False)
        }
        
        print(f"Debug - Initial data: {data}")
        print(f"Debug - Formatted data: {formatted_data}")
        
        # Enhanced logic for account creation date
        if formatted_data["account_created"] in ['N/A', None, '']:
            # Try different possible field names from the API response
            creation_candidates = [
                'created_at', 'date_joined', 'registration_date', 
                'account_creation_date', 'created_time', 'join_date'
            ]
            
            for field in creation_candidates:
                if field in data and data[field] not in [None, '', 'N/A']:
                    formatted_data["account_created"] = data[field]
                    break
            
            # If still not found, try the fallback API
            if formatted_data["account_created"] in ['N/A', None, ''] and formatted_data["id2"] not in ['N/A', None, '']:
                try:
                    print(f"Debug - Trying fallback API with ID: {formatted_data['id2']}")
                    gojo_url = os.getenv('GOJOAPI_URL', 'https://gojoapi.pythonanywhere.com')
                    
                    # Try different endpoints and parameters
                    endpoints_to_try = [
                        f"{gojo_url}/get-year?Id={formatted_data['id2']}",
                        f"{gojo_url}/get-year?id={formatted_data['id2']}",
                        f"{gojo_url}/get-year?user_id={formatted_data['id2']}",
                        f"{gojo_url}/api/get-year?Id={formatted_data['id2']}"
                    ]
                    
                    for endpoint in endpoints_to_try:
                        try:
                            creation_response = requests.get(endpoint, headers=headers, timeout=10)
                            print(f"Debug - Fallback API response: {creation_response.status_code}, {creation_response.text}")
                            
                            if creation_response.status_code == 200:
                                creation_data = creation_response.json()
                                year = creation_data.get('year', creation_data.get('created_year', 'N/A'))
                                
                                if year not in ['N/A', None, '']:
                                    formatted_data["account_created"] = str(year)
                                    print(f"Debug - Found creation year: {year}")
                                    break
                        except Exception as e:
                            print(f"Debug - Error with endpoint {endpoint}: {e}")
                            continue
                    
                    # If still no success, try with numeric ID extraction
                    if formatted_data["account_created"] in ['N/A', None, ''] and formatted_data["id"] not in ['N/A', None, '']:
                        try:
                            # Sometimes the ID field contains the numeric ID
                            numeric_id = str(formatted_data["id"])
                            if numeric_id.isdigit():
                                creation_response = requests.get(
                                    f"{gojo_url}/get-year?Id={numeric_id}",
                                    headers=headers,
                                    timeout=10
                                )
                                if creation_response.status_code == 200:
                                    creation_data = creation_response.json()
                                    year = creation_data.get('year', 'N/A')
                                    if year not in ['N/A', None, '']:
                                        formatted_data["account_created"] = str(year)
                        except Exception as e:
                            print(f"Debug - Error with numeric ID: {e}")
                
                except Exception as e:
                    print(f"Error fetching creation year: {e}")
            
            # Final fallback
            if formatted_data["account_created"] in ['N/A', None, '']:
                formatted_data["account_created"] = 'Could not fetch'
        
        # Format numbers with commas for display
        followers_formatted = f"{formatted_data['followers']:,}" if isinstance(formatted_data['followers'], int) else str(formatted_data['followers'])
        following_formatted = f"{formatted_data['following']:,}" if isinstance(formatted_data['following'], int) else str(formatted_data['following'])
        posts_formatted = f"{formatted_data['posts']:,}" if isinstance(formatted_data['posts'], int) else str(formatted_data['posts'])
        
        # Create display message
        message = f"""
🔍 **Instagram User Details**
━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **User:** {formatted_data['username']}
📛 **Name:** {formatted_data['nickname']}
🆔 **ID:** {formatted_data['id']}
🔢 **Numeric ID:** {formatted_data['id2']}
🔒 **Private:** {'Yes' if formatted_data['private'] else 'No'}
✅ **Verified:** {'Yes' if formatted_data['verified'] else 'No'}
👥 **Followers:** {followers_formatted}
🔄 **Following:** {following_formatted}
📸 **Posts:** {posts_formatted}
📅 **Created In:** {formatted_data['account_created']}
📝 **Bio:** {formatted_data['biography'][:100]}{'...' if len(str(formatted_data['biography'])) > 100 else ''}
🔗 **Meta Status:** {formatted_data['meta_status']}

━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        await loading_msg.edit_text(message, parse_mode='Markdown')
        
    except requests.exceptions.Timeout:
        await loading_msg.edit_text('⏱️ Request timeout. Please try again.')
    except requests.exceptions.RequestException as e:
        await loading_msg.edit_text(f'🚨 Network error occurred: {str(e)}')
    except Exception as e:
        await loading_msg.edit_text(f'🚨 An error occurred: {str(e)}')

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
        
        # Updated Instagram recovery endpoint and headers
        recovery_url = 'https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/'
        
        # More realistic headers
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/accounts/password/reset/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-csrftoken': 'missing',
            'x-ig-app-id': '936619743392459',
            'x-ig-www-claim': '0',
            'x-instagram-ajax': '1',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        # Updated payload format
        payload = {
            'email_or_username': email_or_username,
            'flow': 'fxcal'
        }
        
        # First, try to get CSRF token
        try:
            session = requests.Session()
            login_page = session.get('https://www.instagram.com/accounts/password/reset/', headers={
                'User-Agent': headers['user-agent']
            }, timeout=10)
            
            # Try to extract CSRF token from page
            csrf_token = 'missing'
            if 'csrf_token' in login_page.text:
                import re
                csrf_match = re.search(r'"csrf_token":"([^"]+)"', login_page.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
            
            headers['x-csrftoken'] = csrf_token
            
            # Make the reset request
            response = session.post(recovery_url, data=payload, headers=headers, timeout=15)
            
        except Exception as e:
            print(f"Error with session approach: {e}")
            # Fallback to direct request
            response = requests.post(recovery_url, data=payload, headers=headers, timeout=15)
        
        # Calculate time taken
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        # Get user's display name
        user_name = update.effective_user.first_name or update.effective_user.username or "Unknown User"
        
        print(f"Debug - Reset response: {response.status_code}, {response.text}")
        
        # Parse response to extract email if available
        associated_email = "Not Available"
        try:
            if response.status_code == 200:
                response_data = response.json()
                print(f"Debug - Response JSON: {response_data}")
                
                # Try different possible email fields
                email_fields = ['email', 'obfuscated_email', 'masked_email', 'recovery_email']
                for field in email_fields:
                    if field in response_data and response_data[field]:
                        email = response_data[field]
                        # Email might already be masked
                        if '*' in email:
                            associated_email = email
                        else:
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
                        break
                
                # Check if the request was actually successful
                success = response_data.get('status') == 'ok' or response_data.get('success', False)
                
        except Exception as e:
            print(f"Error parsing response: {e}")
            success = response.status_code == 200
        
        # Format response
        if response.status_code == 200 and success:
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
≭ 𝗘𝗿𝗿𝗼𝗿: `Status {response.status_code}`
            """
        
        await processing_msg.edit_text(result_text, parse_mode='Markdown')
        
    except requests.exceptions.Timeout:
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        error_text = f"""
•𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱 𝗥𝗲𝘀𝗲𝘁 𝗙𝗮𝗶𝗹𝗲𝗱!

≭ 𝗧𝗮𝗿𝗴𝗲𝘁: `{email_or_username}`
≭ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗕𝘆: `{user_name}`
≭ 𝗕𝗼𝘁 𝗕𝘆 / 𝗗𝗲𝘃: @meta_server
≭ 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻: `{time_taken}` 𝘀𝗲𝗰𝗼𝗻𝗱𝘀
≭ 𝗘𝗿𝗿𝗼𝗿: `Request Timeout`
        """
        
        await processing_msg.edit_text(error_text, parse_mode='Markdown')
        
    except Exception as e:
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        user_name = update.effective_user.first_name or update.effective_user.username or "Unknown User"
        
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

async def cancel_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the reset process"""
    user_id = update.effective_user.id
    if user_id in reset_states:
        del reset_states[user_id]
    
    await update.message.reply_text('❌ Password reset cancelled.')
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
        fallbacks=[CommandHandler('cancel', cancel_reset)]
    )
    
    app.add_handler(reset_handler)
    
    print("✅ Instagram info commands loaded")
