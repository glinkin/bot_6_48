"""Handler for managing ticket numbers (not creating tickets)."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot import messages, keyboards
from db.crud import get_user_by_telegram_id
from services.draw_service import generate_random_numbers, validate_numbers, parse_numbers_from_text
from services.user_service import sync_user_data_from_api
from api.client import api_client
from db.crud_tickets import sync_user_tickets_from_api
from db.crud_draws import get_current_draw

logger = logging.getLogger(__name__)
router = Router()


class NumberSelection(StatesGroup):
    """States for number selection."""
    selecting_ticket = State()
    choosing_method = State()
    entering_numbers = State()


@router.message(Command("select_numbers"))
@router.message(F.text == "🎯 Выбрать числа")
async def select_ticket_numbers(message: Message, session: AsyncSession, state: FSMContext):
    """Select numbers for existing ticket."""
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id(session, telegram_id)
    
    if not user:
        await message.answer(
            messages.REQUEST_PHONE_MESSAGE,
            reply_markup=keyboards.get_phone_keyboard()
        )
        return
    
    # Check if user is linked to external customer
    if not user.external_id:
        await message.answer(
            "❌ Ваш аккаунт не связан с системой акции.\n\n"
            "Пожалуйста, используйте /start для регистрации.",
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    # Get customer tickets from API
    try:
        customer_id = int(user.external_id)
        tickets = await api_client.get_customer_tickets(customer_id)
        
        if tickets is None:
            await message.answer(
                "❌ Не удалось получить данные о ваучерах.\n"
                "Попробуйте позже.",
                reply_markup=keyboards.get_main_keyboard()
            )
            return
        
        # Check available_tickets count
        available_count = user.available_tickets or 0
        
        if available_count == 0:
            await message.answer(
                "❌ У вас нет доступных ваучеров для заполнения!\n\n"
                "Ваучеры начисляются за участие в маркетинговых акциях Termoland.",
                reply_markup=keyboards.get_main_keyboard()
            )
            return
        
        # If no existing tickets but have available_tickets, API will create on fill
        # Show number selection (API auto-creates and fills ticket)
        await state.set_state(NumberSelection.choosing_method)
        await state.update_data(customer_id=customer_id)
        await message.answer(
            f"🎯 У вас {available_count} доступных ваучеров для заполнения\n\n"
            "Выберите способ заполнения:",
            reply_markup=keyboards.get_number_selection_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error getting tickets for user {telegram_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при получении ваучеров.",
            reply_markup=keyboards.get_main_keyboard()
        )


@router.callback_query(F.data.startswith("ticket_"), NumberSelection.selecting_ticket)
async def ticket_selected(callback: CallbackQuery, state: FSMContext):
    """Handle ticket selection."""
    await callback.answer()
    
    ticket_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    customer_id = data.get("customer_id")
    
    await state.set_state(NumberSelection.choosing_method)
    await state.update_data(ticket_id=ticket_id, customer_id=customer_id)
    
    await callback.message.edit_text(
        f"🎯 Выбор чисел для ваучера #{ticket_id}\n\n"
        "Выберите способ:",
        reply_markup=keyboards.get_number_selection_keyboard()
    )


@router.callback_query(F.data == "auto_numbers", NumberSelection.choosing_method)
async def auto_generate_numbers(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Auto-generate random numbers for ticket."""
    await callback.answer()
    
    data = await state.get_data()
    customer_id = data.get("customer_id")
    
    # Get current draw
    current_draw = await get_current_draw(session)
    if not current_draw:
        await state.clear()
        await callback.message.edit_text(
            "❌ Нет активной акции.",
            reply_markup=None
        )
        await callback.message.answer(
            "Попробуйте позже.",
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    draw_id = int(current_draw.external_id)
    
    # Generate random numbers
    numbers = generate_random_numbers()
    
    # Fill ticket via API (API auto-selects first unfilled ticket)
    try:
        filled_ticket = await api_client.fill_ticket(customer_id, draw_id, numbers)
        
        if filled_ticket:
            # Update available_tickets count
            telegram_id = callback.from_user.id
            user = await get_user_by_telegram_id(session, telegram_id)
            if user:
                # Decrease available tickets count
                if user.available_tickets and user.available_tickets > 0:
                    user.available_tickets -= 1
                    session.add(user)
                    await session.commit()
                
                # Sync filled ticket to local database
                await sync_user_tickets_from_api(
                    session,
                    user.id,
                    customer_id,
                    [filled_ticket]  # Sync only this filled ticket
                )
            
            await state.clear()
            await callback.message.edit_text(
                messages.NUMBERS_ASSIGNED_TEMPLATE.format(
                    numbers=messages.format_numbers(numbers)
                ),
                reply_markup=None
            )
            
            # Check if user has more unfilled tickets
            remaining_tickets = user.available_tickets if user and user.available_tickets else 0
            
            if remaining_tickets > 0:
                await callback.message.answer(
                    f"✅ Числа успешно назначены!\n\n📝 У вас осталось <b>{remaining_tickets}</b> незаполненных ваучеров.\n💡 Хотите заполнить еще?",
                    reply_markup=keyboards.get_fill_another_keyboard()
                )
            else:
                await callback.message.answer(
                    "✅ Числа успешно назначены!",
                    reply_markup=keyboards.get_main_keyboard()
                )
        else:
            await state.clear()
            await callback.message.edit_text(
                "❌ Не удалось назначить числа для ваучера.\n"
                "Возможно, все ваучеры уже заполнены.",
                reply_markup=None
            )
            await callback.message.answer(
                "Попробуйте ещё раз или обратитесь в поддержку.",
                reply_markup=keyboards.get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Error filling ticket for customer {customer_id}: {e}", exc_info=True)
        await state.clear()
        await callback.message.edit_text(
            "❌ Произошла ошибка при назначении чисел.",
            reply_markup=None
        )
        await callback.message.answer(
            "Попробуйте позже.",
            reply_markup=keyboards.get_main_keyboard()
        )


@router.callback_query(F.data == "manual_numbers", NumberSelection.choosing_method)
async def enter_manual_numbers(callback: CallbackQuery, state: FSMContext):
    """Start manual number entry."""
    await callback.answer()
    await state.set_state(NumberSelection.entering_numbers)
    await callback.message.edit_text(
        messages.ENTER_NUMBERS_PROMPT,
        reply_markup=keyboards.get_cancel_keyboard()
    )


@router.message(NumberSelection.entering_numbers)
async def process_manual_numbers(message: Message, session: AsyncSession, state: FSMContext):
    """Process manually entered numbers."""
    numbers = parse_numbers_from_text(message.text)
    
    if numbers is None:
        await message.answer(
            "❌ Не удалось распознать числа. Попробуйте еще раз.\n"
            "Пример: 1 5 12 23 34 45"
        )
        return
    
    is_valid, error = validate_numbers(numbers)
    if not is_valid:
        await message.answer(f"❌ {error}\nПопробуйте еще раз.")
        return
    
    # Sort numbers for consistency
    sorted_numbers = sorted(numbers)
    
    # Get current draw
    current_draw = await get_current_draw(session)
    if not current_draw:
        await state.clear()
        await message.answer(
            "❌ Нет активной акции.\n"
            "Попробуйте позже.",
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    draw_id = int(current_draw.external_id)
    
    # Fill ticket via API (API auto-selects first unfilled ticket)
    data = await state.get_data()
    customer_id = data.get("customer_id")
    
    try:
        filled_ticket = await api_client.fill_ticket(customer_id, draw_id, sorted_numbers)
        
        if filled_ticket:
            # Update available_tickets count
            telegram_id = message.from_user.id
            user = await get_user_by_telegram_id(session, telegram_id)
            if user:
                # Decrease available tickets count
                if user.available_tickets and user.available_tickets > 0:
                    user.available_tickets -= 1
                    session.add(user)
                    await session.commit()
                
                # Sync filled ticket to local database
                await sync_user_tickets_from_api(
                    session,
                    user.id,
                    customer_id,
                    [filled_ticket]  # Sync only this filled ticket
                )
            
            await state.clear()
            await message.answer(
                messages.NUMBERS_ASSIGNED_TEMPLATE.format(
                    numbers=messages.format_numbers(sorted_numbers)
                ),
                reply_markup=keyboards.get_main_keyboard()
            )
        else:
            await state.clear()
            await message.answer(
                "❌ Не удалось назначить числа для ваучера.\n"
                "Возможно, все ваучеры уже заполнены.",
                reply_markup=keyboards.get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Error filling ticket for customer {customer_id} with manual numbers: {e}", exc_info=True)
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при назначении чисел.\n"
            "Попробуйте позже.",
            reply_markup=keyboards.get_main_keyboard()
        )


@router.callback_query(F.data == "cancel_selection")
async def cancel_selection(callback: CallbackQuery, state: FSMContext):
    """Cancel number selection."""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "❌ Выбор чисел отменён.\n\n"
        "Числа будут автоматически сгенерированы при старте акции.",
        reply_markup=None
    )
    await callback.message.answer(
        "Главное меню",
        reply_markup=keyboards.get_main_keyboard()
    )


@router.callback_query(F.data == "fill_another_ticket")
async def fill_another_ticket(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Handle request to fill another ticket."""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    user = await get_user_by_telegram_id(session, telegram_id)
    
    if not user:
        await callback.message.edit_text(
            messages.REQUEST_PHONE_MESSAGE,
            reply_markup=keyboards.get_phone_keyboard()
        )
        return
    
    # Sync user data from API to get latest available_tickets count
    await sync_user_data_from_api(session, telegram_id, api_client)
    
    # Refresh user object to get updated data
    user = await get_user_by_telegram_id(session, telegram_id)
    
    # Check if user is linked to external customer
    if not user.external_id:
        await callback.message.edit_text(
            "❌ Ваш аккаунт не связан с системой акции.\n\n"
            "Пожалуйста, используйте /start для регистрации.",
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    # Get customer tickets from API
    try:
        customer_id = int(user.external_id)
        
        # Check available_tickets count
        available_count = user.available_tickets or 0
        
        if available_count == 0:
            await callback.message.edit_text(
                "❌ У вас не осталось доступных ваучеров для заполнения!",
                reply_markup=None
            )
            await callback.message.answer(
                "Ваучеры начисляются за участие в маркетинговых акциях Termoland.",
                reply_markup=keyboards.get_main_keyboard()
            )
            return
        
        # Show number selection
        await state.set_state(NumberSelection.choosing_method)
        await state.update_data(customer_id=customer_id)
        await callback.message.edit_text(
            f"🎯 У вас {available_count} доступных ваучеров для заполнения\n\n"
            "Выберите способ заполнения:",
            reply_markup=keyboards.get_number_selection_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error getting tickets for user {telegram_id}: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка при получении ваучеров.",
            reply_markup=None
        )
        await callback.message.answer(
            "Попробуйте позже.",
            reply_markup=keyboards.get_main_keyboard()
        )


@router.callback_query(F.data == "show_my_tickets")
async def show_my_tickets_callback(callback: CallbackQuery, session: AsyncSession):
    """Handle show my tickets callback."""
    await callback.answer()
    await callback.message.delete()
    
    # Import here to avoid circular dependency
    from bot.handlers.ticket import show_my_tickets
    
    # Reuse the handler
    await show_my_tickets(callback.message, session)
