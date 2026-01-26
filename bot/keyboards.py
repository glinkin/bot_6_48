"""Keyboard layouts for the bot."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with phone number request button."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться номером телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎫 Мои билеты")],
            [KeyboardButton(text="🎯 Выбрать числа")],
            [KeyboardButton(text="🏆 Результаты розыгрыша")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_ticket_selection_keyboard(tickets) -> InlineKeyboardMarkup:
    """Get keyboard for selecting which ticket to assign numbers to."""
    buttons = []
    for ticket in tickets:
        buttons.append([InlineKeyboardButton(
            text=f"Билет #{ticket.id}",
            callback_data=f"ticket_{ticket.id}"
        )])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_selection")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_number_selection_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for number selection method."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Случайные числа", callback_data="auto_numbers")],
            [InlineKeyboardButton(text="✏️ Выбрать самому", callback_data="manual_numbers")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_selection")]
        ]
    )
    return keyboard


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with cancel button."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_selection")]
        ]
    )
    return keyboard


# Remove keyboard
remove_keyboard = ReplyKeyboardRemove()
