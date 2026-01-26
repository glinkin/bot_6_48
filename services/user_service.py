"""User registration and phone number handling."""
import re
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud import get_user_by_telegram_id, create_user, get_user_phone


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
