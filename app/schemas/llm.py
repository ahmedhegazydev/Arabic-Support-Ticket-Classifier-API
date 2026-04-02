from pydantic import BaseModel


class LLMSecondOpinionOut(BaseModel):
    request_id: str
    baseline_prediction: str
    baseline_confidence: float
    model_version: str
    llm_enabled: bool
    llm_suggested_category: str | None
    llm_reasoning: str | None
    recommended_final_action: str


class LLMParsedResponse(BaseModel):
    suggested_category: str
    reasoning: str