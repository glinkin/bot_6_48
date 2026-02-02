"""CRUD operations for Ticket model with API sync."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Ticket
from typing import List, Optional
from datetime import datetime


async def get_ticket_by_external_id(session: AsyncSession, external_id: int) -> Optional[Ticket]:
    """Get ticket by external API ID."""
    result = await session.execute(
        select(Ticket).where(Ticket.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def get_user_tickets(session: AsyncSession, user_id: int, draw_id: int = None) -> List[Ticket]:
    """Get all tickets for a user, optionally filtered by draw."""
    query = select(Ticket).where(Ticket.user_id == user_id)
    if draw_id:
        query = query.where(Ticket.draw_id == draw_id)
    query = query.order_by(Ticket.created_at.desc())
    
    result = await session.execute(query)
    return list(result.scalars().all())


def parse_datetime_naive_ticket(date_str: str) -> Optional[datetime]:
    """Parse ISO datetime string and return naive datetime (no timezone)."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


async def create_or_update_ticket(
    session: AsyncSession,
    user_id: int,
    api_data: dict
) -> Ticket:
    """
    Create new ticket or update existing one with data from API.
    
    Args:
        session: Database session
        user_id: User ID in our database
        api_data: Ticket data from API
    
    Returns:
        Ticket object
    """
    external_id = api_data.get("id")
    
    # Check if ticket already exists
    ticket = await get_ticket_by_external_id(session, external_id)
    
    if ticket:
        # Update existing ticket
        ticket.customer_id = api_data.get("customer_id")
        ticket.draw_id = api_data.get("draw_id")
        ticket.numbers = api_data.get("numbers")
        ticket.is_winner = api_data.get("is_winner", False)
        ticket.matched_count = api_data.get("matched_count", 0)
        ticket.prize_amount = float(api_data.get("prize_amount", 0))
        ticket.filled_by = api_data.get("filled_by")
        
        # Parse filled_at
        ticket.filled_at = parse_datetime_naive_ticket(api_data.get("filled_at"))
        
        # Update status based on is_winner
        if api_data.get("is_winner"):
            ticket.status = "won"
        elif api_data.get("numbers"):
            ticket.status = "active"
        else:
            ticket.status = "pending"
        
        ticket.updated_at = datetime.utcnow()
    else:
        # Create new ticket
        ticket = Ticket(
            external_id=external_id,
            user_id=user_id,
            customer_id=api_data.get("customer_id"),
            draw_id=api_data.get("draw_id"),
            numbers=api_data.get("numbers"),
            is_winner=api_data.get("is_winner", False),
            matched_count=api_data.get("matched_count", 0),
            prize_amount=float(api_data.get("prize_amount", 0)),
            filled_by=api_data.get("filled_by"),
            status="active" if api_data.get("numbers") else "pending"
        )
        
        # Parse filled_at
        ticket.filled_at = parse_datetime_naive_ticket(api_data.get("filled_at"))
        
        # Update status based on is_winner
        if api_data.get("is_winner"):
            ticket.status = "won"
        
        session.add(ticket)
    
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def sync_user_tickets_from_api(
    session: AsyncSession,
    user_id: int,
    customer_id: int,
    api_tickets: list
) -> List[Ticket]:
    """
    Synchronize user's tickets from API data.
    
    Args:
        session: Database session
        user_id: User ID in our database
        customer_id: Customer ID from API
        api_tickets: List of ticket dicts from API
    
    Returns:
        List of synced Ticket objects
    """
    synced_tickets = []
    
    for api_ticket in api_tickets:
        ticket = await create_or_update_ticket(session, user_id, api_ticket)
        synced_tickets.append(ticket)
    
    return synced_tickets
