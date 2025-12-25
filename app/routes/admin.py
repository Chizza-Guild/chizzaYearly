"""
Admin routes for data refresh and management.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.config import settings
from app.services.hypixel_service import HypixelService
from app.services.discord_service import DiscordService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin")
security = HTTPBasic()

# Initialize services that don't require Discord
hypixel_service = HypixelService()
analytics_service = AnalyticsService()


def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin password."""
    if credentials.password != settings.admin_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


@router.post("/refresh")
async def refresh_data(authorized: bool = Depends(verify_password)):
    """
    Trigger a full data refresh.
    This will fetch data from both Hypixel and Discord APIs,
    recalculate statistics, and update the database.
    """
    try:
        # Fetch Hypixel data
        print("Fetching Hypixel guild data...")
        guild_response = await hypixel_service.fetch_guild_data()

        if not guild_response.guild:
            raise HTTPException(status_code=500, detail="Failed to fetch guild data")

        # Calculate XP stats
        print("Calculating XP statistics...")
        xp_stats = hypixel_service.calculate_yearly_xp(
            guild_response.guild.members, settings.year
        )

        # Enrich with usernames
        print("Fetching player usernames...")
        xp_stats = await hypixel_service.enrich_members_with_usernames(xp_stats)

        # Fetch Discord data (if enabled)
        if settings.discord_enabled:
            print("Fetching Discord messages (this may take a while)...")
            # Initialize Discord service only when needed
            discord_service = DiscordService()
            messages = await discord_service.fetch_all_messages(
                settings.start_date, settings.end_date
            )

            # Calculate Discord stats
            print("Calculating Discord statistics...")
            discord_stats = discord_service.calculate_stats(messages)
        else:
            print("Discord integration disabled, using empty stats...")
            from app.models.discord import DiscordStats
            discord_stats = DiscordStats()
            messages = []

        # Combine and save
        print("Combining statistics...")
        summary = analytics_service.combine_stats(
            xp_stats, discord_stats, guild_response.guild.name, guild_response.guild.exp, messages
        )

        print("Saving to database...")
        analytics_service.save_to_database(summary)

        return {
            "success": True,
            "message": f"Data refreshed successfully for {settings.year}",
            "stats": {
                "total_members": summary.total_members,
                "total_xp": summary.total_guild_xp,
                "total_messages": summary.total_messages,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing data: {str(e)}")
