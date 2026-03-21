from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
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
    review_status = "pending" if needs_human_review else "not_needed"
    final_category = None if needs_human_review else predicted_category

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
        final_category=final_category,
        review_status=review_status,
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def apply_prediction_review_resolution(
    prediction: TicketPrediction,
    *,
    final_category: str,
) -> TicketPrediction:
    prediction.final_category = final_category
    prediction.review_status = "resolved"
    prediction.reviewed_at = datetime.now(timezone.utc)
    return prediction



def get_prediction_by_request_id(
    db: Session,
    *,
    request_id: str,
) -> Optional[TicketPrediction]:
    stmt = select(TicketPrediction).where(TicketPrediction.request_id == request_id)
    return db.scalar(stmt)


def mark_prediction_as_reviewed(
    db: Session,
    *,
    request_id: str,
    final_category: str,
) -> Optional[TicketPrediction]:
    prediction = get_prediction_by_request_id(db, request_id=request_id)
    if prediction is None:
        return None

    apply_prediction_review_resolution(
        prediction,
        final_category=final_category,
    )

    db.commit()
    db.refresh(prediction)
    return prediction