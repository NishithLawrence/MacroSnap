"""
Unit test suite for MacroSnap analytics.py module.
Tests period history generation, missing day handling, calorie/protein adherence,
consistency score formula, and period averages.
"""

import analytics
from analytics import (
    get_daily_nutrition_history,
    calculate_period_averages,
    calculate_calorie_adherence,
    calculate_protein_adherence,
    calculate_consistency,
    get_goal_interpretation,
    get_period_summary,
)

def test_1_empty_and_missing_days():
    history = get_daily_nutrition_history(days=7)
    assert len(history) == 7

    # By default, if no meals are logged, tracked should be False for all days
    averages = calculate_period_averages(history)
    assert averages["tracked_days"] == 0
    assert averages["avg_calories"] == 0

    print("[PASS] test_1_empty_and_missing_days passed")

def test_2_missing_day_handling_not_zero():
    mock_history = [
        {"date": "2026-10-01", "tracked": True, "calories": 2000, "protein_g": 140, "carbs_g": 200, "fat_g": 60, "meal_count": 3},
        {"date": "2026-10-02", "tracked": False, "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meal_count": 0},
        {"date": "2026-10-03", "tracked": True, "calories": 2200, "protein_g": 160, "carbs_g": 220, "fat_g": 65, "meal_count": 3},
    ]

    averages = calculate_period_averages(mock_history)
    assert averages["tracked_days"] == 2
    assert averages["total_days"] == 3
    # Average calories over 2 tracked days = (2000 + 2200) / 2 = 2100 (NOT (2000+0+2200)/3 = 1400)
    assert averages["avg_calories"] == 2100
    assert averages["avg_protein"] == 150
    print("[PASS] test_2_missing_day_handling_not_zero passed")

def test_3_adherence_calculations():
    target_cal = 2000  # 90%-110% range: [1800, 2200]
    target_p = 150     # >=90% threshold: 135g

    mock_history = [
        {"tracked": True, "calories": 1950, "protein_g": 140},  # On target, P reached
        {"tracked": True, "calories": 1700, "protein_g": 130},  # Below cal target, P below
        {"tracked": True, "calories": 2300, "protein_g": 150},  # Above cal target, P reached
        {"tracked": True, "calories": 2000, "protein_g": 145},  # On target, P reached
    ]

    cal_adh = calculate_calorie_adherence(mock_history, target_cal)
    assert cal_adh["on_target_count"] == 2
    assert cal_adh["below_count"] == 1
    assert cal_adh["above_count"] == 1
    assert cal_adh["ratio_str"] == "2 / 4 days on target"

    p_adh = calculate_protein_adherence(mock_history, target_p)
    assert p_adh["reached_count"] == 3
    assert p_adh["ratio_str"] == "3 / 4 days target reached"
    print("[PASS] test_3_adherence_calculations passed")

def test_4_consistency_score_formula():
    target_cal = 2000
    target_p = 150

    # Perfect day: cals = 2000, P = 150 -> Score = 100
    perfect_history = [{"tracked": True, "calories": 2000, "protein_g": 150}]
    score_perf = calculate_consistency(perfect_history, target_cal, target_p)
    assert score_perf == 100

    # Partial day
    partial_history = [{"tracked": True, "calories": 1500, "protein_g": 100}]
    score_part = calculate_consistency(partial_history, target_cal, target_p)
    assert 0 < score_part < 100
    print("[PASS] test_4_consistency_score_formula passed")

def test_5_goal_interpretation():
    msg_loss = get_goal_interpretation("Fat Loss", 1800, 2000, 2300)
    assert "below your maintenance level" in msg_loss

    msg_bulk = get_goal_interpretation("Lean Bulk", 2600, 2500, 2300)
    assert "above your maintenance level" in msg_bulk
    print("[PASS] test_5_goal_interpretation passed")

if __name__ == "__main__":
    print("Running MacroSnap Analytics Engine Tests...\n")
    test_1_empty_and_missing_days()
    test_2_missing_day_handling_not_zero()
    test_3_adherence_calculations()
    test_4_consistency_score_formula()
    test_5_goal_interpretation()
    print("\nAll Analytics Engine tests passed successfully!")
