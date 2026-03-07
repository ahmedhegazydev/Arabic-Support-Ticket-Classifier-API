import time
import uuid
from functools import lru_cache

from app.models.classifier import get_classifier
# from app.core.config import (
#     CATEGORIES,
#     HIGH_PRIORITY_KEYWORDS,
#     MEDIUM_PRIORITY_KEYWORDS,
#     CONFIDENCE_THRESHOLD,
# )
from app.core.settings import settings
from app.core.logging_config import logger


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


@lru_cache(maxsize=256)
def cached_category_prediction(normalized_text: str):
    logger.info(
        "event=cache_miss action=run_model text_hash=%s text_length=%s",
        hash(normalized_text),
        len(normalized_text),
    )

    classifier = get_classifier()
    result = classifier(normalized_text, settings.CATEGORIES, multi_label=False)

    return {
        "category": result["labels"][0],
        "category_confidence": float(result["scores"][0]),
    }


def classify_ticket(text: str):
    start = time.time()
    request_id = str(uuid.uuid4())
    normalized_text = normalize_text(text)

    logger.info(
        "event=request_received request_id=%s text_length=%s",
        request_id,
        len(normalized_text),
    )

    try:
        before_cache = time.time()
        category_result = cached_category_prediction(normalized_text)
        cache_lookup_ms = int((time.time() - before_cache) * 1000)

        priority = predict_priority_by_rules(normalized_text)

        category_confidence = category_result["category_confidence"]
        needs_human_review = category_confidence < settings.CONFIDENCE_THRESHOLD

        latency = int((time.time() - start) * 1000)

        logger.info(
            "event=request_completed request_id=%s category=%s category_confidence=%.4f priority=%s needs_human_review=%s threshold=%.2f latency_ms=%s cache_lookup_ms=%s",
            request_id,
            category_result["category"],
            category_confidence,
            priority,
            needs_human_review,
            settings.CONFIDENCE_THRESHOLD,
            latency,
            cache_lookup_ms,
        )

        return {
            "request_id": request_id,
            "category": category_result["category"],
            "category_confidence": category_confidence,
            "priority": priority,
            "needs_human_review": needs_human_review,
            "latency_ms": latency,
        }

    except Exception as e:
        latency = int((time.time() - start) * 1000)

        logger.exception(
            "event=request_failed request_id=%s latency_ms=%s error=%s",
            request_id,
            latency,
            str(e),
        )
        raise