"""Handler for ticket status and results display."""
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot import messages, keyboards
from services.user_service import get_user_phone_number
from services.ticket_checker import check_ticket_result
from services.draw_service import get_current_draw_id
from db.crud import get_user_by_telegram_id, get_user_tickets_for_draw
from api.client import api_client

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🎫 Мои билеты")
async def show_my_tickets(message: Message, session: AsyncSession):
    """Show user's current tickets."""
    telegram_id = message.from_user.id
    logger.info(f"=== show_my_tickets handler triggered ===")
    logger.info(f"Message text: '{message.text}'")
    logger.info(f"User {telegram_id} requested tickets")
    
    # Get user
    user = await get_user_by_telegram_id(session, telegram_id)
    
    if not user:
        logger.warning(f"User {telegram_id} not found in database")
        await message.answer(
            messages.REQUEST_PHONE_MESSAGE,
            reply_markup=keyboards.get_phone_keyboard()
        )
        return
    
    logger.info(f"User found: {user.phone}")
    
    # Get user's tickets for current draw
    current_draw = get_current_draw_id()
    tickets = await get_user_tickets_for_draw(session, user.id, current_draw)
    
    if not tickets:
        logger.info(f"No tickets found for user {user.id} in draw {current_draw}")
        await message.answer(
            messages.NO_TICKET_MESSAGE,
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    logger.info(f"Found {len(tickets)} tickets for user {user.id}")
    
    # Format tickets display
    response = f"🎫 Ваши билеты на розыгрыш {current_draw}\n"
    response += f"Всего билетов: {len(tickets)}\n\n"
    
    for idx, ticket in enumerate(tickets, 1):
        response += f"Билет #{idx} (ID: {ticket.id})\n"
        if ticket.numbers is None:
            response += "   ❗️ Числа не выбраны\n"
        else:
            response += f"   🎯 Числа: {messages.format_numbers(ticket.numbers)}\n"
        response += "\n"
    
    if any(t.numbers is None for t in tickets):
        response += "💡 Используйте '🎯 Выбрать числа' для назначения чисел билетам"
    
    await message.answer(
        response,
        reply_markup=keyboards.get_main_keyboard()
    )


@router.message(F.text == "🏆 Результаты розыгрыша")
async def show_draw_results(message: Message, session: AsyncSession):
    """Show current draw results and user's ticket status."""
    telegram_id = message.from_user.id
    
    # Get user's phone
    phone = await get_user_phone_number(session, telegram_id)
    
    if not phone:
        await message.answer(
            messages.REQUEST_PHONE_MESSAGE,
            reply_markup=keyboards.get_phone_keyboard()
        )
        return
    
    # Get current draw
    draw = await api_client.get_current_draw()
    
    if not draw or not draw.get("winning_numbers"):
        await message.answer(
            "⏳ Розыгрыш еще не проведен.",
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    # Get user's ticket
    ticket = await api_client.get_ticket_by_phone(phone)
    
    if not ticket:
        await message.answer(
            messages.NO_TICKET_MESSAGE,
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    # Calculate results
    user_numbers = ticket.get("numbers", [])
    winning_numbers = draw.get("winning_numbers", [])
    
    matches, prize = check_ticket_result(user_numbers, winning_numbers)
    
    # Display result
    if matches >= 3:
        await message.answer(
            messages.TICKET_WON_TEMPLATE.format(
                user_numbers=messages.format_numbers(user_numbers),
                winning_numbers=messages.format_numbers(winning_numbers),
                matches=matches,
                prize=prize
            ),
            reply_markup=keyboards.get_main_keyboard()
        )
    else:
        await message.answer(
            messages.TICKET_LOST_TEMPLATE.format(
                user_numbers=messages.format_numbers(user_numbers),
                winning_numbers=messages.format_numbers(winning_numbers),
                matches=matches
            ),
            reply_markup=keyboards.get_main_keyboard()
        )


async def display_ticket(message: Message, ticket: dict):
    """Display ticket information based on its status."""
    numbers = ticket.get("numbers", [])
    draw_date = ticket.get("draw_date", "Скоро")
    status = ticket.get("status", "pending")
    
    formatted_numbers = messages.format_numbers(numbers)
    
    if status in ["issued", "pending"]:
        await message.answer(
            messages.TICKET_PENDING_TEMPLATE.format(
                numbers=formatted_numbers,
                draw_date=draw_date
            ),
            reply_markup=keyboards.get_main_keyboard()
        )
    elif status == "won":
        winning_numbers = ticket.get("winning_numbers", [])
        matches = ticket.get("matches", 0)
        prize = ticket.get("prize", 0)
        
        await message.answer(
            messages.TICKET_WON_TEMPLATE.format(
                user_numbers=formatted_numbers,
                winning_numbers=messages.format_numbers(winning_numbers),
                matches=matches,
                prize=prize
            ),
            reply_markup=keyboards.get_main_keyboard()
        )
    elif status == "lost":
        winning_numbers = ticket.get("winning_numbers", [])
        matches = ticket.get("matches", 0)
        
        await message.answer(
            messages.TICKET_LOST_TEMPLATE.format(
                user_numbers=formatted_numbers,
                winning_numbers=messages.format_numbers(winning_numbers),
                matches=matches
            ),
            reply_markup=keyboards.get_main_keyboard()
        )


@router.message(F.text)
async def debug_text_handler(message: Message):
    """Debug handler to log all text messages."""
    logger.info(f"=== DEBUG: Text message received ===")
    logger.info(f"Text: '{message.text}'")
    logger.info(f"Text repr: {repr(message.text)}")
    logger.info(f"Text bytes: {message.text.encode('utf-8').hex()}")
    logger.info(f"User: {message.from_user.id}")
