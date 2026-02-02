"""API client for external lottery system."""
import aiohttp
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)


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
            "X-API-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
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
    
    async def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get customer data by phone number from external API.
        
        Args:
            phone: Customer phone number
        
        Returns:
            Customer data dict with 'id', 'external_id', 'name', 'phone', 'email',
            'balance', 'available_tickets', 'birthday', 'sex', 'additional_fields', etc.
            None if customer not found or API error.
        """
        # Normalize phone to digits only
        import re
        normalized_phone = re.sub(r'\D', '', phone)
        
        logger.info(f"Requesting customer data for phone: {phone} (normalized: {normalized_phone})")
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/customers"
                params = {"phone": f"+{normalized_phone}"}  # API expects phone with +
                logger.debug(f"API Request: GET {url} with params={params}")
                
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.debug(f"API Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"API Response data: {data}")
                        
                        # Check for single customer response
                        if data.get("success") and data.get("customer"):
                            customer = data["customer"]
                            logger.info(f"Customer found: {customer.get('name', 'N/A')} (ID: {customer.get('id')})")
                            return customer
                        
                        # Check for list response with pagination
                        if data.get("success") and data.get("data"):
                            customers = data["data"]
                            if customers and len(customers) > 0:
                                customer = customers[0]
                                logger.info(f"Customer found: {customer.get('name', 'N/A')} (ID: {customer.get('id')})")
                                return customer
                        
                        logger.warning(f"No customer data in response for phone: {normalized_phone}")
                        return None
                    
                    if response.status == 404:
                        logger.info(f"Customer not found for phone: {phone}")
                        return None
                    
                    # Log error for other status codes
                    text = await response.text()
                    logger.error(f"API error getting customer: {response.status}, {text}")
                    return None
                    
            except aiohttp.ClientError as e:
                logger.error(f"API connection error getting customer: {e}")
                return None
    
    async def get_current_draw(self) -> Optional[Dict[str, Any]]:
        """
        Get current active draw from external API.
        
        Returns:
            Draw data dict with 'id', 'name', 'status', 'winning_numbers', etc.
            None if no current draw or API error.
        """
        logger.info("Requesting current draw data")
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/draws/current"
                logger.debug(f"API Request: GET {url}")
                
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.debug(f"API Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"API Response data: {data}")
                        
                        if data.get("success") and data.get("draw"):
                            draw = data["draw"]
                            logger.info(f"Current draw found: {draw.get('name', 'N/A')} (ID: {draw.get('id')})")
                            return draw
                        logger.warning("No current draw data in response")
                        return None
                    
                    if response.status == 404:
                        logger.info("No current draw found")
                        return None
                    
                    # Log error for other status codes
                    text = await response.text()
                    logger.error(f"API error getting current draw: {response.status}, {text}")
                    return None
                    
            except aiohttp.ClientError as e:
                logger.error(f"API connection error getting current draw: {e}")
                return None
    
    async def get_draw_by_id(self, draw_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific draw by ID from external API.
        
        Args:
            draw_id: Draw ID
        
        Returns:
            Draw data dict or None if not found or API error.
        """
        logger.info(f"Requesting draw data for ID: {draw_id}")
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/draws/{draw_id}"
                logger.debug(f"API Request: GET {url}")
                
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.debug(f"API Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success") and data.get("draw"):
                            draw = data["draw"]
                            logger.info(f"Draw found: {draw.get('name', 'N/A')} (ID: {draw.get('id')})")
                            return draw
                        return None
                    
                    if response.status == 404:
                        logger.info(f"Draw {draw_id} not found")
                        return None
                    
                    text = await response.text()
                    logger.error(f"API error getting draw {draw_id}: {response.status}, {text}")
                    return None
                    
            except aiohttp.ClientError as e:
                logger.error(f"API connection error getting draw {draw_id}: {e}")
                return None
    
    async def get_customer_tickets(self, customer_id: int, draw_id: int = None) -> Optional[list]:
        """
        Get customer's lottery tickets from external API.
        
        Args:
            customer_id: Customer ID from API
            draw_id: Optional draw ID to filter tickets
        
        Returns:
            List of ticket dicts or None if error.
        """
        logger.info(f"Requesting tickets for customer {customer_id}")
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/customers/{customer_id}/tickets"
                params = {}
                if draw_id:
                    params["draw_id"] = str(draw_id)
                
                logger.debug(f"API Request: GET {url} with params={params}")
                
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.debug(f"API Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"API Response data: {data}")
                        
                        if data.get("success") and data.get("data"):
                            tickets = data["data"]
                            logger.info(f"Found {len(tickets)} tickets for customer {customer_id}")
                            return tickets
                        logger.warning(f"No tickets data in response for customer {customer_id}")
                        return []
                    
                    if response.status == 404:
                        logger.info(f"No tickets found for customer {customer_id}")
                        return []
                    
                    # Log error for other status codes
                    text = await response.text()
                    logger.error(f"API error getting tickets: {response.status}, {text}")
                    return None
                    
            except aiohttp.ClientError as e:
                logger.error(f"API connection error getting tickets: {e}")
                return None
    
    async def create_ticket(self, customer_id: int, draw_id: int, numbers: list = None) -> Optional[dict]:
        """
        Create a new ticket for customer in a draw.
        
        Args:
            customer_id: Customer ID
            draw_id: Draw ID
            numbers: Optional list of 6 numbers (1-45). If not provided, ticket created without numbers.
        
        Returns:
            Created ticket data or None if error
        """
        logger.info(f"Creating ticket for customer {customer_id} in draw {draw_id}")
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/customers/{customer_id}/tickets"
                payload = {"draw_id": draw_id}
                if numbers:
                    payload["numbers"] = numbers
                
                logger.debug(f"API Request: POST {url} with payload={payload}")
                
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.debug(f"API Response status: {response.status}")
                    
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.debug(f"API Response data: {data}")
                        
                        if data.get("success") and data.get("ticket"):
                            ticket = data["ticket"]
                            logger.info(f"Ticket created successfully: ID {ticket.get('id')}")
                            return ticket
                        logger.warning(f"No ticket data in response")
                        return None
                    
                    if response.status == 403:
                        logger.warning(f"Forbidden: Cannot create ticket for customer {customer_id}")
                        return None
                    
                    if response.status == 409:
                        text = await response.text()
                        logger.warning(f"Conflict: {text}")
                        return None
                    
                    # Log error for other status codes
                    text = await response.text()
                    logger.error(f"API error creating ticket: {response.status}, {text}")
                    return None
                    
            except aiohttp.ClientError as e:
                logger.error(f"API connection error creating ticket: {e}")
                return None
    
    async def fill_ticket(self, customer_id: int, draw_id: int, numbers: list) -> Optional[dict]:
        """
        Fill first available ticket with selected numbers via API.
        API automatically selects the first unfilled ticket.
        
        Args:
            customer_id: Customer ID
            draw_id: Draw ID
            numbers: List of 6 numbers (1-45)
        
        Returns:
            First filled ticket data or None if error
        """
        logger.info(f"Filling ticket for customer {customer_id} in draw {draw_id} with numbers {numbers}")
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/customers/{customer_id}/tickets/fill"
                payload = {
                    "draw_id": draw_id,
                    "tickets": [numbers]  # Array of number arrays
                }
                
                logger.debug(f"API Request: POST {url} with payload={payload}")
                
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.debug(f"API Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"API Response data: {data}")
                        
                        if data.get("success") and data.get("tickets"):
                            tickets = data["tickets"]
                            if tickets and len(tickets) > 0:
                                ticket = tickets[0]  # Return first filled ticket
                                logger.info(f"Ticket filled successfully: ID {ticket.get('id')}")
                                return ticket
                        logger.warning(f"No tickets data in response")
                        return None
                    
                    if response.status == 403:
                        logger.warning(f"Forbidden: Cannot fill ticket for customer {customer_id}")
                        return None
                    
                    if response.status == 404:
                        logger.warning(f"No unfilled tickets found for customer {customer_id}")
                        return None
                    
                    if response.status == 409:
                        text = await response.text()
                        logger.warning(f"Conflict: {text}")
                        return None
                    
                    # Log error for other status codes
                    text = await response.text()
                    logger.error(f"API error filling ticket: {response.status}, {text}")
                    return None
                    
            except aiohttp.ClientError as e:
                logger.error(f"API connection error filling ticket: {e}")
                return None


# Singleton instance
api_client = LotteryAPIClient()
