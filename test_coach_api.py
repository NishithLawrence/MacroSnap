"""
Unit tests for MacroSnap Coach API endpoints (/api/coach/context, /api/coach/chat).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_coach_context():
    response = client.get("/api/coach/context")
    assert response.status_code == 200
    data = response.json()
    assert "target_calories" in data
    assert "consumed_calories" in data
    assert "remaining_calories" in data
    assert "target_protein" in data
    assert "consumed_protein" in data
    assert "remaining_protein" in data
    assert "today_meals" in data


def test_coach_chat_missing_message():
    response = client.post("/api/coach/chat", json={})
    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()


def test_coach_chat_valid_payload():
    response = client.post("/api/coach/chat", json={"message": "What should I eat for dinner?"})
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "response" in data
