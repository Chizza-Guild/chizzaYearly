"""
Main FastAPI application for Hypixel Guild Wrapped.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import wrapped, admin

# Create FastAPI app
app = FastAPI(
    title="Hypixel Guild Wrapped",
    description="Year-end wrapped for your Hypixel guild",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(wrapped.router)
app.include_router(admin.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Hypixel Guild Wrapped"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
