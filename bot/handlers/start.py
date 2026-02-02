"""Handler for /start command and phone number registration."""
import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from bot import messages, keyboards
from services.user_service import register_user, get_user_phone_number, sync_user_data_from_api
from api.client import api_client

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command."""
    telegram_id = message.from_user.id
    
    logger.info(f"User {telegram_id} started the bot")
    
    # Check if user already registered
    phone = await get_user_phone_number(session, telegram_id)
    
    if phone:
        logger.info(f"User {telegram_id} already registered with phone: {phone}")
        
        # Sync user data from API to ensure it's up to date
        logger.info(f"Syncing user data from API for {telegram_id}")
        sync_success = await sync_user_data_from_api(session, telegram_id, api_client)
        
        if sync_success:
            logger.info(f"User data synced successfully for {telegram_id}")
        else:
            logger.warning(f"Failed to sync user data for {telegram_id}, but user is registered")
        
        # User already registered, show welcome and main menu
        await message.answer(
            messages.WELCOME_MESSAGE,
            reply_markup=keyboards.get_main_keyboard()
        )
    else:
        logger.info(f"User {telegram_id} not registered, requesting phone number")
        # Request phone number
        await message.answer(
            messages.WELCOME_MESSAGE,
            reply_markup=keyboards.get_phone_keyboard()
        )


@router.message(lambda message: message.content_type == ContentType.CONTACT)
async def handle_contact(message: Message, session: AsyncSession):
    """Handle phone number sharing."""
    telegram_id = message.from_user.id
    contact = message.contact
    
    logger.info(f"Contact received from user {telegram_id}")
    
    # Verify that user shared their own number
    if contact.user_id != telegram_id:
        logger.warning(f"User {telegram_id} tried to share someone else's number")
        await message.answer(
            "❌ Пожалуйста, поделитесь СВОИМ номером телефона.",
            reply_markup=keyboards.get_phone_keyboard()
        )
        return
    
    phone = contact.phone_number
    logger.info(f"Processing registration for user {telegram_id}, phone: {phone}")
    
    # Register user
    success = await register_user(session, telegram_id, phone)
    
    if success:
        logger.info(f"User {telegram_id} registered successfully")
        
        # Sync user data from API
        logger.info(f"Starting API sync for user {telegram_id}")
        sync_success = await sync_user_data_from_api(session, telegram_id, api_client)
        
        if sync_success:
            logger.info(f"API sync completed successfully for user {telegram_id}")
        else:
            logger.warning(f"API sync failed for user {telegram_id}, but registration is OK")
        
        await message.answer(
            messages.PHONE_REGISTRATION_SUCCESS,
            reply_markup=keyboards.get_main_keyboard()
        )
    else:
        logger.error(f"User {telegram_id} registration failed")
        await message.answer(
            messages.PHONE_REGISTRATION_ERROR,
            reply_markup=keyboards.get_phone_keyboard()
        )


async def show_user_ticket(message: Message, phone: str):
    """Display user's current ticket status."""
    # Get ticket from API
    ticket = await api_client.get_ticket_by_phone(phone)
    
    if not ticket:
        await message.answer(
            messages.NO_TICKET_MESSAGE,
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    # Format ticket information
    numbers = ticket.get("numbers", [])
    draw_date = ticket.get("draw_date", "Скоро")
    status = ticket.get("status", "pending")
    
    formatted_numbers = messages.format_numbers(numbers)
    
    if status == "issued" or status == "pending":
        await message.answer(
            messages.TICKET_ISSUED_TEMPLATE.format(
                numbers=formatted_numbers,
                draw_date=draw_date
            ),
            reply_markup=keyboards.get_main_keyboard()
        )
