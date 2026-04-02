import json
from typing import Iterable

from app.schemas.llm import LLMParsedResponse


ALLOWED_CATEGORIES = [
    "billing",
    "refund",
    "login_issue",
    "account_access",
    "technical_support",
]


def build_llm_classification_prompt(
    ticket_text: str,
    baseline_prediction: str,
    confidence: float,
    allowed_categories: Iterable[str] = ALLOWED_CATEGORIES,
) -> str:
    categories_text = "\n".join(f"- {cat}" for cat in allowed_categories)

    return f"""
You are assisting an Arabic support ticket classification system.

Allowed categories:
{categories_text}

Ticket text:
\"\"\"{ticket_text}\"\"\"

Baseline predicted category:
{baseline_prediction}

Baseline confidence:
{confidence}

Return valid JSON only in this format:
{{
  "suggested_category": "one of the allowed categories",
  "reasoning": "short explanation"
}}
""".strip()


def parse_llm_response(raw_text: str) -> LLMParsedResponse:
    data = json.loads(raw_text)

    suggested_category = data["suggested_category"]
    reasoning = data["reasoning"]

    if suggested_category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category returned by LLM: {suggested_category}")

    return LLMParsedResponse(
        suggested_category=suggested_category,
        reasoning=reasoning,
    )

def call_llm_provider(prompt: str) -> str:
    """
    Temporary provider stub.
    Replace this with a real LLM API call later.
    """
    return json.dumps(
        {
            "suggested_category": "login_issue",
            "reasoning": "Temporary stub response for testing integration."
        }
    )