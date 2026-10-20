"""
Unit tests for MacroSnap FastAPI History and Progress endpoints.
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from main import app
import meal_storage
import weight_storage
import profile_storage
import target_storage

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_storage():
    with tempfile.TemporaryDirectory() as test_dir:
        data_dir = os.path.join(test_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        orig_profile = profile_storage.PROFILE_FILE
        orig_target = target_storage.TARGET_FILE
        orig_meal = meal_storage.STORAGE_FILE
        orig_weight = weight_storage.WEIGHT_FILE

        profile_storage.PROFILE_FILE = os.path.join(data_dir, "profile.json")
        target_storage.TARGET_FILE = os.path.join(data_dir, "target_history.json")
        meal_storage.STORAGE_FILE = os.path.join(data_dir, "meals.json")
        weight_storage.WEIGHT_FILE = os.path.join(data_dir, "weight_history.json")

        yield

        profile_storage.PROFILE_FILE = orig_profile
        target_storage.TARGET_FILE = orig_target
        meal_storage.STORAGE_FILE = orig_meal
        weight_storage.WEIGHT_FILE = orig_weight


def test_get_meal_history():
    response = client.get("/api/meals/history")
    assert response.status_code == 200
    data = response.json()
    assert "dates" in data
    assert isinstance(data["dates"], list)


def test_create_update_delete_meal():
    # 1. Create a meal
    test_meal = {
        "meal_type": "Snack",
        "date": "2026-10-07",
        "foods": [
            {"name": "Apple", "portion": "1 medium", "calories": 95, "protein_g": 0.5, "carbs_g": 25, "fat_g": 0.3}
        ]
    }
    create_res = client.post("/api/meals", json=test_meal)
    assert create_res.status_code == 200
    created_data = create_res.json()
    meal_id = created_data["meal"]["meal_id"]
    assert meal_id is not None

    # 2. Update the meal
    updated_meal = {
        "meal_id": meal_id,
        "meal_type": "Snack",
        "date": "2026-10-07",
        "foods": [
            {"name": "Apple", "portion": "1 large", "calories": 120, "protein_g": 1, "carbs_g": 30, "fat_g": 0.5}
        ]
    }
    update_res = client.put(f"/api/meals/{meal_id}", json=updated_meal)
    assert update_res.status_code == 200

    # 3. Delete the meal
    del_res = client.delete(f"/api/meals/{meal_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"

    # Delete non-existent meal returns 404
    del_fail = client.delete(f"/api/meals/non_existent_id_9999")
    assert del_fail.status_code == 404


def test_get_progress_analytics():
    response = client.get("/api/progress/analytics?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["days_period"] == 7
    assert "consistency_pct" in data
    assert "averages" in data
    assert "cal_adherence" in data
    assert "p_adherence" in data
    assert "interpretation" in data
    assert "targets" in data


def test_log_weight():
    response = client.post("/api/progress/weight", json={"weight_kg": 74.5})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "weight_change" in data


def test_get_profile():
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "active_plan" in data
    assert "options" in data
    assert "goals" in data["options"]
    assert "activity_levels" in data["options"]


def test_preview_profile_plan():
    payload = {
        "age": 28,
        "sex": "Female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Aggressive"
    }
    response = client.post("/api/profile/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "current_plan" in data
    assert "proposed_plan" in data
    assert data["proposed_plan"]["target_calories"] > 0
    assert data["proposed_plan"]["goal"] == "Fat Loss"
    assert data["proposed_plan"]["intensity"] == "Aggressive"

    # Test invalid payload fails validation with 400
    invalid_payload = {**payload, "age": -5}
    invalid_res = client.post("/api/profile/preview", json=invalid_payload)
    assert invalid_res.status_code == 400


def test_apply_profile_plan():
    payload = {
        "age": 30,
        "sex": "Male",
        "height_cm": 180.0,
        "weight_kg": 82.0,
        "activity_level": "Very Active",
        "goal": "Lean Bulk",
        "intensity": "Moderate surplus"
    }
    response = client.post("/api/profile/apply", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "target_snapshot" in data
    assert data["target_snapshot"]["calorie_target"] > 0
    assert data["target_snapshot"]["weight_kg"] == 82.0

    # Verify profile was updated
    get_res = client.get("/api/profile")
    assert get_res.status_code == 200
    prof = get_res.json()["profile"]
    assert prof["age"] == 30
    assert prof["weight_kg"] == 82.0
    assert prof["goal"] == "Lean Bulk"


def test_profile_preview_and_apply_with_name():
    """Verify preview and apply endpoints handle optional name field seamlessly."""
    payload = {
        "name": "Morgan Davis",
        "age": 27,
        "sex": "Female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    # 1. Preview
    prev_res = client.post("/api/profile/preview", json=payload)
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["proposed_profile"]["name"] == "Morgan Davis"

    # 2. Apply
    apply_res = client.post("/api/profile/apply", json=payload)
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    assert apply_data["status"] == "ok"
    assert apply_data["profile"]["name"] == "Morgan Davis"

    # 3. GET profile
    get_res = client.get("/api/profile")
    assert get_res.status_code == 200
    assert get_res.json()["profile"]["name"] == "Morgan Davis"

    # 4. Coach context
    coach_res = client.get("/api/coach/context")
    assert coach_res.status_code == 200
    assert coach_res.json()["user_name"] == "Morgan Davis"


def test_meal_totals_update_after_edit_and_delete():
    """Verify editing and deleting meals updates daily totals correctly."""
    meal_date = "2026-10-15"
    meal_payload = {
        "meal_type": "Lunch",
        "date": meal_date,
        "foods": [
            {"name": "Chicken & Rice", "portion": "300g", "calories": 500, "protein_g": 40, "carbs_g": 60, "fat_g": 10}
        ]
    }
    create_res = client.post("/api/meals", json=meal_payload)
    assert create_res.status_code == 200
    meal_id = create_res.json()["meal"]["meal_id"]

    # Check totals before edit
    hist1 = client.get("/api/meals/history").json()
    day_group = next(d for d in hist1["dates"] if d["date"] == meal_date)
    assert day_group["totals"]["calories"] == 500
    assert day_group["totals"]["protein_g"] == 40

    # Edit meal to higher calories and protein
    edit_payload = {
        "meal_id": meal_id,
        "meal_type": "Lunch",
        "date": meal_date,
        "foods": [
            {"name": "Chicken & Rice Extra", "portion": "400g", "calories": 650, "protein_g": 55, "carbs_g": 75, "fat_g": 12}
        ]
    }
    edit_res = client.put(f"/api/meals/{meal_id}", json=edit_payload)
    assert edit_res.status_code == 200

    # Verify totals updated
    hist2 = client.get("/api/meals/history").json()
    day_group2 = next(d for d in hist2["dates"] if d["date"] == meal_date)
    assert day_group2["totals"]["calories"] == 650
    assert day_group2["totals"]["protein_g"] == 55

    # Delete meal
    del_res = client.delete(f"/api/meals/{meal_id}")
    assert del_res.status_code == 200

    # Verify totals reset/removed
    hist3 = client.get("/api/meals/history").json()
    matching_days = [d for d in hist3["dates"] if d["date"] == meal_date]
    assert len(matching_days) == 0


def test_meal_scan_failure_does_not_persist_meal():
    """Verify meal scanning failures or scans never create fake nutrition entries."""
    meals_before = meal_storage.load_meals()

    # Attempting to scan non-image should fail with 400
    files = {"file": ("test.txt", b"plain text", "text/plain")}
    res = client.post("/api/meals/scan", files=files)
    assert res.status_code == 400

    # Storage must remain untouched
    meals_after = meal_storage.load_meals()
    assert len(meals_after) == len(meals_before)


def test_profile_preview_does_not_modify_saved_data():
    """Verify profile previews do not modify saved data."""
    # Ensure baseline profile
    initial_profile = {
        "age": 25,
        "sex": "Male",
        "height_cm": 178.0,
        "weight_kg": 75.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    profile_storage.save_profile(initial_profile)

    # Preview radically different profile
    preview_payload = {
        "age": 55,
        "sex": "Female",
        "height_cm": 150.0,
        "weight_kg": 99.0,
        "activity_level": "Sedentary",
        "goal": "Fat Loss",
        "intensity": "Aggressive"
    }
    prev_res = client.post("/api/profile/preview", json=preview_payload)
    assert prev_res.status_code == 200

    # Saved profile must remain strictly equal to initial
    saved = profile_storage.load_profile()
    assert saved["age"] == 25
    assert saved["sex"] == "Male"
    assert saved["weight_kg"] == 75.0


