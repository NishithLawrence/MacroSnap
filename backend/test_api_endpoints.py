"""
Unit tests for MacroSnap FastAPI History and Progress endpoints.
"""

import pytest
import os
import json
import tempfile
from fastapi.testclient import TestClient
from main import app
import meal_storage
import weight_storage
import profile_storage
import target_storage

from auth import create_access_token

client = TestClient(app)
client.headers["Authorization"] = f"Bearer {create_access_token()}"


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


def test_preview_apply_calculation_parity_and_error_handling():
    """Verify preview and apply endpoints have exact calculation parity and return 400 for invalid/infeasible inputs."""
    payload = {
        "name": "Parity User",
        "age": 29,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 72.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Slow"
    }

    # 1. Preview
    prev_res = client.post("/api/profile/preview", json=payload)
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    proposed = prev_data["proposed_plan"]

    # 2. Apply
    apply_res = client.post("/api/profile/apply", json=payload)
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    snapshot = apply_data["target_snapshot"]

    # Exact parity check
    assert proposed["target_calories"] == snapshot["calorie_target"]
    assert proposed["protein_g"] == snapshot["protein_target"]
    assert proposed["carbs_g"] == snapshot["carbs_target"]
    assert proposed["fat_g"] == snapshot["fat_target"]

    # 3. Client error handling (HTTP 400, never 500) for out-of-bounds or non-finite inputs
    bad_payloads = [
        {**payload, "age": 15},            # Underage (<18)
        {**payload, "height_cm": 50.0},     # Unrealistic height
        {**payload, "weight_kg": 15.0},     # Unrealistic weight
        {**payload, "age": "not-a-number"}, # Non-numeric
    ]
    for bad in bad_payloads:
        p_res = client.post("/api/profile/preview", json=bad)
        assert p_res.status_code == 400
        a_res = client.post("/api/profile/apply", json=bad)
        assert a_res.status_code == 400


def test_apply_profile_disk_failure_returns_500_and_no_partial_snapshot(monkeypatch):
    """Verify simulated profile disk-write failure returns HTTP 500 and prevents partial snapshot creation."""
    payload = {
        "name": "Disk Failure User",
        "age": 28,
        "sex": "Female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Slow"
    }

    initial_snapshots_count = len(target_storage.load_target_snapshots())

    # Simulate disk failure on profile saving
    monkeypatch.setattr(profile_storage, "save_profile", lambda data: False)

    res = client.post("/api/profile/apply", json=payload)
    assert res.status_code == 500
    assert "Failed to save profile to disk" in res.json()["detail"]

    # Target snapshots must not have been created
    final_snapshots_count = len(target_storage.load_target_snapshots())
    assert final_snapshots_count == initial_snapshots_count


def test_apply_snapshot_disk_failure_rolls_back_profile_and_returns_500(monkeypatch):
    """Verify failed snapshot creation rolls back profile updates and returns HTTP 500."""
    initial_payload = {
        "name": "Stable User",
        "age": 30,
        "sex": "Male",
        "height_cm": 178.0,
        "weight_kg": 75.0,
        "activity_level": "Moderately Active",
        "goal": "Maintenance",
        "intensity": "Maintenance"
    }
    init_res = client.post("/api/profile/apply", json=initial_payload)
    assert init_res.status_code == 200

    # Simulate snapshot creation failure
    monkeypatch.setattr(target_storage, "create_target_snapshot", lambda plan, effective_date=None: (False, None))

    attempted_payload = {
        "name": "Corrupted User",
        "age": 35,
        "sex": "Male",
        "height_cm": 182.0,
        "weight_kg": 85.0,
        "activity_level": "Very Active",
        "goal": "Lean Bulk",
        "intensity": "Moderate surplus"
    }
    fail_res = client.post("/api/profile/apply", json=attempted_payload)
    assert fail_res.status_code == 500
    assert "Failed to create target snapshot" in fail_res.json()["detail"]

    # Verify profile was rolled back to Stable User, not left in the attempted state
    prof_res = client.get("/api/profile")
    assert prof_res.status_code == 200
    current_prof = prof_res.json()["profile"]
    assert current_prof["name"] == "Stable User"
    assert current_prof["age"] == 30
    assert current_prof["weight_kg"] == 75.0


def test_end_to_end_preview_apply_coach_consistency():
    """Verify preview targets, applied profile targets, saved snapshot targets, and Coach context targets match exactly."""
    payload = {
        "name": "Consistency User",
        "age": 27,
        "sex": "Female",
        "height_cm": 168.0,
        "weight_kg": 62.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }

    # 1. Preview
    prev_res = client.post("/api/profile/preview", json=payload)
    assert prev_res.status_code == 200
    prev_plan = prev_res.json()["proposed_plan"]

    # 2. Apply
    apply_res = client.post("/api/profile/apply", json=payload)
    assert apply_res.status_code == 200
    snap = apply_res.json()["target_snapshot"]

    # 3. Coach Context
    coach_res = client.get("/api/coach/context")
    assert coach_res.status_code == 200
    coach = coach_res.json()

    # Exact four-way consistency check
    assert prev_plan["target_calories"] == snap["calorie_target"] == coach["target_calories"]
    assert prev_plan["protein_g"] == snap["protein_target"] == coach["target_protein"]
    assert prev_plan["carbs_g"] == snap["carbs_target"] == coach["target_carbs"]
    assert prev_plan["fat_g"] == snap["fat_target"] == coach["target_fat"]
    assert coach["user_name"] == "Consistency User"





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


def test_first_time_user_endpoints(monkeypatch):
    """Verify first-time user with no saved profile receives has_profile: False and no fabricated targets."""
    import main
    monkeypatch.setattr(main, "load_profile", lambda: None)

    # 1. Profile endpoint
    res = client.get("/api/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["has_profile"] is False
    assert data["profile"] is None
    assert data["active_plan"] is None
    assert "options" in data
    assert "goals" in data["options"]

    # 2. Coach context endpoint
    coach_res = client.get("/api/coach/context")
    assert coach_res.status_code == 200
    coach_data = coach_res.json()
    assert coach_data["has_profile"] is False
    assert coach_data["user_name"] == "there"
    assert coach_data["target_calories"] == 0
    assert coach_data["target_protein"] == 0
    assert coach_data["consumed_calories"] == 0

    # 3. Progress analytics endpoint
    prog_res = client.get("/api/progress/analytics?days=7")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["has_profile"] is False
    assert prog_data["targets"]["calories"] == 0

    # 4. Coach chat endpoint prompts for profile setup
    chat_res = client.post("/api/coach/chat", json={"message": "What should I eat for dinner?"})
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "complete your profile setup" in chat_data["response"].lower()


def test_returning_user_endpoints(monkeypatch):
    """Verify returning user with a saved profile receives has_profile: True and calculated targets."""
    import main
    mock_profile = {
        "name": "Sarah Connor",
        "age": 29,
        "sex": "Female",
        "height_cm": 168.0,
        "weight_kg": 62.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    monkeypatch.setattr(main, "load_profile", lambda: dict(mock_profile))

    # 1. Profile endpoint
    res = client.get("/api/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["has_profile"] is True
    assert data["profile"]["name"] == "Sarah Connor"
    assert data["active_plan"] is not None
    assert data["active_plan"]["target_calories"] > 0

    # 2. Coach context endpoint
    coach_res = client.get("/api/coach/context")
    assert coach_res.status_code == 200
    coach_data = coach_res.json()
    assert coach_data["has_profile"] is True
    assert coach_data["user_name"] == "Sarah Connor"
    assert coach_data["target_calories"] > 0


def test_missing_name_fallback_handling(monkeypatch):
    """Verify empty or missing name falls back to neutral 'there' in coach context."""
    import main
    mock_profile = {
        "name": "   ",
        "age": 25,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "activity_level": "Lightly Active",
        "goal": "Maintenance",
        "intensity": "Maintenance"
    }
    monkeypatch.setattr(main, "load_profile", lambda: dict(mock_profile))

    coach_res = client.get("/api/coach/context")
    assert coach_res.status_code == 200
    assert coach_res.json()["user_name"] == "there"


def test_failed_profile_save_validations():
    """Verify profile save validates required inputs and returns 400 on bad data."""
    base_valid = {
        "age": 25,
        "sex": "Male",
        "height_cm": 178.0,
        "weight_kg": 75.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }

    # Missing age
    bad_age = {**base_valid, "age": -1}
    res = client.post("/api/profile/apply", json=bad_age)
    assert res.status_code == 400
    assert "age" in res.json()["detail"].lower()

    # Invalid sex
    bad_sex = {**base_valid, "sex": "Other"}
    res = client.post("/api/profile/apply", json=bad_sex)
    assert res.status_code == 400
    assert "sex" in res.json()["detail"].lower()

    # Invalid activity level
    bad_act = {**base_valid, "activity_level": "NonExistent"}
    res = client.post("/api/profile/apply", json=bad_act)
    assert res.status_code == 400

    # Invalid intensity for goal
    bad_int = {**base_valid, "intensity": "WildlyAggressive"}
    res = client.post("/api/profile/apply", json=bad_int)
    assert res.status_code == 400


def test_cors_preflight_production_vercel_origin():
    """Verify preflight OPTIONS request from production Vercel frontend is accepted."""
    headers = {
        "Origin": "https://macro-snap-eosin.vercel.app",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    res = client.options("/api/profile", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://macro-snap-eosin.vercel.app"

    # Regex test for Vercel preview deployments
    preview_headers = {
        "Origin": "https://macro-snap-staging-123-nishithlawrence.vercel.app",
        "Access-Control-Request-Method": "GET",
    }
    prev_res = client.options("/api/profile", headers=preview_headers)
    assert prev_res.status_code == 200
    assert prev_res.headers.get("access-control-allow-origin") == "https://macro-snap-staging-123-nishithlawrence.vercel.app"


def test_regression_clean_onboarding_no_synthetic_profile(monkeypatch):
    """
    Regression Test 1 & 2:
    A new visitor with no profile must receive has_profile: False, profile: None, active_plan: None.
    Never silently populate a first-time visitor's profile using generic demo data or fabricated fallbacks.
    """
    import main
    monkeypatch.setattr(main, "load_profile", lambda: None)
    monkeypatch.setattr(main, "get_latest_target_snapshot", lambda: None)

    res = client.get("/api/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["has_profile"] is False
    assert data["profile"] is None
    assert data["active_plan"] is None
    assert "options" in data


def test_regression_profile_reset_production_flag_absent_returns_403(monkeypatch, tmp_path):
    """
    Regression Test 1:
    Production environment with ENABLE_DEMO_RESET absent must reject reset with 403
    and make ZERO modifications to persistent storage.
    """
    import profile_storage
    import target_storage

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ENABLE_DEMO_RESET", raising=False)

    temp_profile_file = tmp_path / "profile.json"
    temp_target_file = tmp_path / "target_history.json"
    initial_profile_data = '{"age": 25, "sex": "Male", "height_cm": 178.0, "weight_kg": 75.0, "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"}'
    initial_target_data = '{"snapshots": [{"snapshot_id": "test", "effective_date": "2026-10-01", "calorie_target": 2000, "protein_target": 150, "carbs_target": 200, "fat_target": 65}]}'
    temp_profile_file.write_text(initial_profile_data, encoding="utf-8")
    temp_target_file.write_text(initial_target_data, encoding="utf-8")

    monkeypatch.setattr(profile_storage, "PROFILE_FILE", str(temp_profile_file))
    monkeypatch.setattr(target_storage, "TARGET_FILE", str(temp_target_file))

    res = client.post("/api/profile/reset")
    assert res.status_code == 403
    assert "disabled in production" in res.json()["detail"].lower()

    # Zero storage modification verification
    assert os.path.exists(str(temp_profile_file))
    assert temp_profile_file.read_text(encoding="utf-8") == initial_profile_data
    assert temp_target_file.read_text(encoding="utf-8") == initial_target_data


def test_regression_profile_reset_production_flag_false_returns_403(monkeypatch, tmp_path):
    """
    Regression Test 2:
    Production environment with ENABLE_DEMO_RESET=false must reject reset with 403
    and make ZERO modifications to persistent storage.
    """
    import profile_storage
    import target_storage

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_DEMO_RESET", "false")

    temp_profile_file = tmp_path / "profile.json"
    temp_target_file = tmp_path / "target_history.json"
    initial_profile_data = '{"age": 29, "sex": "Female", "height_cm": 165.0, "weight_kg": 60.0, "activity_level": "Lightly Active", "goal": "Maintenance", "intensity": "Maintenance"}'
    initial_target_data = '{"snapshots": [{"snapshot_id": "test-stay", "effective_date": "2026-10-01", "calorie_target": 1800, "protein_target": 110, "carbs_target": 210, "fat_target": 55}]}'
    temp_profile_file.write_text(initial_profile_data, encoding="utf-8")
    temp_target_file.write_text(initial_target_data, encoding="utf-8")

    monkeypatch.setattr(profile_storage, "PROFILE_FILE", str(temp_profile_file))
    monkeypatch.setattr(target_storage, "TARGET_FILE", str(temp_target_file))

    res = client.post("/api/profile/reset")
    assert res.status_code == 403
    assert "disabled in production" in res.json()["detail"].lower()

    # Storage remains untouched
    assert os.path.exists(str(temp_profile_file))
    assert temp_profile_file.read_text(encoding="utf-8") == initial_profile_data
    assert temp_target_file.read_text(encoding="utf-8") == initial_target_data


def test_regression_profile_reset_production_flag_true_permits_reset(monkeypatch, tmp_path):
    """
    Regression Test 3:
    Production environment with ENABLE_DEMO_RESET=true explicitly configured allows authenticated reset.
    """
    import profile_storage
    import target_storage

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_DEMO_RESET", "true")

    temp_profile_file = tmp_path / "profile.json"
    temp_target_file = tmp_path / "target_history.json"
    temp_profile_file.write_text('{"age": 25, "sex": "Male", "height_cm": 178.0, "weight_kg": 75.0, "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"}', encoding="utf-8")
    temp_target_file.write_text('{"snapshots": [{"snapshot_id": "test", "effective_date": "2026-10-01", "calorie_target": 2000, "protein_target": 150, "carbs_target": 200, "fat_target": 65}]}', encoding="utf-8")

    monkeypatch.setattr(profile_storage, "PROFILE_FILE", str(temp_profile_file))
    monkeypatch.setattr(target_storage, "TARGET_FILE", str(temp_target_file))

    res = client.post("/api/profile/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["has_profile"] is False
    assert data["profile"] is None
    assert data["active_plan"] is None

    # Storage reset verified
    assert not os.path.exists(str(temp_profile_file))
    with open(str(temp_target_file), "r", encoding="utf-8") as f:
        target_data = json.load(f)
        assert target_data["snapshots"] == []


def test_regression_profile_reset_non_production_permitted(monkeypatch, tmp_path):
    """
    Regression Test 4:
    Non-production environments (development/test) permit authenticated reset for developer workflow.
    """
    import profile_storage
    import target_storage

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("ENABLE_DEMO_RESET", raising=False)

    temp_profile_file = tmp_path / "profile.json"
    temp_target_file = tmp_path / "target_history.json"
    temp_profile_file.write_text('{"age": 25, "sex": "Male", "height_cm": 178.0, "weight_kg": 75.0, "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"}', encoding="utf-8")
    temp_target_file.write_text('{"snapshots": [{"snapshot_id": "test", "effective_date": "2026-10-01", "calorie_target": 2000, "protein_target": 150, "carbs_target": 200, "fat_target": 65}]}', encoding="utf-8")

    monkeypatch.setattr(profile_storage, "PROFILE_FILE", str(temp_profile_file))
    monkeypatch.setattr(target_storage, "TARGET_FILE", str(temp_target_file))

    res = client.post("/api/profile/reset")
    assert res.status_code == 200
    assert not os.path.exists(str(temp_profile_file))


def test_regression_profile_endpoint_cache_control_no_store():
    """
    Regression Test 5:
    GET /api/profile must include 'Cache-Control: no-store' header to prevent any browser caching.
    """
    res = client.get("/api/profile")
    assert res.status_code == 200
    assert "cache-control" in res.headers
    assert "no-store" in res.headers["cache-control"].lower()


def test_regression_preview_parity_with_canonical_backend():
    """
    Regression Test 3:
    Valid submitted details produce a preview consistent with backend calculations.
    """
    from calculations import calculate_full_plan

    payload = {
        "name": "Alex",
        "age": 30,
        "sex": "Female",
        "height_cm": 165.0,
        "weight_kg": 65.0,
        "activity_level": "Lightly Active",
        "goal": "Lean Bulk",
        "intensity": "Conservative surplus"
    }

    canonical_plan = calculate_full_plan(
        weight_kg=payload["weight_kg"],
        height_cm=payload["height_cm"],
        age=payload["age"],
        sex=payload["sex"],
        activity_level=payload["activity_level"],
        goal=payload["goal"],
        intensity=payload["intensity"]
    )

    res = client.post("/api/profile/preview", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "proposed_plan" in data
    prop = data["proposed_plan"]

    assert prop["bmr"] == canonical_plan["bmr"]
    assert prop["tdee"] == canonical_plan["tdee"]
    assert prop["target_calories"] == canonical_plan["target_calories"]
    assert prop["protein_g"] == canonical_plan["protein_g"]
    assert prop["carbs_g"] == canonical_plan["carbs_g"]
    assert prop["fat_g"] == canonical_plan["fat_g"]


def test_regression_changing_inputs_refreshes_preview_accurately():
    """
    Regression Test 4:
    Changing profile inputs refreshes the preview calculation correctly.
    """
    base_payload = {
        "name": "Jordan",
        "age": 28,
        "sex": "Male",
        "height_cm": 180.0,
        "weight_kg": 80.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    res1 = client.post("/api/profile/preview", json=base_payload)
    assert res1.status_code == 200
    plan1 = res1.json()["proposed_plan"]

    # Change weight and intensity
    modified_payload = {
        **base_payload,
        "weight_kg": 90.0,
        "intensity": "Aggressive"
    }
    res2 = client.post("/api/profile/preview", json=modified_payload)
    assert res2.status_code == 200
    plan2 = res2.json()["proposed_plan"]

    # Calculations must reflect changes
    assert plan2["weight_kg"] == 90.0
    assert plan2["bmr"] > plan1["bmr"]
    assert plan2["tdee"] > plan1["tdee"]
    assert plan2["target_calories"] != plan1["target_calories"]


def test_regression_unauthorized_endpoints_do_not_return_mock_data():
    """
    Regression Test 6:
    Unauthorized or unauthenticated API calls must fail with 401 and never return demo data.
    """
    unauth_client = TestClient(app)  # No auth headers

    res_profile = unauth_client.get("/api/profile")
    assert res_profile.status_code == 401
    assert "detail" in res_profile.json()

    res_preview = unauth_client.post("/api/profile/preview", json={"age": 25})
    assert res_preview.status_code == 401

    res_apply = unauth_client.post("/api/profile/apply", json={"age": 25})
    assert res_apply.status_code == 401

    res_reset = unauth_client.post("/api/profile/reset")
    assert res_reset.status_code == 401


def test_regression_missing_fields_never_trigger_fabricated_defaults():
    """
    Regression Test 5:
    Missing profile fields return 400 validation error, never falling back to fabricated defaults.
    """
    incomplete_payload = {
        "age": 25,
        "sex": "Male"
        # Missing height_cm, weight_kg, activity_level, goal, intensity
    }
    res = client.post("/api/profile/preview", json=incomplete_payload)
    assert res.status_code == 400
    assert "height" in res.json()["detail"].lower()


def test_regression_incomplete_inputs_cannot_activate_plan():
    """
    Regression Test 6:
    Incomplete or invalid inputs cannot activate a plan via POST /api/profile/apply.
    """
    incomplete_payload = {
        "name": "Bob",
        "age": 25,
        "sex": "Male"
        # Missing biometrics
    }
    res = client.post("/api/profile/apply", json=incomplete_payload)
    assert res.status_code == 400

    # Non-adult age rejection
    minor_payload = {
        "name": "Minor",
        "age": 16,
        "sex": "Male",
        "height_cm": 170.0,
        "weight_kg": 65.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    minor_res = client.post("/api/profile/apply", json=minor_payload)
    assert minor_res.status_code == 400
    assert "adult" in minor_res.json()["detail"].lower()


def test_regression_activation_uses_current_validated_profile_and_matches_preview():
    """
    Regression Test 7:
    Activation applies the current validated submitted profile, not any previous preview.
    """
    from calculations import calculate_full_plan

    profile_a = {
        "name": "Persona A",
        "age": 26,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    # User previews profile A
    preview_res = client.post("/api/profile/preview", json=profile_a)
    assert preview_res.status_code == 200

    # User modifies form to profile B and applies
    profile_b = {
        "name": "Persona B",
        "age": 34,
        "sex": "Female",
        "height_cm": 162.0,
        "weight_kg": 58.0,
        "activity_level": "Lightly Active",
        "goal": "Lean Bulk",
        "intensity": "Conservative surplus"
    }
    apply_res = client.post("/api/profile/apply", json=profile_b)
    assert apply_res.status_code == 200
    applied_data = apply_res.json()

    expected_plan_b = calculate_full_plan(
        weight_kg=58.0,
        height_cm=162.0,
        age=34,
        sex="Female",
        activity_level="Lightly Active",
        goal="Lean Bulk",
        intensity="Conservative surplus"
    )

    assert applied_data["profile"]["name"] == "Persona B"
    assert applied_data["profile"]["weight_kg"] == 58.0
    assert applied_data["active_plan"]["target_calories"] == expected_plan_b["target_calories"]
    assert applied_data["active_plan"]["protein_g"] == expected_plan_b["protein_g"]


def test_regression_profile_and_snapshot_refer_to_same_inputs():
    """
    Regression Test 8:
    Saved profile and latest target snapshot must refer to the exact same biometrics and goals.
    """
    profile_c = {
        "name": "Persona C",
        "age": 27,
        "sex": "Male",
        "height_cm": 182.0,
        "weight_kg": 85.0,
        "activity_level": "Very Active",
        "goal": "Maintenance",
        "intensity": "Maintenance"
    }
    apply_res = client.post("/api/profile/apply", json=profile_c)
    assert apply_res.status_code == 200

    profile_res = client.get("/api/profile")
    assert profile_res.status_code == 200
    pdata = profile_res.json()

    prof = pdata["profile"]
    snap = pdata["active_plan"]

    assert prof["weight_kg"] == snap["weight_kg"]
    assert prof["goal"] == snap["goal"]
    assert prof["intensity"] == (snap.get("goal_intensity") or snap.get("intensity"))
    assert prof["activity_level"] == snap["activity_level"]
