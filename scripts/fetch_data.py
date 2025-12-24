"""
Data collection script for Hypixel Guild Wrapped.
Run this script at year-end to fetch all data from Hypixel and Discord APIs.

Usage:
    python scripts/fetch_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.services.hypixel_service import HypixelService
from app.services.discord_service import DiscordService
from app.services.analytics_service import AnalyticsService


async def fetch_all_data():
    """Main function to fetch and process all data."""

    print("=" * 60)
    print(f"Hypixel Guild Wrapped - Data Collection for {settings.year}")
    print("=" * 60)
    print()

    # Initialize services
    hypixel_service = HypixelService()
    discord_service = DiscordService()
    analytics_service = AnalyticsService()

    try:
        # Step 1: Fetch Hypixel guild data
        print("📊 Step 1/5: Fetching Hypixel guild data...")
        print(f"   Guild ID: {settings.hypixel_guild_id}")

        guild_response = await hypixel_service.fetch_guild_data(cache=True)

        if not guild_response.guild:
            print("❌ Error: Failed to fetch guild data from Hypixel API")
            return False

        print(f"✅ Successfully fetched data for guild: {guild_response.guild.name}")
        print(f"   Total members: {len(guild_response.guild.members)}")
        print()

        # Step 2: Calculate XP statistics
        print("📈 Step 2/5: Calculating XP statistics...")

        xp_stats = hypixel_service.calculate_yearly_xp(
            guild_response.guild.members,
            settings.year
        )

        total_xp = sum(member.total_xp for member in xp_stats)
        new_members = [m for m in xp_stats if m.joined_this_year]

        print(f"✅ XP statistics calculated")
        print(f"   Total guild XP: {total_xp:,}")
        print(f"   New members this year: {len(new_members)}")
        print()

        # Step 3: Fetch player usernames
        print("👤 Step 3/5: Fetching player usernames from Mojang API...")
        print(f"   This may take a while for {len(xp_stats)} members...")

        xp_stats = await hypixel_service.enrich_members_with_usernames(xp_stats)

        print(f"✅ Usernames fetched")
        print()

        # Step 4: Fetch Discord messages
        print("💬 Step 4/5: Fetching Discord messages...")
        print(f"   Channels: {len(settings.channel_ids_list)}")
        print(f"   Date range: {settings.start_date} to {settings.end_date}")
        print(f"   ⚠️  This may take 10-30 minutes depending on server activity!")
        print()

        messages = await discord_service.fetch_all_messages(
            settings.start_date,
            settings.end_date,
            cache=True
        )

        print()
        print(f"✅ Discord messages fetched: {len(messages):,}")
        print()

        # Step 5: Calculate Discord statistics
        print("📊 Step 5/5: Calculating Discord statistics...")

        discord_stats = discord_service.calculate_stats(messages)

        print(f"✅ Discord statistics calculated")
        print(f"   Total messages: {discord_stats.total_messages:,}")
        print(f"   Unique users: {len(discord_stats.user_stats)}")
        print(f"   Most active day: {discord_stats.most_active_day}")
        print()

        # Step 6: Combine and save
        print("💾 Combining data and saving to database...")

        summary = analytics_service.combine_stats(
            xp_stats,
            discord_stats,
            guild_response.guild.name
        )

        analytics_service.save_to_database(summary)

        print()
        print("=" * 60)
        print("✅ SUCCESS! Data collection complete!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  Guild: {summary.guild_name}")
        print(f"  Year: {summary.year}")
        print(f"  Total members: {summary.total_members}")
        print(f"  Total XP: {summary.total_guild_xp:,}")
        print(f"  Total messages: {summary.total_messages:,}")
        print(f"  New members: {summary.new_members_count}")
        print()
        print(f"View your wrapped at: http://localhost:8000/wrapped/{settings.year}")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR during data collection")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return False


def main():
    """Entry point for the script."""

    # Check if .env file exists
    if not Path(".env").exists():
        print("❌ Error: .env file not found!")
        print()
        print("Please create a .env file based on .env.example")
        print("Copy .env.example to .env and fill in your API keys:")
        print("  - HYPIXEL_API_KEY")
        print("  - HYPIXEL_GUILD_ID")
        print("  - DISCORD_BOT_TOKEN")
        print("  - DISCORD_GUILD_ID")
        print("  - DISCORD_CHANNEL_IDS")
        print()
        return

    # Run the async function
    success = asyncio.run(fetch_all_data())

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
