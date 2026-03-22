from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, func, select
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


def get_finalized_predictions(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[TicketPrediction]:
    stmt = (
        select(TicketPrediction)
        .where(TicketPrediction.final_category.is_not(None))
        .order_by(TicketPrediction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_evaluation_metrics(db: Session) -> dict:
    total_stmt = (
        select(func.count())
        .select_from(TicketPrediction)
        .where(TicketPrediction.final_category.is_not(None))
    )

    matched_stmt = (
        select(func.count())
        .select_from(TicketPrediction)
        .where(TicketPrediction.final_category.is_not(None))
        .where(TicketPrediction.predicted_category == TicketPrediction.final_category)
    )

    corrected_stmt = (
        select(func.count())
        .select_from(TicketPrediction)
        .where(TicketPrediction.final_category.is_not(None))
        .where(TicketPrediction.predicted_category != TicketPrediction.final_category)
    )

    total_finalized = db.scalar(total_stmt) or 0
    matched_predictions = db.scalar(matched_stmt) or 0
    corrected_predictions = db.scalar(corrected_stmt) or 0

    agreement_rate = (
        matched_predictions / total_finalized
        if total_finalized > 0
        else 0.0
    )

    return {
        "total_finalized": total_finalized,
        "matched_predictions": matched_predictions,
        "corrected_predictions": corrected_predictions,
        "agreement_rate": round(agreement_rate, 4),
    }

def get_evaluation_by_category(db: Session) -> list[dict]:
    stmt = (
        select(
            TicketPrediction.predicted_category.label("predicted_category"),
            func.count().label("total_predictions"),
            func.sum(
                (TicketPrediction.predicted_category == TicketPrediction.final_category).cast(Integer)
            ).label("matched_predictions"),
            func.sum(
                (TicketPrediction.predicted_category != TicketPrediction.final_category).cast(Integer)
            ).label("corrected_predictions"),
        )
        .where(TicketPrediction.final_category.is_not(None))
        .group_by(TicketPrediction.predicted_category)
        .order_by(func.count().desc())
    )

    rows = db.execute(stmt).all()

    results = []
    for row in rows:
        total_predictions = row.total_predictions or 0
        matched_predictions = row.matched_predictions or 0
        corrected_predictions = row.corrected_predictions or 0

        agreement_rate = (
            matched_predictions / total_predictions
            if total_predictions > 0
            else 0.0
        )

        results.append(
            {
                "predicted_category": row.predicted_category,
                "total_predictions": total_predictions,
                "matched_predictions": matched_predictions,
                "corrected_predictions": corrected_predictions,
                "agreement_rate": round(agreement_rate, 4),
            }
        )

    return results