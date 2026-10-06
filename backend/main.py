import io
import os
import uuid
import datetime
from typing import Dict, Any, Optional
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import backend business logic modules
from vision import analyze_meal_image
from meal_storage import add_meal, load_meals, delete_meal, get_meals_for_date, get_daily_totals
from profile_storage import load_profile
from target_storage import get_latest_target_snapshot
from nutrition_ai import query_nutrition_assistant
from calculations import calculate_tdee, calculate_full_plan

app = FastAPI(
    title="MacroSnap API",
    description="Backend API for MacroSnap AI Nutrition & Fitness Tracking",
    version="1.0.0"
)

# Enable CORS for local frontend development & production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def get_health():
    """
    Health check endpoint for MacroSnap API.
    """
    return {
        "status": "ok",
        "service": "macrosnap-api"
    }


@app.post("/api/meals/scan")
async def scan_meal(
    file: UploadFile = File(...),
    meal_type: Optional[str] = Form("Lunch")
):
    """
    Gemini Vision analysis endpoint for meal photos.
    Receives an image file, passes it to the Gemini Vision engine server-side,
    and returns structured meal analysis with detected foods, portions, and macros.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    try:
        image_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(image_bytes))

        # Convert palette/RGBA images to RGB
        if pil_image.mode not in ("RGB", "L"):
            pil_image = pil_image.convert("RGB")

        success, meal_data, message = analyze_meal_image(pil_image)

        # Fallback for local testing if GEMINI_API_KEY is not set in environment
        if not success or not meal_data:
            if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
                meal_data = {
                    "foods": [
                        {"id": "item_1", "name": "Scrambled Eggs & Toast", "portion": "2 eggs, 1 toast (180g)", "calories": 250, "protein_g": 16, "carbs_g": 22, "fat_g": 12, "confidence": "high"},
                        {"id": "item_2", "name": "Avocado Slices", "portion": "1/2 avocado (70g)", "calories": 110, "protein_g": 2, "carbs_g": 6, "fat_g": 10, "confidence": "high"}
                    ],
                    "total": {"calories": 360, "protein_g": 18, "carbs_g": 28, "fat_g": 22},
                    "confidence": "high",
                    "notes": ["Sample detected items from meal plate"]
                }
            else:
                raise HTTPException(status_code=422, detail=message or "Unable to analyze meal image.")

        # Ensure meal_type is set on response
        meal_data["meal_type"] = meal_type or "Lunch"
        return meal_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")


@app.post("/api/meals")
def create_meal(meal: Dict[str, Any]):
    """
    Persists a confirmed meal into meal_storage JSON.
    """
    if not isinstance(meal, dict):
        raise HTTPException(status_code=400, detail="Invalid meal payload.")

    # Auto-generate IDs & timestamps if missing
    if "meal_id" not in meal or not meal["meal_id"]:
        meal["meal_id"] = f"meal_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    if "date" not in meal or not meal["date"]:
        meal["date"] = today_str

    if "timestamp" not in meal or not meal["timestamp"]:
        meal["timestamp"] = datetime.datetime.now().isoformat()

    success, msg = add_meal(meal)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"status": "ok", "meal": meal}


@app.delete("/api/meals/{meal_id}")
def remove_meal(meal_id: str):
    """
    Deletes a meal from storage.
    """
    success = delete_meal(meal_id)
    if not success:
        raise HTTPException(status_code=444, detail="Meal not found.")
    return {"status": "ok", "deleted": meal_id}


@app.get("/api/coach/context")
def get_coach_context():
    """
    Returns current live user profile, daily targets, consumed totals,
    remaining totals, and today's confirmed meals for the Coach UI context card.
    """
    today_str = datetime.date.today().isoformat()
    profile = load_profile() or {
        "age": 25, "sex": "Male", "height_cm": 178.0, "weight_kg": 75.0,
        "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"
    }

    snap = get_latest_target_snapshot()
    if snap:
        target_cal = snap.get("calorie_target", 2380)
        target_p = snap.get("protein_target", 144)
        target_c = snap.get("carbs_target", 302)
        target_f = snap.get("fat_target", 66)
    else:
        plan = calculate_full_plan(
            weight_kg=profile["weight_kg"],
            height_cm=profile["height_cm"],
            age=profile["age"],
            sex=profile["sex"],
            activity_level=profile["activity_level"],
            goal=profile["goal"],
            intensity=profile["intensity"]
        )
        target_cal = plan.get("target_calories", 2380)
        target_p = plan.get("protein_g", 144)
        target_c = plan.get("carbs_g", 302)
        target_f = plan.get("fat_g", 66)

    consumed = get_daily_totals(today_str)
    today_meals = get_meals_for_date(today_str)

    cons_cal = consumed.get("calories", 0)
    cons_p = consumed.get("protein_g", 0)
    cons_c = consumed.get("carbs_g", 0)
    cons_f = consumed.get("fat_g", 0)

    return {
        "user_name": "Nishith",
        "target_calories": target_cal,
        "consumed_calories": cons_cal,
        "remaining_calories": max(0, target_cal - cons_cal),
        "target_protein": target_p,
        "consumed_protein": cons_p,
        "remaining_protein": max(0, target_p - cons_p),
        "target_carbs": target_c,
        "consumed_carbs": cons_c,
        "remaining_carbs": max(0, target_c - cons_c),
        "target_fat": target_f,
        "consumed_fat": cons_f,
        "remaining_fat": max(0, target_f - cons_f),
        "today_meals": today_meals
    }


@app.post("/api/coach/chat")
def coach_chat(payload: Dict[str, Any]):
    """
    Contextual AI Nutrition Coach endpoint.
    Retrieves live server-side Python context (profile, targets, consumed, meals)
    and sends prompt + history to Gemini Vision/Assistant engine.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a dictionary.")

    message = payload.get("message")
    if not message or not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="Field 'message' is required.")

    conversation = payload.get("conversation", [])

    today_str = datetime.date.today().isoformat()
    profile = load_profile() or {
        "age": 25, "sex": "Male", "height_cm": 178.0, "weight_kg": 75.0,
        "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"
    }

    snap = get_latest_target_snapshot()
    if snap:
        user_plan = {
            "age": profile.get("age", 25),
            "sex": profile.get("sex", "Male"),
            "height_cm": profile.get("height_cm", 178),
            "weight_kg": profile.get("weight_kg", 75),
            "activity_level": profile.get("activity_level", "Moderately Active"),
            "goal": profile.get("goal", "Fat Loss"),
            "intensity": profile.get("intensity", "Moderate"),
            "target_calories": snap.get("calorie_target", 2380),
            "protein_g": snap.get("protein_target", 144),
            "carbs_g": snap.get("carbs_target", 302),
            "fat_g": snap.get("fat_target", 66),
            "tdee": snap.get("tdee", 2800)
        }
    else:
        plan = calculate_full_plan(
            weight_kg=profile["weight_kg"],
            height_cm=profile["height_cm"],
            age=profile["age"],
            sex=profile["sex"],
            activity_level=profile["activity_level"],
            goal=profile["goal"],
            intensity=profile["intensity"]
        )
        user_plan = plan

    consumed = get_daily_totals(today_str)
    today_meals = get_meals_for_date(today_str)

    success, response_text = query_nutrition_assistant(
        user_prompt=message,
        user_plan=user_plan,
        consumed=consumed,
        today_meals=today_meals,
        chat_history=conversation
    )

    if not success:
        return {
            "success": False,
            "error": response_text,
            "response": response_text
        }

    return {
        "success": True,
        "response": response_text
    }

