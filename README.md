# Chizza Guild Wrapped

A year-end "Wrapped" web application for your Hypixel guild, inspired by Spotify Wrapped. View your guild's statistics including most active members, message counts, new members, and most mentioned members.

## Features

- **Most Active Members** - Top guild members by XP earned
- **Top Messengers** - Members who sent the most Discord messages
- **New Members** - Members who joined this year
- **Most Pinged** - Most mentioned members in Discord
- **Beautiful UI** - Spotify Wrapped-inspired design with smooth animations
- **Mobile Responsive** - Works great on all devices

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Jinja2 templates, vanilla JavaScript, CSS
- **Database**: SQLite
- **APIs**: Hypixel Public API, Discord API

## Prerequisites

- Python 3.8 or higher
- Hypixel API key (get by running `/api new` in-game)
- Discord bot token (create at [Discord Developer Portal](https://discord.com/developers/applications))

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Chizza-Guild/chizzaYearly.git
cd chizzaYearly
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Configuration

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Hypixel API
HYPIXEL_API_KEY=your-hypixel-api-key
HYPIXEL_GUILD_ID=your-guild-id

# Discord API
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_GUILD_ID=your-discord-server-id
DISCORD_CHANNEL_IDS=channel1-id,channel2-id

# Application
YEAR=2025
START_DATE=2025-01-01
END_DATE=2025-12-31

# Security
ADMIN_PASSWORD=your-secure-password
```

#### Getting Your Credentials

**Hypixel API Key:**
1. Join Hypixel (mc.hypixel.net)
2. Run `/api new` in chat
3. Copy the API key

**Hypixel Guild ID:**
1. Visit: `https://api.hypixel.net/guild?key=YOUR_API_KEY&name=YOUR_GUILD_NAME`
2. Copy the `_id` field from the response

**Discord Bot:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Go to "Bot" section and click "Add Bot"
4. **IMPORTANT**: Enable these intents:
   - Message Content Intent ✅ (Required!)
   - Server Members Intent ✅
   - Messages Intent ✅
5. Copy the bot token
6. Go to OAuth2 → URL Generator
7. Select scopes: `bot`
8. Select permissions: `Read Message History`, `View Channels`
9. Use the generated URL to add the bot to your Discord server

**Discord Guild/Channel IDs:**
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your server → "Copy Server ID"
3. Right-click channels → "Copy Channel ID"

### 5. Initialize Database

```bash
python scripts/init_db.py
```

## Usage

### Collect Year-End Data

Run this script on December 31st or January 1st to collect data for the year:

```bash
python scripts/fetch_data.py
```

This will:
- Fetch guild data from Hypixel API
- Calculate XP statistics
- Fetch Discord message history (may take 10-30 minutes)
- Calculate Discord statistics
- Save everything to the database

### Start the Web Server

```bash
python run.py
```

Visit `http://localhost:8000` in your browser.

### View Your Wrapped

Navigate to `http://localhost:8000/wrapped/2025` to view your wrapped!

## Project Structure

```
hypixel-eoy/
├── app/
│   ├── models/          # Pydantic data models
│   ├── services/        # API integration services
│   ├── routes/          # FastAPI routes
│   ├── templates/       # HTML templates
│   ├── static/          # CSS and JavaScript
│   ├── config.py        # Configuration management
│   └── main.py          # FastAPI application
├── data/
│   ├── cache/           # Cached API responses
│   └── wrapped.db       # SQLite database
├── scripts/
│   ├── fetch_data.py    # Data collection script
│   └── init_db.py       # Database initialization
├── .env                 # Your configuration (not committed)
├── .env.example         # Configuration template
├── requirements.txt     # Python dependencies
└── run.py              # Development server
```

## API Endpoints

- `GET /` - Landing page
- `GET /wrapped/{year}` - Wrapped interface for specific year
- `GET /api/stats/{year}` - JSON API for statistics
- `POST /admin/refresh` - Refresh data (password protected)

## Admin Panel

To manually refresh data, visit:
```
POST http://localhost:8000/admin/refresh
```

Use HTTP Basic Auth with:
- Username: (any)
- Password: (your ADMIN_PASSWORD from .env)

Or use curl:
```bash
curl -X POST http://localhost:8000/admin/refresh -u :your-password
```

## Deployment

### Heroku

1. Create a new Heroku app
2. Add a `Procfile`:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
3. Set environment variables in Heroku dashboard
4. Deploy via Git or GitHub integration

### Railway

1. Create new project from GitHub repo
2. Add environment variables
3. Railway will auto-detect and deploy

### VPS (Ubuntu/Debian)

1. Install Python and dependencies
2. Use systemd or supervisor to run the app
3. Set up Nginx as reverse proxy
4. Use Let's Encrypt for HTTPS

## Troubleshooting

### Discord Bot Can't Read Messages

**Problem**: Bot fetches 0 messages
**Solution**: Enable "Message Content Intent" in Discord Developer Portal under Bot settings

### Hypixel API Errors

**Problem**: 403 Forbidden or Invalid API Key
**Solution**:
- Get a new API key with `/api new` in Hypixel
- Make sure the key is correctly set in `.env`

### No Data in Wrapped

**Problem**: Wrapped page shows "No data found"
**Solution**: Run `python scripts/fetch_data.py` first to collect data

### Discord Rate Limits

**Problem**: Script hangs or takes forever
**Solution**: discord.py handles rate limits automatically. Just wait - large message histories take time!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file

## Credits

Created for Chizza Guild

Inspired by Spotify Wrapped

## Support

For issues or questions:
- Open an issue on GitHub
- Check the troubleshooting section above

## Roadmap

Future enhancements:
- [ ] Individual member wrapped
- [ ] Shareable cards/images
- [ ] Year-over-year comparisons
- [ ] More statistics and fun facts
- [ ] Multiple guild support
- [ ] Discord bot integration (`/wrapped` command)
