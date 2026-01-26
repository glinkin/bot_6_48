"""Service for managing lottery draws and tickets."""
import random
from typing import List


CURRENT_DRAW_ID = "2026-03"  # Update this for each new draw


def get_current_draw_id() -> str:
    """Get current draw ID."""
    return CURRENT_DRAW_ID


def generate_random_numbers() -> List[int]:
    """Generate 6 unique random numbers from 1-45."""
    return sorted(random.sample(range(1, 46), 6))


def validate_numbers(numbers: List[int]) -> tuple[bool, str | None]:
    """
    Validate user-selected numbers.
    
    Returns:
        (is_valid, error_message)
    """
    if len(numbers) != 6:
        return False, "Должно быть ровно 6 чисел"
    
    if len(set(numbers)) != 6:
        return False, "Числа должны быть уникальными"
    
    if any(n < 1 or n > 45 for n in numbers):
        return False, "Числа должны быть от 1 до 45"
    
    return True, None


def parse_numbers_from_text(text: str) -> List[int] | None:
    """
    Parse numbers from user text input.
    
    Examples:
        "1 5 12 23 34 45"
        "1, 5, 12, 23, 34, 45"
        "1,5,12,23,34,45"
    
    Returns:
        List of integers or None if parsing failed
    """
    try:
        # Remove commas and split by spaces
        text = text.replace(',', ' ')
        parts = text.split()
        numbers = [int(p) for p in parts if p.strip()]
        return numbers
    except ValueError:
        return None
