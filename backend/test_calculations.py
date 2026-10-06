"""
Unit test suite for MacroSnap calculation engine.
Validates BMR (Mifflin-St Jeor), TDEE multipliers, goal calorie target adjustments,
and mathematical exactness of macro calorie contributions.
"""

import sys
from calculations import (
    calculate_bmr,
    calculate_tdee,
    calculate_target_calories,
    calculate_macros,
    calculate_full_plan,
    ACTIVITY_MULTIPLIERS,
    GOAL_CONFIG,
)

def test_bmr_male():
    # Male: 10 * 80 + 6.25 * 180 - 5 * 25 + 5 = 800 + 1125 - 125 + 5 = 1805.0
    bmr = calculate_bmr(weight_kg=80.0, height_cm=180.0, age=25, sex="Male")
    assert abs(bmr - 1805.0) < 1e-5, f"Expected 1805.0, got {bmr}"
    print("[PASS] test_bmr_male passed")

def test_bmr_female():
    # Female: 10 * 60 + 6.25 * 165 - 5 * 30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
    bmr = calculate_bmr(weight_kg=60.0, height_cm=165.0, age=30, sex="Female")
    assert abs(bmr - 1320.25) < 1e-5, f"Expected 1320.25, got {bmr}"
    print("[PASS] test_bmr_female passed")

def test_all_activity_levels():
    bmr = 1500.0
    expected_tdees = {
        "Sedentary": 1800.0,
        "Lightly Active": 2062.5,
        "Moderately Active": 2325.0,
        "Very Active": 2587.5,
        "Extremely Active": 2850.0,
    }
    for level, expected in expected_tdees.items():
        tdee = calculate_tdee(bmr, level)
        assert abs(tdee - expected) < 1e-5, f"For {level}, expected {expected}, got {tdee}"
    print("[PASS] test_all_activity_levels passed")

def test_all_goals_and_intensities():
    weight_kg = 75.0
    height_cm = 175.0
    age = 28
    
    for sex in ["Male", "Female"]:
        bmr = calculate_bmr(weight_kg, height_cm, age, sex)
        for act_level in ACTIVITY_MULTIPLIERS.keys():
            tdee = calculate_tdee(bmr, act_level)
            for goal, g_config in GOAL_CONFIG.items():
                for intensity in g_config["intensities"].keys():
                    plan = calculate_full_plan(
                        age=age,
                        sex=sex,
                        height_cm=height_cm,
                        weight_kg=weight_kg,
                        activity_level=act_level,
                        goal=goal,
                        intensity=intensity
                    )
                    
                    # Verify mathematical correspondence: p*4 + c*4 + f*9 == total_macro_cals
                    expected_macro_cals = (plan["protein_g"] * 4) + (plan["carbs_g"] * 4) + (plan["fat_g"] * 9)
                    assert plan["total_macro_cals"] == expected_macro_cals, \
                        f"Macro calorie mismatch: sum {expected_macro_cals} vs plan {plan['total_macro_cals']}"
                    
                    # Verify target calories match macro calories closely (within rounding margin)
                    diff = abs(plan["target_calories"] - plan["total_macro_cals"])
                    assert diff <= 4, \
                        f"Target calories {plan['target_calories']} diff from macro sum {plan['total_macro_cals']} is {diff}"

    print("[PASS] test_all_goals_and_intensities passed (all combinations verified)")

def test_sample_plan_confirmation_case():
    plan = calculate_full_plan(
        age=25,
        sex="Male",
        height_cm=180,
        weight_kg=80,
        activity_level="Moderately Active",
        goal="Fat Loss",
        intensity="Moderate"
    )
    print("\n--- Sample Plan Output ---")
    for k, v in plan.items():
        print(f"  {k}: {str(v).encode('ascii', 'replace').decode('ascii')}")
    print("--------------------------\n")
    print("[PASS] test_sample_plan_confirmation_case passed")

if __name__ == "__main__":
    print("Running MacroSnap Calculation Engine Tests...\n")
    test_bmr_male()
    test_bmr_female()
    test_all_activity_levels()
    test_all_goals_and_intensities()
    test_sample_plan_confirmation_case()
    print("\nAll calculation engine tests passed successfully!")
