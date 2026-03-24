from datetime import datetime

from pydantic import BaseModel


class FinalizedPredictionOut(BaseModel):
    request_id: str
    original_text: str
    predicted_category: str
    final_category: str
    confidence: float
    priority: str
    needs_human_review: bool
    review_status: str
    model_version: str
    created_at: datetime
    reviewed_at: datetime | None


class EvaluationMetricsOut(BaseModel):
    total_finalized: int
    matched_predictions: int
    corrected_predictions: int
    agreement_rate: float

class CategoryEvaluationOut(BaseModel):
    predicted_category: str
    total_predictions: int
    matched_predictions: int
    corrected_predictions: int
    agreement_rate: float


class VersionMetricsOut(BaseModel):
    model_version: str
    total_finalized: int
    matched_predictions: int
    corrected_predictions: int
    agreement_rate: float


class VersionComparisonOut(BaseModel):
    baseline: VersionMetricsOut
    candidate: VersionMetricsOut
    agreement_rate_delta: float
    matched_predictions_delta: int
    corrected_predictions_delta: int
    improved: bool