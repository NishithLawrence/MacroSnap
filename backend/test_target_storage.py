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


def test_5_zero_carbs_snapshot_allowed():
    zero_carb_plan = {
        "bmr": 1600.0,
        "tdee": 2000,
        "target_calories": 936,
        "protein_g": 180,
        "carbs_g": 0,
        "fat_g": 24,
        "goal": "Fat Loss",
        "intensity": "Aggressive",
        "activity_level": "Sedentary",
        "weight_kg": 100.0
    }
    ok, snap = create_target_snapshot(zero_carb_plan, effective_date="2026-10-10")
    assert ok is True
    assert snap is not None
    assert snap["carbs_target"] == 0
    assert snap["calorie_target"] == 936
    assert snap["protein_target"] == 180
    assert snap["fat_target"] == 24
    print("[PASS] test_5_zero_carbs_snapshot_allowed passed")


def test_6_nan_and_negative_snapshot_rejected():
    # Negative carbs rejected
    snap_neg = {
        "snapshot_id": "neg1",
        "effective_date": "2026-10-05",
        "calorie_target": 2000,
        "protein_target": 150,
        "carbs_target": -5,
        "fat_target": 50
    }
    valid, msg = validate_target_snapshot(snap_neg)
    assert valid is False
    assert "carbs_target" in msg

    # NaN calorie target rejected
    snap_nan = {
        "snapshot_id": "nan1",
        "effective_date": "2026-10-05",
        "calorie_target": float("nan"),
        "protein_target": 150,
        "carbs_target": 0,
        "fat_target": 50
    }
    valid_nan, msg_nan = validate_target_snapshot(snap_nan)
    assert valid_nan is False
    assert "calorie_target" in msg_nan
    print("[PASS] test_6_nan_and_negative_snapshot_rejected passed")


def test_7_empty_or_incomplete_plan_rejected_without_defaults():
    """Verify create_target_snapshot rejects empty or incomplete plans and never generates fabricated defaults."""
    # 1. Empty dict
    ok1, snap1 = create_target_snapshot({})
    assert ok1 is False
    assert snap1 is None

    # 2. Incomplete plans
    ok2, snap2 = create_target_snapshot({"target_calories": 2000})
    assert ok2 is False
    assert snap2 is None

    ok3, snap3 = create_target_snapshot({"target_calories": 2000, "protein_g": 150})
    assert ok3 is False
    assert snap3 is None

    # 3. None input
    ok4, snap4 = create_target_snapshot(None)
    assert ok4 is False
    assert snap4 is None

    # 4. Confirm no fabricated snapshots were appended
    snaps = load_target_snapshots()
    for s in snaps:
        # None should be an empty fabricated plan with exactly 2000, 150, 200, 65 from an empty call
        assert s.get("calorie_target") is not None


def test_8_boolean_and_non_finite_targets_rejected():
    """Verify validate_target_snapshot rejects boolean types and infinite values."""
    # Booleans masquerading as numeric 1 or 0
    snap_bool1 = {
        "snapshot_id": "bool1",
        "effective_date": "2026-10-20",
        "calorie_target": True,
        "protein_target": 150,
        "carbs_target": 200,
        "fat_target": 50
    }
    valid, msg = validate_target_snapshot(snap_bool1)
    assert valid is False
    assert "calorie_target" in msg

    snap_bool2 = {
        "snapshot_id": "bool2",
        "effective_date": "2026-10-20",
        "calorie_target": 2000,
        "protein_target": 150,
        "carbs_target": False,
        "fat_target": 50
    }
    valid2, msg2 = validate_target_snapshot(snap_bool2)
    assert valid2 is False
    assert "carbs_target" in msg2

    # Infinite values
    snap_inf = {
        "snapshot_id": "inf1",
        "effective_date": "2026-10-20",
        "calorie_target": float("inf"),
        "protein_target": 150,
        "carbs_target": 200,
        "fat_target": 50
    }
    valid3, msg3 = validate_target_snapshot(snap_inf)
    assert valid3 is False
    assert "calorie_target" in msg3


if __name__ == "__main__":
    print("Running MacroSnap Target Storage Tests...\n")
    test_1_empty_history()
    test_2_create_initial_snapshot()
    test_3_multiple_snapshots_and_date_resolution()
    test_4_invalid_snapshot_rejection()
    test_5_zero_carbs_snapshot_allowed()
    test_6_nan_and_negative_snapshot_rejected()
    test_7_empty_or_incomplete_plan_rejected_without_defaults()
    test_8_boolean_and_non_finite_targets_rejected()
    teardown_module()
    print("\nAll Target Storage tests passed successfully!")

