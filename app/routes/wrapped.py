"""
Routes for the wrapped interface.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.analytics_service import AnalyticsService
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
analytics_service = AnalyticsService()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page with year selection."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "current_year": settings.year}
    )


@router.get("/wrapped/{year}", response_class=HTMLResponse)
async def wrapped(request: Request, year: int):
    """Main wrapped interface for a specific year."""
    summary = analytics_service.load_from_database(year)

    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No wrapped data found for {year}. Run the data collection script first."
        )

    return templates.TemplateResponse(
        "wrapped.html",
        {
            "request": request,
            "summary": summary,
            "year": year
        }
    )


@router.get("/api/stats/{year}")
async def get_stats(year: int):
    """JSON API endpoint for wrapped statistics."""
    summary = analytics_service.load_from_database(year)

    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No wrapped data found for {year}"
        )

    return summary
