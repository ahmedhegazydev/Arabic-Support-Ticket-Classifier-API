from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import TicketReview


def create_pending_review(db: Session, *, request_id: str) -> TicketReview:
    review = TicketReview(
        request_id=request_id,
        status="pending",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_pending_reviews(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[TicketReview]:
    stmt = (
        select(TicketReview)
        .where(TicketReview.status == "pending")
        .order_by(TicketReview.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_review_by_request_id(
    db: Session,
    *,
    request_id: str,
) -> Optional[TicketReview]:
    stmt = select(TicketReview).where(TicketReview.request_id == request_id)
    return db.scalar(stmt)


def resolve_review(
    db: Session,
    *,
    request_id: str,
    reviewed_category: str,
    reviewer_name: str,
    reviewer_notes: str | None = None,
) -> Optional[TicketReview]:
    review = get_review_by_request_id(db, request_id=request_id)
    if review is None:
        return None

    review.status = "resolved"
    review.reviewed_category = reviewed_category
    review.reviewer_name = reviewer_name
    review.reviewer_notes = reviewer_notes
    review.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(review)
    return review


def get_review_stats(db: Session) -> dict:
    total_stmt = select(func.count()).select_from(TicketReview)
    pending_stmt = select(func.count()).select_from(TicketReview).where(TicketReview.status == "pending")
    resolved_stmt = select(func.count()).select_from(TicketReview).where(TicketReview.status == "resolved")

    total = db.scalar(total_stmt) or 0
    pending = db.scalar(pending_stmt) or 0
    resolved = db.scalar(resolved_stmt) or 0

    return {
        "total": total,
        "pending": pending,
        "resolved": resolved,
    }