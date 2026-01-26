"""CRUD operations for database models."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User, Ticket
from typing import List


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Get user by Telegram ID."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    """Get user by phone number."""
    result = await session.execute(
        select(User).where(User.phone == phone)
    )
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, telegram_id: int, phone: str) -> User:
    """Create new user with Telegram ID and phone number mapping."""
    user = User(telegram_id=telegram_id, phone=phone)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_phone(session: AsyncSession, telegram_id: int) -> str | None:
    """Get phone number for a Telegram ID."""
    result = await session.execute(
        select(User.phone).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


# Ticket CRUD operations

async def create_ticket(
    session: AsyncSession, 
    user_id: int, 
    draw_id: str, 
    numbers: List[int] | None = None
) -> Ticket:
    """Create new ticket for user."""
    ticket = Ticket(user_id=user_id, draw_id=draw_id, numbers=numbers)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def get_user_ticket_for_draw(
    session: AsyncSession, 
    user_id: int, 
    draw_id: str
) -> Ticket | None:
    """Get user's ticket for specific draw."""
    result = await session.execute(
        select(Ticket).where(
            Ticket.user_id == user_id,
            Ticket.draw_id == draw_id
        )
    )
    return result.scalar_one_or_none()


async def get_user_tickets_for_draw(
    session: AsyncSession, 
    user_id: int, 
    draw_id: str
) -> List[Ticket]:
    """Get all user's tickets for specific draw."""
    result = await session.execute(
        select(Ticket).where(
            Ticket.user_id == user_id,
            Ticket.draw_id == draw_id
        ).order_by(Ticket.created_at)
    )
    return list(result.scalars().all())


async def get_ticket_by_id(session: AsyncSession, ticket_id: int) -> Ticket | None:
    """Get ticket by ID."""
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def update_ticket_numbers(
    session: AsyncSession, 
    ticket_id: int, 
    numbers: List[int]
) -> Ticket:
    """Update ticket numbers."""
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one()
    ticket.numbers = numbers
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def get_tickets_without_numbers(
    session: AsyncSession, 
    draw_id: str
) -> List[Ticket]:
    """Get all tickets without numbers for a draw (for auto-generation)."""
    result = await session.execute(
        select(Ticket).where(
            Ticket.draw_id == draw_id,
            Ticket.numbers.is_(None)
        )
    )
    return list(result.scalars().all())
