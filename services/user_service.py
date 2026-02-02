"""User registration and phone number handling."""
import re
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud import get_user_by_telegram_id, create_user, get_user_phone

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to consistent format.
    Removes all non-digit characters.
    
    Args:
        phone: Raw phone number string
    
    Returns:
        Normalized phone number (digits only)
    """
    return re.sub(r'\D', '', phone)


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number string
    
    Returns:
        True if valid, False otherwise
    """
    normalized = normalize_phone(phone)
    # Basic validation: should have 10-15 digits
    return 10 <= len(normalized) <= 15


async def register_user(session: AsyncSession, telegram_id: int, phone: str) -> bool:
    """
    Register new user with phone number.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        phone: User's phone number
    
    Returns:
        True if registration successful, False if invalid phone
    """
    if not validate_phone(phone):
        return False
    
    normalized_phone = normalize_phone(phone)
    
    # Check if user already exists
    existing_user = await get_user_by_telegram_id(session, telegram_id)
    if existing_user:
        return True  # Already registered
    
    # Create new user
    await create_user(session, telegram_id, normalized_phone)
    return True


async def get_user_phone_number(session: AsyncSession, telegram_id: int) -> str | None:
    """
    Get phone number for Telegram user.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
    
    Returns:
        Phone number or None if not found
    """
    return await get_user_phone(session, telegram_id)


async def sync_user_data_from_api(
    session: AsyncSession,
    telegram_id: int,
    api_client
) -> bool:
    """
    Synchronize user data from external API to database.
    Fetches customer data by phone and updates user record.
    
    Args:
        session: Database session
        telegram_id: User's Telegram ID
        api_client: LotteryAPIClient instance
    
    Returns:
        True if sync successful, False otherwise
    """
    from db.crud import get_user_by_telegram_id, update_user_from_api_data
    
    logger.info(f"Starting user data sync for telegram_id: {telegram_id}")
    
    # Get user from database
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        logger.warning(f"User not found in DB for telegram_id: {telegram_id}")
        return False
    
    logger.info(f"User found in DB: phone={user.phone}")
    
    # Get customer data from API
    customer_data = await api_client.get_customer_by_phone(user.phone)
    if not customer_data:
        logger.warning(f"No customer data from API for phone: {user.phone}")
        return False
    
    logger.info(f"Customer data received from API, updating user...")
    
    # Update user with API data
    await update_user_from_api_data(session, user, customer_data)
    logger.info(f"User data synced successfully for telegram_id: {telegram_id}")
    return True
