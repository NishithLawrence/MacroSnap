"""
Unit tests for MacroSnap Coach API endpoints (/api/coach/context, /api/coach/chat).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

import profile_storage

client = TestClient(app)


def test_get_coach_context():
    response = client.get("/api/coach/context")
    assert response.status_code == 200
    data = response.json()
    assert "user_name" in data
    assert "target_calories" in data
    assert "consumed_calories" in data
    assert "remaining_calories" in data
    assert "target_protein" in data
    assert "consumed_protein" in data
    assert "remaining_protein" in data
    assert "today_meals" in data


def test_coach_context_personalization(tmp_path):
    orig_profile = profile_storage.PROFILE_FILE
    try:
        profile_storage.PROFILE_FILE = str(tmp_path / "profile.json")
        # 1. No profile exists -> fallback to neutral 'there'
        res1 = client.get("/api/coach/context")
        assert res1.status_code == 200
        assert res1.json()["user_name"] == "there"

        # 2. Profile with name -> returns personalized name
        profile_storage.save_profile({
            "name": "Sam Athlete",
            "age": 28,
            "sex": "Female",
            "height_cm": 170.0,
            "weight_kg": 65.0,
            "activity_level": "Moderately Active",
            "goal": "Fat Loss",
            "intensity": "Moderate"
        })
        res2 = client.get("/api/coach/context")
        assert res2.status_code == 200
        assert res2.json()["user_name"] == "Sam Athlete"

        # 3. Profile without name -> falls back to neutral 'there'
        profile_storage.save_profile({
            "age": 28,
            "sex": "Female",
            "height_cm": 170.0,
            "weight_kg": 65.0,
            "activity_level": "Moderately Active",
            "goal": "Fat Loss",
            "intensity": "Moderate"
        })
        res3 = client.get("/api/coach/context")
        assert res3.status_code == 200
        assert res3.json()["user_name"] == "there"
    finally:
        profile_storage.PROFILE_FILE = orig_profile


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
