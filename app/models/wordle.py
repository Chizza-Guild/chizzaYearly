"""
Pydantic models for Wordle statistics.
"""

from pydantic import BaseModel
from typing import List


class WordleResult(BaseModel):
    """Model for a single Wordle result."""

    author_name: str
    wordle_number: int
    guesses: int  # 1-6 for wins, 7 for X/failures
    is_win: bool


class WordleUserStats(BaseModel):
    """Wordle statistics for a user."""

    username: str
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0  # Percentage
    average_guesses: float = 0.0  # Average for wins only


class WordleStats(BaseModel):
    """Complete Wordle statistics."""

    total_games: int = 0
    total_wins: int = 0
    total_losses: int = 0
    user_stats: List[WordleUserStats] = []
