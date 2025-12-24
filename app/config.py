"""
Configuration management for Hypixel Guild Wrapped application.
Loads settings from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Hypixel API
    hypixel_api_key: str
    hypixel_guild_id: str

    # Discord API
    discord_bot_token: str
    discord_guild_id: str
    discord_channel_ids: str  # Comma-separated string

    # Application
    year: int = 2025
    start_date: str = "2025-01-01"
    end_date: str = "2025-12-31"

    # Security
    admin_password: str

    # Database
    database_path: str = "data/wrapped.db"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def channel_ids_list(self) -> List[int]:
        """Parse comma-separated channel IDs into a list of integers."""
        return [int(cid.strip()) for cid in self.discord_channel_ids.split(",")]


# Create a global settings instance
settings = Settings()
