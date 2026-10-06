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

from typing import Dict, Any, Tuple

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

    Algorithm:
    1. Protein = weight_kg * goal_protein_per_kg (rounded to nearest gram)
       Protein Calories = Protein_g * 4
    2. Fat Calories = Target Calories * fat_pct (initially ~25%)
       Fat_g = max(10, round(Fat Calories / 9.0))
    3. Mathematical Alignment:
       Adjust Fat_g by at most ±1 or ±2 grams so that (target_calories - Protein Calories - Fat_g * 9)
       is an exact multiple of 4.
    4. Carbohydrates = (Target Calories - Protein Calories - Fat_g * 9) // 4
    5. Exact Calorie Equivalence Guaranteed:
       (Protein_g * 4) + (Carbs_g * 4) + (Fat_g * 9) == Target Calories.

    Returns:
        dict with protein_g, carbs_g, fat_g, protein_cals, carbs_cals, fat_cals, total_macro_cals
    """
    protein_ratio = GOAL_CONFIG.get(goal, {}).get("protein_per_kg", 1.8)

    # Step 1: Protein
    protein_g = round(weight_kg * protein_ratio)
    protein_cals = protein_g * 4

    # Step 2: Initial Fat (~25% of target calories)
    fat_cals_initial = target_calories * fat_pct
    fat_g = max(10, round(fat_cals_initial / 9.0))

    # Step 3: Align fat_g so remaining calories for carbs are divisible by 4
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
        fat_g -= 1

    fat_cals = fat_g * 9
    carb_cals_remaining = target_calories - protein_cals - fat_cals
    carbs_g = max(0, carb_cals_remaining // 4)

    final_protein_cals = protein_g * 4
    final_carbs_cals = carbs_g * 4
    final_fat_cals = fat_g * 9
    final_macro_cals = final_protein_cals + final_carbs_cals + final_fat_cals

    return {
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "protein_cals": final_protein_cals,
        "carbs_cals": final_carbs_cals,
        "fat_cals": final_fat_cals,
        "total_macro_cals": final_macro_cals,
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
    }
