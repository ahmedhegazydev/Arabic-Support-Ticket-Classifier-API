from unittest.mock import patch
from app.services.inference_service import (
    normalize_text,
    predict_priority_by_rules,
)
from app.services.inference_service import classify_ticket


def test_normalize_text_removes_extra_spaces_and_lowercases():
    text = "   HELLO   World   "
    result = normalize_text(text)

    assert result == "hello world"


def test_predict_priority_by_rules_returns_high():
    text = "النظام متوقف ولا أستطيع الدخول"
    result = predict_priority_by_rules(text)

    assert result == "High"


def test_predict_priority_by_rules_returns_medium():
    text = "هناك خطأ بسيط وتأخير في النظام"
    result = predict_priority_by_rules(text)

    assert result == "Medium"


def test_predict_priority_by_rules_returns_low():
    text = "أريد الاستفسار عن حالة الطلب"
    result = predict_priority_by_rules(text)

    assert result == "Low"


def test_classify_ticket_sets_human_review_true_when_confidence_low():
    mock_prediction = {
        "category": "استفسار عام",
        "category_confidence": 0.20,
    }

    with patch(
        "app.services.inference_service.cached_category_prediction",
        return_value=mock_prediction,
    ):
        result = classify_ticket("أحتاج مساعدة في شيء غير واضح")

    assert result["needs_human_review"] is True


def test_classify_ticket_sets_human_review_false_when_confidence_high():
    mock_prediction = {
        "category": "مشكلة تسجيل دخول",
        "category_confidence": 0.90,
    }

    with patch(
        "app.services.inference_service.cached_category_prediction",
        return_value=mock_prediction,
    ):
        result = classify_ticket("لا أستطيع تسجيل الدخول والنظام متوقف")

    assert result["needs_human_review"] is False