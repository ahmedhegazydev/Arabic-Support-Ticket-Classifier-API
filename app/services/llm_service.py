from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TicketPrediction


def get_llm_second_opinion(
    db: Session,
    request_id: str,
    threshold: float = 0.80,
) -> dict | None:
    stmt = (
        select(
            TicketPrediction.request_id,
            TicketPrediction.original_text,
            TicketPrediction.predicted_category,
            TicketPrediction.confidence,
            TicketPrediction.needs_human_review,
            TicketPrediction.review_status,
            TicketPrediction.model_version,
        )
        .where(TicketPrediction.request_id == request_id)
    )

    row = db.execute(stmt).one_or_none()

    if row is None:
        return None

    should_use_llm = (
        row.confidence < threshold or row.needs_human_review
    )

    if not should_use_llm:
        return {
            "request_id": row.request_id,
            "baseline_prediction": row.predicted_category,
            "baseline_confidence": row.confidence,
            "model_version": row.model_version,
            "llm_enabled": False,
            "llm_suggested_category": None,
            "llm_reasoning": None,
            "recommended_final_action": "auto_accept",
        }

    # placeholder behavior for now
    return {
        "request_id": row.request_id,
        "baseline_prediction": row.predicted_category,
        "baseline_confidence": row.confidence,
        "model_version": row.model_version,
        "llm_enabled": True,
        "llm_suggested_category": row.predicted_category,
        "llm_reasoning": "LLM fallback placeholder: second-opinion integration not yet connected.",
        "recommended_final_action": "send_to_review",
    }