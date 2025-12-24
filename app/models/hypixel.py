"""
Pydantic models for Hypixel API responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class GuildMember(BaseModel):
    """Model for a guild member."""

    uuid: str
    rank: str
    joined: int  # Unix timestamp in milliseconds
    exp_history: Dict[str, int] = Field(default_factory=dict, alias="expHistory")
    quest_participation: int = Field(0, alias="questParticipation")

    class Config:
        populate_by_name = True


class Guild(BaseModel):
    """Model for guild data."""

    name: str
    members: List[GuildMember]
    exp: int = 0  # Total guild XP
    created: Optional[int] = None
    tag: Optional[str] = None
    tag_color: Optional[str] = Field(None, alias="tagColor")

    class Config:
        populate_by_name = True


class HypixelGuildResponse(BaseModel):
    """Model for the complete Hypixel API guild response."""

    success: bool
    guild: Optional[Guild] = None


class MemberXPStats(BaseModel):
    """Model for member XP statistics."""

    uuid: str
    username: str = "Unknown"
    total_xp: int = 0
    joined_timestamp: int
    joined_this_year: bool = False
