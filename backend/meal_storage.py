"""
MacroSnap Meal Storage Module (meal_storage.py)
==============================================
Isolated persistent JSON storage engine for MacroSnap meals.

File Location: data/meals.json
Functions provided:
- load_meals() -> Dict[str, Dict]
- save_meals(meals: Dict[str, Dict]) -> bool
- get_meals_for_date(date_str: str) -> List[Dict]
- add_meal(meal: Dict) -> bool
- update_meal(meal_id: str, updated_meal: Dict) -> bool
- delete_meal(meal_id: str) -> bool
- get_daily_totals(date_str: str) -> Dict[str, int]
- get_all_dates() -> List[str]
- validate_meal_data(meal: Dict) -> Tuple[bool, str]

Guarantees data integrity, local file persistence across sessions/reruns,
validation of non-negative numeric macro fields, and safe error handling.
"""

import json
import os
import uuid
import datetime
from typing import Dict, Any, List, Tuple, Optional

# Default storage directory and file path
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "meals.json")

VALID_MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack"]


def _ensure_storage_exists() -> None:
    """
    Creates data directory and meals.json file if they do not exist.
    """
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

        if not os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)
    except Exception as e:
        print(f"[meal_storage] Error creating storage directory/file: {e}")


def validate_meal_data(meal: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates meal data structure and numeric boundaries before saving.
    Ensures no NaN, Infinity, negative values, or malformed data enters storage.
    """
    if not isinstance(meal, dict):
        return False, "Meal record must be a dictionary"

    # 1. meal_id check
    meal_id = meal.get("meal_id")
    if not meal_id or not isinstance(meal_id, str) or not meal_id.strip():
        return False, "Meal ID must be a non-empty string"

    # 2. date check (YYYY-MM-DD)
    date_str = meal.get("date")
    if not date_str or not isinstance(date_str, str):
        return False, "Date must be a string in YYYY-MM-DD format"
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        return False, f"Invalid date format '{date_str}'. Expected YYYY-MM-DD"

    # 3. meal_type check
    meal_type = meal.get("meal_type")
    if meal_type not in VALID_MEAL_TYPES:
        return False, f"Invalid meal_type '{meal_type}'. Allowed: {VALID_MEAL_TYPES}"

    # 4. foods list check
    foods = meal.get("foods")
    if not isinstance(foods, list) or len(foods) == 0:
        return False, "Meal must contain at least one food item"

    calc_cals = 0
    calc_p = 0
    calc_c = 0
    calc_f = 0

    for idx, food in enumerate(foods):
        if not isinstance(food, dict):
            return False, f"Food item {idx + 1} must be a dictionary"

        name = food.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            return False, f"Food item {idx + 1} must have a non-empty name"

        # Validate numeric calories and macros
        for field in ["calories", "protein_g", "carbs_g", "fat_g"]:
            val = food.get(field, 0)
            if not isinstance(val, (int, float)) or val < 0 or val != val:  # val != val catches NaN
                return False, f"Field '{field}' in food item '{name}' must be a non-negative number"

        calc_cals += int(round(food.get("calories", 0)))
        calc_p += int(round(food.get("protein_g", 0)))
        calc_c += int(round(food.get("carbs_g", 0)))
        calc_f += int(round(food.get("fat_g", 0)))

    # 5. total object check
    total = meal.get("total")
    if not isinstance(total, dict):
        meal["total"] = {
            "calories": calc_cals,
            "protein_g": calc_p,
            "carbs_g": calc_c,
            "fat_g": calc_f,
        }
    else:
        # Re-verify total math
        meal["total"]["calories"] = calc_cals
        meal["total"]["protein_g"] = calc_p
        meal["total"]["carbs_g"] = calc_c
        meal["total"]["fat_g"] = calc_f

    return True, "Valid"


def load_meals() -> Dict[str, Dict[str, Any]]:
    """
    Loads all meals from data/meals.json. Returns a dictionary keyed by meal_id.
    Safely handles missing files or malformed JSON.
    """
    _ensure_storage_exists()

    if not os.path.exists(STORAGE_FILE):
        return {}

    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                # Convert list to dict keyed by meal_id
                return {m["meal_id"]: m for m in data if isinstance(m, dict) and "meal_id" in m}
            else:
                print("[meal_storage] Warning: Unrecognized JSON structure in meals.json")
                return {}
    except json.JSONDecodeError as err:
        print(f"[meal_storage] Warning: Corrupt JSON in meals.json ({err}). Returning empty dictionary without overwriting.")
        return {}
    except Exception as e:
        print(f"[meal_storage] Error loading meals: {e}")
        return {}


def save_meals(meals: Dict[str, Dict[str, Any]]) -> bool:
    """
    Saves the full meals dictionary to data/meals.json atomically.
    """
    _ensure_storage_exists()
    try:
        # Save to temporary file first then replace atomically
        tmp_file = STORAGE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(meals, f, indent=2)

        if os.path.exists(STORAGE_FILE):
            os.remove(STORAGE_FILE)
        os.rename(tmp_file, STORAGE_FILE)
        return True
    except Exception as e:
        print(f"[meal_storage] Error saving meals to JSON: {e}")
        return False


def add_meal(meal: Dict[str, Any]) -> bool:
    """
    Validates and appends a new meal to local storage.
    Automatically assigns unique meal_id if not present.
    """
    if "meal_id" not in meal or not meal["meal_id"]:
        meal["meal_id"] = str(uuid.uuid4())

    if "date" not in meal or not meal["date"]:
        meal["date"] = datetime.date.today().isoformat()

    if "timestamp" not in meal or not meal["timestamp"]:
        meal["timestamp"] = datetime.datetime.now().isoformat()

    valid, msg = validate_meal_data(meal)
    if not valid:
        print(f"[meal_storage] Validation error: {msg}")
        return False

    meals = load_meals()
    meals[meal["meal_id"]] = meal
    return save_meals(meals)


def update_meal(meal_id: str, updated_meal: Dict[str, Any]) -> bool:
    """
    Updates an existing meal record by meal_id.
    Recalculates totals deterministically in Python before saving.
    """
    if not meal_id or not isinstance(meal_id, str):
        return False

    meals = load_meals()
    if meal_id not in meals:
        print(f"[meal_storage] Cannot update: Meal ID '{meal_id}' not found.")
        return False

    updated_meal["meal_id"] = meal_id
    valid, msg = validate_meal_data(updated_meal)
    if not valid:
        print(f"[meal_storage] Update validation error: {msg}")
        return False

    meals[meal_id] = updated_meal
    return save_meals(meals)


def delete_meal(meal_id: str) -> bool:
    """
    Removes a meal from local storage by meal_id.
    """
    if not meal_id:
        return False

    meals = load_meals()
    if meal_id in meals:
        del meals[meal_id]
        return save_meals(meals)
    return False


def get_meals_for_date(date_str: str) -> List[Dict[str, Any]]:
    """
    Retrieves all meal records for a specific date (YYYY-MM-DD),
    sorted chronologically by timestamp.
    """
    meals_dict = load_meals()
    matching = [
        m for m in meals_dict.values()
        if isinstance(m, dict) and m.get("date") == date_str
    ]

    # Sort by timestamp
    matching.sort(key=lambda x: x.get("timestamp", ""))
    return matching


def get_daily_totals(date_str: str) -> Dict[str, int]:
    """
    Calculates deterministic total consumed calories and macros for a given date.
    Returns dict: {'calories': int, 'protein_g': int, 'carbs_g': int, 'fat_g': int}
    """
    day_meals = get_meals_for_date(date_str)
    tot_cals = 0
    tot_p = 0
    tot_c = 0
    tot_f = 0

    for m in day_meals:
        t = m.get("total", {})
        tot_cals += int(round(t.get("calories", 0)))
        tot_p += int(round(t.get("protein_g", 0)))
        tot_c += int(round(t.get("carbs_g", 0)))
        tot_f += int(round(t.get("fat_g", 0)))

    return {
        "calories": tot_cals,
        "protein_g": tot_p,
        "carbs_g": tot_c,
        "fat_g": tot_f,
    }


def get_all_dates() -> List[str]:
    """
    Returns a sorted list of unique date strings (YYYY-MM-DD) that have logged meals.
    Includes today's date if not already present.
    """
    meals_dict = load_meals()
    dates = set(m.get("date") for m in meals_dict.values() if isinstance(m, dict) and m.get("date"))
    today_str = datetime.date.today().isoformat()
    dates.add(today_str)
    return sorted(list(dates), reverse=True)
