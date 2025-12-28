"""
Pydantic models for custom wrapped pages loaded from JSON.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union


# Leaderboard Page Models
class LeaderboardItem(BaseModel):
    """Single item in a leaderboard."""
    rank: int = Field(ge=1)
    name: str
    stat: str


class LeaderboardPage(BaseModel):
    """Leaderboard page configuration."""
    page_type: Literal["leaderboard"]
    title: str
    subtitle: Optional[str] = None
    items: List[LeaderboardItem]
    background_gradient: Optional[str] = None


# Grid Page Models
class GridItem(BaseModel):
    """Single item in a member grid."""
    name: str
    detail: str


class GridPage(BaseModel):
    """Member grid page configuration."""
    page_type: Literal["grid"]
    title: str
    subtitle: Optional[str] = None
    items: List[GridItem]
    background_gradient: Optional[str] = None


# Stats Page Models
class StatItem(BaseModel):
    """Single stat display."""
    value: int
    label: str


class StatsPage(BaseModel):
    """Stats display page configuration."""
    page_type: Literal["stats"]
    title: str
    subtitle: Optional[str] = None
    stats: List[StatItem]
    fun_fact: Optional[str] = None
    background_gradient: Optional[str] = None


# Text Page Models
class TextPage(BaseModel):
    """Simple text page configuration."""
    page_type: Literal["text"]
    title: str
    subtitle: Optional[str] = None
    body: str
    background_gradient: Optional[str] = None


# Union type for discriminated union
CustomPage = Union[LeaderboardPage, GridPage, StatsPage, TextPage]


# Root model
class CustomPagesConfig(BaseModel):
    """Root configuration for custom pages."""
    version: str = "1.0"
    custom_pages: List[CustomPage] = Field(default_factory=list, discriminator="page_type")
