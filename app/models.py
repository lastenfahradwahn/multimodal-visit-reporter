"""
Pydantic data model for a customer visit report.
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Visit(BaseModel):
    """Canonical schema for a single customer visit report."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    customer_name: str | None = None
    company: str | None = None
    visit_date: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    )
    topics: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    sentiment: Literal["positive", "neutral", "negative"] | None = None
    raw_input_type: Literal["audio", "image", "text"]
    created_at: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
