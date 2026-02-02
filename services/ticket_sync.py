"""Service for synchronizing user tickets from API."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from api.client import LotteryAPIClient
from db.crud_tickets import sync_user_tickets_from_api, get_user_tickets
from db.crud import get_user_by_telegram_id

logger = logging.getLogger(__name__)


async def sync_tickets_for_user(
    session: AsyncSession,
    telegram_id: int,
    api_client: LotteryAPIClient,
    draw_id: int = None
) -> list:
    """
    Synchronize tickets for a specific user from API.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        api_client: API client instance
        draw_id: Optional draw ID to filter tickets
    
    Returns:
        List of synced tickets
    """
    try:
        logger.info(f"Syncing tickets for user {telegram_id}")
        
        # Get user from database
        user = await get_user_by_telegram_id(session, telegram_id)
        if not user:
            logger.warning(f"User {telegram_id} not found in database")
            return []
        
        # Check if user has external_id (customer ID in API)
        if not user.external_id:
            logger.warning(f"User {telegram_id} has no external_id, cannot fetch tickets")
            # Try to get customer data first
            from services.user_service import sync_user_data_from_api
            await sync_user_data_from_api(session, telegram_id, api_client)
            
            # Refresh user
            await session.refresh(user)
            if not user.external_id:
                logger.error(f"Still no external_id for user {telegram_id}")
                return []
        
        customer_id = int(user.external_id)
        logger.info(f"Fetching tickets for customer {customer_id}")
        
        # Get tickets from API
        api_tickets = await api_client.get_customer_tickets(customer_id, draw_id)
        
        if api_tickets is None:
            logger.error(f"Failed to fetch tickets from API for customer {customer_id}")
            return []
        
        if not api_tickets:
            logger.info(f"No tickets found for customer {customer_id}")
            return []
        
        # Sync tickets to database
        logger.info(f"Syncing {len(api_tickets)} tickets to database")
        synced_tickets = await sync_user_tickets_from_api(
            session, user.id, customer_id, api_tickets
        )
        
        logger.info(f"Successfully synced {len(synced_tickets)} tickets for user {telegram_id}")
        return synced_tickets
    
    except Exception as e:
        logger.error(f"Error syncing tickets for user {telegram_id}: {e}", exc_info=True)
        return []


async def get_user_tickets_with_sync(
    session: AsyncSession,
    telegram_id: int,
    api_client: LotteryAPIClient,
    draw_id: int = None,
    force_sync: bool = True
) -> list:
    """
    Get user's tickets with optional sync from API.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        api_client: API client instance
        draw_id: Optional draw ID to filter tickets
        force_sync: If True, sync from API first
    
    Returns:
        List of tickets
    """
    # Sync from API if requested
    if force_sync:
        await sync_tickets_for_user(session, telegram_id, api_client, draw_id)
    
    # Get user from database
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return []
    
    # Get tickets from database
    tickets = await get_user_tickets(session, user.id, draw_id)
    return tickets
