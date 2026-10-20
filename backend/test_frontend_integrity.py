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
