from fastapi import APIRouter, Depends, HTTPException, Response, Query
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
from app.schemas.confusion import (
    ConfusionPairItem,
    ConfusionPairExampleItem,
)

from app.services.inference_service import classify_ticket

from app.repositories.ticket_repository import (
    get_finalized_predictions,
    get_evaluation_metrics,
    get_evaluation_by_category,
    get_confusion_pairs,
     get_confusion_pair_examples,
     get_model_versions, 
     compare_model_versions, 
     get_low_confidence_tickets,
     get_low_confidence_summary, 
     get_threshold_sweep,
     get_review_recommendation
     
)

from app.schemas.evaluation import (
    EvaluationMetricsOut,
    FinalizedPredictionOut,
    CategoryEvaluationOut, 
    VersionComparisonOut, 
    LowConfidenceTicketItem, 
    LowConfidenceSummaryOut, 
    ThresholdSweepItemOut,
    ReviewRecommendationOut

)

from app.schemas.llm import LLMSecondOpinionOut
from app.services.llm_service import get_llm_second_opinion

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
def evaluation_metrics(
    model_version: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return get_evaluation_metrics(db, model_version=model_version)


@router.get("/evaluation/by-category", response_model=list[CategoryEvaluationOut])
def evaluation_by_category(
    model_version: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return get_evaluation_by_category(db, model_version=model_version)

@router.get("/evaluation/confusion-pairs", response_model=list[ConfusionPairItem])
def confusion_pairs(
    limit: int = Query(20, ge=1, le=100),
    model_version: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return get_confusion_pairs(
        db=db,
        limit=limit,
        model_version=model_version,
    )

    
@router.get(
    "/evaluation/confusion-pairs/examples",
    response_model=list[ConfusionPairExampleItem],
)
def confusion_pair_examples(
    predicted_category: str = Query(...),
    final_category: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    model_version: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return get_confusion_pair_examples(
        db=db,
        predicted_category=predicted_category,
        final_category=final_category,
        limit=limit,
        model_version=model_version,
    )

@router.get("/evaluation/model-versions", response_model=list[str])
def evaluation_model_versions(db: Session = Depends(get_db)):
    return get_model_versions(db)


@router.get("/evaluation/compare", response_model=VersionComparisonOut)
def evaluation_compare(
    baseline_version: str = Query(...),
    candidate_version: str = Query(...),
    db: Session = Depends(get_db),
):
    return compare_model_versions(
        db=db,
        baseline_version=baseline_version,
        candidate_version=candidate_version,
    )


@router.get(
    "/evaluation/low-confidence-tickets",
    response_model=list[LowConfidenceTicketItem],
)
def low_confidence_tickets(
    threshold: float = Query(0.80, gt=0.0, lt=1.0),
    limit: int = Query(20, ge=1, le=100),
    # model_version: str | None = Query(None),
    model_version: str | None = Query("v1"),
    finalized_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    return get_low_confidence_tickets(
        db=db,
        threshold=threshold,
        limit=limit,
        model_version=model_version,
        finalized_only=finalized_only,
    )

@router.get(
    "/evaluation/low-confidence-summary",
    response_model=LowConfidenceSummaryOut,
)
def low_confidence_summary(
    threshold: float = Query(0.80, gt=0.0, lt=1.0),
    model_version: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return get_low_confidence_summary(
        db=db,
        threshold=threshold,
        model_version=model_version,
    )

@router.get(
    "/evaluation/threshold-sweep",
    response_model=list[ThresholdSweepItemOut],
)
def threshold_sweep(
    model_version: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return get_threshold_sweep(
        db=db,
        model_version=model_version,
    )


@router.get(
    "/evaluation/review-recommendation/{request_id}",
    response_model=ReviewRecommendationOut,
)
def review_recommendation(
    request_id: str,
    threshold: float = Query(0.80, gt=0.0, lt=1.0),
    db: Session = Depends(get_db),
):
    result = get_review_recommendation(
        db=db,
        request_id=request_id,
        threshold=threshold,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Ticket prediction not found")

    return result


@router.get(
    "/postprocess/llm-second-opinion/{request_id}",
    response_model=LLMSecondOpinionOut,
)
def llm_second_opinion(
    request_id: str,
    threshold: float = Query(0.80, gt=0.0, lt=1.0),
    db: Session = Depends(get_db),
):
    result = get_llm_second_opinion(
        db=db,
        request_id=request_id,
        threshold=threshold,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Ticket prediction not found")

    return result