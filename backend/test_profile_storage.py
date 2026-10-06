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

if __name__ == "__main__":
    print("Running MacroSnap Profile Storage Tests...\n")
    test_1_empty_profile()
    test_2_save_and_load_valid_profile()
    test_3_invalid_values_rejection()
    test_4_malformed_json_recovery()
    teardown_module()
    print("\nAll Profile Storage tests passed successfully!")
