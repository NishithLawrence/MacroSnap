import io
import os
import sys
import uuid
import datetime
from typing import Dict, Any, Optional
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend package directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import backend business logic modules
from vision import analyze_meal_image
from meal_storage import add_meal, load_meals, update_meal, delete_meal, get_meals_for_date, get_daily_totals, get_all_dates
from profile_storage import load_profile, save_profile, validate_profile_data
from target_storage import get_latest_target_snapshot, create_target_snapshot
from nutrition_ai import query_nutrition_assistant
from calculations import calculate_tdee, calculate_full_plan, GOAL_CONFIG, ACTIVITY_MULTIPLIERS, ACTIVITY_DESCRIPTIONS
import weight_storage
from analytics import get_period_summary

app = FastAPI(
    title="MacroSnap API",
    description="Backend API for MacroSnap AI Nutrition & Fitness Tracking",
    version="1.0.0"
)

# Configure explicit CORS origins for security (no unrestricted wildcards in production)
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
]
custom_origins = os.environ.get("FRONTEND_ORIGIN") or os.environ.get("CORS_ORIGINS")
allowed_origins = list(default_origins)
if custom_origins:
    for origin in custom_origins.split(","):
        cleaned = origin.strip()
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

    if not add_meal(meal):
        raise HTTPException(status_code=400, detail="Failed to save meal.")

    return {"status": "ok", "meal": meal}


@app.get("/api/meals/history")
def get_meal_history():
    """
    Returns logged meals grouped by date (newest date first),
    with daily total macros for each date.
    """
    dates = get_all_dates()
    dates_with_meals = []
    for d in dates:
        m_list = get_meals_for_date(d)
        if m_list:
            try:
                date_obj = datetime.date.fromisoformat(d)
                date_fmt = date_obj.strftime("%a, %b %d")
            except Exception:
                date_fmt = d
            totals = get_daily_totals(d)
            dates_with_meals.append({
                "date": d,
                "date_formatted": date_fmt,
                "totals": totals,
                "meals": m_list
            })
    return {"dates": dates_with_meals}


@app.put("/api/meals/{meal_id}")
def edit_meal(meal_id: str, updated_meal: Dict[str, Any]):
    """
    Updates an existing meal record.
    """
    if not isinstance(updated_meal, dict):
        raise HTTPException(status_code=400, detail="Invalid meal payload.")

    success = update_meal(meal_id, updated_meal)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update meal. Check meal ID and values.")

    return {"status": "ok", "meal": updated_meal}


@app.delete("/api/meals/{meal_id}")
def remove_meal(meal_id: str):
    """
    Deletes a meal from storage.
    """
    success = delete_meal(meal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meal not found.")
    return {"status": "ok", "deleted": meal_id}


@app.get("/api/progress/analytics")
def get_progress_analytics(days: int = 7):
    """
    Returns period analytics (averages, calorie adherence, protein adherence,
    consistency score, goal interpretation, weight trend) using real backend data.
    """
    if days not in (7, 30):
        days = 7

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
        tdee = snap.get("tdee", 2800)
    else:
        plan = calculate_full_plan(
            weight_kg=profile.get("weight_kg", 75.0),
            height_cm=profile.get("height_cm", 178.0),
            age=profile.get("age", 25),
            sex=profile.get("sex", "Male"),
            activity_level=profile.get("activity_level", "Moderately Active"),
            goal=profile.get("goal", "Fat Loss"),
            intensity=profile.get("intensity", "Moderate")
        )
        target_cal = plan.get("target_calories", 2380)
        target_p = plan.get("protein_g", 144)
        target_c = plan.get("carbs_g", 302)
        target_f = plan.get("fat_g", 66)
        tdee = plan.get("tdee", 2800)

    goal = profile.get("goal", "Fat Loss")

    summary = get_period_summary(
        days=days,
        target_calories=target_cal,
        target_protein=target_p,
        target_carbs=target_c,
        target_fat=target_f,
        goal=goal,
        tdee=tdee,
    )

    weight_history = weight_storage.get_weight_for_period(days)
    weight_change = weight_storage.get_weight_change()

    return {
        **summary,
        "goal": goal,
        "targets": {
            "calories": target_cal,
            "protein": target_p,
            "carbs": target_c,
            "fat": target_f,
        },
        "weight_history": weight_history,
        "weight_change": weight_change,
    }


@app.get("/api/profile")
def get_profile_endpoint():
    """
    Returns saved user profile, active target snapshot/plan, and authoritative goal/activity options.
    """
    profile = load_profile() or {
        "age": 25,
        "sex": "Male",
        "height_cm": 178.0,
        "weight_kg": 75.0,
        "activity_level": "Moderately Active",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }

    snap = get_latest_target_snapshot()
    if snap:
        active_plan = snap
    else:
        active_plan = calculate_full_plan(
            weight_kg=profile.get("weight_kg", 75.0),
            height_cm=profile.get("height_cm", 178.0),
            age=profile.get("age", 25),
            sex=profile.get("sex", "Male"),
            activity_level=profile.get("activity_level", "Moderately Active"),
            goal=profile.get("goal", "Fat Loss"),
            intensity=profile.get("intensity", "Moderate")
        )

    options = {
        "activity_levels": [
            {
                "name": level,
                "multiplier": mult,
                "description": ACTIVITY_DESCRIPTIONS.get(level, "")
            }
            for level, mult in ACTIVITY_MULTIPLIERS.items()
        ],
        "goals": {
            g_name: {
                "emoji": g_cfg.get("emoji", "🎯"),
                "description": g_cfg.get("description", ""),
                "protein_per_kg": g_cfg.get("protein_per_kg", 1.8),
                "intensities": list(g_cfg.get("intensities", {}).keys()),
                "intensity_details": {
                    i_name: {
                        "label": i_cfg.get("label", i_name),
                        "type": i_cfg.get("type", "maintenance"),
                        "pct": i_cfg.get("pct", 0.0)
                    }
                    for i_name, i_cfg in g_cfg.get("intensities", {}).items()
                }
            }
            for g_name, g_cfg in GOAL_CONFIG.items()
        }
    }

    return {
        "profile": profile,
        "active_plan": active_plan,
        "options": options
    }


@app.post("/api/profile/preview")
def preview_profile_plan(payload: Dict[str, Any]):
    """
    Calculates proposed plan preview based on user edits without saving or updating snapshots.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid profile payload.")

    valid, msg = validate_profile_data(payload)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    curr_profile = load_profile() or {
        "age": 25, "sex": "Male", "height_cm": 178.0, "weight_kg": 75.0,
        "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"
    }
    snap = get_latest_target_snapshot()
    if snap:
        current_plan = snap
    else:
        current_plan = calculate_full_plan(
            weight_kg=curr_profile.get("weight_kg", 75.0),
            height_cm=curr_profile.get("height_cm", 178.0),
            age=curr_profile.get("age", 25),
            sex=curr_profile.get("sex", "Male"),
            activity_level=curr_profile.get("activity_level", "Moderately Active"),
            goal=curr_profile.get("goal", "Fat Loss"),
            intensity=curr_profile.get("intensity", "Moderate")
        )

    proposed_plan = calculate_full_plan(
        weight_kg=float(payload["weight_kg"]),
        height_cm=float(payload["height_cm"]),
        age=int(payload["age"]),
        sex=str(payload["sex"]),
        activity_level=str(payload["activity_level"]),
        goal=str(payload["goal"]),
        intensity=str(payload["intensity"])
    )

    return {
        "current_profile": curr_profile,
        "current_plan": current_plan,
        "proposed_profile": payload,
        "proposed_plan": proposed_plan
    }


@app.post("/api/profile/apply")
def apply_profile_plan(payload: Dict[str, Any]):
    """
    Validates, saves user profile, logs weight entry, calculates new plan,
    and creates a new immutable target snapshot.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid profile payload.")

    valid, msg = validate_profile_data(payload)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    save_success = save_profile(payload)
    if not save_success:
        raise HTTPException(status_code=500, detail="Failed to save profile to disk.")

    weight_val = float(payload["weight_kg"])
    eff_date = payload.get("effective_date") or datetime.date.today().isoformat()
    weight_storage.add_weight_entry(weight_val, date_str=eff_date)

    new_plan = calculate_full_plan(
        weight_kg=weight_val,
        height_cm=float(payload["height_cm"]),
        age=int(payload["age"]),
        sex=str(payload["sex"]),
        activity_level=str(payload["activity_level"]),
        goal=str(payload["goal"]),
        intensity=str(payload["intensity"])
    )

    snap_success, snapshot = create_target_snapshot(new_plan, effective_date=eff_date)
    if not snap_success or not snapshot:
        raise HTTPException(status_code=500, detail="Failed to create target snapshot.")

    return {
        "status": "ok",
        "profile": payload,
        "target_snapshot": snapshot,
        "active_plan": new_plan
    }


@app.post("/api/progress/weight")
def log_weight(payload: Dict[str, Any]):
    """
    Logs a weight entry into weight_storage JSON and syncs current profile weight.
    """
    if not isinstance(payload, dict) or "weight_kg" not in payload:
        raise HTTPException(status_code=400, detail="Field 'weight_kg' is required.")

    try:
        weight_val = float(payload["weight_kg"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="weight_kg must be a valid number.")

    date_str = payload.get("date")
    success, msg = weight_storage.add_weight_entry(weight_val, date_str)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    profile = load_profile()
    if profile:
        profile["weight_kg"] = weight_val
        save_profile(profile)

    return {"status": "ok", "weight_change": weight_storage.get_weight_change()}


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

