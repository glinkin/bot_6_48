# 6-45Bot - Telegram Lottery Bot

Telegram bot for weekly numerical lottery (6 numbers from 1-45). Displays ticket status, lottery results, and winnings.

## Features

- 📱 Phone number identification
- 🎟️ **Tickets issued externally** (marketing campaigns)
- 🎯 **Number selection** for tickets:
  - 🎲 Auto-generate random numbers
  - ✏️ Manually select your numbers (1-45)
  - ⏰ Defer to auto-generation at draw start
- 🎫 Ticket status display
- 🏆 Results and prize calculation
- 🤖 Automatic number generation for unassigned tickets

## Tech Stack

- **Bot**: aiogram 3.x (Python async Telegram bot)
- **Database**: PostgreSQL (async SQLAlchemy)
- **API**: REST with API key authentication

## Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone <repo-url>
cd 6-45Bot

# 2. Configure environment
cp .env.example .env
# Edit .env with your tokens

# 3. Start services
docker-compose up -d

# 4. View logs
docker-compose logs -f bot
```

### Option 2: Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
API_BASE_URL=https://api.lottery-system.example.com
API_KEY=your_api_key
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/lottery_bot
```Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# View logs
docker-compose logs -f bot
docker-compose logs -f db

# Access database
docker-compose exec db psql -U lottery_user -d lottery_bot

# Run migrations
docker-compose exec bot alembic upgrade head

# Restart bot only
docker-compose restart bot
```

## 

### 3. Setup Database

```bash
# Create database
psql -U postgres -c "CREATE DATABASE lottery_bot;"

# Run migrations
alembic upgrade head
```

### 4. Run Bot

```bash
python main.py
```

## Project Structure

```
6-45Bot/
├── main.py                 # Bot entry point
├── config.py              # Settings from .env
├── bot/
│   ├── handlers/          # Command handlers
│   ├── keyboards.py       # Telegram keyboards
│   ├── messages.py        # Message templates
│   └── middleware.py      # DB session injection
├── api/
│   └── client.py          # External API client
├── db/
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # DB connection
│   └── crud.py            # Database operations
├── services/
│   ├── ticket_checker.py  # Prize calculation
│   └── user_service.py    # User registration
└── alembic/               # Database migrations
```

## Business Rules

### Lottery Mechanics
- One draw per week
- 6 unique numbers (1-45)
- One ticket per user per draw
- **Tickets issued by external system** (marketing campaigns)
- User can select numbers for their ticket

### Prize Distribution (Total: 500,000)
- 6 matches → 200,000 (40%)
- 5 matches → 125,000 (25%)
- 4 matches → 100,000 (20%)
- 3 matches → 75,000 (15%)
- 0-2 matches → No prize

## Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
pytest tests/
```

## User Flow
**Marketing Campaign** → User participates and earns ticket
2. **Issue Ticket** (external system):
   ```bash
   docker-compose exec bot python scripts/issue_ticket.py 79652223633
   ```
3. User opens bot → `/start`
4. Bot requests phone number
5. User shares contact
6. View ticket → "🎫 Мой билет" (numbers not assigned yet)
7. **Select numbers** → "🎯 Выбрать числа"
   - Auto-generate numbers
   - Enter manually (e.g., "1 5 12 23 34 45")
   - Skip (auto-generate at draw start)
8. Check results → "🏆 Результаты розыгрыша"

## Issue Tickets (External System)

Simulate ticket issuance after marketing campaign:

```bash
# Issue ticket to user by phone number
docker-compose exec bot python scripts/issue_ticket.py <phone>

# Example
docker-compose exec bot python scripts/issue_ticket.py 79652223633
```

**Note**: User must register in bot first (/start + share contact)
7. Check results → "🏆 Реtickets NOT created by users
- Tickets issued only after marketing campaigns
- Users can only select numbers for issued tickets
- Numbers cannot be changed once assigned

Run this command before starting the draw:

```bash
# Inside Docker container
docker-compose exec bot python scripts/generate_numbers.py

# Or locally
python scripts/generate_numbers.py
```

This will generate random numbers for all tickets that deferred selection.

## Important Notes

- Bot is **READ-ONLY** - no ticket creation/editing
- Phone number is primary identifier
- All tickets assigned by external system
- Multiple tickets per draw NOT allowed

## License

MIT
