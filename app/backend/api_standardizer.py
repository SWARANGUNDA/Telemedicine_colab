"""
api_standardizer.py — Unified API Response Schema Envelope & Formatting Helper (Phase 4).

Standardizes all backend HTTP response payloads into a consistent, enterprise-grade schema:
{
    "success": true,
    "message": "Operation completed successfully.",
    "data": { ... },
    "metadata": { ... },
    "warnings": [ ... ],
    "errors": [ ... ],
    "request_id": "req-xxx",
    "timestamp": "2026-08-02T00:00:00Z"
}
"""

import datetime
from typing import Any, Dict, List, Optional
from fastapi import Request
from fastapi.responses import JSONResponse


def standardize_response(
    data: Optional[Any] = None,
    message: str = "Operation completed successfully.",
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    status_code: int = 200,
    request: Optional[Request] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Build a standardized JSONResponse with clean envelope structure.

    Args:
        data: Main response payload object or dictionary.
        message: Human-readable status message.
        success: Boolean success indicator.
        metadata: Optional metadata (e.g. pagination, model versions, audit logs).
        warnings: Optional list of non-fatal warning messages.
        errors: Optional list of error messages.
        status_code: HTTP status code (default 200).
        request: Optional FastAPI request object to extract request_id from state.
        request_id: Explicit request_id string override.

    Returns:
        JSONResponse adhering strictly to standard envelope schema.
    """
    req_id = request_id
    if not req_id and request and hasattr(request.state, "request_id"):
        req_id = request.state.request_id
    req_id = req_id or "req-unknown"

    envelope = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
        "metadata": metadata if metadata is not None else {},
        "warnings": warnings or [],
        "errors": errors or [],
        "request_id": req_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    return JSONResponse(status_code=status_code, content=envelope)
