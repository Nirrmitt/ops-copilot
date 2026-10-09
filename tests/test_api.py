"""API smoke checks."""
from fastapi.testclient import TestClient

from app.api import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200


def test_empty_question_is_rejected() -> None:
    response = TestClient(app).post("/ask", json={"question": ""})
    assert response.status_code == 422
