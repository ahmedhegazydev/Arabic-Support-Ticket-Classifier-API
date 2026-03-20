from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.review_repository import get_pending_reviews
from app.schemas.review import ReviewQueueItemOut
from app.schemas.ticket import TicketIn, TicketOut
from app.services.inference_service import classify_ticket

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