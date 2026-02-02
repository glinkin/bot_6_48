"""Test script to check API integration."""
import asyncio
import sys
from api.client import LotteryAPIClient


async def test_api():
    """Test API connection and customer endpoint."""
    client = LotteryAPIClient()
    
    print("="*60)
    print("Testing Lottery API Integration")
    print("="*60)
    print(f"\nAPI Base URL: {client.base_url}")
    print(f"API Key: {client.api_key[:10]}...{client.api_key[-5:]}")
    print()
    
    # Test phone number
    test_phone = input("Enter phone number to test (or press Enter for +79652223633): ").strip()
    if not test_phone:
        test_phone = "+79652223633"
    
    print(f"\n{'='*60}")
    print(f"Testing customer lookup for: {test_phone}")
    print(f"{'='*60}\n")
    
    # Get customer data
    customer = await client.get_customer_by_phone(test_phone)
    
    if customer:
        print("✅ Customer found!")
        print(f"\n{'='*60}")
        print("Customer Data:")
        print(f"{'='*60}")
        print(f"ID: {customer.get('id')}")
        print(f"External ID: {customer.get('external_id')}")
        print(f"Name: {customer.get('name')}")
        print(f"Phone: {customer.get('phone')}")
        print(f"Email: {customer.get('email')}")
        print(f"Balance: {customer.get('balance')}")
        print(f"Available Tickets: {customer.get('available_tickets')}")
        print(f"Birthday: {customer.get('birthday')}")
        print(f"Sex: {customer.get('sex')}")
        print(f"Additional Fields: {customer.get('additional_fields')}")
        print(f"Created: {customer.get('created_at')}")
        print(f"Updated: {customer.get('updated_at')}")
    else:
        print("❌ Customer not found or API error")
        print("Check logs above for details")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_api())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(0)
