"""CRUD operations for Draw model."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Draw
from typing import Optional
import json
from datetime import datetime


def parse_datetime_naive(date_str: str) -> Optional[datetime]:
    """Parse ISO datetime string and return naive datetime (no timezone)."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.replace(tzinfo=None)  # Remove timezone for PostgreSQL
    except (ValueError, TypeError):
        return None


async def get_draw_by_external_id(session: AsyncSession, external_id: int) -> Optional[Draw]:
    """Get draw by external API ID."""
    result = await session.execute(
        select(Draw).where(Draw.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def get_current_draw(session: AsyncSession) -> Optional[Draw]:
    """Get the most recent active or pending draw."""
    result = await session.execute(
        select(Draw)
        .where(Draw.status.in_(['active', 'pending']))
        .order_by(Draw.scheduled_at.desc())
    )
    return result.scalar_one_or_none()


async def create_or_update_draw(session: AsyncSession, api_data: dict) -> Draw:
    """
    Create new draw or update existing one with data from API.
    
    Args:
        session: Database session
        api_data: Draw data from API
    
    Returns:
        Draw object
    """
    external_id = api_data.get("id")
    
    # Check if draw already exists
    draw = await get_draw_by_external_id(session, external_id)
    
    if draw:
        # Update existing draw
        draw.name = api_data.get("name")
        draw.status = api_data.get("status")
        draw.prize_pool = float(api_data.get("prize_pool", 0))
        draw.draw_type = api_data.get("type")
        draw.periodicity = api_data.get("periodicity")
        draw.numbers_to_pick = api_data.get("numbers_to_pick", 6)
        draw.numbers_total = api_data.get("numbers_total", 45)
        
        # Parse dates
        draw.scheduled_at = parse_datetime_naive(api_data.get("scheduled_at"))
        draw.executed_at = parse_datetime_naive(api_data.get("executed_at"))
        
        # Store complex fields as JSON
        if api_data.get("prize_grid"):
            draw.prize_grid = json.dumps(api_data["prize_grid"])
        
        if api_data.get("winning_numbers"):
            draw.winning_numbers = api_data["winning_numbers"]
        
        if api_data.get("statistics"):
            draw.statistics = json.dumps(api_data["statistics"])
        
        draw.updated_at = datetime.utcnow()
    else:
        # Create new draw
        draw = Draw(
            external_id=external_id,
            name=api_data.get("name"),
            status=api_data.get("status"),
            prize_pool=float(api_data.get("prize_pool", 0)),
            draw_type=api_data.get("type"),
            periodicity=api_data.get("periodicity"),
            numbers_to_pick=api_data.get("numbers_to_pick", 6),
            numbers_total=api_data.get("numbers_total", 45)
        )
        
        # Parse dates
        draw.scheduled_at = parse_datetime_naive(api_data.get("scheduled_at"))
        draw.executed_at = parse_datetime_naive(api_data.get("executed_at"))
        
        # Store complex fields as JSON
        if api_data.get("prize_grid"):
            draw.prize_grid = json.dumps(api_data["prize_grid"])
        
        if api_data.get("winning_numbers"):
            draw.winning_numbers = api_data["winning_numbers"]
        
        if api_data.get("statistics"):
            draw.statistics = json.dumps(api_data["statistics"])
        
        session.add(draw)
    
    await session.commit()
    await session.refresh(draw)
    return draw
