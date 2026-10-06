"""
MacroSnap Profile Storage Engine (profile_storage.py)
=====================================================
Isolated persistent storage module for MacroSnap user profile data.

File Location: data/profile.json
Data Model:
{
  "age": 25,
  "sex": "Male",
  "height_cm": 178.0,
  "weight_kg": 75.0,
  "activity_level": "Moderately Active",
  "goal": "Fat Loss",
  "intensity": "Moderate",
  "updated_at": "2026-10-05T09:00:00"
}

Functions provided:
- load_profile() -> Optional[Dict]
- save_profile(profile_data: Dict) -> bool
- validate_profile_data(profile_data: Dict) -> Tuple[bool, str]
"""

import json
import os
import datetime
from typing import Dict, Any, Tuple, Optional
from calculations import ACTIVITY_MULTIPLIERS, GOAL_CONFIG

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")


def _ensure_profile_storage_exists() -> None:
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
    except Exception as e:
        print(f"[profile_storage] Error creating storage directory: {e}")


def validate_profile_data(profile: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates profile numerical values, text strings, and goal/intensity pairings.
    Rejects NaN, Infinity, negative values, or zero where invalid.
    """
    if not isinstance(profile, dict):
        return False, "Profile data must be a dictionary"

    # Age check
    age = profile.get("age")
    if not isinstance(age, (int, float)) or age <= 0 or age != age or age == float("inf"):
        return False, f"Invalid age '{age}'. Must be a positive integer."

    # Sex check
    sex = str(profile.get("sex", "")).strip().capitalize()
    if sex not in ["Male", "Female"]:
        return False, f"Invalid sex '{sex}'. Must be 'Male' or 'Female'."

    # Height check
    height = profile.get("height_cm")
    if not isinstance(height, (int, float)) or height <= 0 or height != height or height == float("inf"):
        return False, f"Invalid height '{height}'. Must be positive."

    # Weight check
    weight = profile.get("weight_kg")
    if not isinstance(weight, (int, float)) or weight <= 0 or weight != weight or weight == float("inf"):
        return False, f"Invalid weight '{weight}'. Must be positive."

    # Activity level check
    activity = profile.get("activity_level")
    if activity not in ACTIVITY_MULTIPLIERS:
        return False, f"Invalid activity level '{activity}'."

    # Goal check
    goal = profile.get("goal")
    if goal not in GOAL_CONFIG:
        return False, f"Invalid goal '{goal}'."

    # Intensity check
    intensity = profile.get("intensity")
    valid_intensities = GOAL_CONFIG[goal]["intensities"]
    if intensity not in valid_intensities:
        return False, f"Invalid intensity '{intensity}' for goal '{goal}'. Allowed: {list(valid_intensities.keys())}"

    return True, "Valid"


def load_profile() -> Optional[Dict[str, Any]]:
    """
    Loads user profile from data/profile.json. Returns None if missing or corrupt.
    """
    _ensure_profile_storage_exists()
    if not os.path.exists(PROFILE_FILE):
        return None

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            data = json.loads(content)
            valid, msg = validate_profile_data(data)
            if valid:
                return data
            print(f"[profile_storage] Loaded profile failed validation: {msg}")
            return None
    except json.JSONDecodeError as err:
        print(f"[profile_storage] Corrupt JSON in profile.json ({err}). Returning None.")
        return None
    except Exception as e:
        print(f"[profile_storage] Error loading profile: {e}")
        return None


def save_profile(profile_data: Dict[str, Any]) -> bool:
    """
    Validates and saves user profile to data/profile.json atomically.
    """
    _ensure_profile_storage_exists()
    valid, msg = validate_profile_data(profile_data)
    if not valid:
        print(f"[profile_storage] Validation error: {msg}")
        return False

    profile_data["updated_at"] = datetime.datetime.now().isoformat()

    try:
        tmp_file = PROFILE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

        if os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)
        os.rename(tmp_file, PROFILE_FILE)
        return True
    except Exception as e:
        print(f"[profile_storage] Error saving profile: {e}")
        return False
