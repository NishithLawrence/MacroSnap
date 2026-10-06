"""
Unit test suite for MacroSnap weight_storage.py module.
Tests persistent JSON operations, validation, date filtering, malformed file safety,
and weight change calculations.
"""

import os
import shutil
import tempfile
import datetime

import weight_storage
from weight_storage import (
    add_weight_entry,
    load_weight_history,
    delete_weight_entry,
    get_latest_weight,
    get_previous_weight,
    get_weight_change,
    get_weight_for_period,
    validate_weight_entry,
)

TEST_DIR = tempfile.mkdtemp(prefix="macrosnap_weight_test_")
TEST_FILE = os.path.join(TEST_DIR, "weight_history.json")

def setup_module():
    weight_storage.DATA_DIR = TEST_DIR
    weight_storage.WEIGHT_FILE = TEST_FILE
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

def teardown_module():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_1_empty_file():
    setup_module()
    history = load_weight_history()
    assert isinstance(history, list)
    assert len(history) == 0
    print("[PASS] test_1_empty_file passed")

def test_2_add_and_latest_weight():
    d5 = (datetime.date.today() - datetime.timedelta(days=5)).isoformat()
    ok, msg = add_weight_entry(75.5, d5)
    assert ok is True
    latest = get_latest_weight()
    assert latest["weight_kg"] == 75.5
    assert latest["date"] == d5
    print("[PASS] test_2_add_and_latest_weight passed")

def test_3_multiple_entries_and_change_calculation():
    d2 = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    d0 = datetime.date.today().isoformat()
    add_weight_entry(74.8, d2)
    add_weight_entry(74.2, d0)

    history = load_weight_history()
    assert len(history) == 3

    latest = get_latest_weight()
    prev = get_previous_weight()
    assert latest["weight_kg"] == 74.2
    assert prev["weight_kg"] == 74.8

    change = get_weight_change()
    assert change["current"] == 74.2
    assert change["previous"] == 74.8
    assert change["change_kg"] == -0.6
    print("[PASS] test_3_multiple_entries_and_change_calculation passed")

def test_4_period_filtering():
    d0 = datetime.date.today().isoformat()
    period_3d = get_weight_for_period(days=3)
    assert len(period_3d) == 2
    assert any(e["date"] == d0 for e in period_3d)
    print("[PASS] test_4_period_filtering passed")

def test_5_invalid_values_rejection():
    # Negative weight
    ok1, msg1 = add_weight_entry(-70.0, "2026-10-05")
    assert ok1 is False

    # Zero weight
    ok2, msg2 = add_weight_entry(0.0, "2026-10-05")
    assert ok2 is False

    # NaN weight
    ok3, msg3 = add_weight_entry(float("nan"), "2026-10-05")
    assert ok3 is False

    # Infinity weight
    ok4, msg4 = add_weight_entry(float("inf"), "2026-10-05")
    assert ok4 is False
    print("[PASS] test_5_invalid_values_rejection passed")

def test_6_malformed_json_recovery():
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write("{corrupt_weight_json!!")

    history = load_weight_history()
    assert history == []
    print("[PASS] test_6_malformed_json_recovery passed")

if __name__ == "__main__":
    print("Running MacroSnap Weight Storage Tests...\n")
    test_1_empty_file()
    test_2_add_and_latest_weight()
    test_3_multiple_entries_and_change_calculation()
    test_4_period_filtering()
    test_5_invalid_values_rejection()
    test_6_malformed_json_recovery()
    teardown_module()
    print("\nAll Weight Storage tests passed successfully!")
