"""
Hypixel API integration service.
Handles fetching guild data and calculating statistics.
"""

import httpx
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from app.config import settings
from app.models.hypixel import HypixelGuildResponse, MemberXPStats


class HypixelService:
    """Service for interacting with the Hypixel API."""

    BASE_URL = "https://api.hypixel.net"

    def __init__(self):
        self.api_key = settings.hypixel_api_key
        self.guild_id = settings.hypixel_guild_id

    async def fetch_guild_data(self, cache: bool = True) -> HypixelGuildResponse:
        """
        Fetch guild data from Hypixel API.

        Args:
            cache: Whether to cache the response to disk

        Returns:
            HypixelGuildResponse object with guild data
        """
        url = f"{self.BASE_URL}/guild"
        params = {"key": self.api_key, "id": self.guild_id}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        guild_response = HypixelGuildResponse(**data)

        if cache:
            self._cache_response(data, settings.year)

        return guild_response

    def _cache_response(self, data: dict, year: int):
        """Cache the API response to disk."""
        cache_dir = Path(f"data/cache/{year}")
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / "hypixel_guild.json"
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Cached Hypixel data to {cache_file}")

    def load_cached_data(self, year: int) -> Optional[HypixelGuildResponse]:
        """Load cached guild data from disk."""
        cache_file = Path(f"data/cache/{year}/hypixel_guild.json")

        if not cache_file.exists():
            return None

        with open(cache_file, "r") as f:
            data = json.load(f)

        return HypixelGuildResponse(**data)

    def calculate_yearly_xp(
        self, members: list, year: int
    ) -> List[MemberXPStats]:
        """
        Calculate total XP gained by each member during the specified year.

        Args:
            members: List of GuildMember objects
            year: Year to calculate XP for (e.g., 2025)

        Returns:
            List of MemberXPStats sorted by total XP (descending)
        """
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        member_stats = []

        for member in members:
            total_xp = 0

            # Sum XP from expHistory for dates within the year
            for date_str, xp in member.exp_history.items():
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if start_date <= date <= end_date:
                        total_xp += xp
                except ValueError:
                    continue

            # Check if member joined this year
            joined_date = datetime.fromtimestamp(member.joined / 1000)
            joined_this_year = start_date <= joined_date <= end_date

            member_stats.append(
                MemberXPStats(
                    uuid=member.uuid,
                    total_xp=total_xp,
                    quest_participation=member.quest_participation,
                    joined_timestamp=member.joined,
                    joined_this_year=joined_this_year,
                )
            )

        # Sort by quest participation descending (more meaningful than 7-day XP)
        member_stats.sort(key=lambda x: x.quest_participation, reverse=True)

        return member_stats

    def get_members_joined_this_year(
        self, members: list, year: int
    ) -> List[MemberXPStats]:
        """
        Get list of members who joined during the specified year.

        Args:
            members: List of GuildMember objects
            year: Year to filter by

        Returns:
            List of MemberXPStats for members who joined this year
        """
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        new_members = []

        for member in members:
            joined_date = datetime.fromtimestamp(member.joined / 1000)

            if start_date <= joined_date <= end_date:
                new_members.append(
                    MemberXPStats(
                        uuid=member.uuid,
                        joined_timestamp=member.joined,
                        joined_this_year=True,
                    )
                )

        # Sort by join date (most recent first)
        new_members.sort(key=lambda x: x.joined_timestamp, reverse=True)

        return new_members

    async def get_player_username(self, uuid: str) -> str:
        """
        Fetch player username from Mojang API using UUID.

        Args:
            uuid: Player UUID (with or without dashes)

        Returns:
            Player's current username
        """
        # Remove dashes from UUID if present
        clean_uuid = uuid.replace("-", "")

        url = f"https://sessionserver.mojang.com/session/minecraft/profile/{clean_uuid}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                return data.get("name", "Unknown")
        except Exception as e:
            print(f"⚠️  Failed to fetch username for {uuid}: {e}")
            return "Unknown"

    async def enrich_members_with_usernames(
        self, member_stats: List[MemberXPStats]
    ) -> List[MemberXPStats]:
        """
        Fetch and add usernames for all members.

        Args:
            member_stats: List of MemberXPStats

        Returns:
            Same list with usernames populated
        """
        for member in member_stats:
            member.username = await self.get_player_username(member.uuid)

        return member_stats
