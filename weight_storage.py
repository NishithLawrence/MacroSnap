"""
MacroSnap Weight Storage Engine (weight_storage.py)
===================================================
Isolated persistent JSON storage module for body weight tracking entries.

File Location: data/weight_history.json
Data Model:
{
  "entries": [
    {
      "id": "uuid-v4",
      "date": "2026-10-05",
      "weight_kg": 75.0,
      "timestamp": "2026-10-05T09:00:00"
    }
  ]
}

Functions provided:
- load_weight_history() -> List[Dict]
- save_weight_history(entries: List[Dict]) -> bool
- add_weight_entry(weight_kg: float, date_str: Optional[str] = None) -> Tuple[bool, str]
- delete_weight_entry(entry_id: str) -> bool
- get_latest_weight() -> Optional[Dict]
- get_previous_weight() -> Optional[Dict]
- get_weight_change() -> Dict[str, Any]
- get_weight_for_period(days: int) -> List[Dict]
- validate_weight_entry(entry: Dict) -> Tuple[bool, str]
"""

import json
import os
import uuid
import datetime
from typing import Dict, Any, List, Tuple, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
WEIGHT_FILE = os.path.join(DATA_DIR, "weight_history.json")


def _ensure_weight_storage_exists() -> None:
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

        if not os.path.exists(WEIGHT_FILE):
            with open(WEIGHT_FILE, "w", encoding="utf-8") as f:
                json.dump({"entries": []}, f, indent=2)
    except Exception as e:
        print(f"[weight_storage] Error initializing storage: {e}")


def validate_weight_entry(entry: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(entry, dict):
        return False, "Weight entry must be a dictionary"

    entry_id = entry.get("id")
    if not entry_id or not isinstance(entry_id, str):
        return False, "Weight entry must have a valid string ID"

    date_str = entry.get("date")
    if not date_str or not isinstance(date_str, str):
        return False, "Date must be a YYYY-MM-DD string"
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        return False, f"Invalid date format '{date_str}'. Expected YYYY-MM-DD"

    weight = entry.get("weight_kg")
    if not isinstance(weight, (int, float)) or weight <= 0 or weight != weight or weight == float("inf") or weight == float("-inf"):
        return False, f"Weight must be a positive, finite number. Got: {weight}"

    return True, "Valid"


def load_weight_history() -> List[Dict[str, Any]]:
    _ensure_weight_storage_exists()

    if not os.path.exists(WEIGHT_FILE):
        return []

    try:
        with open(WEIGHT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, dict) and "entries" in data and isinstance(data["entries"], list):
                entries = data["entries"]
            elif isinstance(data, list):
                entries = data
            else:
                return []

            # Sort by date ascending
            entries.sort(key=lambda x: (x.get("date", ""), x.get("timestamp", "")))
            return entries
    except json.JSONDecodeError as err:
        print(f"[weight_storage] Corrupt JSON in weight_history.json ({err}). Returning empty list without overwriting.")
        return []
    except Exception as e:
        print(f"[weight_storage] Error loading weight history: {e}")
        return []


def save_weight_history(entries: List[Dict[str, Any]]) -> bool:
    _ensure_weight_storage_exists()
    try:
        tmp_file = WEIGHT_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump({"entries": entries}, f, indent=2)

        if os.path.exists(WEIGHT_FILE):
            os.remove(WEIGHT_FILE)
        os.rename(tmp_file, WEIGHT_FILE)
        return True
    except Exception as e:
        print(f"[weight_storage] Error saving weight history: {e}")
        return False


def add_weight_entry(weight_kg: float, date_str: Optional[str] = None) -> Tuple[bool, str]:
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    new_entry = {
        "id": str(uuid.uuid4()),
        "date": date_str,
        "weight_kg": float(weight_kg) if isinstance(weight_kg, (int, float)) else weight_kg,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    valid, msg = validate_weight_entry(new_entry)
    if not valid:
        return False, msg

    entries = load_weight_history()

    # Overwrite if an entry for the same date already exists
    updated_entries = [e for e in entries if e.get("date") != date_str]
    updated_entries.append(new_entry)
    updated_entries.sort(key=lambda x: (x.get("date", ""), x.get("timestamp", "")))

    ok = save_weight_history(updated_entries)
    if ok:
        return True, "Weight logged successfully"
    return False, "Failed to save weight entry to disk"


def delete_weight_entry(entry_id: str) -> bool:
    if not entry_id:
        return False
    entries = load_weight_history()
    filtered = [e for e in entries if e.get("id") != entry_id]
    if len(filtered) < len(entries):
        return save_weight_history(filtered)
    return False


def get_latest_weight() -> Optional[Dict[str, Any]]:
    entries = load_weight_history()
    return entries[-1] if entries else None


def get_previous_weight() -> Optional[Dict[str, Any]]:
    entries = load_weight_history()
    return entries[-2] if len(entries) >= 2 else None


def get_weight_change() -> Dict[str, Any]:
    entries = load_weight_history()
    if not entries:
        return {"count": 0, "current": None, "previous": None, "change_kg": 0.0, "trend": "No data"}

    if len(entries) == 1:
        c_val = round(entries[0]["weight_kg"], 1)
        return {"count": 1, "current": c_val, "previous": None, "change_kg": 0.0, "trend": "Baseline recorded"}

    current = round(entries[-1]["weight_kg"], 1)
    previous = round(entries[-2]["weight_kg"], 1)
    diff = round(current - previous, 1)

    trend_str = f"{'+' if diff > 0 else ''}{diff} kg"
    return {
        "count": len(entries),
        "current": current,
        "previous": previous,
        "change_kg": diff,
        "trend": trend_str,
    }


def get_weight_for_period(days: int = 7) -> List[Dict[str, Any]]:
    entries = load_weight_history()
    if not entries:
        return []

    cutoff_date = (datetime.date.today() - datetime.timedelta(days=days - 1)).isoformat()
    period_entries = [e for e in entries if e.get("date", "") >= cutoff_date]
    return period_entries
