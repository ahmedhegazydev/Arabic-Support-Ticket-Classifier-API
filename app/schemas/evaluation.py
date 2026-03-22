from datetime import datetime

from pydantic import BaseModel


class FinalizedPredictionOut(BaseModel):
    request_id: str
    original_text: str
    predicted_category: str
    final_category: str
    confidence: float
    priority: str
    needs_human_review: bool
    review_status: str
    model_version: str
    created_at: datetime
    reviewed_at: datetime | None