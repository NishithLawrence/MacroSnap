"""
MacroSnap Restricted Demo Authentication Module (backend/auth.py)
================================================================
Implements server-enforced, fail-closed authentication for the portfolio demonstration.
Uses PyJWT (HS256) for signed, short-lived Bearer tokens.
Enforces constant-time password comparison, token expiration, and claims validation.
"""

import os
import time
import secrets
import threading
from typing import Dict, Any, Optional
from datetime import timedelta
import jwt
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"
DEFAULT_TOKEN_EXPIRE_HOURS = 4
MIN_SECRET_LENGTH = 32

# In-memory rate limiting structures
# Note on limitations: In-memory rate limiting applies per worker process.
# On multi-worker deployments (e.g. multiple Gunicorn/Uvicorn workers on Render),
# limits are partitioned across workers. For full production multi-worker consistency,
# a distributed store (e.g., Redis) should be used in Phase 3.
_rate_limit_lock = threading.Lock()
_login_failed_attempts: Dict[str, list] = {}
_endpoint_access_log: Dict[str, list] = {}


SUPPORTED_ENVS = {"production", "development", "test"}


def get_app_env() -> str:
    raw = os.environ.get("APP_ENV")
    return raw.strip().lower() if raw is not None else "production"


def is_unauthenticated_dev_mode() -> bool:
    env = get_app_env()
    allow_unauth = os.environ.get("ALLOW_UNAUTHENTICATED", "").strip().lower() == "true"
    return env == "development" and allow_unauth


def validate_token_expire_hours() -> int:
    """
    Validates TOKEN_EXPIRE_HOURS environment variable.
    Must be an integer between 1 and 72 inclusive.
    Fails closed at startup with RuntimeError rather than converting to a runtime 500.
    """
    raw = os.environ.get("TOKEN_EXPIRE_HOURS")
    if raw is None or not raw.strip():
        return DEFAULT_TOKEN_EXPIRE_HOURS

    val_str = raw.strip()
    try:
        val = int(val_str)
    except ValueError:
        raise RuntimeError(
            f"FATAL: Invalid TOKEN_EXPIRE_HOURS '{raw}'. Must be an integer between 1 and 72. "
            "Server startup aborted to fail closed."
        )

    if val < 1 or val > 72:
        raise RuntimeError(
            f"FATAL: TOKEN_EXPIRE_HOURS must be between 1 and 72 inclusive. Got: {val}. "
            "Server startup aborted to fail closed."
        )

    return val


def validate_auth_config() -> None:
    """
    Validates authentication environment variables at startup.
    Fails closed in production, test, and any unrecognized or misspelled environment.
    """
    raw_env = os.environ.get("APP_ENV")
    env = raw_env.strip().lower() if raw_env is not None else "production"

    if env not in SUPPORTED_ENVS:
        raise RuntimeError(
            f"FATAL: Unsupported or invalid APP_ENV '{raw_env}'. Must be one of {sorted(list(SUPPORTED_ENVS))}. "
            "Server startup aborted to fail closed."
        )

    # Validate TOKEN_EXPIRE_HOURS bounds
    validate_token_expire_hours()

    if env == "development":
        allow_unauth = os.environ.get("ALLOW_UNAUTHENTICATED", "").strip().lower() == "true"
        if allow_unauth:
            print("[SECURITY WARNING] MacroSnap is running in unauthenticated development mode. Do not use in production.")
            return
        # Authenticated development mode: set dev defaults if not explicitly configured
        if not os.environ.get("DEMO_PASSWORD"):
            os.environ["DEMO_PASSWORD"] = "dev-demo-password-1234"
        if not os.environ.get("AUTH_SECRET_KEY"):
            os.environ["AUTH_SECRET_KEY"] = "dev-secret-key-must-be-at-least-32-chars-long"

    elif env == "production":
        demo_pwd = os.environ.get("DEMO_PASSWORD", "").strip()
        if not demo_pwd or len(demo_pwd) < 8:
            raise RuntimeError(
                "FATAL: In production (APP_ENV=production), DEMO_PASSWORD must be configured and at least 8 characters. "
                "Server startup aborted to fail closed."
            )

        secret_key = os.environ.get("AUTH_SECRET_KEY", "").strip()
        if not secret_key or len(secret_key) < MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"FATAL: In production, AUTH_SECRET_KEY must be configured and at least {MIN_SECRET_LENGTH} characters. "
                "Server startup aborted to fail closed."
            )

    elif env == "test":
        # In test mode, fallback to standard mock test credentials if not explicitly supplied
        if "DEMO_PASSWORD" not in os.environ:
            os.environ["DEMO_PASSWORD"] = "mock-test-demo-password"
        if "AUTH_SECRET_KEY" not in os.environ:
            os.environ["AUTH_SECRET_KEY"] = "mock-test-secret-key-at-least-32-chars-long"


def reset_rate_limits() -> None:
    """Helper to reset in-memory rate limiting state (used by test suites)."""
    with _rate_limit_lock:
        _login_failed_attempts.clear()
        _endpoint_access_log.clear()


def get_secret_key() -> str:
    secret = os.environ.get("AUTH_SECRET_KEY", "")
    if not secret:
        if get_app_env() == "test":
            return "mock-test-secret-key-at-least-32-chars-long"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication configuration error."
        )
    return secret


def get_demo_password() -> str:
    pwd = os.environ.get("DEMO_PASSWORD", "")
    if not pwd and get_app_env() == "test":
        return "mock-test-demo-password"
    return pwd


def verify_demo_password(provided_password: str) -> bool:
    """
    Performs constant-time comparison against configured demo password.
    """
    if not isinstance(provided_password, str) or not provided_password:
        return False
    expected = get_demo_password()
    if not expected:
        return False
    return secrets.compare_digest(provided_password, expected)


def create_access_token(
    data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a signed JWT access token with HS256 algorithm and explicit expiry.
    """
    to_encode = dict(data) if data else {}
    now = int(time.time())
    if expires_delta:
        expire = now + int(expires_delta.total_seconds())
    else:
        expire_hours = validate_token_expire_hours()
        expire = now + (expire_hours * 3600)

    to_encode.update({
        "sub": "demo_reviewer",
        "scope": "demo_access",
        "iat": now,
        "exp": expire,
    })

    secret = get_secret_key()
    return jwt.encode(to_encode, secret, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates JWT token with strict signature, algorithm, and claim checks.
    """
    secret = get_secret_key()
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["exp", "sub", "scope"],
            }
        )
        if payload.get("sub") != "demo_reviewer" or payload.get("scope") != "demo_access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token.",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_reviewer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces authentication on protected routes.
    """
    if is_unauthenticated_dev_mode():
        return {"sub": "dev_user", "mode": "unauthenticated"}

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return verify_access_token(credentials.credentials)


def check_rate_limit(
    key: str,
    max_requests: int,
    window_seconds: int,
    action_desc: str = "requests"
) -> None:
    """
    Sliding window in-memory rate limiter.
    """
    now = time.time()
    with _rate_limit_lock:
        if key not in _endpoint_access_log:
            _endpoint_access_log[key] = []
        # Prune timestamps outside window
        _endpoint_access_log[key] = [t for t in _endpoint_access_log[key] if now - t < window_seconds]
        if len(_endpoint_access_log[key]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: too many {action_desc}. Please wait a moment before retrying."
            )
        _endpoint_access_log[key].append(now)


def record_failed_login(client_ip: str) -> None:
    now = time.time()
    with _rate_limit_lock:
        if client_ip not in _login_failed_attempts:
            _login_failed_attempts[client_ip] = []
        _login_failed_attempts[client_ip] = [t for t in _login_failed_attempts[client_ip] if now - t < 300]
        _login_failed_attempts[client_ip].append(now)


def check_login_rate_limit(client_ip: str) -> None:
    now = time.time()
    with _rate_limit_lock:
        attempts = [t for t in _login_failed_attempts.get(client_ip, []) if now - t < 300]
        if len(attempts) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please wait 5 minutes before trying again."
            )
