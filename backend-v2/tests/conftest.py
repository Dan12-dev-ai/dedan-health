"""
Shared pytest configuration and fixtures for the DEDAN Health backend suite.

Design constraints
------------------
1. The suite MUST run with no provider credentials and no network access.
   `AI_PROVIDER_MODE=offline` is exported *before* the application module is
   imported so `ProviderFactory` selects the deterministic `OfflineProvider`.
2. `backend-v2/` uses a flat module layout (not a package), so the backend root
   is prepended to `sys.path`. This keeps `pytest` runnable from any cwd.
"""

import os
import sys
from pathlib import Path

import pytest

# --- Credential-free, deterministic mode -------------------------------------
# Set before importing the application: the factory reads these at init time.
os.environ.setdefault("AI_PROVIDER_MODE", "offline")
# Suppress the interactive docs and stack-trace leakage in error payloads.
os.environ.setdefault("DEBUG", "false")
# Blank out credentials so a developer's real keys in the shell cannot cause a
# live provider call (which would also make the suite non-deterministic).
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# The app enforces an in-process per-IP rate limit (30 req/min by default).
# A full test run issues far more requests than that from a single client, so
# the limit is raised here. It is NOT disabled: tests still assert the limiter
# is present, and the production default is unchanged.
os.environ.setdefault("RATE_LIMIT_REQUESTS", "100000")


@pytest.fixture(scope="session")
def app_module():
    """Import the FastAPI application module once per session."""
    import main_clinical

    return main_clinical


@pytest.fixture(scope="session")
def client(app_module):
    """A synchronous ``TestClient`` bound to the ASGI app."""
    from fastapi.testclient import TestClient

    return TestClient(app_module.app)


@pytest.fixture
def valid_payload():
    """A minimal request body that satisfies ``AnalyzeRequest`` validation."""
    return {
        "patient_age": 30,
        "patient_sex": "female",
        "symptom_description": "persistent headache for two days",
        "consent": True,
    }
