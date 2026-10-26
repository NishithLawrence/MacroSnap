import io
import os
import sys
import uuid
import math
import datetime
from typing import Dict, Any, Optional
from PIL import Image
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# Ensure backend package directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import auth
from auth import (
    get_current_reviewer,
    verify_demo_password,
    create_access_token,
    check_login_rate_limit,
    record_failed_login,
    check_rate_limit,
    validate_auth_config,
)

from vision import analyze_meal_image
from meal_storage import add_meal, load_meals, update_meal, delete_meal, get_meals_for_date, get_daily_totals, get_all_dates
import profile_storage
import target_storage
from nutrition_ai import query_nutrition_assistant
from calculations import calculate_tdee, calculate_full_plan, GOAL_CONFIG, ACTIVITY_MULTIPLIERS, ACTIVITY_DESCRIPTIONS
import weight_storage
from analytics import get_period_summary

def load_profile():
    return profile_storage.load_profile()

def save_profile(data):
    return profile_storage.save_profile(data)

def validate_profile_data(data):
    return profile_storage.validate_profile_data(data)

def get_latest_target_snapshot():
    return target_storage.get_latest_target_snapshot()

def create_target_snapshot(data, effective_date=None):
    return target_storage.create_target_snapshot(data, effective_date=effective_date)

def reset_profile_storage():
    return profile_storage.reset_profile_storage()

def reset_target_storage():
    return target_storage.reset_target_storage()

def is_production_env() -> bool:
    return os.environ.get("APP_ENV", "production").strip().lower() == "production"

def is_demo_reset_enabled() -> bool:
    return os.environ.get("ENABLE_DEMO_RESET", "false").strip().lower() in ("true", "1", "yes")

def _extract_coach_targets(source: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """
    Safely extracts nutritional targets from a snapshot or plan dictionary.
    Supports current snapshot keys (calorie_target, protein_target, carbs_target, fat_target)
    and plan/legacy keys (target_calories, protein_g, carbs_g, fat_g).
    Returns None if required values are missing or invalid (never uses fabricated mock numbers).
    """
    if not isinstance(source, dict):
        return None

    cal = source.get("calorie_target") if source.get("calorie_target") is not None else source.get("target_calories")
    p = source.get("protein_target") if source.get("protein_target") is not None else source.get("protein_g")
    c = source.get("carbs_target") if source.get("carbs_target") is not None else source.get("carbs_g")
    f = source.get("fat_target") if source.get("fat_target") is not None else source.get("fat_g")

    if (
        isinstance(cal, (int, float)) and not math.isnan(cal) and not math.isinf(cal) and cal > 0 and
        isinstance(p, (int, float)) and not math.isnan(p) and not math.isinf(p) and p > 0 and
        isinstance(c, (int, float)) and not math.isnan(c) and not math.isinf(c) and c >= 0 and
        isinstance(f, (int, float)) and not math.isnan(f) and not math.isinf(f) and f > 0
    ):
        return {
            "calories": int(round(cal)),
            "protein": int(round(p)),
            "carbs": int(round(c)),
            "fat": int(round(f)),
        }
    return None


# Disable public API documentation in production for security, enable in dev/test
is_production = os.environ.get("APP_ENV", "production").strip().lower() == "production"

app = FastAPI(
    title="Revelation API",
    description="Backend API for Revelation AI Nutrition & Fitness",
    version="1.0.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# Configure explicit CORS origins for security (no unrestricted wildcards in production)
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "https://macro-snap-eosin.vercel.app",
]
custom_origins = os.environ.get("FRONTEND_ORIGIN") or os.environ.get("CORS_ORIGINS")
allowed_origins = list(default_origins)
if custom_origins:
    for origin in custom_origins.split(","):
        cleaned = origin.strip()
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

# Strict preview origin regex: strictly matches the authorized project name and GitHub user account
# Disallows arbitrary third-party Vercel projects matching generic "macro-snap*" prefix
preview_origin_regex = (
    os.environ.get("FRONTEND_PREVIEW_REGEX")
    or r"^https:\/\/macro-snap-[a-z0-9-]+-nishithlawrence.*\.vercel\.app$"
)

MAX_STANDARD_REQUEST_SIZE = 1 * 1024 * 1024  # 1 MB for standard JSON endpoints
MAX_UPLOAD_REQUEST_SIZE = 6 * 1024 * 1024    # 6 MB for multipart image upload
MAX_IMAGE_FILE_SIZE = 5 * 1024 * 1024        # 5 MB for individual image file


class SecurityGuardMiddleware:
    """
    ASGI Security Guard Middleware:
    1. Intercepts requests before request body parsing occurs.
    2. Rejects unauthenticated requests to protected /api/* endpoints with HTTP 401 before
       deserializing JSON or reading request streams into memory.
    3. Enforces payload size limits (1 MB for JSON, 6 MB for multipart scan) even for chunked
       transfers or missing/misleading Content-Length headers.
    4. Preserves CORS preflight OPTIONS requests without requiring authentication or size checks.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        method = scope.get("method", "")

        # 1. CORS preflight OPTIONS requests are handled by CORSMiddleware
        if method == "OPTIONS":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))

        # 2. Public endpoints: health, login, docs/redoc/openapi
        is_public = (
            path in ("/api/health", "/api/auth/login")
            or path.startswith(("/docs", "/redoc", "/openapi.json"))
        )

        # 3. For protected endpoints under /api/, enforce authentication BEFORE reading body
        if not is_public and path.startswith("/api/"):
            if not auth.is_unauthenticated_dev_mode():
                auth_header = headers.get(b"authorization", b"").decode("latin-1")
                if not auth_header.startswith("Bearer "):
                    response = JSONResponse(
                        status_code=401,
                        content={"detail": "Authentication required. Please provide a valid Bearer token."},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                    return await response(scope, receive, send)

                token = auth_header[7:].strip()
                try:
                    auth.verify_access_token(token)
                except HTTPException as exc:
                    response = JSONResponse(
                        status_code=exc.status_code,
                        content={"detail": exc.detail},
                        headers=exc.headers or {"WWW-Authenticate": "Bearer"}
                    )
                    return await response(scope, receive, send)

        # 4. Enforce payload size limits: check Content-Length AND bound streaming receive
        limit = MAX_UPLOAD_REQUEST_SIZE if path.startswith("/api/meals/scan") else MAX_STANDARD_REQUEST_SIZE

        cl_raw = headers.get(b"content-length")
        if cl_raw:
            try:
                if int(cl_raw) > limit:
                    response = JSONResponse(
                        status_code=413,
                        content={"detail": f"Request payload exceeds maximum allowed size ({limit // (1024*1024)} MB)."}
                    )
                    return await response(scope, receive, send)
            except ValueError:
                pass

        total_bytes = 0

        async def bounded_receive():
            nonlocal total_bytes
            message = await receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                total_bytes += len(chunk)
                if total_bytes > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request payload exceeds maximum allowed size ({limit // (1024*1024)} MB)."
                    )
            return message

        try:
            return await self.app(scope, bounded_receive, send)
        except Exception as exc:
            if isinstance(exc, HTTPException) and exc.status_code == 413:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": exc.detail}
                )
                return await response(scope, receive, send)
            raise


# Register SecurityGuardMiddleware first, then CORSMiddleware second
# In Starlette, the last added middleware is the outermost.
# This ensures CORSMiddleware is outermost:
# - Preflight OPTIONS requests receive CORS headers and exit early.
# - 401 and 413 responses from SecurityGuardMiddleware receive appropriate CORS headers.
app.add_middleware(SecurityGuardMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=preview_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Validates configuration at startup and fails closed if required secrets are missing."""
    validate_auth_config()


def get_client_ip(request: Optional[Request]) -> str:
    """
    Safely resolves client IP for rate limiting.
    By default, strictly prefers the direct peer address (request.client.host)
    to prevent client-controlled forwarding header spoofing.
    Proxy headers are ONLY inspected if TRUST_PROXY_HEADERS=true AND the direct peer
    is verified to be a trusted loopback/private proxy address.
    """
    if not request:
        return "127.0.0.1"

    peer_ip = request.client.host if request.client else "127.0.0.1"

    trust_proxies = os.environ.get("TRUST_PROXY_HEADERS", "false").strip().lower() == "true"
    if not trust_proxies:
        return peer_ip

    is_trusted_peer = (
        peer_ip in ("127.0.0.1", "::1", "localhost", "testclient")
        or peer_ip.startswith((
            "10.", "192.168.",
            "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.",
            "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.",
            "172.28.", "172.29.", "172.30.", "172.31."
        ))
    )
    if not is_trusted_peer:
        return peer_ip

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # In a trusted proxy chain, the trusted proxy appends the client IP at the END
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[-1]

    return peer_ip


class LoginPayload(BaseModel):
    password: str


@app.post("/api/auth/login")
def login_reviewer(payload: LoginPayload, request: Request):
    """
    Public reviewer login endpoint. Validates passcode in constant time,
    enforces per-IP login rate limiting, and issues short-lived JWT Bearer token.
    """
    client_ip = get_client_ip(request)
    check_login_rate_limit(client_ip)

    if not verify_demo_password(payload.password):
        record_failed_login(client_ip)
        raise HTTPException(
            status_code=401,
            detail="Invalid reviewer password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token()
    return {
        "status": "ok",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 14400,
        "scope": "demo_access",
        "message": "Authenticated as demo reviewer."
    }


@app.get("/api/auth/verify")
def verify_reviewer_token(reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Protected session validation endpoint. Verifies the Bearer token claims and expiration.
    """
    return {
        "status": "ok",
        "authenticated": True,
        "sub": reviewer.get("sub", "demo_reviewer"),
        "scope": reviewer.get("scope", "demo_access")
    }



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
    meal_type: Optional[str] = Form("Lunch"),
    request: Request = None,
    _reviewer: Dict[str, Any] = Depends(get_current_reviewer)
):
    """
    Gemini Vision analysis endpoint for meal photos.
    Enforces authentication, upload size limit (5 MB), and rate limiting.
    """
    client_ip = get_client_ip(request)
    check_rate_limit(f"scan:{client_ip}", max_requests=10, window_seconds=60, action_desc="meal scan requests")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    try:
        # Enforce upload size limit by reading up to 5MB + 1 byte
        image_bytes = await file.read(MAX_IMAGE_FILE_SIZE + 1)
        if len(image_bytes) > MAX_IMAGE_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds maximum allowed limit (5 MB).")

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
def create_meal(meal: Dict[str, Any], _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
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
def get_meal_history(_reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
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
def edit_meal(meal_id: str, updated_meal: Dict[str, Any], _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
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
def remove_meal(meal_id: str, _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Deletes a meal from storage.
    """
    success = delete_meal(meal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meal not found.")
    return {"status": "ok", "deleted": meal_id}


@app.get("/api/progress/analytics")
def get_progress_analytics(days: int = 7, _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Returns period analytics (averages, calorie adherence, protein adherence,
    consistency score, goal interpretation, weight trend) using real backend data.
    """
    if days not in (7, 30):
        days = 7

    profile = load_profile()
    if not profile:
        return {
            "has_profile": False,
            "days_period": days,
            "history": [],
            "averages": {
                "total_days": days,
                "tracked_days": 0,
                "avg_calories": 0,
                "avg_protein": 0,
                "avg_carbs": 0,
                "avg_fat": 0,
                "total_meals": 0,
            },
            "cal_adherence": {
                "total_days": days,
                "tracked_days": 0,
                "on_target_days": 0,
                "adherence_pct": 0,
            },
            "p_adherence": {
                "total_days": days,
                "tracked_days": 0,
                "on_target_days": 0,
                "adherence_pct": 0,
            },
            "consistency_pct": 0,
            "weight_change": weight_storage.get_weight_change(),
            "interpretation": "No profile configured yet. Please complete onboarding.",
            "goal": "None",
            "targets": {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0,
            },
            "weight_history": [],
        }
    snap = get_latest_target_snapshot()
    targets = None
    tdee = 0
    if snap:
        targets = _extract_coach_targets(snap)
        tdee = snap.get("tdee") or 0

    if not targets:
        try:
            plan = calculate_full_plan(
                weight_kg=float(profile["weight_kg"]),
                height_cm=float(profile["height_cm"]),
                age=int(profile["age"]),
                sex=str(profile["sex"]),
                activity_level=str(profile["activity_level"]),
                goal=str(profile["goal"]),
                intensity=str(profile["intensity"])
            )
            targets = _extract_coach_targets(plan)
            tdee = plan.get("tdee", 0)
        except Exception:
            targets = None

    if not targets:
        raise HTTPException(
            status_code=422,
            detail="User nutritional targets are unavailable and cannot be recalculated."
        )

    target_cal = targets["calories"]
    target_p = targets["protein"]
    target_c = targets["carbs"]
    target_f = targets["fat"]
    goal = str(profile.get("goal", ""))

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
        "has_profile": True,
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
def get_profile_endpoint(response: Response, _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Returns saved user profile, active target snapshot/plan, and authoritative goal/activity options.
    Distinguishes first-time users (has_profile=False, profile=None) from returning users.
    Includes Cache-Control: no-store to prevent client or intermediary caching.
    """
    response.headers["Cache-Control"] = "no-store"
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

    profile = load_profile()
    if not profile:
        return {
            "has_profile": False,
            "profile": None,
            "active_plan": None,
            "options": options
        }

    if "name" not in profile or profile["name"] is None:
        profile["name"] = ""

    snap = get_latest_target_snapshot()
    if snap:
        active_plan = snap
    else:
        try:
            active_plan = calculate_full_plan(
                weight_kg=float(profile["weight_kg"]),
                height_cm=float(profile["height_cm"]),
                age=int(profile["age"]),
                sex=str(profile["sex"]),
                activity_level=str(profile["activity_level"]),
                goal=str(profile["goal"]),
                intensity=str(profile["intensity"])
            )
        except Exception as err:
            logger.warning(f"Failed to calculate active plan from profile: {err}")
            active_plan = None

    return {
        "has_profile": True,
        "profile": profile,
        "active_plan": active_plan,
        "options": options
    }


@app.post("/api/profile/preview")
def preview_profile_plan(payload: Dict[str, Any], _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Calculates proposed plan preview based on user edits without saving or updating snapshots.
    Handles both first-time onboarding previews and returning user plan revisions.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid profile payload.")

    valid, msg = validate_profile_data(payload)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    curr_profile = load_profile()
    current_plan = None
    if curr_profile:
        if "name" not in curr_profile or curr_profile["name"] is None:
            curr_profile["name"] = ""
        snap = get_latest_target_snapshot()
        if snap:
            current_plan = snap
        else:
            try:
                current_plan = calculate_full_plan(
                    weight_kg=float(curr_profile["weight_kg"]),
                    height_cm=float(curr_profile["height_cm"]),
                    age=int(curr_profile["age"]),
                    sex=str(curr_profile["sex"]),
                    activity_level=str(curr_profile["activity_level"]),
                    goal=str(curr_profile["goal"]),
                    intensity=str(curr_profile["intensity"])
                )
            except Exception:
                current_plan = None

    try:
        proposed_plan = calculate_full_plan(
            weight_kg=float(payload["weight_kg"]),
            height_cm=float(payload["height_cm"]),
            age=int(payload["age"]),
            sex=str(payload["sex"]),
            activity_level=str(payload["activity_level"]),
            goal=str(payload["goal"]),
            intensity=str(payload["intensity"])
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "current_profile": curr_profile,
        "current_plan": current_plan,
        "proposed_profile": payload,
        "proposed_plan": proposed_plan
    }


@app.post("/api/profile/apply")
def apply_profile_plan(payload: Dict[str, Any], _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Validates, calculates plan, saves user profile, logs weight entry,
    and creates a new immutable target snapshot.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid profile payload.")

    valid, msg = validate_profile_data(payload)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    weight_val = float(payload["weight_kg"])
    eff_date = payload.get("effective_date") or datetime.date.today().isoformat()

    # Calculate plan first to ensure feasibility before persisting state
    try:
        new_plan = calculate_full_plan(
            weight_kg=weight_val,
            height_cm=float(payload["height_cm"]),
            age=int(payload["age"]),
            sex=str(payload["sex"]),
            activity_level=str(payload["activity_level"]),
            goal=str(payload["goal"]),
            intensity=str(payload["intensity"])
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Pre-validate snapshot candidate before mutating persistent storage
    test_snap = {
        "snapshot_id": "pre-check-validation",
        "effective_date": eff_date,
        "calorie_target": new_plan.get("target_calories"),
        "protein_target": new_plan.get("protein_g"),
        "carbs_target": new_plan.get("carbs_g"),
        "fat_target": new_plan.get("fat_g"),
    }
    snap_valid, snap_msg = target_storage.validate_target_snapshot(test_snap)
    if not snap_valid:
        raise HTTPException(status_code=400, detail=f"Calculated plan failed snapshot validation: {snap_msg}")

    prev_profile = load_profile()
    save_success = save_profile(payload)
    if not save_success:
        raise HTTPException(status_code=500, detail="Failed to save profile to disk.")

    snap_success, snapshot = create_target_snapshot(new_plan, effective_date=eff_date)
    if not snap_success or not snapshot:
        # Rollback profile if snapshot persistence fails to prevent partial state
        if prev_profile is not None:
            save_profile(prev_profile)
        else:
            reset_profile_storage()
        raise HTTPException(status_code=500, detail="Failed to create target snapshot.")

    weight_storage.add_weight_entry(weight_val, date_str=eff_date)

    saved_profile = load_profile() or payload
    if "name" not in saved_profile or saved_profile["name"] is None:
        saved_profile["name"] = payload.get("name", "")

    return {
        "status": "ok",
        "profile": saved_profile,
        "target_snapshot": snapshot,
        "active_plan": new_plan
    }


@app.post("/api/profile/reset")
def reset_profile_endpoint(_reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Resets profile and target snapshot storage.
    Enables demo reviewers to test a genuinely clean onboarding flow from scratch.
    Disabled in production by default to protect shared reviewer data.
    Permitted in production only when ENABLE_DEMO_RESET=true is explicitly configured.
    """
    if is_production_env() and not is_demo_reset_enabled():
        raise HTTPException(
            status_code=403,
            detail="Profile reset is disabled in production to protect shared reviewer data. Set ENABLE_DEMO_RESET=true to enable."
        )

    reset_profile_storage()
    reset_target_storage()
    return {
        "status": "ok",
        "message": "Profile and target snapshots have been reset. Onboarding state is now clean.",
        "has_profile": False,
        "profile": None,
        "active_plan": None
    }


@app.post("/api/progress/weight")
def log_weight(payload: Dict[str, Any], _reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
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
def get_coach_context(_reviewer: Dict[str, Any] = Depends(get_current_reviewer)):
    """
    Returns current live user profile, daily targets, consumed totals,
    remaining totals, and today's confirmed meals for the Coach UI context card.
    """
    today_str = datetime.date.today().isoformat()
    profile = load_profile()
    if not profile:
        return {
            "has_profile": False,
            "user_name": "there",
            "target_calories": 0,
            "consumed_calories": 0,
            "remaining_calories": 0,
            "target_protein": 0,
            "consumed_protein": 0,
            "remaining_protein": 0,
            "target_carbs": 0,
            "consumed_carbs": 0,
            "remaining_carbs": 0,
            "target_fat": 0,
            "consumed_fat": 0,
            "remaining_fat": 0,
            "today_meals": []
        }

    targets = None
    snap = get_latest_target_snapshot()
    if snap:
        targets = _extract_coach_targets(snap)

    # If snapshot is missing or invalid, recalculate from active profile
    if not targets:
        try:
            plan = calculate_full_plan(
                weight_kg=float(profile["weight_kg"]),
                height_cm=float(profile["height_cm"]),
                age=int(profile["age"]),
                sex=str(profile["sex"]),
                activity_level=str(profile["activity_level"]),
                goal=str(profile["goal"]),
                intensity=str(profile["intensity"])
            )
            targets = _extract_coach_targets(plan)
        except Exception:
            targets = None

    if not targets:
        raise HTTPException(
            status_code=422,
            detail="User nutritional targets are unavailable and cannot be recalculated."
        )

    target_cal = targets["calories"]
    target_p = targets["protein"]
    target_c = targets["carbs"]
    target_f = targets["fat"]

    consumed = get_daily_totals(today_str)
    today_meals = get_meals_for_date(today_str)

    cons_cal = consumed.get("calories", 0)
    cons_p = consumed.get("protein_g", 0)
    cons_c = consumed.get("carbs_g", 0)
    cons_f = consumed.get("fat_g", 0)

    raw_name = profile.get("name")
    user_name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else "there"

    return {
        "has_profile": True,
        "user_name": user_name,
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
def coach_chat(
    payload: Dict[str, Any],
    request: Request = None,
    _reviewer: Dict[str, Any] = Depends(get_current_reviewer)
):
    """
    Contextual AI Nutrition Coach endpoint.
    Retrieves live server-side Python context (profile, targets, consumed, meals)
    and sends prompt + history to Gemini Vision/Assistant engine.
    Enforces authentication and rate limiting.
    """
    client_ip = get_client_ip(request)
    check_rate_limit(f"coach:{client_ip}", max_requests=15, window_seconds=60, action_desc="AI Coach chat requests")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a dictionary.")

    message = payload.get("message")
    if not message or not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="Field 'message' is required.")

    conversation = payload.get("conversation", [])

    today_str = datetime.date.today().isoformat()
    profile = load_profile()
    if not profile:
        return {
            "success": True,
            "response": "Welcome to Revelation! Before I can give you personalized nutrition coaching, please complete your profile setup so I know your exact targets and dietary goals.",
            "suggested_actions": ["Complete Profile", "Set Nutrition Goals", "Log First Meal"]
        }

    targets = None
    snap = get_latest_target_snapshot()
    if snap:
        targets = _extract_coach_targets(snap)

    if not targets:
        try:
            plan = calculate_full_plan(
                weight_kg=float(profile["weight_kg"]),
                height_cm=float(profile["height_cm"]),
                age=int(profile["age"]),
                sex=str(profile["sex"]),
                activity_level=str(profile["activity_level"]),
                goal=str(profile["goal"]),
                intensity=str(profile["intensity"])
            )
            targets = _extract_coach_targets(plan)
        except Exception:
            targets = None

    if not targets:
        raise HTTPException(
            status_code=422,
            detail="User nutritional targets are unavailable and cannot be recalculated."
        )

    user_plan = {
        "name": profile.get("name", ""),
        "age": profile.get("age"),
        "sex": profile.get("sex"),
        "height_cm": profile.get("height_cm"),
        "weight_kg": profile.get("weight_kg"),
        "activity_level": profile.get("activity_level"),
        "goal": profile.get("goal"),
        "intensity": profile.get("intensity"),
        "target_calories": targets["calories"],
        "protein_g": targets["protein"],
        "carbs_g": targets["carbs"],
        "fat_g": targets["fat"],
        "tdee": snap.get("tdee") if (snap and "tdee" in snap) else targets["calories"]
    }

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

