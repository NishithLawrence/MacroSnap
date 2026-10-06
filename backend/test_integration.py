import os
import sys
import math
import tempfile
import json
import unittest
from datetime import datetime, date, timedelta

# Import MacroSnap modules
import calculations
import profile_storage
import target_storage
import meal_storage
import weight_storage
import nutrition_ai
import analytics

class TestMacroSnapIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for isolation
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_dir = os.path.join(self.test_dir.name, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Override file paths in storage modules for isolated testing
        self.orig_profile_path = profile_storage.PROFILE_FILE
        self.orig_target_path = target_storage.TARGET_FILE
        self.orig_meal_path = meal_storage.STORAGE_FILE
        self.orig_weight_path = weight_storage.WEIGHT_FILE

        profile_storage.PROFILE_FILE = os.path.join(self.data_dir, "profile.json")
        target_storage.TARGET_FILE = os.path.join(self.data_dir, "target_history.json")
        meal_storage.STORAGE_FILE = os.path.join(self.data_dir, "meals.json")
        weight_storage.WEIGHT_FILE = os.path.join(self.data_dir, "weight_history.json")

    def tearDown(self):
        # Restore original paths and cleanup temp dir
        profile_storage.PROFILE_FILE = self.orig_profile_path
        target_storage.TARGET_FILE = self.orig_target_path
        meal_storage.STORAGE_FILE = self.orig_meal_path
        weight_storage.WEIGHT_FILE = self.orig_weight_path
        self.test_dir.cleanup()

    def test_full_end_to_end_user_journey(self):
        """
        Tests the complete pipeline:
        Profile -> Target Snapshot -> Meal -> Daily Totals -> Coach Context -> Analytics -> Profile Edit -> Snapshot B -> Date Resolution
        """
        # Step 1: User Onboarding Profile Creation
        profile_data = {
            "age": 28,
            "sex": "Male",
            "height_cm": 178.0,
            "weight_kg": 75.0,
            "activity_level": "Moderately Active",
            "activity_description": "Exercise 3-5 days/week",
            "goal": "Fat Loss",
            "goal_emoji": "🔥",
            "intensity": "Moderate",
            "bmr": 1716.25,
            "tdee": 2660,
            "target_calories": 2261,
            "adjustment_type": "Deficit",
            "adjustment_kcal": 399,
            "protein_g": 150,
            "carbs_g": 272,
            "fat_g": 63,
            "protein_cals": 600,
            "carbs_cals": 1088,
            "fat_cals": 567,
            "total_macro_cals": 2255
        }
        
        # Save profile
        self.assertTrue(profile_storage.save_profile(profile_data))
        loaded_profile = profile_storage.load_profile()
        self.assertEqual(loaded_profile["age"], 28)
        self.assertEqual(loaded_profile["target_calories"], 2261)

        # Step 2: Initial Target Snapshot Creation
        today_str = date.today().isoformat()
        ok_a, snap_a = target_storage.create_target_snapshot(profile_data, effective_date=today_str)
        self.assertTrue(ok_a)
        self.assertIsNotNone(snap_a)
        self.assertEqual(snap_a["calorie_target"], 2261)

        # Step 3: Meal Logging and Deterministic Recalculation
        meal_1 = {
            "meal_id": "integration_meal_1",
            "meal_type": "Breakfast",
            "date": today_str,
            "timestamp": "08:30:00",
            "notes": "Oatmeal with protein powder",
            "foods": [
                {"name": "Oatmeal", "portion": "1 cup", "calories": 150, "protein_g": 5, "carbs_g": 27, "fat_g": 3},
                {"name": "Whey Scoop", "portion": "30g", "calories": 120, "protein_g": 24, "carbs_g": 2, "fat_g": 1.5}
            ]
        }
        
        saved_ok = meal_storage.add_meal(meal_1)
        self.assertTrue(saved_ok)
        all_meals = meal_storage.load_meals()
        self.assertIn("integration_meal_1", all_meals)
        saved_meal = all_meals["integration_meal_1"]
        self.assertEqual(saved_meal["total"]["calories"], 270)
        self.assertEqual(saved_meal["total"]["protein_g"], 29.0)

        # Retrieve today's daily totals
        today_totals = meal_storage.get_daily_totals(today_str)
        self.assertEqual(today_totals["calories"], 270)
        self.assertEqual(today_totals["protein_g"], 29)

        # Step 4: Coach Context Integration
        user_plan = profile_data
        coach_context = nutrition_ai.build_coach_context(user_plan, today_totals, [saved_meal])
        self.assertIn("Fat Loss", coach_context)
        self.assertIn("2,261 kcal", coach_context)
        self.assertIn("270 kcal", coach_context)
        self.assertIn("29 g", coach_context)

        # Step 5: Target Change & Snapshots
        # User changes goal to Lean Bulk 5 days later
        future_date_str = (date.today() + timedelta(days=5)).isoformat()
        new_profile = dict(profile_data)
        new_profile["goal"] = "Lean Bulk"
        new_profile["intensity"] = "Moderate surplus"
        new_profile["target_calories"] = 2800

        ok_b, snap_b = target_storage.create_target_snapshot(new_profile, effective_date=future_date_str)
        self.assertTrue(ok_b)
        self.assertIsNotNone(snap_b)

        # Resolution for today resolves to Snapshot A (2261 kcal)
        resolved_today = target_storage.get_target_for_date(today_str)
        self.assertEqual(resolved_today["calorie_target"], 2261)

        # Resolution for future_date_str resolves to Snapshot B (2800 kcal)
        resolved_future = target_storage.get_target_for_date(future_date_str)
        self.assertEqual(resolved_future["calorie_target"], 2800)

        # Step 6: Analytics Target Snapshot Resolution
        analytics_data = analytics.get_period_summary(
            days=7,
            target_calories=2261,
            target_protein=150,
            target_carbs=272,
            target_fat=63,
            goal="Fat Loss",
            tdee=2660
        )
        self.assertEqual(analytics_data["averages"]["tracked_days"], 1)
        self.assertEqual(analytics_data["days_period"], 7)

    def test_invalid_input_rejections(self):
        """Tests that invalid inputs (negative values, NaN, Inf) are rejected across storage layers."""
        invalid_profile = {
            "age": -5,
            "sex": "Male",
            "height_cm": 180,
            "weight_kg": float('nan'),
            "activity_level": "Moderately Active",
            "goal": "Fat Loss",
            "intensity": "Moderate"
        }
        self.assertFalse(profile_storage.save_profile(invalid_profile))

        invalid_meal = {
            "meal_id": "invalid_1",
            "meal_type": "Lunch",
            "date": date.today().isoformat(),
            "foods": [
                {"name": "Bad Food", "portion": "100g", "calories": -500, "protein_g": float('inf'), "carbs_g": 0, "fat_g": 0}
            ]
        }
        self.assertFalse(meal_storage.add_meal(invalid_meal))

    def test_corrupted_storage_recovery(self):
        """Tests safe handling of corrupted JSON files."""
        # Corrupt profile file
        with open(profile_storage.PROFILE_FILE, "w", encoding="utf-8") as f:
            f.write("{corrupt json...")
        
        self.assertIsNone(profile_storage.load_profile())

        # Corrupt target storage file
        with open(target_storage.TARGET_FILE, "w", encoding="utf-8") as f:
            f.write("{corrupt target history...")
            
        history = target_storage.load_target_snapshots()
        self.assertEqual(history, [])

def run_tests():
    print("Running MacroSnap Integration Tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMacroSnapIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("\n[PASS] All Integration Tests Passed Successfully!")

if __name__ == "__main__":
    run_tests()
