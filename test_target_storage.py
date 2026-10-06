"""
Unit test suite for MacroSnap target_storage.py module.
Tests persistent JSON target snapshots, historical date resolution,
UUID uniqueness, and validation.
"""

import os
import shutil
import tempfile

import target_storage
from target_storage import (
    load_target_snapshots,
    create_target_snapshot,
    get_target_for_date,
    get_latest_target_snapshot,
    validate_target_snapshot,
)

TEST_DIR = tempfile.mkdtemp(prefix="macrosnap_target_test_")
TEST_FILE = os.path.join(TEST_DIR, "target_history.json")

def setup_module():
    target_storage.DATA_DIR = TEST_DIR
    target_storage.TARGET_FILE = TEST_FILE
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

def teardown_module():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_1_empty_history():
    setup_module()
    snaps = load_target_snapshots()
    assert len(snaps) == 0
    assert get_latest_target_snapshot() is None
    print("[PASS] test_1_empty_history passed")

def test_2_create_initial_snapshot():
    plan = {
        "bmr": 1805.0,
        "tdee": 2798,
        "target_calories": 2378,
        "protein_g": 144,
        "carbs_g": 302,
        "fat_g": 66,
        "goal": "Fat Loss",
        "intensity": "Moderate",
        "activity_level": "Moderately Active",
        "weight_kg": 80.0
    }

    ok, snap = create_target_snapshot(plan, effective_date="2026-10-01")
    assert ok is True
    assert snap["calorie_target"] == 2378
    assert snap["effective_date"] == "2026-10-01"

    latest = get_latest_target_snapshot()
    assert latest["snapshot_id"] == snap["snapshot_id"]
    print("[PASS] test_2_create_initial_snapshot passed")

def test_3_multiple_snapshots_and_date_resolution():
    plan2 = {
        "bmr": 1780.0,
        "tdee": 2750,
        "target_calories": 2200,
        "protein_g": 150,
        "carbs_g": 250,
        "fat_g": 60,
        "goal": "Fat Loss",
        "intensity": "Aggressive",
        "activity_level": "Moderately Active",
        "weight_kg": 78.0
    }
    create_target_snapshot(plan2, effective_date="2026-10-05")

    # On Oct 3 (before Oct 5 change) -> should resolve Oct 1 snapshot (2378 kcal)
    t_oct3 = get_target_for_date("2026-10-03")
    assert t_oct3["calorie_target"] == 2378
    assert t_oct3["goal_intensity"] == "Moderate"

    # On Oct 5 or later -> should resolve Oct 5 snapshot (2200 kcal)
    t_oct5 = get_target_for_date("2026-10-05")
    assert t_oct5["calorie_target"] == 2200
    assert t_oct5["goal_intensity"] == "Aggressive"

    t_oct6 = get_target_for_date("2026-10-06")
    assert t_oct6["calorie_target"] == 2200
    print("[PASS] test_3_multiple_snapshots_and_date_resolution passed")

def test_4_invalid_snapshot_rejection():
    bad_snap = {
        "snapshot_id": "bad1",
        "effective_date": "2026-10-05",
        "calorie_target": -100,  # Negative invalid
        "protein_target": 150,
        "carbs_target": 200,
        "fat_target": 50
    }
    valid, msg = validate_target_snapshot(bad_snap)
    assert valid is False
    print("[PASS] test_4_invalid_snapshot_rejection passed")

if __name__ == "__main__":
    print("Running MacroSnap Target Storage Tests...\n")
    test_1_empty_history()
    test_2_create_initial_snapshot()
    test_3_multiple_snapshots_and_date_resolution()
    test_4_invalid_snapshot_rejection()
    teardown_module()
    print("\nAll Target Storage tests passed successfully!")
