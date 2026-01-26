"""Script to auto-generate numbers for tickets without numbers at draw start."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from db.database import async_session_maker
from db.crud import get_tickets_without_numbers, update_ticket_numbers
from services.draw_service import generate_random_numbers, get_current_draw_id


async def auto_generate_missing_numbers():
    """Generate numbers for all tickets that don't have numbers yet."""
    draw_id = get_current_draw_id()
    
    async with async_session_maker() as session:
        # Get tickets without numbers
        tickets = await get_tickets_without_numbers(session, draw_id)
        
        if not tickets:
            print(f"✅ No tickets without numbers for draw {draw_id}")
            return
        
        print(f"🎲 Generating numbers for {len(tickets)} tickets...")
        
        for ticket in tickets:
            numbers = generate_random_numbers()
            await update_ticket_numbers(session, ticket.id, numbers)
            print(f"   Ticket #{ticket.id}: {numbers}")
        
        print(f"✅ Successfully generated numbers for {len(tickets)} tickets!")


if __name__ == "__main__":
    asyncio.run(auto_generate_missing_numbers())
