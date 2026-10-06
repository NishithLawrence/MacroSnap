"""
Unit test suite for MacroSnap meal_storage.py module.
Verifies JSON persistence, meal CRUD operations, date filtering,
data validation, malformed file safety, and daily totals calculation.
"""

import os
import json
import shutil
import tempfile
import datetime

import meal_storage
from meal_storage import (
    add_meal,
    load_meals,
    save_meals,
    get_meals_for_date,
    get_daily_totals,
    update_meal,
    delete_meal,
    get_all_dates,
    validate_meal_data,
)

# Use a temporary directory for test storage to avoid touching main data
TEST_DIR = tempfile.mkdtemp(prefix="macrosnap_test_data_")
TEST_FILE = os.path.join(TEST_DIR, "meals.json")

def setup_module():
    meal_storage.DATA_DIR = TEST_DIR
    meal_storage.STORAGE_FILE = TEST_FILE
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

def teardown_module():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_1_empty_storage():
    setup_module()
    meals = load_meals()
    assert isinstance(meals, dict)
    assert len(meals) == 0
    print("[PASS] test_1_empty_storage passed")

def test_2_add_and_load_meal():
    meal = {
        "meal_id": "test-uuid-1",
        "date": "2026-10-05",
        "timestamp": "2026-10-05T08:30:00",
        "meal_type": "Breakfast",
        "foods": [
            {"name": "Oatmeal", "portion": "100g", "calories": 350, "protein_g": 12, "carbs_g": 60, "fat_g": 6}
        ],
        "total": {"calories": 350, "protein_g": 12, "carbs_g": 60, "fat_g": 6}
    }
    ok = add_meal(meal)
    assert ok is True

    loaded = load_meals()
    assert "test-uuid-1" in loaded
    assert loaded["test-uuid-1"]["meal_type"] == "Breakfast"
    print("[PASS] test_2_add_and_load_meal passed")

def test_3_retrieve_today_and_historical_meals():
    today_str = datetime.date.today().isoformat()
    m_today = {
        "meal_id": "today-meal-1",
        "date": today_str,
        "timestamp": f"{today_str}T12:00:00",
        "meal_type": "Lunch",
        "foods": [
            {"name": "Chicken Salad", "portion": "200g", "calories": 400, "protein_g": 40, "carbs_g": 10, "fat_g": 15}
        ]
    }
    m_hist = {
        "meal_id": "hist-meal-1",
        "date": "2026-10-01",
        "timestamp": "2026-10-01T19:00:00",
        "meal_type": "Dinner",
        "foods": [
            {"name": "Steak & Veggies", "portion": "300g", "calories": 600, "protein_g": 50, "carbs_g": 20, "fat_g": 30}
        ]
    }

    assert add_meal(m_today) is True
    assert add_meal(m_hist) is True

    today_meals = get_meals_for_date(today_str)
    assert len(today_meals) >= 1
    assert any(m["meal_id"] == "today-meal-1" for m in today_meals)

    hist_meals = get_meals_for_date("2026-10-01")
    assert len(hist_meals) == 1
    assert hist_meals[0]["meal_id"] == "hist-meal-1"
    print("[PASS] test_3_retrieve_today_and_historical_meals passed")

def test_4_multiple_meals_and_daily_totals():
    date_str = "2026-10-04"
    m1 = {
        "meal_id": "m1",
        "date": date_str,
        "timestamp": "2026-10-04T08:00:00",
        "meal_type": "Breakfast",
        "foods": [{"name": "Eggs", "portion": "2 eggs", "calories": 140, "protein_g": 12, "carbs_g": 2, "fat_g": 10}]
    }
    m2 = {
        "meal_id": "m2",
        "date": date_str,
        "timestamp": "2026-10-04T13:00:00",
        "meal_type": "Lunch",
        "foods": [{"name": "Rice Bowl", "portion": "1 bowl", "calories": 500, "protein_g": 30, "carbs_g": 70, "fat_g": 10}]
    }
    add_meal(m1)
    add_meal(m2)

    totals = get_daily_totals(date_str)
    assert totals["calories"] == 640
    assert totals["protein_g"] == 42
    assert totals["carbs_g"] == 72
    assert totals["fat_g"] == 20
    print("[PASS] test_4_multiple_meals_and_daily_totals passed")

def test_5_update_and_delete_meal():
    date_str = "2026-10-04"
    upd = {
        "meal_id": "m1",
        "date": date_str,
        "timestamp": "2026-10-04T08:00:00",
        "meal_type": "Breakfast",
        "foods": [{"name": "Eggs & Toast", "portion": "2 eggs 2 toast", "calories": 300, "protein_g": 18, "carbs_g": 30, "fat_g": 12}]
    }
    ok_upd = update_meal("m1", upd)
    assert ok_upd is True

    tot_upd = get_daily_totals(date_str)
    assert tot_upd["calories"] == 800  # 300 + 500

    ok_del = delete_meal("m1")
    assert ok_del is True

    tot_after_del = get_daily_totals(date_str)
    assert tot_after_del["calories"] == 500  # only m2 remains
    print("[PASS] test_5_update_and_delete_meal passed")

def test_6_invalid_data_validation():
    # Negative calories
    invalid_meal_1 = {
        "meal_id": "inv1",
        "date": "2026-10-05",
        "meal_type": "Snack",
        "foods": [{"name": "Chips", "calories": -100, "protein_g": 0, "carbs_g": 0, "fat_g": 0}]
    }
    valid, msg = validate_meal_data(invalid_meal_1)
    assert valid is False

    # Invalid meal type
    invalid_meal_2 = {
        "meal_id": "inv2",
        "date": "2026-10-05",
        "meal_type": "Midnight Feast",
        "foods": [{"name": "Pizza", "calories": 300, "protein_g": 10, "carbs_g": 30, "fat_g": 10}]
    }
    valid2, msg2 = validate_meal_data(invalid_meal_2)
    assert valid2 is False

    # NaN / String calories
    invalid_meal_3 = {
        "meal_id": "inv3",
        "date": "2026-10-05",
        "meal_type": "Lunch",
        "foods": [{"name": "Pizza", "calories": float("nan"), "protein_g": 10, "carbs_g": 30, "fat_g": 10}]
    }
    valid3, msg3 = validate_meal_data(invalid_meal_3)
    assert valid3 is False
    print("[PASS] test_6_invalid_data_validation passed")

def test_7_malformed_json_recovery():
    # Write corrupt data to TEST_FILE
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write("{corrupt_json_structure!!!")

    loaded = load_meals()
    assert loaded == {}  # Should return empty dict gracefully without crashing
    print("[PASS] test_7_malformed_json_recovery passed")

if __name__ == "__main__":
    print("Running MacroSnap Meal Storage Tests...\n")
    test_1_empty_storage()
    test_2_add_and_load_meal()
    test_3_retrieve_today_and_historical_meals()
    test_4_multiple_meals_and_daily_totals()
    test_5_update_and_delete_meal()
    test_6_invalid_data_validation()
    test_7_malformed_json_recovery()
    teardown_module()
    print("\nAll meal storage tests passed successfully!")
