"""
Discord API integration service.
Handles fetching message history and calculating statistics.
"""

import discord
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from collections import defaultdict, Counter
from app.config import settings
from app.models.discord import DiscordMessage, UserMessageStats, DiscordStats


class DiscordService:
    """Service for interacting with the Discord API."""

    def __init__(self):
        self.token = settings.discord_bot_token
        self.guild_id = int(settings.discord_guild_id)
        self.channel_ids = settings.channel_ids_list

        # Set up Discord client with required intents
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True  # Required to read message content
        intents.guilds = True

        self.client = discord.Client(intents=intents)

    async def fetch_all_messages(
        self, start_date: str, end_date: str, cache: bool = True
    ) -> List[DiscordMessage]:
        """
        Fetch all messages from configured channels within the date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            cache: Whether to cache messages to disk

        Returns:
            List of DiscordMessage objects
        """
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)

        all_messages = []

        @self.client.event
        async def on_ready():
            nonlocal all_messages
            print(f"✅ Discord bot connected as {self.client.user}")

            for channel_id in self.channel_ids:
                try:
                    channel = self.client.get_channel(channel_id)
                    if not channel:
                        print(f"⚠️  Channel {channel_id} not found")
                        continue

                    print(f"📥 Fetching messages from #{channel.name}...")
                    count = 0

                    async for message in channel.history(
                        after=start_dt, before=end_dt, limit=None
                    ):
                        all_messages.append(
                            DiscordMessage(
                                author_id=message.author.id,
                                author_name=message.author.name,
                                content=message.content,
                                mentions=[m.id for m in message.mentions],
                                timestamp=message.created_at.isoformat(),
                            )
                        )
                        count += 1

                        if count % 1000 == 0:
                            print(f"   Fetched {count} messages from #{channel.name}...")

                    print(f"✅ Fetched {count} messages from #{channel.name}")

                except Exception as e:
                    print(f"❌ Error fetching from channel {channel_id}: {e}")

            if cache:
                self._cache_messages(all_messages, settings.year)

            print(f"\n✅ Total messages fetched: {len(all_messages)}")

            # Close the client after fetching
            await self.client.close()

        # Run the bot
        await self.client.start(self.token)

        return all_messages

    def _cache_messages(self, messages: List[DiscordMessage], year: int):
        """Cache messages to disk."""
        cache_dir = Path(f"data/cache/{year}")
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / "discord_messages.json"

        # Convert Pydantic models to dicts for JSON serialization
        messages_data = [msg.model_dump() for msg in messages]

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(messages_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Cached {len(messages)} Discord messages to {cache_file}")

    def load_cached_messages(self, year: int) -> List[DiscordMessage]:
        """Load cached messages from disk."""
        cache_file = Path(f"data/cache/{year}/discord_messages.json")

        if not cache_file.exists():
            return []

        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [DiscordMessage(**msg) for msg in data]

    def calculate_stats(self, messages: List[DiscordMessage]) -> DiscordStats:
        """
        Calculate statistics from messages.

        Args:
            messages: List of DiscordMessage objects

        Returns:
            DiscordStats object with aggregated statistics
        """
        # Count messages per user
        message_counts = defaultdict(int)
        mention_counts = defaultdict(int)
        user_names = {}
        day_counts = Counter()

        for msg in messages:
            # Count messages
            message_counts[msg.author_id] += 1
            user_names[msg.author_id] = msg.author_name

            # Count mentions
            for mentioned_id in msg.mentions:
                mention_counts[mentioned_id] += 1

            # Count messages per day
            day = msg.timestamp[:10]  # Extract YYYY-MM-DD
            day_counts[day] += 1

        # Create user stats
        user_stats = []
        all_user_ids = set(message_counts.keys()) | set(mention_counts.keys())

        for user_id in all_user_ids:
            user_stats.append(
                UserMessageStats(
                    user_id=user_id,
                    username=user_names.get(user_id, "Unknown"),
                    message_count=message_counts.get(user_id, 0),
                    times_pinged=mention_counts.get(user_id, 0),
                )
            )

        # Find most active day
        most_active_day = ""
        if day_counts:
            most_active_day = day_counts.most_common(1)[0][0]

        return DiscordStats(
            total_messages=len(messages),
            user_stats=user_stats,
            most_active_day=most_active_day,
        )

    def get_top_messengers(
        self, stats: DiscordStats, limit: int = 10
    ) -> List[UserMessageStats]:
        """Get top users by message count."""
        sorted_stats = sorted(
            stats.user_stats, key=lambda x: x.message_count, reverse=True
        )
        return sorted_stats[:limit]

    def get_top_pinged(
        self, stats: DiscordStats, limit: int = 10
    ) -> List[UserMessageStats]:
        """Get top users by times mentioned."""
        sorted_stats = sorted(
            stats.user_stats, key=lambda x: x.times_pinged, reverse=True
        )
        # Filter out users with 0 pings
        return [s for s in sorted_stats if s.times_pinged > 0][:limit]
