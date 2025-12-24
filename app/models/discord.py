"""
Pydantic models for Discord data.
"""

from pydantic import BaseModel
from typing import List
from datetime import datetime


class DiscordMessage(BaseModel):
    """Model for a Discord message."""

    author_id: int
    author_name: str
    content: str
    mentions: List[int]  # List of user IDs mentioned
    timestamp: str


class UserMessageStats(BaseModel):
    """Model for user message statistics."""

    user_id: int
    username: str
    message_count: int = 0
    times_pinged: int = 0


class DiscordStats(BaseModel):
    """Model for aggregated Discord statistics."""

    total_messages: int = 0
    user_stats: List[UserMessageStats] = []
    most_active_day: str = ""
