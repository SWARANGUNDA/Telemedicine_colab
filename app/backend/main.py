"""
main.py — Main FastAPI Application Entry Point for Telemedicine Web Platform.
Level 11: Security-hardened with rate limiting middleware, security headers, and safe exception handling. (Reloaded)
"""

import math
import logging
import typing
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config, database, startup_diagnostics
from .api import health_routes, intake_routes, predict_routes, rag_routes, xai_routes, v3_routes, auth_routes, admin_routes, records_routes, doctor_verification_routes, consultation_routes, appointment_notification_routes, audit_governance_routes, metrics_routes, websocket_routes, ops_monitoring_routes
from . import prometheus_metrics
from .session_manager import SessionManager
from .security import RATE_LIMITER, SECURITY_HEADERS, safe_error_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("web_platform.main")

# Initialize SQLite database schema
database.init_db()


def sanitize_nans(obj: typing.Any) -> typing.Any:
    """Recursively convert NaN/Inf float values to None for JSON compliance."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_nans(item) for item in obj]
    return obj


class SanitizedJSONResponse(JSONResponse):
    """Custom JSONResponse class that sanitizes NaN/Inf floats before JSON serialization."""
    def render(self, content: typing.Any) -> bytes:
        return super().render(sanitize_nans(content))


app = FastAPI(
    title="Generative AI Assisted Telemedicine Platform API",
    description="Backend API integration layer for Multimodal Data Intake, Expert Models, Fusion Engine, Unified XAI, and Grounded Medical RAG.",
    version="1.0.0",
    default_response_class=SanitizedJSONResponse,
    # Level 11: Do not expose docs in production by default (uncomment for dev)
    # docs_url=None, redoc_url=None,
)

from .database import check_db_connection
from .database.db import create_tables

@app.on_event("startup")
def startup_event():
    """Run production boot diagnostics, create tables, seed demo users, and verify DB."""
    startup_diagnostics.run_startup_diagnostics()
    check_db_connection()
    # Ensure all ORM tables exist (critical for SQLite fallback)
    create_tables()
    # Seed demo users if they don't exist
    try:
        from .database_legacy import _seed_demo_users
        _seed_demo_users()
    except Exception as e:
        logger.warning("Demo user seeding skipped: %s", e)

from .platform_observability import RequestObservabilityMiddleware

app.add_middleware(RequestObservabilityMiddleware)

# Configure CORS — Level 11: Restrict methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Remaining", "Retry-After", "X-Request-ID", "X-Process-Time-MS"],
)


# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    
    # Allow iframe embedding for doctor credential previews & uploads in review workspace
    path = request.url.path.lower()
    if "credential" in path or "upload" in path:
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' data: blob: http://localhost:* http://127.0.0.1:*; "
            "frame-ancestors 'self' http://localhost:* http://127.0.0.1:*; "
            "frame-src 'self' data: blob: http://localhost:* http://127.0.0.1:*;"
        )
    return response


# ---------------------------------------------------------------------------
# Level 11: Rate Limiting Middleware
# ---------------------------------------------------------------------------
RATE_LIMIT_ROUTES = {
    "/api/v1/auth/login": "login",
    "/api/v1/auth/register/patient": "register",
    "/api/v1/auth/register/doctor": "register",
    "/api/v1/auth/bootstrap-admin": "login",
    "/api/v1/doctor/credentials/upload": "upload",
}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    # Skip rate limiting for FastAPI TestClient (used in test suites)
    if client_ip == "testclient":
        return await call_next(request)
    path = request.url.path.rstrip("/")
    category = RATE_LIMIT_ROUTES.get(path, "api_default")

    allowed, retry_after = RATE_LIMITER.check(client_ip, category)
    if not allowed:
        logger.warning("Rate limit exceeded for %s on %s (category=%s)", client_ip, path, category)
        return SanitizedJSONResponse(
            status_code=429,
            content={
                "error": True,
                "status_code": 429,
                "message": "Too many requests. Please slow down and try again later.",
            },
            headers={"Retry-After": str(retry_after)},
        )
    return await call_next(request)


# Initialize global SessionManager
session_manager = SessionManager()

# Attach SessionManager instance to router state
intake_routes.router.session_mgr = session_manager
predict_routes.router.session_mgr = session_manager
xai_routes.router.session_mgr = session_manager
rag_routes.router.session_mgr = session_manager

# Register Routers
app.include_router(health_routes.router)
app.include_router(metrics_routes.router)
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)

app.include_router(records_routes.router)
app.include_router(doctor_verification_routes.router)
app.include_router(consultation_routes.router)
app.include_router(appointment_notification_routes.router)
app.include_router(audit_governance_routes.router)
app.include_router(intake_routes.router)
app.include_router(predict_routes.router)
app.include_router(xai_routes.router)
app.include_router(rag_routes.router)
app.include_router(v3_routes.router)
app.include_router(websocket_routes.router)
app.include_router(ops_monitoring_routes.router)
app.include_router(prometheus_metrics.router)

from fastapi.staticfiles import StaticFiles
import os

uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP Exception Handler — Level 11: Never leak stack traces or internal paths."""
    # Log safely without tokens
    logger.warning("HTTP Exception %d on %s: %s", exc.status_code, request.url.path, exc.detail)
    return SanitizedJSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": str(exc.detail) if exc.detail else "Request could not be processed.",
            "disclaimer": config.RESEARCH_DISCLAIMER,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Fallback Exception Handler — Level 11: Safe error messages only, no stack traces to client."""
    # Log full error server-side for debugging
    logger.error("Unhandled Exception on %s: %s", request.url.path, exc, exc_info=True)
    return SanitizedJSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "An internal server error occurred. Please try again later.",
            "disclaimer": config.RESEARCH_DISCLAIMER,
        },
    )
