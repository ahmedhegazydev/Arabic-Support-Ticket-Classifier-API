from fastapi import APIRouter, Depends, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.review_repository import (
    get_pending_reviews,
    get_pending_reviews_with_predictions, 
    resolve_review,
    get_review_stats,
)
from app.schemas.ticket import TicketIn, TicketOut
from app.schemas.review import (
    ReviewQueueItemOut,
    ReviewQueueDetailedItemOut, 
    ReviewResolutionIn,
    ReviewResolutionOut,
    ReviewStatsOut
)

from app.services.inference_service import classify_ticket

from app.repositories.ticket_repository import get_finalized_predictions
from app.schemas.evaluation import FinalizedPredictionOut

from app.repositories.ticket_repository import (
    get_evaluation_metrics,
    get_finalized_predictions,
)
from app.schemas.evaluation import (
    EvaluationMetricsOut,
    FinalizedPredictionOut,
)


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.post("/classify", response_model=TicketOut)
def classify(ticket: TicketIn, db: Session = Depends(get_db)):
    result = classify_ticket(ticket.text, db=db)
    return result

# @router.get("/review/queue", response_model=list[ReviewQueueItemOut])
# def review_queue(db: Session = Depends(get_db)):
#     reviews = get_pending_reviews(db)
#     return reviews

@router.get("/review/queue", response_model=list[ReviewQueueDetailedItemOut])
def review_queue(db: Session = Depends(get_db)):
    rows = get_pending_reviews_with_predictions(db)

    return [
        ReviewQueueDetailedItemOut(
            request_id=review.request_id,
            status=review.status,
            created_at=review.created_at,
            original_text=prediction.original_text,
            predicted_category=prediction.predicted_category,
            confidence=prediction.confidence,
            priority=prediction.priority,
            needs_human_review=prediction.needs_human_review,
            model_version=prediction.model_version,
        )
        for review, prediction in rows
    ]

@router.post("/review/{request_id}/resolve", response_model=ReviewResolutionOut)
def resolve_review_endpoint(
    request_id: str,
    payload: ReviewResolutionIn,
    db: Session = Depends(get_db),
):
    review = resolve_review(
        db,
        request_id=request_id,
        reviewed_category=payload.reviewed_category,
        reviewer_name=payload.reviewer_name,
        reviewer_notes=payload.reviewer_notes,
    )

    if review is None:
        raise HTTPException(status_code=404, detail="Review item not found")

    return review

@router.get("/review/stats", response_model=ReviewStatsOut)
def review_stats(db: Session = Depends(get_db)):
    stats = get_review_stats(db)
    return stats


@router.get("/evaluation/reviewed-dataset", response_model=list[FinalizedPredictionOut])
def reviewed_dataset(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    rows = get_finalized_predictions(db, limit=limit, offset=offset)
    return rows

@router.get("/evaluation/metrics", response_model=EvaluationMetricsOut)
def evaluation_metrics(db: Session = Depends(get_db)):
    return get_evaluation_metrics(db)

