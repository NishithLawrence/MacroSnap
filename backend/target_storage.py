"""
MacroSnap Target Snapshots Storage Engine (target_storage.py)
============================================================
Isolated persistent storage for historical target snapshots.

File Location: data/target_history.json
Data Model:
{
  "snapshots": [
    {
      "snapshot_id": "uuid-v4",
      "effective_date": "2026-10-05",
      "timestamp": "2026-10-05T09:00:00",
      "bmr": 1805.0,
      "tdee": 2798,
      "calorie_target": 2378,
      "protein_target": 144,
      "carbs_target": 302,
      "fat_target": 66,
      "goal": "Fat Loss",
      "goal_intensity": "Moderate",
      "activity_level": "Moderately Active",
      "weight_kg": 80.0
    }
  ]
}

Functions provided:
- load_target_snapshots() -> List[Dict]
- save_target_snapshots(snapshots: List[Dict]) -> bool
- create_target_snapshot(plan: Dict, effective_date: Optional[str] = None) -> Tuple[bool, Optional[Dict]]
- get_target_for_date(date_str: str) -> Optional[Dict]
- get_latest_target_snapshot() -> Optional[Dict]
"""

import json
import os
import uuid
import datetime
import math
from typing import Dict, Any, List, Tuple, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TARGET_FILE = os.path.join(DATA_DIR, "target_history.json")


def _ensure_target_storage_exists() -> None:
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

        if not os.path.exists(TARGET_FILE):
            with open(TARGET_FILE, "w", encoding="utf-8") as f:
                json.dump({"snapshots": []}, f, indent=2)
    except Exception as e:
        print(f"[target_storage] Error initializing target storage: {e}")


def validate_target_snapshot(snap: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(snap, dict):
        return False, "Snapshot must be a dictionary"

    snap_id = snap.get("snapshot_id")
    if not snap_id or not isinstance(snap_id, str):
        return False, "Snapshot must have a valid string ID"

    eff_date = snap.get("effective_date")
    if not eff_date or not isinstance(eff_date, str):
        return False, "Effective date must be a string YYYY-MM-DD"
    try:
        datetime.date.fromisoformat(eff_date)
    except ValueError:
        return False, f"Invalid date format '{eff_date}'"

    for field in ["calorie_target", "protein_target", "fat_target"]:
        val = snap.get(field)
        if (
            val is None
            or type(val) is bool
            or not isinstance(val, (int, float))
            or math.isnan(val)
            or math.isinf(val)
            or val <= 0
        ):
            return False, f"Field '{field}' must be a positive number. Got: {val}"

    carbs_val = snap.get("carbs_target")
    if (
        carbs_val is None
        or type(carbs_val) is bool
        or not isinstance(carbs_val, (int, float))
        or math.isnan(carbs_val)
        or math.isinf(carbs_val)
        or carbs_val < 0
    ):
        return False, f"Field 'carbs_target' must be a non-negative number. Got: {carbs_val}"

    for opt_field in ["bmr", "tdee", "weight_kg"]:
        if opt_field in snap and snap[opt_field] is not None:
            opt_val = snap[opt_field]
            if (
                type(opt_val) is bool
                or not isinstance(opt_val, (int, float))
                or math.isnan(opt_val)
                or math.isinf(opt_val)
                or opt_val <= 0
            ):
                return False, f"Field '{opt_field}' must be a positive number. Got: {opt_val}"

    return True, "Valid"


def load_target_snapshots() -> List[Dict[str, Any]]:
    _ensure_target_storage_exists()
    if not os.path.exists(TARGET_FILE):
        return []

    try:
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, dict) and "snapshots" in data and isinstance(data["snapshots"], list):
                snaps = data["snapshots"]
            elif isinstance(data, list):
                snaps = data
            else:
                return []

            snaps.sort(key=lambda x: (x.get("effective_date", ""), x.get("timestamp", "")))
            return snaps
    except json.JSONDecodeError as err:
        print(f"[target_storage] Corrupt JSON in target_history.json ({err}). Returning empty list.")
        return []
    except Exception as e:
        print(f"[target_storage] Error loading target history: {e}")
        return []


def save_target_snapshots(snapshots: List[Dict[str, Any]]) -> bool:
    _ensure_target_storage_exists()
    try:
        tmp_file = TARGET_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump({"snapshots": snapshots}, f, indent=2)

        if os.path.exists(TARGET_FILE):
            os.remove(TARGET_FILE)
        os.rename(tmp_file, TARGET_FILE)
        return True
    except Exception as e:
        print(f"[target_storage] Error saving target history: {e}")
        return False


def create_target_snapshot(plan: Dict[str, Any], effective_date: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Creates and records a target snapshot from a calculated plan dictionary.
    Rejects incomplete, missing, or invalid plan targets without fabricating default values.
    """
    if not isinstance(plan, dict):
        return False, None

    if effective_date is None:
        effective_date = datetime.date.today().isoformat()

    cal = plan.get("calorie_target") if plan.get("calorie_target") is not None else plan.get("target_calories")
    p = plan.get("protein_target") if plan.get("protein_target") is not None else plan.get("protein_g")
    c = plan.get("carbs_target") if plan.get("carbs_target") is not None else plan.get("carbs_g")
    f = plan.get("fat_target") if plan.get("fat_target") is not None else plan.get("fat_g")

    snapshot = {
        "snapshot_id": str(uuid.uuid4()),
        "effective_date": effective_date,
        "timestamp": datetime.datetime.now().isoformat(),
        "bmr": plan.get("bmr"),
        "tdee": plan.get("tdee"),
        "calorie_target": cal,
        "protein_target": p,
        "carbs_target": c,
        "fat_target": f,
        "goal": plan.get("goal"),
        "goal_intensity": plan.get("goal_intensity") if plan.get("goal_intensity") is not None else plan.get("intensity"),
        "activity_level": plan.get("activity_level"),
        "weight_kg": plan.get("weight_kg"),
    }

    valid, msg = validate_target_snapshot(snapshot)
    if not valid:
        print(f"[target_storage] Validation error: {msg}")
        return False, None

    snapshots = load_target_snapshots()
    snapshots.append(snapshot)
    snapshots.sort(key=lambda x: (x.get("effective_date", ""), x.get("timestamp", "")))

    ok = save_target_snapshots(snapshots)
    if ok:
        return True, snapshot
    return False, None


def get_latest_target_snapshot() -> Optional[Dict[str, Any]]:
    snaps = load_target_snapshots()
    return snaps[-1] if snaps else None


def get_target_for_date(date_str: str) -> Optional[Dict[str, Any]]:
    """
    Resolves the target snapshot applicable to `date_str` using the most recent
    snapshot whose effective_date <= date_str.
    Falls back to the earliest available snapshot if date_str precedes all recorded dates.
    """
    snaps = load_target_snapshots()
    if not snaps:
        return None

    # Filter snapshots with effective_date <= date_str
    applicable = [s for s in snaps if s.get("effective_date", "") <= date_str]
    if applicable:
        return applicable[-1]

    # Fall back to earliest snapshot if before all effective dates
    return snaps[0]
