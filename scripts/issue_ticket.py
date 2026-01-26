"""Script to issue ticket to user (simulates external marketing system)."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from db.database import async_session_maker
from db.crud import get_user_by_phone, create_ticket
from services.draw_service import get_current_draw_id


async def issue_ticket(phone: str):
    """Issue ticket to user by phone number."""
    draw_id = get_current_draw_id()
    
    async with async_session_maker() as session:
        # Find user by phone
        user = await get_user_by_phone(session, phone)
        
        if not user:
            print(f"❌ User with phone {phone} not found!")
            print("   User must register in bot first (/start)")
            return
        
        # Create ticket without numbers (user will select later)
        ticket = await create_ticket(session, user.id, draw_id, numbers=None)
        
        print(f"✅ Ticket issued successfully!")
        print(f"   User: {user.phone}")
        print(f"   Ticket ID: {ticket.id}")
        print(f"   Draw: {draw_id}")
        print(f"   Numbers: Not assigned yet (user will select)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python issue_ticket.py <phone_number>")
        print("Example: python issue_ticket.py 79652223633")
        sys.exit(1)
    
    phone = sys.argv[1]
    asyncio.run(issue_ticket(phone))
