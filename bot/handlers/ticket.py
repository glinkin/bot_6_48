"""Handler for ticket status and results display."""
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot import messages, keyboards
from services.user_service import get_user_phone_number, sync_user_data_from_api
from services.ticket_checker import check_ticket_result
from services.draw_service import get_current_draw_id
from services.ticket_sync import get_user_tickets_with_sync
from db.crud import get_user_by_telegram_id
from db.crud_draws import get_current_draw
from api.client import api_client

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🎫 Мои ваучеры")
async def show_my_tickets(message: Message, session: AsyncSession):
    """Show user's current tickets with sync from API."""
    telegram_id = message.from_user.id
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
    
    logger.info(f"User found: {user.phone}, available_tickets: {user.available_tickets}")
    
    # Show loading message
    loading_msg = await message.answer("⏳ Загрузка ваучеров...")
    
    # Sync user data from API to get latest available_tickets count
    await sync_user_data_from_api(session, telegram_id, api_client)
    
    # Refresh user object to get updated data
    user = await get_user_by_telegram_id(session, telegram_id)
    logger.info(f"After sync: available_tickets={user.available_tickets}, external_id={user.external_id}")
    
    # Get current draw
    current_draw_obj = await get_current_draw(session)
    current_draw_id = current_draw_obj.external_id if current_draw_obj else None
    
    # Sync and get filled tickets from API (only if user has external_id)
    filled_tickets = []
    if user.external_id:
        filled_tickets = await get_user_tickets_with_sync(
            session, 
            telegram_id, 
            api_client,
            draw_id=current_draw_id,
            force_sync=True
        )
    else:
        logger.warning(f"User {telegram_id} has no external_id, skipping ticket sync")
    
    # Delete loading message
    await loading_msg.delete()
    
    # Count available (unfilled) tickets
    available_count = user.available_tickets or 0
    filled_count = len(filled_tickets)
    total_count = available_count + filled_count
    
    if total_count == 0:
        logger.info(f"No tickets (filled or available) for user {telegram_id}")
        await message.answer(
            messages.NO_TICKET_MESSAGE,
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    logger.info(f"User {telegram_id}: {filled_count} filled, {available_count} available tickets")
    
    # Format tickets display
    draw_name = current_draw_obj.name if current_draw_obj else "текущая акция"
    response = f"🎫 <b>Ваши ваучеры</b>\n"
    response += f"📋 {draw_name}\n"
    response += f"Всего ваучеров: <b>{total_count}</b>\n\n"
    
    # Show filled tickets
    if filled_tickets:
        response += f"<b>✅ Заполненные ваучеры ({filled_count}):</b>\n\n"
        for idx, ticket in enumerate(filled_tickets, 1):
            response += f"<b>Ваучер #{idx}</b>\n"
            
            if ticket.numbers:
                response += f"   🎯 Числа: {messages.format_numbers(ticket.numbers)}\n"
                
                if ticket.is_winner:
                    response += f"   🏆 <b>ВЫИГРЫШ: {int(ticket.prize_amount)} руб!</b>\n"
                    response += f"   ✅ Совпадений: {ticket.matched_count}\n"
                elif current_draw_obj and current_draw_obj.status == "completed":
                    response += f"   😔 Совпадений: {ticket.matched_count}\n"
            
            response += "\n"
    
    # Show available (unfilled) tickets
    if available_count > 0:
        response += f"<b>📝 Доступно для заполнения: {available_count}</b>\n"
        response += f"💡 Выберите числа для своих ваучеров через раздел '🎯 Выбрать числа'\n\n"
    
    # Show winning info if any
    winners = [t for t in filled_tickets if t.is_winner]
    if winners:
        total_prize = sum(t.prize_amount for t in winners)
        response += f"\n💰 <b>Общий выигрыш: {int(total_prize)} руб!</b>\n"
    
    await message.answer(
        response,
        reply_markup=keyboards.get_main_keyboard()
    )


@router.message(F.text == "🏆 Результаты акции")
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


@router.message(F.text == "❓ Частые вопросы")
async def show_faq(message: Message):
    """Show frequently asked questions."""
    await message.answer(
        messages.FAQ_MESSAGE,
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
