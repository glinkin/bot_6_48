"""Ticket checking and prize calculation logic."""
from typing import List, Tuple


# Prize distribution (total fund: 500,000)
PRIZE_TABLE = {
    6: 200_000,  # 40%
    5: 125_000,  # 25%
    4: 100_000,  # 20%
    3: 75_000,   # 15%
    # 0-2 matches: no prize
}


def calculate_matches(ticket_numbers: List[int], winning_numbers: List[int]) -> int:
    """
    Calculate number of matching numbers between ticket and winning combination.
    
    Args:
        ticket_numbers: List of 6 numbers on user's ticket
        winning_numbers: List of 6 winning numbers
    
    Returns:
        Number of matches (0-6)
    """
    ticket_set = set(ticket_numbers)
    winning_set = set(winning_numbers)
    return len(ticket_set & winning_set)


def get_prize_amount(matches: int) -> int:
    """
    Get prize amount for given number of matches.
    
    Args:
        matches: Number of matching numbers (0-6)
    
    Returns:
        Prize amount in currency units (0 if no prize)
    """
    return PRIZE_TABLE.get(matches, 0)


def check_ticket_result(ticket_numbers: List[int], winning_numbers: List[int]) -> Tuple[int, int]:
    """
    Check ticket against winning numbers and return matches and prize.
    
    Args:
        ticket_numbers: User's ticket numbers
        winning_numbers: Winning combination
    
    Returns:
        Tuple of (matches, prize_amount)
    """
    matches = calculate_matches(ticket_numbers, winning_numbers)
    prize = get_prize_amount(matches)
    return matches, prize
