"""Handler for /start command and phone number registration."""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from bot import messages, keyboards
from services.user_service import register_user, get_user_phone_number
from api.client import api_client

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command."""
    telegram_id = message.from_user.id
    
    # Check if user already registered
    phone = await get_user_phone_number(session, telegram_id)
    
    if phone:
        # User already registered, show welcome and main menu
        await message.answer(
            messages.WELCOME_MESSAGE,
            reply_markup=keyboards.get_main_keyboard()
        )
    else:
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
    
    # Verify that user shared their own number
    if contact.user_id != telegram_id:
        await message.answer(
            "❌ Пожалуйста, поделитесь СВОИМ номером телефона.",
            reply_markup=keyboards.get_phone_keyboard()
        )
        return
    
    phone = contact.phone_number
    
    # Register user
    success = await register_user(session, telegram_id, phone)
    
    if success:
        await message.answer(
            messages.PHONE_REGISTRATION_SUCCESS,
            reply_markup=keyboards.get_main_keyboard()
        )
    else:
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
