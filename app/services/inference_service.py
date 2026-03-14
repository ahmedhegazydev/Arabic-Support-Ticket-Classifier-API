import time
import uuid
from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.metrics import (
    CACHE_LOOKUP_LATENCY_MS,
    CACHE_MISS_COUNT,
    HUMAN_REVIEW_COUNT,
    REQUEST_COUNT,
    REQUEST_FAILURE_COUNT,
    REQUEST_LATENCY_MS,
)
from app.core.settings import settings
from app.models.classifier import get_classifier
from app.repositories.ticket_repository import create_ticket_prediction


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def predict_priority_by_rules(text: str) -> str:
    normalized = normalize_text(text)

    for keyword in settings.HIGH_PRIORITY_KEYWORDS:
        if keyword in normalized:
            return "High"

    for keyword in settings.MEDIUM_PRIORITY_KEYWORDS:
        if keyword in normalized:
            return "Medium"

    return "Low"


@lru_cache(maxsize=settings.CACHE_SIZE)
def cached_category_prediction(normalized_text: str):
    CACHE_MISS_COUNT.inc()

    logger.info(
        "event=cache_miss action=run_model text_hash=%s text_length=%s",
        hash(normalized_text),
        len(normalized_text),
    )

    classifier = get_classifier()
    result = classifier(
        normalized_text,
        settings.CATEGORIES,
        multi_label=False,
    )

    return {
        "category": result["labels"][0],
        "category_confidence": float(result["scores"][0]),
    }


def classify_ticket(text: str, db: Session):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    normalized_text = normalize_text(text)

    REQUEST_COUNT.inc()

    logger.info(
        "event=request_received request_id=%s text_length=%s",
        request_id,
        len(normalized_text),
    )

    try:
        before_cache = time.perf_counter()
        category_result = cached_category_prediction(normalized_text)
        cache_lookup_ms = (time.perf_counter() - before_cache) * 1000
        CACHE_LOOKUP_LATENCY_MS.observe(cache_lookup_ms)

        priority = predict_priority_by_rules(normalized_text)

        category_confidence = category_result["category_confidence"]
        needs_human_review = category_confidence < settings.CONFIDENCE_THRESHOLD

        if needs_human_review:
            HUMAN_REVIEW_COUNT.inc()

        latency_ms = (time.perf_counter() - start) * 1000
        REQUEST_LATENCY_MS.observe(latency_ms)

        result = {
            "request_id": request_id,
            "category": category_result["category"],
            "category_confidence": category_confidence,
            "priority": priority,
            "needs_human_review": needs_human_review,
            "latency_ms": round(latency_ms, 3),
            "model_version": settings.MODEL_VERSION,
        }

        create_ticket_prediction(
            db,
            request_id=request_id,
            original_text=text,
            normalized_text=normalized_text,
            predicted_category=category_result["category"],
            confidence=category_confidence,
            priority=priority,
            needs_human_review=needs_human_review,
            latency_ms=result["latency_ms"],
            model_version=settings.MODEL_VERSION,
        )

        logger.info(
            "event=request_completed request_id=%s category=%s category_confidence=%.4f priority=%s needs_human_review=%s threshold=%.2f latency_ms=%.3f cache_lookup_ms=%.3f model_version=%s",
            request_id,
            category_result["category"],
            category_confidence,
            priority,
            needs_human_review,
            settings.CONFIDENCE_THRESHOLD,
            latency_ms,
            cache_lookup_ms,
            settings.MODEL_VERSION,
        )

        return result

    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        REQUEST_FAILURE_COUNT.inc()
        REQUEST_LATENCY_MS.observe(latency_ms)

        logger.exception(
            "event=request_failed request_id=%s latency_ms=%.3f error=%s",
            request_id,
            latency_ms,
            str(e),
        )
        raise