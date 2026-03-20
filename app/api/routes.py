from fastapi import APIRouter, Depends, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.review_repository import (
    get_pending_reviews,
    resolve_review,
)
from app.schemas.review import ReviewQueueItemOut
from app.schemas.ticket import TicketIn, TicketOut
from app.services.inference_service import classify_ticket

from app.schemas.review import (
    ReviewQueueItemOut,
    ReviewResolutionIn,
    ReviewResolutionOut,
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

@router.get("/review/queue", response_model=list[ReviewQueueItemOut])
def review_queue(db: Session = Depends(get_db)):
    reviews = get_pending_reviews(db)
    return reviews

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