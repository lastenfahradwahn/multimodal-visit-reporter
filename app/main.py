"""
Main FastAPI application for the Multimodal Visit Reporter.
"""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.routers.visits import router as visits_router

# Load environment variables early
load_dotenv()

app = FastAPI(
    title="Multimodal Visit Reporter",
    version="0.1.0",
    description="Extract structured visit reports from audio, image, or text input.",
)

# Include the visits router
app.include_router(visits_router)


@app.get("/")
async def root():
    """Root health-check endpoint."""
    return {"message": "Multimodal Visit Reporter API", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
