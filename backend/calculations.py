"""
MacroSnap Calculation Engine
============================
Deterministic calculation module for BMR, TDEE, goal-adjusted calorie targets,
and daily macronutrient distributions.

All calculations follow standard scientific formulas:
- BMR: Mifflin-St Jeor Equation
- TDEE: BMR x Activity Level Multiplier
- Calorie Targets: Deficit or surplus based on goal & intensity percentage
- Macro Targets: Protein based on body weight & goal; Fat at ~25% of calories;
  Carbs fill the remaining calories.

IMPORTANT: All macro targets mathematically correspond to the target calories:
(Protein_g * 4) + (Fat_g * 9) + (Carbs_g * 4) == Target Calories.
"""

import math
from typing import Dict, Any, Tuple, List, Optional

# Standard Activity Multipliers (Mifflin-St Jeor TDEE)
ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "Sedentary": 1.2,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
    "Extremely Active": 1.9,
}

ACTIVITY_DESCRIPTIONS: Dict[str, str] = {
    "Sedentary": "Little or no exercise",
    "Lightly Active": "Exercise 1–3 days/week",
    "Moderately Active": "Exercise 3–5 days/week",
    "Very Active": "Exercise 6–7 days/week",
    "Extremely Active": "Hard training / physically demanding activity",
}

# Fitness Goals and Intensity Configurations
GOAL_CONFIG: Dict[str, Dict[str, Any]] = {
    "Fat Loss": {
        "emoji": "🔥",
        "description": "Reduce body fat",
        "intensities": {
            "Slow": {"type": "deficit", "pct": 0.10, "label": "10% deficit (Slow)"},
            "Moderate": {"type": "deficit", "pct": 0.15, "label": "15% deficit (Moderate)"},
            "Aggressive": {"type": "deficit", "pct": 0.20, "label": "20% deficit (Aggressive)"},
        },
        "protein_per_kg": 1.8,
    },
    "Body Recomposition": {
        "emoji": "⚖️",
        "description": "Reduce body fat while building/maintaining muscle",
        "intensities": {
            "Small deficit": {"type": "deficit", "pct": 0.05, "label": "5% deficit"},
            "Around maintenance": {"type": "maintenance", "pct": 0.00, "label": "0% deficit"},
        },
        "protein_per_kg": 2.0,
    },
    "Lean Bulk": {
        "emoji": "💪",
        "description": "Build muscle with controlled weight gain",
        "intensities": {
            "Conservative surplus": {"type": "surplus", "pct": 0.05, "label": "5% surplus"},
            "Moderate surplus": {"type": "surplus", "pct": 0.10, "label": "10% surplus"},
        },
        "protein_per_kg": 1.8,
    },
    "Maintenance": {
        "emoji": "⚖️",
        "description": "Maintain current body weight",
        "intensities": {
            "Maintenance": {"type": "maintenance", "pct": 0.00, "label": "0% adjustment"},
        },
        "protein_per_kg": 1.6,
    },
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """
    Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Male:   BMR = (10 x weight_kg) + (6.25 x height_cm) - (5 x age) + 5
    Female: BMR = (10 x weight_kg) + (6.25 x height_cm) - (5 x age) - 161
    """
    for val, name in [(weight_kg, "Weight"), (height_cm, "Height"), (age, "Age")]:
        if type(val) is bool or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"{name} must be a valid finite number")

    if weight_kg <= 0:
        raise ValueError("Weight must be greater than 0 kg")
    if height_cm <= 0:
        raise ValueError("Height must be greater than 0 cm")
    if age <= 0:
        raise ValueError("Age must be greater than 0")

    sex_normalized = sex.strip().capitalize()
    if sex_normalized == "Male":
        return (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + 5.0
    elif sex_normalized == "Female":
        return (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) - 161.0
    else:
        raise ValueError(f"Invalid sex '{sex}'. Expected 'Male' or 'Female'.")


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Calculate Total Daily Energy Expenditure (TDEE / Maintenance Calories).
    TDEE = BMR x Activity Multiplier
    """
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise ValueError(
            f"Invalid activity level '{activity_level}'. Allowed values: {list(ACTIVITY_MULTIPLIERS.keys())}"
        )
    return bmr * ACTIVITY_MULTIPLIERS[activity_level]


def calculate_target_calories(tdee: float, goal: str, intensity: str) -> Tuple[int, str, int]:
    """
    Calculate daily calorie target based on fitness goal and goal intensity.

    Returns:
        (target_calories, adjustment_type, adjustment_kcal)
        where adjustment_type is 'Deficit', 'Surplus', or 'Maintenance'
        and adjustment_kcal is the absolute difference between TDEE and target_calories.
    """
    if goal not in GOAL_CONFIG:
        raise ValueError(f"Invalid goal '{goal}'. Allowed values: {list(GOAL_CONFIG.keys())}")

    intensities = GOAL_CONFIG[goal]["intensities"]
    if intensity not in intensities:
        raise ValueError(
            f"Invalid intensity '{intensity}' for goal '{goal}'. Allowed values: {list(intensities.keys())}"
        )

    config = intensities[intensity]
    adj_type = config["type"]
    pct = config["pct"]

    if adj_type == "deficit":
        target = round(tdee * (1.0 - pct))
        adjustment_type = "Deficit"
    elif adj_type == "surplus":
        target = round(tdee * (1.0 + pct))
        adjustment_type = "Surplus"
    else:
        target = round(tdee)
        adjustment_type = "Maintenance"

    adjustment_kcal = abs(target - round(tdee))
    return target, adjustment_type, adjustment_kcal


def calculate_macros(weight_kg: float, target_calories: int, goal: str, fat_pct: float = 0.25) -> Dict[str, int]:
    """
    Calculate macronutrient distribution (Protein, Carbohydrates, Fat in grams).

    Algorithm & Contract:
    1. Calorie targets represent daily energy in whole kilocalories (kcal) and MUST be integers.
       Fractional/decimal targets (e.g. 2000.5), booleans, non-finite values (NaN/inf),
       and zero/negative values are rejected at validation boundary.
    2. Protein = round(weight_kg * goal_protein_per_kg)
       Protein Calories = Protein_g * 4
    3. Initial Fat Calories = target_calories * fat_pct (initially ~25%)
       Fat_g = max(10, round(Fat Calories / 9.0))  # Minimum 10g floor
    4. Mathematical Modulo-4 Alignment:
       Adjust Fat_g so that (target_calories - Protein Calories - Fat_g * 9) is an exact multiple of 4.
       - rem == 1: fat_g += 1  (>= 11g)
       - rem == 2: fat_g -= 2 if fat_g - 2 >= 10 else fat_g += 2  (>= 10g)
       - rem == 3: fat_g -= 1 if fat_g - 1 >= 10 else fat_g += 3  (>= 10g)
       Guarantees fat_g >= 10g across all alignment branches without dropping to 9g.
    5. Feasibility Guard:
       If the remaining calories after protein and fat are negative, the target is mathematically
       infeasible under the configured rules. Raise ValueError with a clear breakdown rather than
       silently altering targets or generating macro calories exceeding target calories.
    6. Carbohydrates = (target_calories - Protein Calories - Fat_g * 9) // 4
    7. Exact Calorie Equivalence Guaranteed:
       (Protein_g * 4) + (Carbs_g * 4) + (Fat_g * 9) == Target Calories.

    Returns:
        dict with protein_g, carbs_g, fat_g, protein_cals, carbs_cals, fat_cals, total_macro_cals
    """
    if type(weight_kg) is bool:
        raise ValueError("Weight cannot be a boolean value.")
    if not isinstance(weight_kg, (int, float)) or math.isnan(weight_kg) or math.isinf(weight_kg):
        raise ValueError("Weight must be a valid finite number")
    if weight_kg <= 0:
        raise ValueError(f"Weight must be greater than 0 kg. Got: {weight_kg}")

    if type(target_calories) is bool:
        raise ValueError("Target calories cannot be a boolean value.")
    if not isinstance(target_calories, (int, float)) or math.isnan(target_calories) or math.isinf(target_calories):
        raise ValueError("Target calories must be a valid finite number")
    if isinstance(target_calories, float) and not target_calories.is_integer():
        raise ValueError(f"Target calories must be an integer, got non-integer value: {target_calories}")
    if target_calories <= 0:
        raise ValueError(f"Target calories must be greater than 0. Got: {target_calories}")

    target_calories = int(target_calories)
    protein_ratio = GOAL_CONFIG.get(goal, {}).get("protein_per_kg", 1.8)

    # Step 1: Protein
    protein_g = round(weight_kg * protein_ratio)
    protein_cals = protein_g * 4

    # Step 2: Initial Fat (~25% of target calories, minimum 10g)
    fat_cals_initial = target_calories * fat_pct
    fat_g = max(10, round(fat_cals_initial / 9.0))

    # Step 3: Align fat_g so remaining calories for carbs are divisible by 4 while respecting >= 10g floor
    rem_target = target_calories - protein_cals
    rem = (rem_target - fat_g) % 4

    if rem == 1:
        fat_g += 1
    elif rem == 2:
        if fat_g - 2 >= 10:
            fat_g -= 2
        else:
            fat_g += 2
    elif rem == 3:
        if fat_g - 1 >= 10:
            fat_g -= 1
        else:
            fat_g += 3

    fat_cals = fat_g * 9
    carb_cals_remaining = target_calories - protein_cals - fat_cals

    # Step 4: Feasibility Check
    # If carb_cals_remaining < 0, protein + fat exceed target calories.
    # We must not silently alter protein or fat, nor generate macro sum > target_calories.
    if carb_cals_remaining < 0:
        deficit_amount = abs(carb_cals_remaining)
        raise ValueError(
            f"Target of {target_calories} kcal is mathematically infeasible under configured macro rules for "
            f"weight {weight_kg} kg and goal '{goal}'. Required protein ({protein_g}g = {protein_cals} kcal) "
            f"and minimum fat ({fat_g}g = {fat_cals} kcal) total {protein_cals + fat_cals} kcal, "
            f"exceeding target calories by {deficit_amount} kcal."
        )

    carbs_g = carb_cals_remaining // 4

    final_protein_cals = protein_g * 4
    final_carbs_cals = carbs_g * 4
    final_fat_cals = fat_g * 9
    final_macro_cals = final_protein_cals + final_carbs_cals + final_fat_cals

    # Exact invariance
    assert final_macro_cals == target_calories, (
        f"Macro calorie mismatch: {final_macro_cals} != {target_calories}"
    )

    return {
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "protein_cals": final_protein_cals,
        "carbs_cals": final_carbs_cals,
        "fat_cals": final_fat_cals,
        "total_macro_cals": final_macro_cals,
    }


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index (BMI = kg / m^2) rounded to 1 decimal place."""
    for val, name in [(weight_kg, "Weight"), (height_cm, "Height")]:
        if type(val) is bool or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"{name} must be a valid finite number to calculate BMI.")
    if height_cm <= 0:
        raise ValueError("Height must be greater than 0 cm to calculate BMI.")
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than 0 kg to calculate BMI.")
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m * height_m), 1)


def evaluate_health_safeguards(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    target_calories: int,
    goal: str,
) -> Dict[str, Any]:
    """
    Evaluates health and clinical advisories for user metrics and targets.
    Kept separate from mathematical BMR/TDEE calculations so calculation accuracy
    remains independently testable.
    """
    bmi = calculate_bmi(weight_kg=weight_kg, height_cm=height_cm)
    advisories: List[Dict[str, str]] = []

    # 1. Very low BMI (Underweight / Severe Thinness)
    if bmi < 16.0:
        advisories.append({
            "type": "severe_underweight",
            "severity": "critical",
            "message": (
                f"Your calculated Body Mass Index (BMI) of {bmi} indicates severe underweight. "
                "Automated calorie and macronutrient formulas are not medical clearance. Revelation strongly "
                "advises consulting a qualified healthcare professional or physician for a comprehensive clinical "
                "assessment before starting or following any nutrition plan."
            ),
        })
    elif bmi < 18.5:
        advisories.append({
            "type": "underweight",
            "severity": "warning",
            "message": (
                f"Your calculated Body Mass Index (BMI) of {bmi} is in the underweight range. "
                "Estimated calorie targets may not account for individual metabolic needs or health requirements. "
                "We recommend consulting with a healthcare professional."
            ),
        })

    # 2. Underweight with Bulking or Calorie Deficit
    if bmi < 18.5:
        if goal == "Lean Bulk":
            advisories.append({
                "type": "underweight_bulking",
                "severity": "advisory",
                "message": (
                    "An automated weight-gain or muscle-building calorie target does not establish medical "
                    "safety or clinical guidance for underweight recovery. Please consult a physician."
                ),
            })
        elif goal == "Fat Loss":
            advisories.append({
                "type": "underweight_deficit",
                "severity": "warning",
                "message": (
                    f"A calorie-deficit goal is not clinically advised for an underweight BMI ({bmi}). "
                    "Please consult a physician or registered dietitian before attempting weight reduction."
                ),
            })

    # 3. Unusually low calorie targets (< 1200 kcal for general, or < 1500 kcal for adult male)
    sex_norm = str(sex).strip().capitalize()
    if target_calories < 1200:
        advisories.append({
            "type": "very_low_calories",
            "severity": "warning",
            "message": (
                f"The calculated daily calorie target ({target_calories} kcal) is very low. Very low-calorie diets "
                "require professional healthcare supervision to ensure nutritional adequacy and prevent deficiencies. "
                "This target should not be followed without clinical guidance."
            ),
        })
    elif sex_norm == "Male" and target_calories < 1500:
        advisories.append({
            "type": "low_calories_male",
            "severity": "advisory",
            "message": (
                f"The calculated daily calorie target ({target_calories} kcal) is below typical clinical reference "
                "intakes for adult males (1,500 kcal). Consider a more moderate deficit."
            ),
        })

    category = "Normal weight"
    if bmi < 16.0:
        category = "Severe Underweight"
    elif bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal weight"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obesity"

    return {
        "bmi": bmi,
        "bmi_category": category,
        "advisories": advisories,
        "has_warnings": len(advisories) > 0,
    }


def calculate_full_plan(
    age: int,
    sex: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
    intensity: str,
) -> Dict[str, Any]:
    """
    High-level engine function: takes user parameters and computes the full MacroSnap Plan.

    Returns complete plan dictionary containing BMR, TDEE, Target Calories, Macros, and Metadata.
    """
    bmr = calculate_bmr(weight_kg=weight_kg, height_cm=height_cm, age=age, sex=sex)
    tdee = calculate_tdee(bmr=bmr, activity_level=activity_level)
    target_calories, adj_type, adj_kcal = calculate_target_calories(tdee=tdee, goal=goal, intensity=intensity)
    macros = calculate_macros(weight_kg=weight_kg, target_calories=target_calories, goal=goal)

    safeguards = evaluate_health_safeguards(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        sex=sex,
        target_calories=target_calories,
        goal=goal,
    )

    return {
        "age": age,
        "sex": sex,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "activity_level": activity_level,
        "activity_description": ACTIVITY_DESCRIPTIONS.get(activity_level, ""),
        "goal": goal,
        "goal_emoji": GOAL_CONFIG.get(goal, {}).get("emoji", "🎯"),
        "intensity": intensity,
        "bmr": round(bmr, 1),
        "tdee": round(tdee),
        "target_calories": target_calories,
        "adjustment_type": adj_type,
        "adjustment_kcal": adj_kcal,
        "protein_g": macros["protein_g"],
        "carbs_g": macros["carbs_g"],
        "fat_g": macros["fat_g"],
        "protein_cals": macros["protein_cals"],
        "carbs_cals": macros["carbs_cals"],
        "fat_cals": macros["fat_cals"],
        "total_macro_cals": macros["total_macro_cals"],
        "bmi": safeguards["bmi"],
        "bmi_category": safeguards["bmi_category"],
        "health_advisories": safeguards["advisories"],
    }
