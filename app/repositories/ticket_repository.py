from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, func, select, desc
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


def get_evaluation_metrics(
    db: Session,
    model_version: str | None = None,
) -> dict:
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

    if model_version:
        total_stmt = total_stmt.where(TicketPrediction.model_version == model_version)
        matched_stmt = matched_stmt.where(TicketPrediction.model_version == model_version)
        corrected_stmt = corrected_stmt.where(TicketPrediction.model_version == model_version)

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

def get_evaluation_by_category(
    db: Session,
    model_version: str | None = None,
) -> list[dict]:
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
    )

    if model_version:
        stmt = stmt.where(TicketPrediction.model_version == model_version)

    stmt = (
        stmt.group_by(TicketPrediction.predicted_category)
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

def get_confusion_pairs(
    db: Session,
    limit: int = 20,
    model_version: str | None = None,
):
    stmt = (
        select(
            TicketPrediction.predicted_category.label("predicted_category"),
            TicketPrediction.final_category.label("final_category"),
            func.count().label("count"),
        )
        .where(TicketPrediction.final_category.is_not(None))
        .where(TicketPrediction.predicted_category != TicketPrediction.final_category)
    )

    if model_version:
        stmt = stmt.where(TicketPrediction.model_version == model_version)

    stmt = (
        stmt.group_by(
            TicketPrediction.predicted_category,
            TicketPrediction.final_category,
        )
        .order_by(desc("count"))
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return [
        {
            "predicted_category": row.predicted_category,
            "final_category": row.final_category,
            "count": row.count,
        }
        for row in rows
    ]


def get_confusion_pair_examples(
    db: Session,
    predicted_category: str,
    final_category: str,
    limit: int = 20,
    model_version: str | None = None,
):
    stmt = (
        select(
            TicketPrediction.request_id,
            TicketPrediction.original_text,
            TicketPrediction.predicted_category,
            TicketPrediction.final_category,
            TicketPrediction.confidence,
            TicketPrediction.review_status,
            TicketPrediction.reviewed_at,
            TicketPrediction.model_version,
        )
        .where(TicketPrediction.final_category.is_not(None))
        .where(TicketPrediction.predicted_category == predicted_category)
        .where(TicketPrediction.final_category == final_category)
    )

    if model_version:
        stmt = stmt.where(TicketPrediction.model_version == model_version)

    stmt = (
        stmt.order_by(TicketPrediction.reviewed_at.desc(), TicketPrediction.created_at.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return [
        {
            "request_id": row.request_id,
            "original_text": row.original_text,
            "predicted_category": row.predicted_category,
            "final_category": row.final_category,
            "confidence": row.confidence,
            "review_status": row.review_status,
            "reviewed_at": row.reviewed_at,
            "model_version": row.model_version,
        }
        for row in rows
    ]


def get_model_versions(db: Session) -> list[str]:
    stmt = (
        select(TicketPrediction.model_version)
        .distinct()
        .order_by(TicketPrediction.model_version.desc())
    )

    rows = db.execute(stmt).all()
    return [row.model_version for row in rows]


def compare_model_versions(
    db: Session,
    baseline_version: str,
    candidate_version: str,
) -> dict:
    baseline_metrics = get_evaluation_metrics(db, model_version=baseline_version)
    candidate_metrics = get_evaluation_metrics(db, model_version=candidate_version)

    agreement_rate_delta = round(
        candidate_metrics["agreement_rate"] - baseline_metrics["agreement_rate"],
        4,
    )

    matched_predictions_delta = (
        candidate_metrics["matched_predictions"] - baseline_metrics["matched_predictions"]
    )

    corrected_predictions_delta = (
        candidate_metrics["corrected_predictions"] - baseline_metrics["corrected_predictions"]
    )

    return {
        "baseline": {
            "model_version": baseline_version,
            **baseline_metrics,
        },
        "candidate": {
            "model_version": candidate_version,
            **candidate_metrics,
        },
        "agreement_rate_delta": agreement_rate_delta,
        "matched_predictions_delta": matched_predictions_delta,
        "corrected_predictions_delta": corrected_predictions_delta,
        "improved": agreement_rate_delta > 0,
    }

def get_low_confidence_tickets(
    db: Session,
    threshold: float = 0.80,
    limit: int = 20,
    model_version: str | None = None,
    finalized_only: bool = False,
) -> list[dict]:
    stmt = (
        select(
            TicketPrediction.request_id,
            TicketPrediction.original_text,
            TicketPrediction.predicted_category,
            TicketPrediction.final_category,
            TicketPrediction.confidence,
            TicketPrediction.needs_human_review,
            TicketPrediction.review_status,
            TicketPrediction.model_version,
            TicketPrediction.created_at,
            TicketPrediction.reviewed_at,
        )
        .where(TicketPrediction.confidence < threshold)
    )

    if model_version:
        stmt = stmt.where(TicketPrediction.model_version == model_version)

    if finalized_only:
        stmt = stmt.where(TicketPrediction.final_category.is_not(None))

    stmt = (
        stmt.order_by(TicketPrediction.confidence.asc(), TicketPrediction.created_at.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return [
        {
            "request_id": row.request_id,
            "original_text": row.original_text,
            "predicted_category": row.predicted_category,
            "final_category": row.final_category,
            "confidence": row.confidence,
            "needs_human_review": row.needs_human_review,
            "review_status": row.review_status,
            "model_version": row.model_version,
            "created_at": row.created_at,
            "reviewed_at": row.reviewed_at,
        }
        for row in rows
    ]


def get_low_confidence_summary(
    db: Session,
    threshold: float = 0.80,
    model_version: str | None = None,
) -> dict:
    base_stmt = (
        select(
            func.count().label("total_low_confidence"),
            func.sum(
                (TicketPrediction.final_category.is_not(None)).cast(Integer)
            ).label("finalized_low_confidence"),
            func.sum(
                (
                    (TicketPrediction.final_category.is_not(None)) &
                    (TicketPrediction.predicted_category == TicketPrediction.final_category)
                ).cast(Integer)
            ).label("matched_low_confidence"),
            func.sum(
                (
                    (TicketPrediction.final_category.is_not(None)) &
                    (TicketPrediction.predicted_category != TicketPrediction.final_category)
                ).cast(Integer)
            ).label("corrected_low_confidence"),
        )
        .where(TicketPrediction.confidence < threshold)
    )

    if model_version:
        base_stmt = base_stmt.where(TicketPrediction.model_version == model_version)

    row = db.execute(base_stmt).one()

    total_low_confidence = row.total_low_confidence or 0
    finalized_low_confidence = row.finalized_low_confidence or 0
    matched_low_confidence = row.matched_low_confidence or 0
    corrected_low_confidence = row.corrected_low_confidence or 0

    agreement_rate = (
        matched_low_confidence / finalized_low_confidence
        if finalized_low_confidence > 0
        else 0.0
    )

    correction_rate = (
        corrected_low_confidence / finalized_low_confidence
        if finalized_low_confidence > 0
        else 0.0
    )

    return {
        "threshold": threshold,
        "model_version": model_version,
        "total_low_confidence": total_low_confidence,
        "finalized_low_confidence": finalized_low_confidence,
        "matched_low_confidence": matched_low_confidence,
        "corrected_low_confidence": corrected_low_confidence,
        "agreement_rate": round(agreement_rate, 4),
        "correction_rate": round(correction_rate, 4),
    }


def get_threshold_sweep(
    db: Session,
    model_version: str | None = None,
    thresholds: list[float] | None = None,
) -> list[dict]:
    if thresholds is None:
        thresholds = [0.60, 0.70, 0.80, 0.90]

    results = []

    for threshold in thresholds:
        stmt = (
            select(
                func.count().label("total_below_threshold"),
                func.sum(
                    (TicketPrediction.final_category.is_not(None)).cast(Integer)
                ).label("finalized_below_threshold"),
                func.sum(
                    (
                        (TicketPrediction.final_category.is_not(None)) &
                        (TicketPrediction.predicted_category == TicketPrediction.final_category)
                    ).cast(Integer)
                ).label("matched_below_threshold"),
                func.sum(
                    (
                        (TicketPrediction.final_category.is_not(None)) &
                        (TicketPrediction.predicted_category != TicketPrediction.final_category)
                    ).cast(Integer)
                ).label("corrected_below_threshold"),
            )
            .where(TicketPrediction.confidence < threshold)
        )

        if model_version:
            stmt = stmt.where(TicketPrediction.model_version == model_version)

        row = db.execute(stmt).one()

        total_below_threshold = row.total_below_threshold or 0
        finalized_below_threshold = row.finalized_below_threshold or 0
        matched_below_threshold = row.matched_below_threshold or 0
        corrected_below_threshold = row.corrected_below_threshold or 0

        agreement_rate = (
            matched_below_threshold / finalized_below_threshold
            if finalized_below_threshold > 0
            else 0.0
        )

        correction_rate = (
            corrected_below_threshold / finalized_below_threshold
            if finalized_below_threshold > 0
            else 0.0
        )

        results.append(
            {
                "threshold": round(threshold, 2),
                "total_below_threshold": total_below_threshold,
                "finalized_below_threshold": finalized_below_threshold,
                "matched_below_threshold": matched_below_threshold,
                "corrected_below_threshold": corrected_below_threshold,
                "agreement_rate": round(agreement_rate, 4),
                "correction_rate": round(correction_rate, 4),
            }
        )

    return results