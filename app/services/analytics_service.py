"""
Analytics service for combining Hypixel and Discord data.
Generates wrapped statistics and stores them in the database.
"""

import sqlite3
from typing import List, Dict
from datetime import datetime
from app.config import settings
from app.models.hypixel import MemberXPStats
from app.models.discord import DiscordStats, UserMessageStats
from app.models.wrapped import MemberWrappedStats, WrappedSummary


class AnalyticsService:
    """Service for combining data and generating wrapped statistics."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path

    def combine_stats(
        self,
        hypixel_stats: List[MemberXPStats],
        discord_stats: DiscordStats,
        guild_name: str = "Chizza Guild",
        total_guild_xp: int = 0,
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
        top_xp = sorted(combined_members, key=lambda x: x.guild_xp, reverse=True)[:10]
        top_msg = sorted(discord_members, key=lambda x: x.discord_messages, reverse=True)[:10]
        new_members = sorted(
            [m for m in combined_members if m.joined_this_year],
            key=lambda x: x.joined_timestamp,
            reverse=True  # Most recent first
        )
        most_pinged = sorted(discord_members, key=lambda x: x.times_pinged, reverse=True)[:10]
        most_pinged = [m for m in most_pinged if m.times_pinged > 0]

        # Calculate aggregate stats
        # Use the guild's total XP if provided, otherwise sum member contributions
        total_xp = total_guild_xp if total_guild_xp > 0 else sum(m.guild_xp for m in combined_members)
        total_members = len(combined_members)
        new_members_count = len(new_members)

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
                (snapshot_id, member_uuid, member_name, guild_xp, joined_this_year, joined_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    member.uuid,
                    member.username,
                    member.guild_xp,
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
                (snapshot_id, member_uuid, member_name, guild_xp, joined_this_year, joined_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    member.uuid,
                    member.username,
                    member.guild_xp,
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
        all_members = [
            MemberWrappedStats(
                uuid=m["member_uuid"] or "",
                username=m["member_name"],
                guild_xp=m["guild_xp"] or 0,
                discord_messages=m["discord_messages"] or 0,
                times_pinged=m["times_pinged"] or 0,
                joined_this_year=bool(m["joined_this_year"]),
                joined_date=m["joined_date"] or "",
            )
            for m in members
        ]

        # Separate into categories
        top_xp = [m for m in all_members if m.guild_xp > 0][:10]
        top_msg = sorted(all_members, key=lambda x: x.discord_messages, reverse=True)[:10]
        new_members = sorted(
            [m for m in all_members if m.joined_this_year],
            key=lambda x: x.joined_date,
            reverse=True  # Most recent first
        )
        most_pinged = sorted(all_members, key=lambda x: x.times_pinged, reverse=True)[:10]
        most_pinged = [m for m in most_pinged if m.times_pinged > 0]

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
        )
