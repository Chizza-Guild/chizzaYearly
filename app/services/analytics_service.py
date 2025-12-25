"""
Analytics service for combining Hypixel and Discord data.
Generates wrapped statistics and stores them in the database.
"""

import sqlite3
from typing import List, Dict
from datetime import datetime
from app.config import settings
from app.models.hypixel import MemberXPStats
from app.models.discord import DiscordStats, UserMessageStats, DiscordMessage
from app.models.wrapped import MemberWrappedStats, WrappedSummary
from app.services.wordle_service import WordleService


class AnalyticsService:
    """Service for combining data and generating wrapped statistics."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self.wordle_service = WordleService()

    def combine_stats(
        self,
        hypixel_stats: List[MemberXPStats],
        discord_stats: DiscordStats,
        guild_name: str = "Chizza Guild",
        total_guild_xp: int = 0,
        discord_messages: List[DiscordMessage] = None,
    ) -> WrappedSummary:
        """
        Combine Hypixel and Discord statistics into a wrapped summary.

        Args:
            hypixel_stats: List of member XP stats from Hypixel
            discord_stats: Discord statistics
            guild_name: Name of the guild

        Returns:
            WrappedSummary with all combined statistics
        """
        # Create a mapping of Discord user stats
        discord_map: Dict[int, UserMessageStats] = {
            stat.user_id: stat for stat in discord_stats.user_stats
        }

        # Combine stats for all members
        combined_members = []

        for hypixel_member in hypixel_stats:
            # Convert timestamp to readable date
            joined_date = datetime.fromtimestamp(hypixel_member.joined_timestamp / 1000).strftime("%Y-%m-%d")

            combined_members.append(
                MemberWrappedStats(
                    uuid=hypixel_member.uuid,
                    username=hypixel_member.username,
                    guild_xp=hypixel_member.total_xp,
                    quest_participation=hypixel_member.quest_participation,
                    joined_this_year=hypixel_member.joined_this_year,
                    joined_timestamp=hypixel_member.joined_timestamp,
                    joined_date=joined_date,
                    discord_messages=0,  # We can't link Discord to Hypixel easily
                    times_pinged=0,
                )
            )

        # Create separate entries for Discord-only stats
        # (since we can't easily link Discord IDs to Hypixel UUIDs)
        discord_members = []
        for user_stat in discord_stats.user_stats:
            discord_members.append(
                MemberWrappedStats(
                    uuid="",  # No UUID for Discord-only users
                    username=user_stat.username,
                    guild_xp=0,
                    discord_messages=user_stat.message_count,
                    times_pinged=user_stat.times_pinged,
                )
            )

        # Get top lists
        # Sort by quest participation (top_xp is kept for template compatibility)
        top_xp = sorted(combined_members, key=lambda x: x.quest_participation, reverse=True)[:10]
        top_msg = sorted(discord_members, key=lambda x: x.discord_messages, reverse=True)[:10]
        new_members = sorted(
            [m for m in combined_members if m.joined_this_year],
            key=lambda x: x.joined_timestamp,
            reverse=True  # Most recent first
        )
        most_pinged = sorted(discord_members, key=lambda x: x.times_pinged, reverse=True)[:10]
        most_pinged = [m for m in most_pinged if m.times_pinged > 0]

        # Get guild veterans (oldest members by join date)
        # Filter out members with invalid timestamps (0 or None) and sort by timestamp
        valid_members = [m for m in combined_members if m.joined_timestamp > 0]
        guild_veterans = sorted(valid_members, key=lambda x: x.joined_timestamp)[:12]

        # Calculate aggregate stats
        # Use the guild's total XP if provided, otherwise sum member contributions
        total_xp = total_guild_xp if total_guild_xp > 0 else sum(m.guild_xp for m in combined_members)
        total_members = len(combined_members)
        new_members_count = len(new_members)

        # Calculate Wordle stats
        wordle_top_winners = []
        wordle_top_failures = []
        total_wordle_games = 0

        if discord_messages:
            wordle_results = self.wordle_service.parse_wordle_results(
                discord_messages, discord_stats.user_stats
            )
            wordle_stats = self.wordle_service.calculate_stats(wordle_results)
            wordle_top_winners = self.wordle_service.get_top_winners(wordle_stats, limit=5)
            wordle_top_failures = self.wordle_service.get_top_failures(wordle_stats, limit=5)
            total_wordle_games = wordle_stats.total_games

        # Generate fun facts
        fun_facts = self._generate_fun_facts(
            total_members=total_members,
            total_xp=total_xp,
            total_messages=discord_stats.total_messages,
            new_members_count=new_members_count,
            most_active_day=discord_stats.most_active_day,
            top_earner=top_xp[0] if top_xp else None,
            top_messenger=top_msg[0] if top_msg else None,
        )

        return WrappedSummary(
            year=settings.year,
            guild_name=guild_name,
            total_members=total_members,
            total_guild_xp=total_xp,
            total_messages=discord_stats.total_messages,
            new_members_count=new_members_count,
            most_active_day=discord_stats.most_active_day,
            top_xp_earners=top_xp,
            top_messengers=top_msg,
            new_members=new_members,
            most_pinged=most_pinged,
            guild_veterans=guild_veterans,
            wordle_top_winners=wordle_top_winners,
            wordle_top_failures=wordle_top_failures,
            total_wordle_games=total_wordle_games,
            fun_facts=fun_facts,
        )

    def _generate_fun_facts(
        self,
        total_members: int,
        total_xp: int,
        total_messages: int,
        new_members_count: int,
        most_active_day: str,
        top_earner: MemberWrappedStats = None,
        top_messenger: MemberWrappedStats = None,
    ) -> List[str]:
        """Generate fun facts from the data."""
        facts = []

        if total_members:
            facts.append(f"{total_members:,} members strong!")

        if total_xp:
            facts.append(f"{total_xp:,} total guild XP earned")
            if total_members:
                avg_xp = total_xp // total_members
                facts.append(f"{avg_xp:,} average XP per member")

        if total_messages:
            facts.append(f"{total_messages:,} messages sent in Discord")
            if total_members:
                avg_msg = total_messages // total_members
                facts.append(f"{avg_msg:,} average messages per member")

        if new_members_count:
            facts.append(f"{new_members_count} new members joined this year")

        if most_active_day:
            facts.append(f"Most active day: {most_active_day}")

        if top_earner and top_earner.guild_xp:
            facts.append(f"{top_earner.username} earned the most XP: {top_earner.guild_xp:,}")

        if top_messenger and top_messenger.discord_messages:
            facts.append(
                f"{top_messenger.username} sent the most messages: {top_messenger.discord_messages:,}"
            )

        return facts

    def save_to_database(self, summary: WrappedSummary):
        """
        Save wrapped summary to the database.

        Args:
            summary: WrappedSummary object to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert or update snapshot
        cursor.execute(
            """
            INSERT OR REPLACE INTO wrapped_snapshots (year, hypixel_data_path, discord_data_path)
            VALUES (?, ?, ?)
            """,
            (
                summary.year,
                f"data/cache/{summary.year}/hypixel_guild.json",
                f"data/cache/{summary.year}/discord_messages.json",
            ),
        )
        snapshot_id = cursor.lastrowid

        # Delete existing member stats for this snapshot
        cursor.execute("DELETE FROM member_stats WHERE snapshot_id = ?", (snapshot_id,))

        # Insert member stats (Hypixel data - top XP earners)
        for member in summary.top_xp_earners:
            cursor.execute(
                """
                INSERT INTO member_stats
                (snapshot_id, member_uuid, member_name, guild_xp, quest_participation, joined_this_year, joined_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    member.uuid,
                    member.username,
                    member.guild_xp,
                    member.quest_participation,
                    member.joined_this_year,
                    member.joined_date,
                ),
            )

        # Insert new members (with join dates)
        for member in summary.new_members:
            # Skip if already inserted (in top XP earners)
            if member in summary.top_xp_earners:
                continue
            cursor.execute(
                """
                INSERT INTO member_stats
                (snapshot_id, member_uuid, member_name, guild_xp, quest_participation, joined_this_year, joined_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    member.uuid,
                    member.username,
                    member.guild_xp,
                    member.quest_participation,
                    member.joined_this_year,
                    member.joined_date,
                ),
            )

        # Insert Discord stats
        for member in summary.top_messengers:
            cursor.execute(
                """
                INSERT INTO member_stats
                (snapshot_id, member_name, discord_messages, times_pinged)
                VALUES (?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    member.username,
                    member.discord_messages,
                    member.times_pinged,
                ),
            )

        # Insert guild stats
        cursor.execute(
            """
            INSERT OR REPLACE INTO guild_stats
            (snapshot_id, total_members, total_xp, total_messages, new_members_count, most_active_day)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                summary.total_members,
                summary.total_guild_xp,
                summary.total_messages,
                summary.new_members_count,
                summary.most_active_day,
            ),
        )

        conn.commit()
        conn.close()

        print(f"✅ Saved wrapped summary for {summary.year} to database")

    def load_from_database(self, year: int) -> WrappedSummary:
        """
        Load wrapped summary from the database.

        Args:
            year: Year to load data for

        Returns:
            WrappedSummary object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get snapshot
        cursor.execute("SELECT * FROM wrapped_snapshots WHERE year = ?", (year,))
        snapshot = cursor.fetchone()

        if not snapshot:
            conn.close()
            return None

        snapshot_id = snapshot["id"]

        # Get guild stats
        cursor.execute("SELECT * FROM guild_stats WHERE snapshot_id = ?", (snapshot_id,))
        guild_stats = cursor.fetchone()

        # Get member stats
        cursor.execute(
            """
            SELECT * FROM member_stats
            WHERE snapshot_id = ?
            ORDER BY guild_xp DESC
            """,
            (snapshot_id,),
        )
        members = cursor.fetchall()

        conn.close()

        # Convert to models
        all_members = []
        for m in members:
            # Parse joined_date to timestamp if available
            joined_timestamp = 0
            if m["joined_date"]:
                try:
                    from datetime import datetime
                    dt = datetime.strptime(m["joined_date"], "%Y-%m-%d")
                    joined_timestamp = int(dt.timestamp() * 1000)  # Convert to milliseconds
                except:
                    joined_timestamp = 0

            all_members.append(
                MemberWrappedStats(
                    uuid=m["member_uuid"] or "",
                    username=m["member_name"],
                    guild_xp=m["guild_xp"] or 0,
                    quest_participation=m["quest_participation"] or 0,
                    discord_messages=m["discord_messages"] or 0,
                    times_pinged=m["times_pinged"] or 0,
                    joined_this_year=bool(m["joined_this_year"]),
                    joined_timestamp=joined_timestamp,
                    joined_date=m["joined_date"] or "",
                )
            )

        # Separate into categories
        # Sort by quest participation (top_xp is kept for template compatibility)
        top_xp = sorted(all_members, key=lambda x: x.quest_participation, reverse=True)[:10]
        top_xp = [m for m in top_xp if m.quest_participation > 0]
        top_msg = sorted(all_members, key=lambda x: x.discord_messages, reverse=True)[:10]
        new_members = sorted(
            [m for m in all_members if m.joined_this_year],
            key=lambda x: x.joined_date,
            reverse=True  # Most recent first
        )
        most_pinged = sorted(all_members, key=lambda x: x.times_pinged, reverse=True)[:10]
        most_pinged = [m for m in most_pinged if m.times_pinged > 0]

        # Get guild veterans (oldest members by join date)
        # Filter out members with invalid timestamps (0 or None) and sort by timestamp
        valid_veteran_members = [m for m in all_members if m.joined_timestamp and m.joined_timestamp > 0]
        guild_veterans = sorted(valid_veteran_members, key=lambda x: x.joined_timestamp)[:12]

        # Calculate Wordle stats from cached Discord messages
        wordle_top_winners = []
        wordle_top_failures = []
        total_wordle_games = 0

        try:
            # Load cached Discord messages
            from app.services.discord_service import DiscordService
            discord_service = DiscordService()
            cached_messages = discord_service.load_cached_messages(year)

            if cached_messages:
                # Calculate user stats for ID mapping
                from app.models.discord import UserMessageStats
                user_stats = [
                    UserMessageStats(
                        user_id=m.author_id,
                        username=m.author_name,
                        message_count=0,
                        times_pinged=0
                    )
                    for m in cached_messages
                ]
                # Deduplicate by user_id
                seen = set()
                user_stats = [x for x in user_stats if x.user_id not in seen and not seen.add(x.user_id)]

                # Parse and calculate Wordle stats
                wordle_results = self.wordle_service.parse_wordle_results(cached_messages, user_stats)
                wordle_stats = self.wordle_service.calculate_stats(wordle_results)
                wordle_top_winners = self.wordle_service.get_top_winners(wordle_stats, limit=5)
                wordle_top_failures = self.wordle_service.get_top_failures(wordle_stats, limit=5)
                total_wordle_games = wordle_stats.total_games
        except Exception as e:
            print(f"Warning: Could not load Wordle stats: {e}")

        return WrappedSummary(
            year=year,
            total_members=guild_stats["total_members"] if guild_stats else 0,
            total_guild_xp=guild_stats["total_xp"] if guild_stats else 0,
            total_messages=guild_stats["total_messages"] if guild_stats else 0,
            new_members_count=guild_stats["new_members_count"] if guild_stats else 0,
            most_active_day=guild_stats["most_active_day"] if guild_stats else "",
            top_xp_earners=top_xp,
            top_messengers=top_msg,
            new_members=new_members,
            most_pinged=most_pinged,
            guild_veterans=guild_veterans,
            wordle_top_winners=wordle_top_winners,
            wordle_top_failures=wordle_top_failures,
            total_wordle_games=total_wordle_games,
        )
