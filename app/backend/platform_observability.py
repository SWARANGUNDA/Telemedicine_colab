"""
platform_observability.py — Centralized Structured JSON Logging, Observability & Error Middleware (Phase 3).

Provides:
1. Structured JSON Formatting (timestamp, request_id, session_id, patient_id_masked, stage, level)
2. Request ID Tracking Middleware (x-request-id)
3. Patient PII Masking (e.g. P000301 ➔ P***01)
4. Central Exception Handling Middleware
5. Latency & Performance Monitoring
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("telemed.observability")


def mask_patient_id(patient_id: Optional[str]) -> str:
    """Mask Patient PII ID for privacy compliance.

    Examples:
      'P000301' ➔ 'P***01'
      'AP-987654' ➔ 'A***54'
      'P_GUEST' ➔ 'P_GUEST'
    """
    if not patient_id or patient_id in ("P_GUEST", "UNKNOWN", "NONE"):
        return "P_GUEST"
    pid_str = str(patient_id).strip()
    if len(pid_str) <= 4:
        return pid_str[0] + "***"
    return pid_str[0] + "***" + pid_str[-2:]


class JSONLogFormatter(logging.Formatter):
    """Custom Log Formatter producing structured JSON log lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "N/A"),
            "session_id": getattr(record, "session_id", "N/A"),
            "patient_id_masked": mask_patient_id(getattr(record, "patient_id", None)),
            "pipeline_stage": getattr(record, "pipeline_stage", "GENERAL"),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for assigning Request IDs, tracking latencies, and logging API calls."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex[:12]}"
        session_token = request.headers.get("x-session-token") or "anonymous"

        # Store in request state
        request.state.request_id = request_id
        request.state.session_token = session_token

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            response.headers["x-request-id"] = request_id
            response.headers["x-process-time-ms"] = str(elapsed_ms)
            return response
        except HTTPException:
            raise
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            logger.error(
                "Unhandled API Exception on %s: %s",
                request.url.path, str(exc),
                extra={"request_id": request_id, "pipeline_stage": "API_MIDDLEWARE"},
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "status": "ERROR",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred. Please contact support with the provided Request ID.",
                    "request_id": request_id,
                    "process_time_ms": elapsed_ms
                },
                headers={"x-request-id": request_id, "x-process-time-ms": str(elapsed_ms)}
            )
