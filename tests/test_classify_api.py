from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)


def test_classify_endpoint_success():
    mock_result = {
        "request_id": "test-id-123",
        "category": "مشكلة تسجيل دخول",
        "category_confidence": 0.82,
        "priority": "High",
        "needs_human_review": False,
        "latency_ms": 12.5,
    }

    with patch("app.api.routes.classify_ticket", return_value=mock_result):
        response = client.post(
            "/classify",
            json={"text": "لا أستطيع تسجيل الدخول والنظام متوقف"},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["request_id"] == "test-id-123"
    assert data["category"] == "مشكلة تسجيل دخول"
    assert data["priority"] == "High"
    assert data["needs_human_review"] is False
    assert isinstance(data["latency_ms"], float)


def test_classify_endpoint_validation_error_for_short_text():
    response = client.post(
        "/classify",
        json={"text": "ا"},
    )

    assert response.status_code == 422