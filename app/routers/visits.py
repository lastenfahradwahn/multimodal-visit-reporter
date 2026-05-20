"""
Router providing visit extraction, creation, and listing endpoints.
"""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.models import Visit
from app.services.ai import (
    extract_from_image,
    extract_from_text,
    transcribe_audio,
)
from app.services.storage import load_visits, save_visit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visits", tags=["visits"])

# ---------------------------------------------------------------------------
# Request body for the POST / endpoint
# ---------------------------------------------------------------------------
class VisitCreate(BaseModel):
    """Data required to create a new visit (received from the UI after extraction)."""
    customer_name: str | None = None
    company: str | None = None
    visit_date: str | None = None
    topics: list[str] = []
    action_items: list[str] = []
    sentiment: Literal["positive", "neutral", "negative"] | None = None
    raw_input_type: Literal["audio", "image", "text"]


# ---------------------------------------------------------------------------
# Extraction endpoint
# ---------------------------------------------------------------------------
@router.post("/extract")
async def extract_visit(
    input_type: Annotated[Literal["audio", "image", "text"], Form()],
    file: UploadFile = File(...),
):
    """
    Accept an uploaded file (audio, image, or text) and return a structured
    visit report. The report is not saved; the client can edit it before
    calling POST /api/visits/ to persist.
    """
    # Validate input_type
    if input_type not in {"audio", "image", "text"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input_type '{input_type}'. Must be one of: audio, image, text",
        )

    temp_path = None
    try:
        # Save uploaded file to a temporary location
        suffix = Path(file.filename).suffix if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            shutil.copyfileobj(file.file, tmp)

        # Process according to input type
        if input_type == "text":
            text = file.file.read().decode("utf-8")  # read from upload buffer
            report = extract_from_text(text)
        elif input_type == "audio":
            transcript = transcribe_audio(str(temp_path))
            report = extract_from_text(transcript)
        elif input_type == "image":
            report = extract_from_image(str(temp_path))

        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Extraction failed: {str(e)}",
        )
    except Exception as e:
        logger.exception("Unexpected error during extraction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during extraction.",
        )
    finally:
        # Clean up temporary file
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Create (save) endpoint
# ---------------------------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_visit(visit_data: VisitCreate):
    """
    Persist a new visit report. The client sends the extracted (or edited)
    fields, and the server generates an ID and timestamp.
    """
    try:
        visit = Visit(
            **visit_data.model_dump(),
        )
        saved = save_visit(visit.model_dump())
        return saved
    except Exception as e:
        logger.exception("Error saving visit")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save the visit.",
        )


# ---------------------------------------------------------------------------
# List all visits
# ---------------------------------------------------------------------------
@router.get("/")
async def list_visits():
    """Return all saved visit reports, latest first."""
    visits = load_visits()
    # Reverse to show newest first (optional)
    return visits[::-1]
