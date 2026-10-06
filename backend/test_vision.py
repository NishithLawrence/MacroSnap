"""
Unit test suite for MacroSnap AI Vision Scanner module (vision.py).
Tests JSON parsing, validation, mathematical total normalization, error handling,
and edge cases for structured meal response.
"""

import json
from vision import validate_and_format_meal_data, clean_json_response

def test_clean_json_response():
    raw_markdown = "```json\n{\"foods\": [], \"total\": {\"calories\": 0, \"protein_g\": 0, \"carbs_g\": 0, \"fat_g\": 0}, \"confidence\": \"high\", \"notes\": []}\n```"
    cleaned = clean_json_response(raw_markdown)
    assert cleaned.startswith("{") and cleaned.endswith("}")
    data = json.loads(cleaned)
    assert "foods" in data
    print("[PASS] test_clean_json_response passed")

def test_validate_and_format_meal_data():
    raw_response = {
        "foods": [
            {
                "name": "Grilled Chicken Breast",
                "portion": "approx 150 g",
                "calories": 240,
                "protein_g": 46,
                "carbs_g": 0,
                "fat_g": 5,
                "confidence": "high"
            },
            {
                "name": "Steamed Broccoli",
                "portion": "approx 100 g",
                "calories": 50,
                "protein_g": 3,
                "carbs_g": 10,
                "fat_g": 1,
                "confidence": "medium"
            }
        ],
        "confidence": "high",
        "notes": ["Portion based on visual comparison."]
    }

    result = validate_and_format_meal_data(raw_response)
    assert len(result["foods"]) == 2
    assert result["total"]["calories"] == 290
    assert result["total"]["protein_g"] == 49
    assert result["total"]["carbs_g"] == 10
    assert result["total"]["fat_g"] == 6
    assert result["confidence"] == "high"
    print("[PASS] test_validate_and_format_meal_data passed")

def test_malformed_food_fields():
    raw_response = {
        "foods": [
            {
                "name": "Uncertain food item",
                "portion": "unknown",
                "calories": "invalid_number",
                "protein_g": None,
                "carbs_g": 15.6,
                "fat_g": 2.2,
                "confidence": "INVALID_CONF"
            }
        ],
        "confidence": "unknown_value",
        "notes": "Single string note"
    }

    result = validate_and_format_meal_data(raw_response)
    assert len(result["foods"]) == 1
    assert result["foods"][0]["calories"] == 0
    assert result["foods"][0]["protein_g"] == 0
    assert result["foods"][0]["carbs_g"] == 16  # rounded
    assert result["foods"][0]["fat_g"] == 2      # rounded
    assert result["foods"][0]["confidence"] == "medium"
    assert result["confidence"] == "medium"
    assert isinstance(result["notes"], list)
    print("[PASS] test_malformed_food_fields passed")

if __name__ == "__main__":
    print("Running MacroSnap Vision Engine Tests...\n")
    test_clean_json_response()
    test_validate_and_format_meal_data()
    test_malformed_food_fields()
    print("\nAll Vision engine tests passed successfully!")
