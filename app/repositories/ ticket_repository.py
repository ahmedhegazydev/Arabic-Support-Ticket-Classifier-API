from sqlalchemy.orm import Session

from app.db.models import TicketPrediction


def create_ticket_prediction(
    db: Session,
    *,
    request_id: str,
    original_text: str,
    normalized_text: str,
    predicted_category: str,
    confidence: float,
    priority: str,
    needs_human_review: bool,
    latency_ms: float,
    model_version: str,
) -> TicketPrediction:
    record = TicketPrediction(
        request_id=request_id,
        original_text=original_text,
        normalized_text=normalized_text,
        predicted_category=predicted_category,
        confidence=confidence,
        priority=priority,
        needs_human_review=needs_human_review,
        latency_ms=latency_ms,
        model_version=model_version,
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record