import pytest
import math
from calculations import (
    calculate_bmr,
    calculate_tdee,
    calculate_target_calories,
    calculate_macros,
    calculate_full_plan,
    calculate_bmi,
    evaluate_health_safeguards,
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
                    
                    # Exact equivalence
                    assert plan["target_calories"] == plan["total_macro_cals"]

    print("[PASS] test_all_goals_and_intensities passed (all combinations verified)")


def test_phase_1_persona_case_1():
    """Case 1: Male, age 21, 180 cm, 48 kg, moderate activity, Lean Bulk, moderate surplus."""
    plan = calculate_full_plan(
        age=21,
        sex="Male",
        height_cm=180.0,
        weight_kg=48.0,
        activity_level="Moderately Active",
        goal="Lean Bulk",
        intensity="Moderate surplus"
    )
    assert plan["bmr"] == 1505.0
    assert plan["tdee"] == 2333
    assert plan["target_calories"] == 2566
    assert plan["protein_g"] == 86
    assert plan["fat_g"] == 70
    assert plan["carbs_g"] == 398
    assert (plan["protein_g"] * 4 + plan["fat_g"] * 9 + plan["carbs_g"] * 4) == 2566
    assert plan["bmi"] == 14.8
    assert plan["bmi_category"] == "Severe Underweight"
    assert any(adv["type"] == "severe_underweight" for adv in plan["health_advisories"])


def test_phase_1_persona_case_2():
    """Case 2: Male, age 21, 180 cm, 70 kg, moderate activity, maintain weight."""
    plan = calculate_full_plan(
        age=21,
        sex="Male",
        height_cm=180.0,
        weight_kg=70.0,
        activity_level="Moderately Active",
        goal="Maintenance",
        intensity="Maintenance"
    )
    assert plan["bmr"] == 1725.0
    assert plan["tdee"] == 2674
    assert plan["target_calories"] == 2674
    assert plan["protein_g"] == 112
    assert plan["fat_g"] == 74
    assert plan["carbs_g"] == 390
    assert (plan["protein_g"] * 4 + plan["fat_g"] * 9 + plan["carbs_g"] * 4) == 2674
    assert plan["bmi"] == 21.6
    assert plan["bmi_category"] == "Normal weight"


def test_phase_1_persona_case_3():
    """Case 3: Female, age 30, 165 cm, 60 kg, light activity, lose weight, mild intensity (Slow)."""
    plan = calculate_full_plan(
        age=30,
        sex="Female",
        height_cm=165.0,
        weight_kg=60.0,
        activity_level="Lightly Active",
        goal="Fat Loss",
        intensity="Slow"
    )
    assert plan["bmr"] == 1320.2
    assert plan["tdee"] == 1815
    assert plan["target_calories"] == 1634
    assert plan["protein_g"] == 108
    assert plan["fat_g"] == 46
    assert plan["carbs_g"] == 197
    assert (plan["protein_g"] * 4 + plan["fat_g"] * 9 + plan["carbs_g"] * 4) == 1634
    assert plan["bmi"] == 22.0


def test_macro_overflow_regression():
    """Verify that infeasible macro targets raise a structured ValueError rather than generating invalid macros."""
    with pytest.raises(ValueError) as excinfo:
        calculate_macros(weight_kg=100.0, target_calories=500, goal="Fat Loss")
    err_msg = str(excinfo.value)
    assert "mathematically infeasible" in err_msg
    assert "100.0 kg" in err_msg
    assert "500 kcal" in err_msg


def test_macro_valid_zero_carbs():
    """Verify that a target providing protein and fat without remaining carbs produces 0 carbs cleanly."""
    # 100 kg on Fat Loss -> protein is 180g (720 kcal). At 936 kcal, fat is 24g (216 kcal). Carbs is 0g.
    macros = calculate_macros(weight_kg=100.0, target_calories=936, goal="Fat Loss")
    assert macros["protein_g"] == 180
    assert macros["fat_g"] == 24
    assert macros["carbs_g"] == 0
    assert macros["total_macro_cals"] == 936


def test_bmr_non_finite_rejection():
    """Verify calculate_bmr rejects NaN, Infinity, and non-positive numbers."""
    with pytest.raises(ValueError, match="finite"):
        calculate_bmr(weight_kg=float("nan"), height_cm=170, age=25, sex="Male")
    with pytest.raises(ValueError, match="finite"):
        calculate_bmr(weight_kg=70, height_cm=float("inf"), age=25, sex="Male")
    with pytest.raises(ValueError, match="Weight must be greater than 0"):
        calculate_bmr(weight_kg=0, height_cm=170, age=25, sex="Male")
    with pytest.raises(ValueError, match="Height must be greater than 0"):
        calculate_bmr(weight_kg=70, height_cm=0, age=25, sex="Male")
    with pytest.raises(ValueError, match="Age must be greater than 0"):
        calculate_bmr(weight_kg=70, height_cm=170, age=0, sex="Male")
    with pytest.raises(ValueError, match="Invalid sex"):
        calculate_bmr(weight_kg=70, height_cm=170, age=25, sex="Invalid")


def test_health_safeguards_clinical_advisories():
    """Verify that health safeguards flag concerning BMI and calorie conditions."""
    safeguards = evaluate_health_safeguards(
        weight_kg=40.0,
        height_cm=175.0,
        age=22,
        sex="Female",
        target_calories=950,
        goal="Fat Loss"
    )
    assert safeguards["bmi"] == 13.1
    assert safeguards["bmi_category"] == "Severe Underweight"
    advisory_types = [a["type"] for a in safeguards["advisories"]]
    assert "severe_underweight" in advisory_types
    assert "underweight_deficit" in advisory_types
    assert "very_low_calories" in advisory_types
    # Verify non-diagnostic language is used
    for a in safeguards["advisories"]:
        assert "not medical" in a["message"] or "consult" in a["message"] or "guidance" in a["message"]


def test_target_calories_integer_requirement_and_booleans():
    """Verify that calculate_macros requires integer calorie targets and rejects fractional, boolean, and non-finite inputs."""
    # 1. Fractional / decimal calories must raise ValueError (not AssertionError)
    with pytest.raises(ValueError, match="must be an integer"):
        calculate_macros(weight_kg=70.0, target_calories=2000.5, goal="Maintenance")

    with pytest.raises(ValueError, match="must be an integer"):
        calculate_macros(weight_kg=70.0, target_calories=1500.25, goal="Fat Loss")

    # 2. Boolean inputs must be rejected
    with pytest.raises(ValueError, match="boolean"):
        calculate_macros(weight_kg=70.0, target_calories=True, goal="Maintenance")

    with pytest.raises(ValueError, match="boolean"):
        calculate_macros(weight_kg=70.0, target_calories=False, goal="Maintenance")

    with pytest.raises(ValueError, match="boolean"):
        calculate_macros(weight_kg=True, target_calories=2000, goal="Maintenance")

    # 3. Non-finite values
    with pytest.raises(ValueError, match="finite"):
        calculate_macros(weight_kg=70.0, target_calories=float("nan"), goal="Maintenance")
    with pytest.raises(ValueError, match="finite"):
        calculate_macros(weight_kg=70.0, target_calories=float("inf"), goal="Maintenance")
    with pytest.raises(ValueError, match="finite"):
        calculate_macros(weight_kg=70.0, target_calories=float("-inf"), goal="Maintenance")

    # 4. Zero and negative calories
    with pytest.raises(ValueError, match="greater than 0"):
        calculate_macros(weight_kg=70.0, target_calories=0, goal="Maintenance")
    with pytest.raises(ValueError, match="greater than 0"):
        calculate_macros(weight_kg=70.0, target_calories=-500, goal="Maintenance")

    # 5. Valid integer values (both int and float with .is_integer())
    res1 = calculate_macros(weight_kg=70.0, target_calories=2000, goal="Maintenance")
    assert res1["total_macro_cals"] == 2000
    res2 = calculate_macros(weight_kg=70.0, target_calories=2000.0, goal="Maintenance")
    assert res2["total_macro_cals"] == 2000


def test_fat_minimum_floor_at_rem_3_boundary():
    """Verify that fat alignment strictly maintains the >= 10g floor and never drops to 9g."""
    # Infeasible case: 30 kg adult on Fat Loss (54g protein = 216 kcal) with 317 kcal target.
    # At 317 kcal, initial fat=10g, rem=3. With >= 10g floor, fat becomes 13g (117 kcal).
    # 216 + 117 = 333 kcal > 317 kcal. Must be rejected as infeasible, never silently reduced to 9g.
    with pytest.raises(ValueError, match="mathematically infeasible"):
        calculate_macros(weight_kg=30.0, target_calories=317, goal="Fat Loss")

    # Feasible nearby case: 30 kg on Fat Loss with 345 kcal target.
    # rem_target = 345 - 216 = 129. rem = (129 - 10) % 4 = 3.
    # fat_g becomes 13g (117 kcal). carb_cals = 345 - 216 - 117 = 12 kcal (3g carbs).
    res = calculate_macros(weight_kg=30.0, target_calories=345, goal="Fat Loss")
    assert res["fat_g"] >= 10
    assert res["fat_g"] == 13
    assert res["protein_g"] == 54
    assert res["carbs_g"] == 3
    assert res["total_macro_cals"] == 345
    assert (res["protein_g"] * 4 + res["fat_g"] * 9 + res["carbs_g"] * 4) == 345

    # Sweep across low targets to confirm fat_g is NEVER < 10 for any returned plan
    for t in range(250, 500):
        for w in [30.0, 35.0, 40.0]:
            try:
                plan_macros = calculate_macros(weight_kg=w, target_calories=t, goal="Fat Loss")
                assert plan_macros["fat_g"] >= 10, f"fat_g dropped below 10: {plan_macros['fat_g']} at target {t}"
                assert plan_macros["total_macro_cals"] == t
            except ValueError:
                pass  # Infeasible plans properly rejected


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
    assert plan["target_calories"] == plan["total_macro_cals"]
    print("[PASS] test_sample_plan_confirmation_case passed")


if __name__ == "__main__":
    print("Running MacroSnap Calculation Engine Tests...\n")
    test_bmr_male()
    test_bmr_female()
    test_all_activity_levels()
    test_all_goals_and_intensities()
    test_phase_1_persona_case_1()
    test_phase_1_persona_case_2()
    test_phase_1_persona_case_3()
    test_macro_overflow_regression()
    test_macro_valid_zero_carbs()
    test_bmr_non_finite_rejection()
    test_health_safeguards_clinical_advisories()
    test_sample_plan_confirmation_case()
    print("\nAll calculation engine tests passed successfully!")
