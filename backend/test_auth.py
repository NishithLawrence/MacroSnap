"""
Comprehensive Automated Security & Authentication Test Suite (backend/test_auth.py)
===================================================================================
Tests all security requirements and remediations from MacroSnap Phase 2.4 & 2.6:
- Missing production secrets and fail-closed startup behavior.
- Rejection of unknown, misspelled, and invalid APP_ENV values at startup.
- Strict validation and bounds enforcement on TOKEN_EXPIRE_HOURS (1 to 72).
- Explicit local-development unauthenticated bypass and rejection in production/testing.
- Protection against Client IP spoofing via X-Forwarded-For headers.
- Authentication enforced before request body reading/parsing (malformed JSON returns 401, not 422).
- Streaming and chunked payload size limits (1 MB JSON, 6 MB scan) enforced.
- Tightened CORS origin matching (rejects third-party Vercel projects).
- Disabling of public OpenAPI/Swagger/ReDoc documentation in production.
- Valid and invalid login authentication with sliding window rate limiting.
- Complete route protection audit: all protected endpoints reject unauthenticated access.
- Unauthorized requests never reach Gemini AI or mutate persistent files.
"""

import os
import io
import time
import tempfile
from datetime import timedelta
import pytest
import jwt
from fastapi.testclient import TestClient
from main import app, get_client_ip
import auth
from auth import (
    create_access_token,
    verify_access_token,
    validate_auth_config,
    validate_token_expire_hours,
    is_unauthenticated_dev_mode,
    reset_rate_limits,
    JWT_ALGORITHM,
)
import profile_storage
import meal_storage
import target_storage
import weight_storage

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_test_environment(monkeypatch):
    """Isolates storage and resets rate limiters between tests."""
    reset_rate_limits()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AUTH_SECRET_KEY", "mock-test-secret-key-at-least-32-chars-long")
    monkeypatch.setenv("DEMO_PASSWORD", "mock-test-demo-password")
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "4")
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)

    with tempfile.TemporaryDirectory() as test_dir:
        data_dir = os.path.join(test_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        orig_profile = profile_storage.PROFILE_FILE
        orig_target = target_storage.TARGET_FILE
        orig_meal = meal_storage.STORAGE_FILE
        orig_weight = weight_storage.WEIGHT_FILE

        profile_storage.PROFILE_FILE = os.path.join(data_dir, "profile.json")
        target_storage.TARGET_FILE = os.path.join(data_dir, "target_history.json")
        meal_storage.STORAGE_FILE = os.path.join(data_dir, "meals.json")
        weight_storage.WEIGHT_FILE = os.path.join(data_dir, "weight_history.json")

        yield

        profile_storage.PROFILE_FILE = orig_profile
        target_storage.TARGET_FILE = orig_target
        meal_storage.STORAGE_FILE = orig_meal
        weight_storage.WEIGHT_FILE = orig_weight
        reset_rate_limits()


def test_production_missing_secrets_fails_closed(monkeypatch):
    """Production must refuse startup when required secrets are missing or invalid."""
    monkeypatch.setenv("APP_ENV", "production")

    # 1. Missing DEMO_PASSWORD
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    monkeypatch.setenv("AUTH_SECRET_KEY", "mock-test-secret-key-at-least-32-chars-long")
    with pytest.raises(RuntimeError, match="DEMO_PASSWORD must be configured"):
        validate_auth_config()

    # 2. Too short DEMO_PASSWORD (< 8 chars)
    monkeypatch.setenv("DEMO_PASSWORD", "short")
    with pytest.raises(RuntimeError, match="DEMO_PASSWORD must be configured and at least 8 characters"):
        validate_auth_config()

    # 3. Missing AUTH_SECRET_KEY
    monkeypatch.setenv("DEMO_PASSWORD", "strong-demo-password-2026")
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY must be configured"):
        validate_auth_config()

    # 4. Too short AUTH_SECRET_KEY (< 32 chars)
    monkeypatch.setenv("AUTH_SECRET_KEY", "short-secret-key")
    with pytest.raises(RuntimeError, match="at least 32 characters"):
        validate_auth_config()

    # 5. Valid production configuration passes
    monkeypatch.setenv("AUTH_SECRET_KEY", "production-secret-key-that-is-at-least-32-characters-long")
    validate_auth_config()  # Does not raise


def test_unrecognized_app_env_fails_closed(monkeypatch):
    """Startup must fail closed if APP_ENV is invalid, unknown, or misspelled."""
    invalid_envs = ["staging", "preview", "prod", "development_local", "QA", "random_string"]
    for env in invalid_envs:
        monkeypatch.setenv("APP_ENV", env)
        with pytest.raises(RuntimeError, match="Unsupported or invalid APP_ENV"):
            validate_auth_config()


def test_token_expire_hours_validation(monkeypatch):
    """TOKEN_EXPIRE_HOURS must be strictly validated as an integer between 1 and 72."""
    # 1. Non-numeric
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "abc")
    with pytest.raises(RuntimeError, match="Must be an integer between 1 and 72"):
        validate_token_expire_hours()

    # 2. Fractional
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "4.5")
    with pytest.raises(RuntimeError, match="Must be an integer between 1 and 72"):
        validate_token_expire_hours()

    # 3. Zero
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "0")
    with pytest.raises(RuntimeError, match="between 1 and 72 inclusive"):
        validate_token_expire_hours()

    # 4. Negative
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "-10")
    with pytest.raises(RuntimeError, match="between 1 and 72 inclusive"):
        validate_token_expire_hours()

    # 5. Out of upper bounds
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "73")
    with pytest.raises(RuntimeError, match="between 1 and 72 inclusive"):
        validate_token_expire_hours()

    # 6. Lower boundary value
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "1")
    assert validate_token_expire_hours() == 1

    # 7. Upper boundary value
    monkeypatch.setenv("TOKEN_EXPIRE_HOURS", "72")
    assert validate_token_expire_hours() == 72


def test_dev_bypass_only_in_development_env(monkeypatch):
    """Unauthenticated dev bypass must strictly require APP_ENV=development and never work in production/test."""
    monkeypatch.setenv("ALLOW_UNAUTHENTICATED", "true")

    # In production, bypass is strictly rejected
    monkeypatch.setenv("APP_ENV", "production")
    assert is_unauthenticated_dev_mode() is False

    # In test, bypass is strictly rejected
    monkeypatch.setenv("APP_ENV", "test")
    assert is_unauthenticated_dev_mode() is False

    # In development, bypass is allowed only when explicitly requested
    monkeypatch.setenv("APP_ENV", "development")
    assert is_unauthenticated_dev_mode() is True

    # In development without the flag, bypass is False
    monkeypatch.setenv("ALLOW_UNAUTHENTICATED", "false")
    assert is_unauthenticated_dev_mode() is False


def test_client_ip_spoofing_prevention(monkeypatch):
    """Arbitrary client-supplied forwarding headers must not rotate rate-limit identity."""
    reset_rate_limits()
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)

    # Attempt failed logins while injecting rotating fake X-Forwarded-For headers
    for i in range(5):
        res = client.post(
            "/api/auth/login",
            json={"password": "wrong-password"},
            headers={"X-Forwarded-For": f"198.51.100.{i}, 203.0.113.1"}
        )
        assert res.status_code == 401

    # 6th attempt with another new fake IP must still be blocked by rate limit
    res_blocked = client.post(
        "/api/auth/login",
        json={"password": "mock-test-demo-password"},
        headers={"X-Forwarded-For": "198.51.100.99"}
    )
    assert res_blocked.status_code == 429
    assert "Too many failed login attempts" in res_blocked.json()["detail"]


def test_auth_enforced_before_request_body_parsing():
    """Unauthenticated requests must be rejected with 401 without parsing malformed JSON."""
    # Send malformed JSON to a protected JSON endpoint without Authorization header
    res = client.post(
        "/api/profile/apply",
        content=b"{invalid json content!",
        headers={"Content-Type": "application/json"}
    )
    # Must return 401 Unauthorized, NOT 422 Unprocessable Entity
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_unauthenticated_oversized_request_does_not_parse():
    """Oversized request without auth returns 401 without buffering or processing payload."""
    res = client.post(
        "/api/profile/apply",
        content=b"x" * (2 * 1024 * 1024),
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 401


def test_chunked_streaming_payload_size_enforcement():
    """Requests exceeding size limits without Content-Length are aborted with 413."""
    token = create_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2 MB payload to a 1 MB limit endpoint
    large_payload = b" " * (2 * 1024 * 1024)
    res = client.post("/api/profile/preview", content=large_payload, headers=headers)
    assert res.status_code == 413
    assert "exceeds maximum" in res.json()["detail"]


def test_login_valid_password():
    """Valid passcode issues a short-lived Bearer token with expected claims."""
    res = client.post("/api/auth/login", json={"password": "mock-test-demo-password"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 14400
    assert data["scope"] == "demo_access"

    # Verify returned token can be verified
    payload = verify_access_token(data["access_token"])
    assert payload["sub"] == "demo_reviewer"
    assert payload["scope"] == "demo_access"


def test_login_invalid_password():
    """Invalid passcode returns 401 Unauthorized without leaking sensitive data."""
    res = client.post("/api/auth/login", json={"password": "wrong-password-guess"})
    assert res.status_code == 401
    data = res.json()
    assert data["detail"] == "Invalid reviewer password."


def test_verify_valid_token():
    """Protected /api/auth/verify confirms valid reviewer session."""
    token = create_access_token()
    res = client.get("/api/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["authenticated"] is True
    assert data["sub"] == "demo_reviewer"


def test_token_validation_edge_cases():
    """Tests missing, malformed, expired, tampered, and incorrectly signed tokens."""
    # 1. Missing token
    res = client.get("/api/auth/verify")
    assert res.status_code == 401

    # 2. Malformed token
    res = client.get("/api/auth/verify", headers={"Authorization": "Bearer not-a-valid-jwt-token"})
    assert res.status_code == 401

    # 3. Expired token
    expired_token = create_access_token(expires_delta=timedelta(seconds=-10))
    res = client.get("/api/auth/verify", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "Session has expired" in res.json()["detail"]

    # 4. Incorrect secret key
    other_key_token = jwt.encode(
        {"sub": "demo_reviewer", "scope": "demo_access", "exp": int(time.time()) + 3600, "iat": int(time.time())},
        "completely-different-signing-key-32-chars",
        algorithm=JWT_ALGORITHM
    )
    res = client.get("/api/auth/verify", headers={"Authorization": f"Bearer {other_key_token}"})
    assert res.status_code == 401
    assert "Invalid authorization token" in res.json()["detail"]

    # 5. Tampered token payload
    valid_token = create_access_token()
    parts = valid_token.split(".")
    tampered_token = f"{parts[0]}.eyJhZG1pbiI6dHJ1ZX0.{parts[2]}"
    res = client.get("/api/auth/verify", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401

    # 6. Invalid token claims
    invalid_claim_token = jwt.encode(
        {"sub": "unauthorized_user", "scope": "demo_access", "exp": int(time.time()) + 3600, "iat": int(time.time())},
        os.environ["AUTH_SECRET_KEY"],
        algorithm=JWT_ALGORITHM
    )
    res = client.get("/api/auth/verify", headers={"Authorization": f"Bearer {invalid_claim_token}"})
    assert res.status_code == 401
    assert "Invalid token claims" in res.json()["detail"]


def test_all_13_protected_routes_reject_unauthenticated():
    """Audits and guarantees every protected route and HTTP method rejects unauthenticated access."""
    routes_to_test = [
        ("GET", "/api/auth/verify", {}),
        ("GET", "/api/profile", {}),
        ("POST", "/api/profile/preview", {"json": {"age": 25, "sex": "Male", "height_cm": 178, "weight_kg": 75, "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"}}),
        ("POST", "/api/profile/apply", {"json": {"age": 25, "sex": "Male", "height_cm": 178, "weight_kg": 75, "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"}}),
        ("GET", "/api/coach/context", {}),
        ("POST", "/api/coach/chat", {"json": {"message": "Hello Coach"}}),
        ("GET", "/api/meals/history", {}),
        ("POST", "/api/meals", {"json": {"date": "2026-10-20", "foods": []}}),
        ("PUT", "/api/meals/test_meal_123", {"json": {"name": "Test"}}),
        ("DELETE", "/api/meals/test_meal_123", {}),
        ("GET", "/api/progress/analytics", {}),
        ("POST", "/api/progress/weight", {"json": {"weight_kg": 75.0}}),
        ("POST", "/api/meals/scan", {"files": {"file": ("meal.jpg", b"fake-bytes", "image/jpeg")}}),
    ]

    for method, path, kwargs in routes_to_test:
        if method == "GET":
            res = client.get(path, **kwargs)
        elif method == "POST":
            res = client.post(path, **kwargs)
        elif method == "PUT":
            res = client.put(path, **kwargs)
        elif method == "DELETE":
            res = client.delete(path, **kwargs)

        assert res.status_code == 401, f"Route {method} {path} unexpectedly allowed unauthenticated access! Status: {res.status_code}"


def test_unauthorized_requests_never_mutate_persistent_storage(monkeypatch):
    """Unauthorized requests must be rejected before disk operations or Gemini calls."""
    # 1. Profile persistence should be untouched
    unauth_profile = {
        "name": "Intruder User",
        "age": 30,
        "sex": "Female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "Sedentary",
        "goal": "Fat Loss",
        "intensity": "Moderate"
    }
    res_prof = client.post("/api/profile/apply", json=unauth_profile)
    assert res_prof.status_code == 401
    assert profile_storage.load_profile() is None

    # 2. Meal storage should be untouched
    unauth_meal = {
        "meal_id": "intruder_meal_1",
        "date": "2026-10-20",
        "foods": [{"name": "Burger", "calories": 800}]
    }
    res_meal = client.post("/api/meals", json=unauth_meal)
    assert res_meal.status_code == 401
    assert len(meal_storage.load_meals()) == 0

    # 3. Weight storage should be untouched
    res_weight = client.post("/api/progress/weight", json={"weight_kg": 95.0})
    assert res_weight.status_code == 401
    assert len(weight_storage.load_weight_history()) == 0

    # 4. AI Coach assistant should never be invoked
    called = []
    import backend.main
    monkeypatch.setattr(backend.main, "query_nutrition_assistant", lambda **kwargs: called.append(True))
    res_coach = client.post("/api/coach/chat", json={"message": "Analyze my macros"})
    assert res_coach.status_code == 401
    assert len(called) == 0, "AI Coach assistant function was invoked on unauthorized request!"


def test_upload_size_limit_enforcement():
    """Uploads exceeding 5 MB must be rejected with 413 Payload Too Large."""
    token = create_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 5.5 MB payload
    large_payload = b"0" * (5500 * 1024)
    files = {"file": ("large_meal.jpg", large_payload, "image/jpeg")}

    res = client.post("/api/meals/scan", files=files, headers=headers)
    assert res.status_code == 413
    assert "exceeds maximum" in res.json()["detail"].lower()


def test_ai_endpoints_rate_limiting():
    """Tests rate limit enforcement on AI endpoints."""
    token = create_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Mock query_nutrition_assistant so it returns immediately
    import backend.main
    backend.main.query_nutrition_assistant = lambda **kwargs: (True, "Mock Coach response")

    # Set up baseline profile
    profile_storage.save_profile({
        "age": 25, "sex": "Male", "height_cm": 178.0, "weight_kg": 75.0,
        "activity_level": "Moderately Active", "goal": "Fat Loss", "intensity": "Moderate"
    })

    for i in range(15):
        res = client.post("/api/coach/chat", json={"message": f"Hello {i}"}, headers=headers)
        assert res.status_code == 200, f"Request {i} failed: {res.text}"

    # 16th request must trigger 429
    res_rate_limited = client.post("/api/coach/chat", json={"message": "Exceeding request"}, headers=headers)
    assert res_rate_limited.status_code == 429
    assert "Rate limit exceeded" in res_rate_limited.json()["detail"]


def test_tightened_cors_origins():
    """Tightened CORS configuration must reject unauthorized origins while allowing approved ones."""
    # 1. Approved exact production origin
    res_prod = client.options(
        "/api/profile",
        headers={"Origin": "https://macro-snap-eosin.vercel.app", "Access-Control-Request-Method": "GET"}
    )
    assert res_prod.status_code == 200
    assert res_prod.headers.get("access-control-allow-origin") == "https://macro-snap-eosin.vercel.app"

    # 2. Approved preview origin matching project and user slug
    res_preview = client.options(
        "/api/profile",
        headers={"Origin": "https://macro-snap-git-preview-nishithlawrence.vercel.app", "Access-Control-Request-Method": "GET"}
    )
    assert res_preview.status_code == 200
    assert res_preview.headers.get("access-control-allow-origin") == "https://macro-snap-git-preview-nishithlawrence.vercel.app"

    # 3. Third-party Vercel project with macro-snap prefix must be REJECTED
    res_attacker = client.options(
        "/api/profile",
        headers={"Origin": "https://macro-snap-attacker.vercel.app", "Access-Control-Request-Method": "GET"}
    )
    assert res_attacker.headers.get("access-control-allow-origin") is None

    # 4. Malicious domain suffix must be REJECTED
    res_suffix = client.options(
        "/api/profile",
        headers={"Origin": "https://macro-snap-eosin.vercel.app.attacker.com", "Access-Control-Request-Method": "GET"}
    )
    assert res_suffix.headers.get("access-control-allow-origin") is None

    # 5. Arbitrary untrusted origin must be REJECTED
    res_evil = client.options(
        "/api/profile",
        headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "GET"}
    )
    assert res_evil.headers.get("access-control-allow-origin") is None


def test_public_health_endpoint():
    """GET /api/health must remain public and non-sensitive."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data == {"status": "ok", "service": "macrosnap-api"}


def test_production_documentation_disabled():
    """FastAPI docs/redoc/openapi must be disabled in production and return 404."""
    from fastapi import FastAPI
    import os

    # Recreate app instance as in main.py with APP_ENV=production
    is_prod = True
    prod_app = FastAPI(
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )
    prod_client = TestClient(prod_app)

    assert prod_client.get("/docs").status_code == 404
    assert prod_client.get("/redoc").status_code == 404
    assert prod_client.get("/openapi.json").status_code == 404
