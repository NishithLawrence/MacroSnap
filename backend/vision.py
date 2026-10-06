"""
MacroSnap AI Vision Scanner Engine
===================================
Isolated module for Gemini Vision API interactions, meal recognition,
portion estimation, structured JSON parsing, and error handling.

Uses 'gemini-3.8-flash' (or fallback models if needed) via google-genai.
API keys are loaded securely from environment variables (GEMINI_API_KEY or GOOGLE_API_KEY).
"""

import json
import os
import re
from typing import Dict, Any, Tuple, Optional
from PIL import Image

try:
    from dotenv import load_dotenv
    _backend_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)
    _root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(_root_env):
        load_dotenv(_root_env)
except Exception:
    pass

from prompts import GEMINI_VISION_PROMPT

# Target model specified by user
PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]


def get_gemini_api_key() -> Optional[str]:
    """
    Securely fetch Gemini API key from environment variables (GEMINI_API_KEY or GOOGLE_API_KEY).
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key and key.strip() and "YOUR_GEMINI" not in key:
        return key.strip()
    return None


def clean_json_response(text: str) -> str:
    """
    Strips markdown code blocks (```json ... ```) from Gemini output.
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"```$", "", text, flags=re.MULTILINE)
    return text.strip()


def validate_and_format_meal_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes structured meal JSON from Gemini.
    Re-calculates totals deterministically from individual food items.
    """
    if not isinstance(data, dict):
        raise ValueError("Root JSON response must be an object")

    foods = data.get("foods", [])
    if not isinstance(foods, list):
        foods = []

    validated_foods = []
    tot_cals = 0
    tot_p = 0
    tot_c = 0
    tot_f = 0

    for idx, item in enumerate(foods):
        if not isinstance(item, dict):
            continue

        name = str(item.get("name") or item.get("food") or f"Food Item {idx + 1}").strip()
        portion = str(item.get("portion") or "estimated serving").strip()

        try:
            cals = max(0, int(round(float(item.get("calories", 0)))))
        except (ValueError, TypeError):
            cals = 0

        try:
            p = max(0, int(round(float(item.get("protein_g", item.get("protein", 0))))))
        except (ValueError, TypeError):
            p = 0

        try:
            c = max(0, int(round(float(item.get("carbs_g", item.get("carbs", 0))))))
        except (ValueError, TypeError):
            c = 0

        try:
            f = max(0, int(round(float(item.get("fat_g", item.get("fat", 0))))))
        except (ValueError, TypeError):
            f = 0

        conf = str(item.get("confidence", "medium")).lower()
        if conf not in ["high", "medium", "low"]:
            conf = "medium"

        validated_foods.append({
            "id": f"item_{idx + 1}",
            "name": name,
            "portion": portion,
            "calories": cals,
            "protein_g": p,
            "carbs_g": c,
            "fat_g": f,
            "confidence": conf,
        })

        tot_cals += cals
        tot_p += p
        tot_c += c
        tot_f += f

    confidence = str(data.get("confidence", "medium")).lower()
    if confidence not in ["high", "medium", "low"]:
        confidence = "medium"

    notes = data.get("notes", [])
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []

    return {
        "foods": validated_foods,
        "total": {
            "calories": tot_cals,
            "protein_g": tot_p,
            "carbs_g": tot_c,
            "fat_g": tot_f,
        },
        "confidence": confidence,
        "notes": [str(n) for n in notes],
    }


def analyze_meal_image(pil_image: Image.Image) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Sends the meal image to Gemini Vision API and returns validated structured meal analysis.

    Returns:
        (success: bool, meal_data: dict or None, message: str)
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return (
            False,
            None,
            "Gemini API key is not configured on the backend.",
        )

    # Attempt calling via google.genai SDK
    client = None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except Exception as e:
        pass

    if client:
        # Try primary model then fallback models
        models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS
        last_error = ""

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[pil_image, GEMINI_VISION_PROMPT],
                )
                if response and response.text:
                    cleaned_json = clean_json_response(response.text)
                    raw_data = json.loads(cleaned_json)
                    meal_data = validate_and_format_meal_data(raw_data)
                    return (True, meal_data, "Success")
            except json.JSONDecodeError:
                return (
                    False,
                    None,
                    "⚠️ MacroSnap AI returned an unreadable response format. Please try scanning again.",
                )
            except Exception as ex:
                last_error = str(ex)
                continue

        return (
            False,
            None,
            "⚠️ MacroSnap AI is temporarily unavailable. Please try again in a moment.",
        )

    # Secondary SDK fallback (google.generativeai if available)
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        
        for model_name in [PRIMARY_MODEL] + FALLBACK_MODELS:
            try:
                model = legacy_genai.GenerativeModel(model_name)
                response = model.generate_content([GEMINI_VISION_PROMPT, pil_image])
                if response and response.text:
                    cleaned_json = clean_json_response(response.text)
                    raw_data = json.loads(cleaned_json)
                    meal_data = validate_and_format_meal_data(raw_data)
                    return (True, meal_data, "Success")
            except Exception:
                continue
    except Exception:
        pass

    return (
        False,
        None,
        "⚠️ MacroSnap AI is temporarily unavailable. Please try again in a moment.",
    )
