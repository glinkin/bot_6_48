"""API client for external lottery system."""
import aiohttp
from typing import Dict, Any, Optional
from config import settings


# Mock data for testing (remove in production)
MOCK_TICKETS = {
    "79652223633": {
        "numbers": [7, 12, 23, 34, 41, 45],
        "status": "pending",
        "draw_date": "20 января 2026",
        "draw_id": "2026-03"
    }
}

MOCK_CURRENT_DRAW = {
    "draw_id": "2026-03",
    "status": "pending",
    "draw_date": "20 января 2026",
    "winning_numbers": None  # Set to [1, 5, 12, 23, 34, 45] after draw
}


class LotteryAPIClient:
    """Client for communicating with external lottery ticket system."""
    
    def __init__(self):
        self.base_url = settings.api_base_url.rstrip('/')
        self.api_key = settings.api_key
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def get_ticket_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get current ticket for user by phone number.
        
        Returns:
            Ticket data dict with 'numbers', 'status', 'draw_id', etc.
            None if no ticket found for current draw.
        """
        # Mock data for testing (remove in production)
        from services.user_service import normalize_phone
        normalized = normalize_phone(phone)
        if normalized in MOCK_TICKETS:
            return MOCK_TICKETS[normalized]
        
        # Real API call (currently returns None)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/tickets/{phone}/current",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 404:
                        return None
                    
                    if response.status == 200:
                        return await response.json()
                    
                    # Log error for other status codes
                    text = await response.text()
                    print(f"API error: {response.status}, {text}")
                    return None
                    
            except aiohttp.ClientError as e:
                print(f"API connection error: {e}")
                return None
    
    async def get_current_draw(self) -> Optional[Dict[str, Any]]:
        # Mock data for testing (remove in production)
        return MOCK_CURRENT_DRAW
        
        # Real API call (currently unused)
        """
        Get current draw information including winning numbers if available.
        
        Returns:
            Draw data dict with 'draw_id', 'winning_numbers', 'status', etc.
            None if no current draw or API error.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/draws/current",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
            except aiohttp.ClientError as e:
                print(f"API connection error: {e}")
                return None


# Singleton instance
api_client = LotteryAPIClient()
