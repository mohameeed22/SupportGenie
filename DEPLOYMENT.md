# Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Telegram bot token (from @BotFather)
- Groq API key (from https://console.groq.com)

### 1. Setup Environment

```bash
# Copy example config
cp .env.example .env

# Edit with your values
nano .env  # or use your favorite editor
```

Update these fields:
- `TELEGRAM_BOT_TOKEN` — Your bot token from @BotFather
- `GROQ_API_KEY` — Your Groq API key
- `ADMIN_USER_IDS` — Your Telegram user ID (comma-separated for multiple admins)

### 2. Run with Docker Compose

```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f supportgenie-bot

# Stop the bot
docker-compose down

# Restart
docker-compose restart
```

### 3. Manual Docker Build

```bash
# Build image
docker build -t supportgenie-bot:latest .

# Run container
docker run -d \
  --name supportgenie \
  --env-file .env \
  -v supportgenie-db:/data \
  supportgenie-bot:latest

# View logs
docker logs -f supportgenie

# Stop
docker stop supportgenie
docker rm supportgenie
```

## Local Development Setup

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/SupportGenie.git
cd SupportGenie
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Bot Locally

```bash
python bot.py
```

The bot will:
1. Create `supportgenie.db` if it doesn't exist
2. Initialize database schema
3. Start polling for Telegram messages
4. Log activity to console

## Production Deployment Options

### Option 1: Docker Compose (Recommended)

**Pros:**
- Simple single-command deployment
- Persistent database in volume
- Automatic restart
- Resource limits configured

**Cons:**
- Requires Docker host
- Single-machine only

**Setup:**
```bash
docker-compose up -d
```

### Option 2: Kubernetes

Requires Helm chart or K8s manifests (not included).

```bash
kubectl apply -f supportgenie-deployment.yaml
```

### Option 3: Cloud Platforms

#### Heroku
```bash
git push heroku main
```

Requires:
- Procfile with `web: python bot.py`
- Config vars in Heroku dashboard

#### Railway / Render
1. Connect GitHub repo
2. Set environment variables in dashboard
3. Auto-deploy on push

## Database Management

### Backup

```bash
# Docker
docker-compose exec supportgenie-bot sqlite3 /data/supportgenie.db ".backup '/tmp/backup.db'"
docker cp supportgenie-bot:/tmp/backup.db ./supportgenie-backup-$(date +%Y%m%d).db

# Local
cp supportgenie.db supportgenie-backup-$(date +%Y%m%d).db
```

### Restore

```bash
# Docker
docker cp supportgenie-backup.db supportgenie-bot:/tmp/backup.db
docker-compose exec supportgenie-bot sqlite3 /data/supportgenie.db ".restore '/tmp/backup.db'"

# Local
cp supportgenie-backup.db supportgenie.db
```

### Inspect Database

```bash
# Docker
docker-compose exec supportgenie-bot sqlite3 /data/supportgenie.db "SELECT COUNT(*) as user_count FROM users;"

# Local
sqlite3 supportgenie.db "SELECT COUNT(*) as user_count FROM users;"
```

## Monitoring

### View Logs

```bash
# Docker
docker-compose logs -f --tail=50 supportgenie-bot

# Local (if running in background)
tail -f bot.log  # Requires logging configuration
```

### Health Check

The Docker container includes a health check that verifies the database exists:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
# Output: supportgenie-bot    Up 2 hours (healthy)
```

### Admin Commands

```
/stats      — View dashboard (users, questions, escalations)
/broadcast  — Send message to all users (admin only)
```

Get bot stats via Telegram admin commands:
- Send `/stats` to the bot (requires ADMIN_USER_IDS)

## Updating

### Docker

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build

# Restart
docker-compose down && docker-compose up -d
```

### Local

```bash
git pull
# Restart: Ctrl+C, then `python bot.py`
```

## Troubleshooting

### Bot doesn't respond
1. Check token: `docker logs supportgenie-bot | grep -i token`
2. Verify in telegram: `/start`
3. Check rate limits aren't blocking

### Database locked
- Stop and restart bot
- Check no other processes access `supportgenie.db`

### Memory usage high
- Check conversation history (20 message limit is set)
- Review user count: `/stats`

### Groq API errors
- Verify API key in .env
- Check Groq status: https://status.groq.com
- Review rate limits for Groq account

## Configuration Reference

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | — | ✓ | From @BotFather |
| `GROQ_API_KEY` | — | ✓ | From console.groq.com |
| `GROQ_MODEL` | llama-3.3-70b-versatile | — | Other options: llama-3.1-8b, mixtral |
| `SUPPORT_EMAIL` | support@novabuy.store | — | Contact for escalations |
| `SUPPORT_HOURS` | Mon-Fri, 9am-6pm EST | — | Display in escalation message |
| `ADMIN_USER_IDS` | — | — | Comma-separated, needed for /stats |
| `RATE_LIMIT_MAX_MESSAGES` | 10 | — | Messages per user per window |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | — | Time window for rate limit (seconds) |
| `SUPPORTGENIE_DB_PATH` | supportgenie.db | — | SQLite database location |

## Performance Tuning

### Database
- WAL mode enabled (faster writes)
- Foreign keys enabled
- Connection pooling with 5 connections

### API
- Streaming responses (0.6s buffer)
- 20-message conversation history limit
- Sentiment pre-check before AI (fast reject on frustration)

### Rate Limiting
- Rolling window per user
- Configurable max messages and window
- Prevents API quota exhaustion

## Security

### Sensitive Data
- Database file (`supportgenie.db`) should not be committed
- `.env` file must be in `.gitignore`
- Docker secrets for production (not implemented)

### API Keys
- Never log `TELEGRAM_BOT_TOKEN` or `GROQ_API_KEY`
- Rotate tokens in admin panel regularly
- Use environment variables only (not hardcoded)

### Telegram Bot Security
- Validate incoming updates
- Restrict admin commands to `ADMIN_USER_IDS`
- Rate limit all endpoints

## Support

For issues:
1. Check logs: `docker-compose logs supportgenie-bot`
2. Review this guide
3. Open GitHub issue with:
   - Error message
   - Environment (Docker/local)
   - Steps to reproduce
