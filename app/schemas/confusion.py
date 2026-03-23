from pydantic import BaseModel
from datetime import datetime

class ConfusionPairItem(BaseModel):
    predicted_category: str
    final_category: str
    count: int


class ConfusionPairExampleItem(BaseModel):
    request_id: str
    original_text: str
    predicted_category: str
    final_category: str
    confidence: float
    review_status: str
    reviewed_at: datetime | None