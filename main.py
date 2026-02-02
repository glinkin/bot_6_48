"""Main entry point for the lottery bot."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from db.database import init_db
from bot.middleware import DatabaseMiddleware
from bot.handlers import start, ticket, create_ticket
from services.draw_sync import draw_sync_worker


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    logger.info("Starting lottery bot...")
    logger.info(f"API Base URL: {settings.api_base_url}")
    logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register middleware
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(create_ticket.router)
    dp.include_router(ticket.router)
    logger.info("Handlers registered")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")
    
    # Start background draw synchronizer
    logger.info("Starting draw synchronizer...")
    sync_task = asyncio.create_task(draw_sync_worker(interval=300))  # Sync every 5 minutes
    logger.info("Draw synchronizer started")
    
    # Start polling
    logger.info("Bot started successfully! Polling for updates...")
    try:
        await dp.start_polling(bot)
    finally:
        sync_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
