"""
config.py — Backend Configuration for Telemedicine Web Platform (Phase 6).

Server settings, file upload limits, CORS configurations, session timeout limits,
and paths to frozen AI engine artifacts.
"""

import os
from pathlib import Path
from typing import List

# Environment & Production Hardening Configuration
TELEMED_ENV: str = os.getenv("TELEMED_ENV", "development").lower()
IS_PRODUCTION: bool = TELEMED_ENV in ("production", "prod")

# Security & Admin Bootstrap Configuration
ALLOW_ADMIN_BOOTSTRAP: bool = os.getenv("TELEMED_ALLOW_ADMIN_BOOTSTRAP", "").lower() in ("true", "1", "yes")
ADMIN_BOOTSTRAP_KEY: str = os.getenv("TELEMED_ADMIN_BOOTSTRAP_KEY", "DEV_SAFE_DEFAULT_BOOTSTRAP_KEY")

# Development Demo & Seeded Credentials Configuration
DEMO_ADMIN_EMAIL: str = os.getenv("TELEMED_DEMO_ADMIN_EMAIL", "admin@telemed.ai")
DEMO_ADMIN_PASSWORD: str = os.getenv("TELEMED_DEMO_ADMIN_PASSWORD", "Password123!")

DEMO_DOCTOR_EMAIL: str = os.getenv("TELEMED_DEMO_DOCTOR_EMAIL", "doctor@telemed.ai")
DEMO_DOCTOR_PASSWORD: str = os.getenv("TELEMED_DEMO_DOCTOR_PASSWORD", "DocSec#2026!MedPortal")

DEMO_PATIENT_EMAIL: str = os.getenv("TELEMED_DEMO_PATIENT_EMAIL", "patient@telemed.ai")
DEMO_PATIENT_PASSWORD: str = os.getenv("TELEMED_DEMO_PATIENT_PASSWORD", "PatSec#2026!HealthApp")

# LLM Integration Configuration
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
def validate_production_config():
    """
    Validate mandatory secrets in Production mode.
    Fails safely with RuntimeError if TELEMED_ENV == 'production' and required secrets are missing.
    Development/test environments permit explicitly marked safe defaults.
    """
    if IS_PRODUCTION:
        missing_secrets = []
        if not os.getenv("TELEMED_JWT_SECRET"):
            missing_secrets.append("TELEMED_JWT_SECRET")
        if ALLOW_ADMIN_BOOTSTRAP and not os.getenv("TELEMED_ADMIN_BOOTSTRAP_KEY"):
            missing_secrets.append("TELEMED_ADMIN_BOOTSTRAP_KEY")
        if missing_secrets:
            raise RuntimeError(
                f"CRITICAL PRODUCTION SECURITY FAILURE: The following mandatory environment secret(s) "
                f"are missing: {', '.join(missing_secrets)}. Production deployments must not run with default fallback keys."
            )

# Execute startup check
validate_production_config()

# Base Paths
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
APP_DIR: Path = BASE_DIR / "app"
BACKEND_DIR: Path = APP_DIR / "backend"
FRONTEND_DIR: Path = APP_DIR / "frontend"
UPLOAD_DIR: Path = BASE_DIR / "runtime" / "temp"
REPORTS_DIR: Path = BASE_DIR / "runtime" / "generated"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Security & Upload Configuration
ALLOWED_EXTENSIONS: set = {
    ".pdf", ".doc", ".docx", ".txt", ".rtf", ".csv", ".tsv", ".json",
    ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tiff"
}
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
SESSION_EXPIRY_SECONDS: int = 3600  # 1 hour

# Disclaimer
RESEARCH_DISCLAIMER: str = (
    "NOTICE: This decision-support system is a research prototype trained on synthetic multimodal data. "
    "Predictions, risk scores, and XAI attributions do NOT constitute clinical diagnosis or medical prescription. "
    "Always consult a qualified healthcare professional."
)

# CORS Origins
raw_cors = os.getenv("CORS_ORIGINS", "")
custom_cors = [orig.strip() for orig in raw_cors.split(",") if orig.strip()] if raw_cors else []

CORS_ORIGINS: List[str] = list(set([
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
] + custom_cors))

# Session State Constants (Strict Order)
class SessionState:
    CREATED = "CREATED"
    EXTRACTED = "EXTRACTED"
    CONFIRMED = "CONFIRMED"
    ANALYZED = "ANALYZED"
    XAI_READY = "XAI_READY"
    REPORT_READY = "REPORT_READY"

# Valid State Transitions (Allows forward workflow and re-analysis/re-upload entry)
VALID_TRANSITIONS = {
    SessionState.CREATED: {SessionState.EXTRACTED},
    SessionState.EXTRACTED: {SessionState.CONFIRMED, SessionState.EXTRACTED, SessionState.ANALYZED},
    SessionState.CONFIRMED: {SessionState.ANALYZED, SessionState.EXTRACTED, SessionState.CONFIRMED},
    SessionState.ANALYZED: {SessionState.XAI_READY, SessionState.REPORT_READY, SessionState.EXTRACTED, SessionState.CONFIRMED, SessionState.ANALYZED},
    SessionState.XAI_READY: {SessionState.REPORT_READY, SessionState.EXTRACTED, SessionState.CONFIRMED, SessionState.ANALYZED},
    SessionState.REPORT_READY: {SessionState.REPORT_READY, SessionState.EXTRACTED, SessionState.CONFIRMED, SessionState.ANALYZED},
}
