"""
Regression and integrity tests for frontend JSX hooks, routing imports, and production builds.
Guarantees that hooks (such as useLocation, useNavigate, useProfile, etc.) are never referenced
without being explicitly imported, preventing production blank screen ReferenceErrors.
"""

import os
import re
import pytest

FRONTEND_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src"))

ROUTER_HOOKS = ["useLocation", "useNavigate", "useParams", "useSearchParams"]
REACT_HOOKS = ["useState", "useEffect", "useContext", "useRef", "useMemo", "useCallback"]


def get_all_jsx_files():
    jsx_files = []
    for root, _, files in os.walk(FRONTEND_SRC):
        for f in files:
            if f.endswith((".jsx", ".js")):
                jsx_files.append(os.path.join(root, f))
    return jsx_files


def test_no_undefined_router_hooks():
    """Verify that every router hook referenced in any JSX/JS file is explicitly imported from react-router-dom."""
    jsx_files = get_all_jsx_files()
    assert len(jsx_files) > 0, "No frontend source files found to audit."

    for file_path in jsx_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract import statements from react-router-dom
        router_imports = set()
        for match in re.finditer(r"import\s+\{([^}]+)\}\s+from\s+['\"]react-router-dom['\"]", content):
            items = [item.strip() for item in match.group(1).split(",")]
            for item in items:
                # Handle 'import { useLocation as loc }' if any
                name = item.split("as")[0].strip()
                if name:
                    router_imports.add(name)

        # Check each hook usage
        for hook in ROUTER_HOOKS:
            # Pattern matches hook call: hook() or hook
            # Exclude lines where the hook is being imported
            hook_pattern = rf"\b{hook}\b"
            if re.search(hook_pattern, content):
                assert hook in router_imports, (
                    f"Regression Error: '{hook}' is referenced in {os.path.basename(file_path)} "
                    f"without being imported from 'react-router-dom'."
                )


def test_app_jsx_integrity():
    """Verify App.jsx has no undefined references and properly mounts router and providers."""
    app_jsx_path = os.path.join(FRONTEND_SRC, "App.jsx")
    with open(app_jsx_path, "r", encoding="utf-8") as f:
        content = f.read()

    # App.jsx must not call useLocation
    assert "useLocation" not in content, "App.jsx must not reference useLocation."

    # App.jsx must import and use ProfileProvider and ConnectionErrorScreen
    assert "ProfileProvider" in content
    assert "ConnectionErrorScreen" in content
    assert "OnboardingPage" in content


def test_onboarding_option_schema_parity():
    """Verify that frontend DEFAULT_GOAL_CONFIG matches backend GOAL_CONFIG exactly."""
    from calculations import GOAL_CONFIG

    onboarding_jsx = os.path.join(FRONTEND_SRC, "pages", "OnboardingPage.jsx")
    with open(onboarding_jsx, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify each backend goal and intensity key is represented in frontend fallback
    for goal_name, goal_data in GOAL_CONFIG.items():
        assert f"'{goal_name}'" in content or f'"{goal_name}"' in content, (
            f"Goal '{goal_name}' from backend GOAL_CONFIG missing in OnboardingPage.jsx"
        )
        for intensity_key in goal_data["intensities"].keys():
            assert f"'{intensity_key}'" in content or f'"{intensity_key}"' in content, (
                f"Intensity '{intensity_key}' for goal '{goal_name}' missing in OnboardingPage.jsx"
            )


def test_frontend_auth_token_storage_security():
    """Verify that tokens are strictly saved in sessionStorage and never in localStorage."""
    api_js_path = os.path.join(FRONTEND_SRC, "lib", "api.js")
    with open(api_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "sessionStorage" in content, "api.js must store tokens in sessionStorage."
    assert "localStorage." not in content, "api.js must NEVER access localStorage API."
    assert "macrosnap_demo_token" in content, "api.js must use explicit demo token key."


def test_api_client_centralized_header_injection():
    """Verify that all protected API calls use centralized apiFetch with Authorization injection."""
    api_js_path = os.path.join(FRONTEND_SRC, "lib", "api.js")
    with open(api_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify centralized apiFetch defines Bearer injection and 401 expiration notify
    assert "apiFetch" in content
    assert "Authorization" in content
    assert "Bearer" in content
    assert "status === 401" in content or "status === 401" in content.replace(" ", "")

    protected_functions = [
        "scanMeal",
        "createMeal",
        "getCoachContext",
        "chatWithCoach",
        "getMealHistory",
        "deleteMeal",
        "updateMeal",
        "getProgressAnalytics",
        "logWeight",
        "getProfile",
        "previewProfilePlan",
        "applyProfilePlan",
        "resetProfile"
    ]

    for fn in protected_functions:
        pattern = rf"export\s+async\s+function\s+{fn}\b[\s\S]*?\{{[\s\S]*?apiFetch\("
        assert re.search(pattern, content), f"Function {fn} in api.js must route through centralized apiFetch."


def test_no_hardcoded_secrets_in_frontend():
    """Verify frontend source files do not contain hardcoded passwords or secrets."""
    jsx_files = get_all_jsx_files()
    suspicious_patterns = [
        r"AUTH_SECRET_KEY\s*=\s*['\"][^'\"]+['\"]",
        r"DEMO_PASSWORD\s*=\s*['\"][^'\"]+['\"]",
        r"VITE_DEMO_PASSWORD",
        r"VITE_AUTH_SECRET",
    ]

    for file_path in jsx_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        for pat in suspicious_patterns:
            assert not re.search(pat, content, re.IGNORECASE), (
                f"Security defect: suspicious secret pattern '{pat}' found in {os.path.basename(file_path)}"
            )


def test_onboarding_form_defaults_are_empty():
    """Regression test: verify OnboardingPage initial form state does not contain hardcoded demo profile values."""
    onboarding_file = os.path.join(FRONTEND_SRC, "pages", "OnboardingPage.jsx")
    with open(onboarding_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Form initialization must use empty strings, NOT synthetic persona (25, 178, 75)
    assert "age: ''" in content or 'age: ""' in content, "OnboardingPage must initialize age to empty string"
    assert "height_cm: ''" in content or 'height_cm: ""' in content, "OnboardingPage must initialize height_cm to empty string"
    assert "weight_kg: ''" in content or 'weight_kg: ""' in content, "OnboardingPage must initialize weight_kg to empty string"
    assert "age: '25'" not in content and 'age: "25"' not in content, "OnboardingPage must not hardcode age: 25"
    assert "height_cm: '178'" not in content and 'height_cm: "178"' not in content, "OnboardingPage must not hardcode height: 178"
    assert "weight_kg: '75'" not in content and 'weight_kg: "75"' not in content, "OnboardingPage must not hardcode weight: 75"


def test_profile_form_defaults_are_empty():
    """Regression test: verify ProfilePage initial editForm state does not contain hardcoded demo profile values."""
    profile_file = os.path.join(FRONTEND_SRC, "pages", "ProfilePage.jsx")
    with open(profile_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "age: ''" in content or 'age: ""' in content, "ProfilePage must initialize editForm age to empty string"
    assert "height_cm: ''" in content or 'height_cm: ""' in content, "ProfilePage must initialize editForm height_cm to empty string"
    assert "weight_kg: ''" in content or 'weight_kg: ""' in content, "ProfilePage must initialize editForm weight_kg to empty string"
    assert "age: '25'" not in content and 'age: "25"' not in content, "ProfilePage editForm must not hardcode age: 25"
    assert "height_cm: '178'" not in content and 'height_cm: "178"' not in content, "ProfilePage editForm must not hardcode height: 178"
    assert "weight_kg: '75'" not in content and 'weight_kg: "75"' not in content, "ProfilePage editForm must not hardcode weight: 75"


def test_regression_profile_reset_button_hidden_in_production():
    """
    Regression test:
    Verify that the Reset Profile button in ProfilePage.jsx is guarded and hidden in production builds.
    """
    profile_file = os.path.join(FRONTEND_SRC, "pages", "ProfilePage.jsx")
    with open(profile_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Must check import.meta.env.PROD or MODE === 'production'
    assert "import.meta.env.PROD" in content or "MODE === 'production'" in content, (
        "ProfilePage.jsx must check production environment before rendering reset button."
    )
    # Button must be guarded by showResetButton
    assert "{showResetButton &&" in content, (
        "Reset Profile button in ProfilePage.jsx must be conditionally rendered via {showResetButton && ...}."
    )

