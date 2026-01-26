"""Handler for managing ticket numbers (not creating tickets)."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot import messages, keyboards
from db.crud import get_user_by_telegram_id, get_user_tickets_for_draw, update_ticket_numbers, get_ticket_by_id
from services.draw_service import get_current_draw_id, generate_random_numbers, validate_numbers, parse_numbers_from_text

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
    
    # Get user's tickets for current draw
    current_draw = get_current_draw_id()
    tickets = await get_user_tickets_for_draw(session, user.id, current_draw)
    
    if not tickets:
        await message.answer(
            "❌ У вас нет билетов на текущий розыгрыш!\n\n"
            "Билеты начисляются за участие в маркетинговых акциях.",
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    # Filter tickets without numbers
    tickets_without_numbers = [t for t in tickets if t.numbers is None]
    
    if not tickets_without_numbers:
        await message.answer(
            "✅ Для всех билетов уже выбраны числа!",
            reply_markup=keyboards.get_main_keyboard()
        )
        return
    
    # If only one ticket without numbers, select it directly
    if len(tickets_without_numbers) == 1:
        await state.set_state(NumberSelection.choosing_method)
        await state.update_data(ticket_id=tickets_without_numbers[0].id)
        await message.answer(
            f"🎯 Выбор чисел для билета #{tickets_without_numbers[0].id}\n\n"
            "Выберите способ:",
            reply_markup=keyboards.get_number_selection_keyboard()
        )
        return
    
    # Show list of tickets to choose from
    await state.set_state(NumberSelection.selecting_ticket)
    await message.answer(
        f"У вас {len(tickets_without_numbers)} билетов без чисел.\n"
        "Выберите билет для назначения чисел:",
        reply_markup=keyboards.get_ticket_selection_keyboard(tickets_without_numbers)
    )


@router.callback_query(F.data.startswith("ticket_"), NumberSelection.selecting_ticket)
async def ticket_selected(callback: CallbackQuery, state: FSMContext):
    """Handle ticket selection."""
    await callback.answer()
    
    ticket_id = int(callback.data.split("_")[1])
    
    await state.set_state(NumberSelection.choosing_method)
    await state.update_data(ticket_id=ticket_id)
    
    await callback.message.edit_text(
        f"🎯 Выбор чисел для билета #{ticket_id}\n\n"
        "Выберите способ:",
        reply_markup=keyboards.get_number_selection_keyboard()
    )


@router.callback_query(F.data == "auto_numbers", NumberSelection.choosing_method)
async def auto_generate_numbers(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Auto-generate random numbers for ticket."""
    await callback.answer()
    
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    
    numbers = generate_random_numbers()
    
    # Update ticket with auto-generated numbers
    await update_ticket_numbers(session, ticket_id, numbers)
    
    await state.clear()
    await callback.message.edit_text(
        messages.NUMBERS_ASSIGNED_TEMPLATE.format(
            numbers=messages.format_numbers(numbers)
        ),
        reply_markup=None
    )
    await callback.message.answer(
        "✅ Числа успешно назначены!",
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
    
    # Update ticket with user numbers
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    
    await update_ticket_numbers(session, ticket_id, sorted(numbers))
    
    await state.clear()
    await message.answer(
        messages.NUMBERS_ASSIGNED_TEMPLATE.format(
            numbers=messages.format_numbers(sorted(numbers))
        ),
        reply_markup=keyboards.get_main_keyboard()
    )


@router.callback_query(F.data == "cancel_selection")
async def cancel_selection(callback: CallbackQuery, state: FSMContext):
    """Cancel number selection."""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "❌ Выбор чисел отменён.\n\n"
        "Числа будут автоматически сгенерированы при старте розыгрыша.",
        reply_markup=None
    )
    await callback.message.answer(
        "Главное меню",
        reply_markup=keyboards.get_main_keyboard()
    )
