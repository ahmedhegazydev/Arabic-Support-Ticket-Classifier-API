from datetime import datetime

from pydantic import BaseModel, Field


class ReviewQueueItemOut(BaseModel):
    request_id: str
    status: str
    created_at: datetime


class ReviewQueueDetailedItemOut(BaseModel):
    request_id: str
    status: str
    created_at: datetime
    original_text: str
    predicted_category: str
    confidence: float
    priority: str
    needs_human_review: bool
    model_version: str


class ReviewResolutionIn(BaseModel):
    reviewed_category: str = Field(..., min_length=2)
    reviewer_name: str = Field(..., min_length=2)
    reviewer_notes: str | None = None


class ReviewResolutionOut(BaseModel):
    request_id: str
    status: str
    reviewed_category: str | None
    reviewer_name: str | None
    reviewer_notes: str | None
    created_at: datetime
    reviewed_at: datetime | None


class ReviewStatsOut(BaseModel):
    total: int
    pending: int
    resolved: int