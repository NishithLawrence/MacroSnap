import pytest
import json
from fastapi.testclient import TestClient
from backend.main import app

import profile_storage
import target_storage

from backend.auth import create_access_token

client = TestClient(app)
client.headers["Authorization"] = f"Bearer {create_access_token()}"


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


def test_coach_context_current_format_snapshot(tmp_path, monkeypatch):
    """1. A valid current-format snapshot (calorie_target, protein_target, etc.)."""
    p_file = str(tmp_path / "profile.json")
    t_file = str(tmp_path / "target_history.json")
    monkeypatch.setattr(profile_storage, "PROFILE_FILE", p_file)
    monkeypatch.setattr(target_storage, "TARGET_FILE", t_file)

    profile_storage.save_profile({
        "name": "Test User",
        "age": 25,
        "sex": "Female",
        "height_cm": 165.0,
        "weight_kg": 58.0,
        "activity_level": "Lightly Active",
        "goal": "Maintenance",
        "intensity": "Maintenance"
    })

    with open(t_file, "w", encoding="utf-8") as f:
        json.dump({
            "snapshots": [{
                "snapshot_id": "snap-cur-1",
                "effective_date": "2026-10-20",
                "timestamp": "2026-10-20T10:00:00",
                "calorie_target": 1850,
                "protein_target": 115,
                "carbs_target": 220,
                "fat_target": 55,
            }]
        }, f)

    res = client.get("/api/coach/context")
    assert res.status_code == 200
    data = res.json()
    assert data["target_calories"] == 1850
    assert data["target_protein"] == 115
    assert data["target_carbs"] == 220
    assert data["target_fat"] == 55


def test_coach_context_legacy_format_snapshot(tmp_path, monkeypatch):
    """2. A valid legacy-format snapshot (target_calories, protein_g, etc.)."""
    p_file = str(tmp_path / "profile.json")
    t_file = str(tmp_path / "target_history.json")
    monkeypatch.setattr(profile_storage, "PROFILE_FILE", p_file)
    monkeypatch.setattr(target_storage, "TARGET_FILE", t_file)

    profile_storage.save_profile({
        "name": "Legacy User",
        "age": 30,
        "sex": "Male",
        "height_cm": 178.0,
        "weight_kg": 75.0,
        "activity_level": "Moderately Active",
        "goal": "Maintenance",
        "intensity": "Maintenance"
    })

    with open(t_file, "w", encoding="utf-8") as f:
        json.dump({
            "snapshots": [{
                "snapshot_id": "snap-leg-1",
                "effective_date": "2026-10-20",
                "timestamp": "2026-10-20T10:00:00",
                "target_calories": 1950,
                "protein_g": 135,
                "carbs_g": 210,
                "fat_g": 62,
            }]
        }, f)

    res = client.get("/api/coach/context")
    assert res.status_code == 200
    data = res.json()
    assert data["target_calories"] == 1950
    assert data["target_protein"] == 135
    assert data["target_carbs"] == 210
    assert data["target_fat"] == 62


def test_coach_context_snapshot_missing_fields_recalculated_from_profile(tmp_path, monkeypatch):
    """3. A snapshot missing required target fields: successfully recovers targets from active profile."""
    p_file = str(tmp_path / "profile.json")
    t_file = str(tmp_path / "target_history.json")
    monkeypatch.setattr(profile_storage, "PROFILE_FILE", p_file)
    monkeypatch.setattr(target_storage, "TARGET_FILE", t_file)

    profile_storage.save_profile({
        "name": "Recomp User",
        "age": 30,
        "sex": "Female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "Lightly Active",
        "goal": "Fat Loss",
        "intensity": "Slow"
    })

    # Snapshot with missing calorie/macro fields
    with open(t_file, "w", encoding="utf-8") as f:
        json.dump({
            "snapshots": [{
                "snapshot_id": "snap-broken",
                "effective_date": "2026-10-20",
                "timestamp": "2026-10-20T10:00:00",
                "weight_kg": 60.0,
            }]
        }, f)

    res = client.get("/api/coach/context")
    assert res.status_code == 200
    data = res.json()
    # Case 3 expected target is 1634 kcal (never arbitrary 2380)
    assert data["target_calories"] == 1634
    assert data["target_protein"] == 108
    assert data["target_fat"] == 46
    assert data["target_carbs"] == 197


def test_coach_context_failed_plan_calculation(tmp_path, monkeypatch):
    """4. A failed plan calculation returns HTTP 422, never fabricated defaults."""
    p_file = str(tmp_path / "profile.json")
    t_file = str(tmp_path / "target_history.json")
    monkeypatch.setattr(profile_storage, "PROFILE_FILE", p_file)
    monkeypatch.setattr(target_storage, "TARGET_FILE", t_file)

    # Save a profile that has invalid values that will cause calculate_full_plan to fail
    with open(p_file, "w", encoding="utf-8") as f:
        json.dump({
            "name": "Corrupt Profile",
            "age": 25,
            "sex": "Male",
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "activity_level": "Invalid Level",
            "goal": "Invalid Goal",
            "intensity": "Invalid Intensity"
        }, f)

    # Empty target snapshot
    with open(t_file, "w", encoding="utf-8") as f:
        json.dump({"snapshots": []}, f)

    # load_profile() will fail validation or return None, or if forced, calculate_full_plan fails
    monkeypatch.setattr(profile_storage, "load_profile", lambda: {
        "name": "Corrupt",
        "age": 25,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "activity_level": "Nonexistent",
        "goal": "Nonexistent",
        "intensity": "Nonexistent"
    })

    res = client.get("/api/coach/context")
    assert res.status_code == 422
    assert "unavailable" in res.json()["detail"].lower()


def test_coach_context_normal_response(tmp_path, monkeypatch):
    """5. A normal Coach-context response returns full metrics cleanly."""
    p_file = str(tmp_path / "profile.json")
    t_file = str(tmp_path / "target_history.json")
    monkeypatch.setattr(profile_storage, "PROFILE_FILE", p_file)
    monkeypatch.setattr(target_storage, "TARGET_FILE", t_file)

    profile_storage.save_profile({
        "name": "Dana Active",
        "age": 24,
        "sex": "Female",
        "height_cm": 168.0,
        "weight_kg": 62.0,
        "activity_level": "Moderately Active",
        "goal": "Maintenance",
        "intensity": "Maintenance"
    })

    res = client.get("/api/coach/context")
    assert res.status_code == 200
    data = res.json()
    assert data["has_profile"] is True
    assert data["user_name"] == "Dana Active"
    assert data["target_calories"] > 0
    assert data["target_protein"] > 0
    assert data["target_fat"] > 0
    assert data["target_carbs"] > 0


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

