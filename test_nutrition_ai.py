"""
Unit test suite for MacroSnap nutrition_ai.py module.
Verifies context construction, dynamic nutrition value injection,
safety rules, read-only guarantees, and error handling without requiring live API keys.
"""

from nutrition_ai import build_coach_context, query_nutrition_assistant, SYSTEM_COACH_PROMPT

def test_context_construction():
    user_plan = {
        "age": 28,
        "sex": "Female",
        "height_cm": 165,
        "weight_kg": 62,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate",
        "tdee": 2100,
        "target_calories": 1785,
        "protein_g": 112,
        "carbs_g": 180,
        "fat_g": 50,
    }

    consumed = {
        "calories": 1100,
        "protein_g": 70,
        "carbs_g": 120,
        "fat_g": 30,
    }

    today_meals = [
        {
            "meal_id": "m1",
            "meal_type": "Breakfast",
            "foods": [{"name": "Greek Yogurt & Berries", "portion": "200g"}],
            "total": {"calories": 350, "protein_g": 25, "carbs_g": 40, "fat_g": 5},
        },
        {
            "meal_id": "m2",
            "meal_type": "Lunch",
            "foods": [{"name": "Chicken Wrap", "portion": "1 wrap"}],
            "total": {"calories": 750, "protein_g": 45, "carbs_g": 80, "fat_g": 25},
        },
    ]

    context = build_coach_context(user_plan, consumed, today_meals)

    # 1. Profile values check
    assert "Age: 28" in context
    assert "Female" in context
    assert "62 kg" in context
    assert "Fat Loss" in context

    # 2. Target check
    assert "1,785 kcal" in context
    assert "Protein: 112 g" in context

    # 3. Consumed check
    assert "1,100 kcal" in context
    assert "Protein Consumed: 70 g" in context

    # 4. Remaining check (1785 - 1100 = 685, 112 - 70 = 42)
    assert "Calories Remaining: 685 kcal" in context
    assert "Protein Remaining: 42 g" in context

    # 5. Today's meals check
    assert "Greek Yogurt & Berries" in context
    assert "Chicken Wrap" in context

    # 6. Check that Python is marked as source of truth
    assert "Calculated by Python" in context
    print("[PASS] test_context_construction passed")


def test_dynamic_context_refresh_after_new_meal():
    user_plan = {"target_calories": 2000, "protein_g": 150, "carbs_g": 200, "fat_g": 60}
    consumed_before = {"calories": 500, "protein_g": 40, "carbs_g": 50, "fat_g": 15}
    today_meals_before = [
        {"meal_type": "Breakfast", "foods": [{"name": "Eggs"}], "total": {"calories": 500, "protein_g": 40, "carbs_g": 50, "fat_g": 15}}
    ]

    ctx_before = build_coach_context(user_plan, consumed_before, today_meals_before)
    assert "Calories Remaining: 1,500 kcal" in ctx_before

    # Simulate logging a new lunch meal of 700 kcal
    consumed_after = {"calories": 1200, "protein_g": 90, "carbs_g": 120, "fat_g": 35}
    today_meals_after = today_meals_before + [
        {"meal_type": "Lunch", "foods": [{"name": "Steak Bowl"}], "total": {"calories": 700, "protein_g": 50, "carbs_g": 70, "fat_g": 20}}
    ]

    ctx_after = build_coach_context(user_plan, consumed_after, today_meals_after)
    assert "Calories Remaining: 800 kcal" in ctx_after
    assert "Steak Bowl" in ctx_after
    print("[PASS] test_dynamic_context_refresh_after_new_meal passed")


def test_system_prompt_read_only_rules():
    assert "READ-ONLY" in SYSTEM_COACH_PROMPT
    assert "single source of truth" in SYSTEM_COACH_PROMPT.lower()
    assert "medical" in SYSTEM_COACH_PROMPT.lower()
    print("[PASS] test_system_prompt_read_only_rules passed")


def test_empty_prompt_and_missing_key_handling():
    # Empty prompt check
    success, msg = query_nutrition_assistant("", {}, {}, [])
    assert success is False
    assert "Please enter a question" in msg

    # Missing API key test (without configuring key)
    success_api, msg_api = query_nutrition_assistant("What should I eat?", {}, {}, [])
    # Should either report missing key or failure gracefully without crashing
    assert isinstance(success_api, bool)
    assert isinstance(msg_api, str)
    print("[PASS] test_empty_prompt_and_missing_key_handling passed")


if __name__ == "__main__":
    print("Running MacroSnap Nutrition AI Assistant Tests...\n")
    test_context_construction()
    test_dynamic_context_refresh_after_new_meal()
    test_system_prompt_read_only_rules()
    test_empty_prompt_and_missing_key_handling()
    print("\nAll Nutrition AI Assistant tests passed successfully!")
