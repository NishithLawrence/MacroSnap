"""
Unit test suite for MacroSnap profile_storage.py module.
Tests persistent JSON operations, validation, numerical constraints,
and invalid value rejection.
"""

import os
import shutil
import tempfile

import profile_storage
from profile_storage import (
    load_profile,
    save_profile,
    validate_profile_data,
)

TEST_DIR = tempfile.mkdtemp(prefix="macrosnap_profile_test_")
TEST_FILE = os.path.join(TEST_DIR, "profile.json")

def setup_module():
    profile_storage.DATA_DIR = TEST_DIR
    profile_storage.PROFILE_FILE = TEST_FILE
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

def teardown_module():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_1_empty_profile():
    setup_module()
    prof = load_profile()
    assert prof is None
    print("[PASS] test_1_empty_profile passed")

def test_2_save_and_load_valid_profile():
    valid_p = {
        "age": 28,
        "sex": "Male",
        "height_cm": 180.0,
        "weight_kg": 80.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }

    ok = save_profile(valid_p)
    assert ok is True

    loaded = load_profile()
    assert loaded is not None
    assert loaded["age"] == 28
    assert loaded["goal"] == "Fat Loss"
    print("[PASS] test_2_save_and_load_valid_profile passed")

def test_3_invalid_values_rejection():
    base = {
        "age": 25,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }

    # Invalid age
    p1 = base.copy()
    p1["age"] = -5
    valid1, msg1 = validate_profile_data(p1)
    assert valid1 is False

    # Invalid height
    p2 = base.copy()
    p2["height_cm"] = 0
    valid2, msg2 = validate_profile_data(p2)
    assert valid2 is False

    # Invalid weight (NaN)
    p3 = base.copy()
    p3["weight_kg"] = float("nan")
    valid3, msg3 = validate_profile_data(p3)
    assert valid3 is False

    # Invalid weight (Infinity)
    p4 = base.copy()
    p4["weight_kg"] = float("inf")
    valid4, msg4 = validate_profile_data(p4)
    assert valid4 is False

    # Mismatched goal and intensity
    p5 = base.copy()
    p5["goal"] = "Fat Loss"
    p5["intensity"] = "Conservative surplus"  # Invalid for Fat Loss
    valid5, msg5 = validate_profile_data(p5)
    assert valid5 is False

    print("[PASS] test_3_invalid_values_rejection passed")

def test_4_malformed_json_recovery():
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write("{corrupt_profile_json!!!")

    loaded = load_profile()
    assert loaded is None
    print("[PASS] test_4_malformed_json_recovery passed")


def test_5_name_validation():
    base = {
        "age": 25,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }

    # Valid string name
    p_valid = base.copy()
    p_valid["name"] = "Alex"
    v, msg = validate_profile_data(p_valid)
    assert v is True

    # Empty string name (valid)
    p_empty = base.copy()
    p_empty["name"] = ""
    v, msg = validate_profile_data(p_empty)
    assert v is True

    # None name (valid)
    p_none = base.copy()
    p_none["name"] = None
    v, msg = validate_profile_data(p_none)
    assert v is True

    # Name omitted (backward compatibility, valid)
    v, msg = validate_profile_data(base.copy())
    assert v is True

    # Non-string name (invalid)
    p_invalid_type = base.copy()
    p_invalid_type["name"] = 12345
    v, msg = validate_profile_data(p_invalid_type)
    assert v is False
    assert "string" in msg.lower()

    # Name too long > 100 chars (invalid)
    p_too_long = base.copy()
    p_too_long["name"] = "A" * 101
    v, msg = validate_profile_data(p_too_long)
    assert v is False
    assert "100" in msg
    print("[PASS] test_5_name_validation passed")


def test_6_save_and_load_profile_with_name():
    p = {
        "name": "  Jordan Athlete  ",
        "age": 29,
        "sex": "Female",
        "height_cm": 168.0,
        "weight_kg": 62.0,
        "activity_level": "Lightly Active",
        "goal": "Maintenance",
        "intensity": "Maintenance"
    }
    ok = save_profile(p)
    assert ok is True

    loaded = load_profile()
    assert loaded is not None
    assert loaded["name"] == "Jordan Athlete"
    assert loaded["age"] == 29
    print("[PASS] test_6_save_and_load_profile_with_name passed")


def test_7_backward_compatibility_profile_without_name():
    p_no_name = {
        "age": 24,
        "sex": "Male",
        "height_cm": 182.0,
        "weight_kg": 78.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    ok = save_profile(p_no_name)
    assert ok is True

    loaded = load_profile()
    assert loaded is not None
    assert loaded["age"] == 24
    assert loaded.get("name") is None or loaded.get("name") == ""
    print("[PASS] test_7_backward_compatibility_profile_without_name passed")


def test_8_adult_bounds_and_finite_checks():
    base = {
        "age": 25,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }

    # Under 18 rejected
    p_minor = base.copy()
    p_minor["age"] = 17
    v, msg = validate_profile_data(p_minor)
    assert v is False
    assert "18" in msg

    # Over 120 rejected
    p_ancient = base.copy()
    p_ancient["age"] = 125
    v, msg = validate_profile_data(p_ancient)
    assert v is False
    assert "120" in msg

    # Height under 100 cm rejected
    p_short = base.copy()
    p_short["height_cm"] = 95.0
    v, msg = validate_profile_data(p_short)
    assert v is False
    assert "100" in msg

    # Height over 250 cm rejected
    p_tall = base.copy()
    p_tall["height_cm"] = 260.0
    v, msg = validate_profile_data(p_tall)
    assert v is False
    assert "250" in msg

    # Weight under 30 kg rejected
    p_light = base.copy()
    p_light["weight_kg"] = 28.0
    v, msg = validate_profile_data(p_light)
    assert v is False
    assert "30" in msg

    # Weight over 350 kg rejected
    p_heavy = base.copy()
    p_heavy["weight_kg"] = 380.0
    v, msg = validate_profile_data(p_heavy)
    assert v is False
    assert "350" in msg

    # Non-finite values
    for field in ["age", "height_cm", "weight_kg"]:
        p_nan = base.copy()
        p_nan[field] = float("nan")
        v, msg = validate_profile_data(p_nan)
        assert v is False
        assert "finite" in msg.lower()

        p_inf = base.copy()
        p_inf[field] = float("inf")
        v, msg = validate_profile_data(p_inf)
        assert v is False
        assert "finite" in msg.lower()
    print("[PASS] test_8_adult_bounds_and_finite_checks passed")


if __name__ == "__main__":
    print("Running MacroSnap Profile Storage Tests...\n")
    test_1_empty_profile()
    test_2_save_and_load_valid_profile()
    test_3_invalid_values_rejection()
    test_4_malformed_json_recovery()
    test_5_name_validation()
    test_6_save_and_load_profile_with_name()
    test_7_backward_compatibility_profile_without_name()
    test_8_adult_bounds_and_finite_checks()
    teardown_module()
    print("\nAll Profile Storage tests passed successfully!")
