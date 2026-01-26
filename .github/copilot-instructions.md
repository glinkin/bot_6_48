# Copilot Instructions for 6-45Bot

## Project Overview
Telegram bot for weekly numerical lottery (6 numbers from 1-45). The bot is READ-ONLY — tickets are issued exclusively via external API, never created in the bot itself.

**Core Purpose**: Display ticket status, lottery results, and winnings based on phone number identification.

## Critical Business Rules

### Lottery Mechanics
- **Weekly draw**: One lottery per week
- **Ticket format**: Exactly 6 unique numbers (1-45)
- **One ticket per user** per draw (strictly enforced)
- **Tickets issued externally** — after marketing campaigns, NOT by bot

### Ticket Number Assignment
- User can select numbers for their ticket:
  - 🎲 **Auto-generate**: Random 6 numbers
  - ✏️ **Manual**: User enters 6 numbers (1-45)
  - ⏰ **Defer**: Auto-generate at draw start
- Numbers **cannot be changed** once assigned
- If not assigned, auto-generated before draw

### Prize Distribution (Total Fund: 500,000)
```
6 matches → 40% (200,000)
5 matches → 25% (125,000)
4 matches → 20% (100,000)
3 matches → 15% (75,000)
0-2 matches → No prize
```

### User Identification
- **Primary ID**: Phone number (NOT Telegram ID)
- Telegram ID used only for linking to phone number
- If phone not found → show "No ticket for current draw"

## Architecture

### Data Flow
```
External System → API → Bot Backend → Telegram User
     ↓               ↓         ↓
  Issues          Checks    Displays
  Ticket          Status     Status
```

### Components
- **Bot Handler**: Telegram message/command processing
- **API Client**: Communicates with external ticket system
- **User Store**: Telegram ID ↔ Phone number mapping
- **Ticket Checker**: Validates ticket existence, calculates matches
- **Status Manager**: Tracks ticket states (issued, pending, won, lost)

### Ticket Status Lifecycle
1. `issued` — Ticket assigned by external system
2. `pending` — Draw not yet conducted
3. `won` — Has winning matches (3+)
4. `lost` — No winning matches (0-2)

## User Flow

### First-Time User
1. User opens bot
2. Bot requests phone number (Telegram contact share)
3. Save `telegram_id ↔ phone` mapping
4. Check ticket via API (by phone)
5. Display ticket or "No ticket" message

### Returning User
1. User opens bot
2. Retrieve phone from stored mapping
3. Check ticket via API
4. Display current ticket status and numbers

### Post-Draw
1. External system publishes winning combination
2. Bot fetches results via API
3. Calculate matches for user's ticket
4. Determine prize amount (if any)
5. Update and display status

## Tech Stack
- **Bot Framework**: aiogram 3.x (async Python Telegram bot library)
- **Database**: PostgreSQL (user phone ↔ telegram_id mapping)
- **External API**: REST with API key authentication
- **Python**: 3.11+

## Development Workflow

### Setup (Local)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup database
psql -U postgres -c "CREATE DATABASE lottery_bot;"
python -m alembic upgrade head
```

### Setup (Docker)
```bash
# Create .env file with your tokens
cp .env.example .env

# Start all services (database + bot)
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Environment Variables
Create `.env` file:
```bash
TELEGRAM_BOT_TOKEN=<your_bot_token>
API_BASE_URL=https://api.lottery-system.example.com
API_KEY=<your_api_key>
DATABASE_URL=postgresql://user:password@localhost:5432/lottery_bot
```

### Running Locally
```bash
# Without Docker
python main.py

# With Docker
docker-compose up
# Migrations run automatically on container start

# Manual migration inside container
docker-compose exec bot alembic revision --autogenerate -m "description"
docker-compose exec bot alembic upgrade head

# Access database
docker-compose exec db psql -U lottery_user -d lottery_boton
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Database Migrations (Docker)
```bash
# Create new migration
alembic revision --autogenerate -m "description"
by users in bot
- ❌ NO ticket editing/modification
- ❌ NO changing numbers after assignment
- ❌ NO multiple tickets per user per draw
- ✅ ALWAYS verify ticket exists before allowing number selection
- ✅ ALWAYS use phone number as primary ID
- ✅ ALWAYS show clear status messages
- ✅ Tickets issued ONLY via scripts (marketing campaigns)
### Critical Constraints (NEVER violate)
- ❌ NO ticket creation in bot
- ❌ NO ticket editing/modification
- ❌ NO multiple tickets per user per draw
- ❌ NO manual number selection
- ✅ ALWAYS verify ticket via API
- ✅ ALWAYS use phone number as primary ID
- ✅ ALWAYS show clear status messages

### API Integration Patterns
When checking tickets:
```python
# Correct approach (using aiohttp for async REST API calls)
async def check_user_ticket(phone: str):
    async with aiohttp.ClientSession() as session:
        headers = {"X-API-Key": settings.API_KEY}
        async with session.get(
            f"{settings.API_BASE_URL}/tickets/{phone}/current",
            headers=headers
        ) as response:
            if response.status == 404:
                return None
            return await response.json()

# In handler
ticket = await api_client.get_ticket_by_phone(phone_number)
if not ticket:
    await message.answer("У вас нет билета на текущий розыгрыш")
else:
    await display_ticket(message, ticket)
```

### Database Patterns
Using SQLAlchemy with async PostgreSQL:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_user_phone(telegram_id: int, session: AsyncSession) -> str | None:
    result = await session.execute(
        select(User.phone).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()
```

### Error Handling
- API unavailable → "Система временно недоступна"
- Phone not found → "У вас нет билета на текущий розыгрыш"
- Invalid ticket data → Log error, show generic message to user
Project Structure
```
6-45Bot/
├── main.py                 # Bot entry point, starts polling
├── bot/
│   ├── handlers/          # Message/command handlers
│   │   ├── start.py       # /start, phone number request
│   │   └── ticket.py      # Ticket status display
│   ├── keyboards.py       # Telegram keyboard layouts
│   ├── messages.py        # Message templates (Russian text)
│   └── middleware.py      # DB session injection
├── api/
│   └── client.py          # REST API client for external system
├── db/
│   ├── models.py          # SQLAlchemy models (User)
│   ├── database.py        # Async engine, session factory
│   └── crud.py            # Database operations
├── services/
│   ├── ticket_checker.py  # Match calculation, prize determination
│   └── user_service.py    # User registration, phone linking
├── alembic/               # Database migrations
├── config.py              # Settings from .env (pydantic)
├── requirements.txt
└── .env
```

## Key Files
- [main.py](main.py) — Initializes bot, registers handlers, starts polling
- [bot/handlers/start.py](bot/handlers/start.py) — `/start` command, phone number request via ReplyKeyboardMarkup
- [bot/handlers/ticket.py](bot/handlers/ticket.py) — Displays ticket status after checking API
- [api/client.py](api/client.py) — Async REST client with API key header
- [db/models.py](db/models.py) — `User` model: `telegram_id`, `phone`, `created_at`
- [services/ticket_checker.py](services/ticket_checker.py) — `calculate_matches()`, `get_prize_amount()`
- [config.py](config.py) — Loads settings via pydantic-settings

## Testing Strategy
```bash
# Run tests with pytest
pytest tests/

# Specific test categories
pytest tests/test_api_client.py      # Mock aiohttp responses
pytest tests/test_ticket_checker.py  # Match calculation (0-6)
pytest tests/test_user_service.py    # Phone validation
```

Test coverage:
- Mock external API responses (ticket found/not found, API errors)
- Test match calculation for all scenarios (0-6 matches)
- Test prize calculation against distribution table
- Test phone number validation and normalization
- Test duplicate ticket prevention per draw
- Test database operations (user creation, phone lookup)ort, clear)

### Integrating New API Endpoint
1. Add method to API client
2. Handle response/error cases
3. Update ticket checker logic if needed
4. Test with mock data first

### Adding Notification Feature
- Notifications NOT initiated by bot
- Bot only displays status when user checks
- SMS/Telegram notifications handled by external system

## Key Files (TODO: Update once implemented)
- `bot.py/main.js` — Bot entry point
- `api_client.py/apiClient.js` — External API integration
- `ticket_checker.py/ticketChecker.js` — Match calculation logic
- `user_store.py/userStore.js` — Phone ↔ Telegram ID mapping
- `config.py/.env` — Environment configuration

## Testing Strategy
- Mock external API responses (ticket found/not found scenarios)
- Test match calculation (0-6 matches)
- Test prize calculation against distribution table
- Test phone number validation
- Test duplicate ticket prevention per draw
