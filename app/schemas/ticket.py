from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    text: str = Field(..., min_length=3)


class TicketOut(BaseModel):
    request_id: str
    category: str
    category_confidence: float
    priority: str
    latency_ms: float
    needs_human_review: bool
