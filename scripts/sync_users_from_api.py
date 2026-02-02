"""Script to sync all users data from external API."""
import asyncio
from sqlalchemy import select
from db.database import async_session_maker
from db.models import User
from api.client import LotteryAPIClient
from db.crud import update_user_from_api_data


async def sync_all_users():
    """Sync all existing users with data from external API."""
    api_client = LotteryAPIClient()
    
    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users to sync")
        
        synced_count = 0
        failed_count = 0
        
        for user in users:
            try:
                print(f"Syncing user {user.telegram_id} (phone: {user.phone})...")
                
                # Get customer data from API
                customer_data = await api_client.get_customer_by_phone(user.phone)
                
                if customer_data:
                    # Update user with API data
                    await update_user_from_api_data(session, user, customer_data)
                    print(f"  ✓ Synced: {customer_data.get('name', 'N/A')}")
                    synced_count += 1
                else:
                    print(f"  ✗ Customer not found in API")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ✗ Error syncing user: {e}")
                failed_count += 1
        
        print(f"\n{'='*50}")
        print(f"Sync completed:")
        print(f"  Synced: {synced_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Total: {len(users)}")


if __name__ == "__main__":
    asyncio.run(sync_all_users())
