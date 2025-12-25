"""
Pydantic models for wrapped statistics.
"""

from pydantic import BaseModel
from typing import List, Optional

# Import Wordle models
from app.models.wordle import WordleUserStats


class MemberWrappedStats(BaseModel):
    """Combined statistics for a guild member."""

    uuid: str
    username: str
    guild_xp: int = 0
    quest_participation: int = 0
    discord_messages: int = 0
    times_pinged: int = 0
    joined_this_year: bool = False
    joined_timestamp: int = 0  # Unix timestamp in milliseconds
    joined_date: str = ""  # Human-readable date (YYYY-MM-DD)


class WrappedSummary(BaseModel):
    """Complete wrapped summary for a year."""

    year: int
    guild_name: str = "Chizza Guild"

    # Aggregate stats
    total_members: int = 0
    total_guild_xp: int = 0
    total_messages: int = 0
    new_members_count: int = 0
    most_active_day: str = ""

    # Top lists
    top_xp_earners: List[MemberWrappedStats] = []
    top_messengers: List[MemberWrappedStats] = []
    new_members: List[MemberWrappedStats] = []
    most_pinged: List[MemberWrappedStats] = []
    guild_veterans: List[MemberWrappedStats] = []

    # Wordle stats
    wordle_top_winners: List[WordleUserStats] = []
    wordle_top_failures: List[WordleUserStats] = []
    total_wordle_games: int = 0

    # Fun facts
    fun_facts: List[str] = []
