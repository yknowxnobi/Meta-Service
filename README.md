# Instagram Multi-Feature Telegram Bot

A comprehensive Telegram bot for Instagram-related tasks including user information lookup, account analysis, reporting tools, and session management.

## Features

- 🔍 **Instagram Info** - Get detailed user information and account creation year
- 🎯 **Meth Analyzer** - Advanced Instagram account analysis
- 📊 **Report Tool** - Automated Instagram reporting system
- 🔐 **Session Manager** - Generate Instagram session IDs
- ⚡ **Password Reset** - Instagram password reset helper

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)
- A Telegram channel for forced subscription

### 2. Local Development

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd instagram-telegram-bot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your bot token and other details

4. **Run the bot:**
```bash
python main.py
```

### 3. Deploy on Render

1. **Create account on Render.com**

2. **Connect your GitHub repository**

3. **Configure the service:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`

4. **Set environment variables:**
   - Go to Environment section
   - Add all variables from your `.env` file

5. **Deploy the service**

## Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here

# Admin Configuration
ADMIN_ID=your_admin_telegram_id

# Channel Configuration
CHANNEL_ID=@YourChannel

# API Configuration (Optional)
NEXTCOUNTS_API=https://api-v2.nextcounts.com
GOJOAPI_URL=https://gojoapi.pythonanywhere.com
IG_INFO_API=https://ig-info-drsudo.vercel.app

# Instagram Configuration
IG_RECOVERY_URL=https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/
IG_HELP_URL=https://help.instagram.com/ajax/help/contact/submit/page

# Bot Configuration
REQUEST_TIMEOUT=7
LOADING_DELAY=500
```

## Project Structure

```
instagram-telegram-bot/
├── main.py                 # Main bot entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── README.md              # This file
└── bot_commands/          # Feature modules
    ├── __init__.py
    ├── insta_info.py      # Instagram info & reset features
    ├── meth_analyzer.py   # Account analysis feature
    ├── report_tool.py     # Instagram reporting tool
    └── session_manager.py # Session ID generator
```

## Commands

- `/start` - Start the bot and show welcome message
- `/help` - Show available commands
- `/insta <username>` - Get Instagram user details
- `/reset` - Instagram password reset helper
- `/meth` - Start Instagram account analysis
- `/report` - Instagram reporting tool
- `/session` - Generate Instagram session ID

## Features Details

### Instagram Info (`/insta`)
- Fetches user details from Instagram
- Shows follower count, following, posts
- Displays account creation year
- Works with public and some private accounts

### Meth Analyzer (`/meth`)
- Advanced account analysis
- Categorizes potential violations
- Provides reporting suggestions
- Interactive confirmation system

### Report Tool (`/report`)
- Automated Instagram reporting
- Multiple report attempts
- Real-time progress tracking
- Success rate statistics

### Session Manager (`/session`)
- Generates Instagram session IDs
- Secure credential processing
- Session validation
- Error handling and troubleshooting

## Security Features

- Automatic password message deletion
- No credential storage
- Secure API requests
- Rate limiting protection
- Channel subscription verification

## Deployment Notes

### For Render:
- Service will auto-restart on crashes
- Logs are available in dashboard
- Environment variables are secure
- Free tier available with limitations

### For other platforms:
- Ensure Python 3.8+ is available
- Install all requirements
- Set proper environment variables
- Keep the service running 24/7

## Troubleshooting

### Common Issues:

1. **Bot not responding:**
   - Check BOT_TOKEN is correct
   - Verify internet connection
   - Check Render logs for errors

2. **Instagram features not working:**
   - Instagram may block requests
   - Use VPN if rate limited
   - Check API endpoints are accessible

3. **Channel subscription not working:**
   - Verify CHANNEL_ID format (@YourChannel)
   - Make sure bot is admin in channel
   - Check channel is public

## Support

For support and updates:
- 📢 Channel: [Your Channel]
- 💬 Support: [Your Support Chat]
- 👨‍💻 Developer: [Your Contact]

## License

This project is for educational purposes only. Use responsibly and in accordance with Instagram's Terms of Service.

## Disclaimer

- This bot is for educational and legitimate use only
- Users are responsible for their actions
- Developer is not liable for misuse
- Respect Instagram's Terms of Service and Community Guidelines
