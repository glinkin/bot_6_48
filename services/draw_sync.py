"""Background service for synchronizing draw data from external API."""
import logging
import asyncio
from api.client import LotteryAPIClient
from db.database import async_session_maker
from db.crud_draws import create_or_update_draw, get_current_draw

logger = logging.getLogger(__name__)


async def sync_current_draw():
    """Synchronize current draw data from API to database."""
    try:
        logger.info("Starting draw synchronization...")
        
        api_client = LotteryAPIClient()
        
        # Get current draw from API
        api_draw = await api_client.get_current_draw()
        
        if not api_draw:
            logger.info("No current draw found in API")
            return
        
        # Save to database
        async with async_session_maker() as session:
            draw = await create_or_update_draw(session, api_draw)
            logger.info(f"Draw synchronized: {draw.name} (ID: {draw.external_id}, Status: {draw.status})")
            
            if draw.winning_numbers:
                logger.info(f"Winning numbers: {draw.winning_numbers}")
    
    except Exception as e:
        logger.error(f"Error synchronizing draw: {e}", exc_info=True)


async def draw_sync_worker(interval: int = 300):
    """
    Background worker that periodically synchronizes draw data.
    
    Args:
        interval: Sync interval in seconds (default: 300 = 5 minutes)
    """
    logger.info(f"Draw sync worker started (interval: {interval}s)")
    
    while True:
        try:
            await sync_current_draw()
        except Exception as e:
            logger.error(f"Unexpected error in draw sync worker: {e}", exc_info=True)
        
        # Wait before next sync
        await asyncio.sleep(interval)
