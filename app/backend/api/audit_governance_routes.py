"""
audit_governance_routes.py — Level 12 Audit, Accountability & Data Governance Endpoints.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
import json
import csv
import io

from ..auth import get_current_user, require_role
from .. import database

router = APIRouter(prefix="/api/v1", tags=["Audit & Data Governance"])

require_patient_user = require_role(["PATIENT"])
require_admin_user = require_role(["ADMIN"])


class DeleteAccountRequest(BaseModel):
    reason: Optional[str] = Field("", max_length=500, description="Optional reason for account deletion")


# ------------------------------------------------------------------
# Patient Data Governance & Access History Endpoints
# ------------------------------------------------------------------

@router.get("/patient/access-history", status_code=status.HTTP_200_OK)
def get_patient_data_access_history(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Data Access History Endpoint.
    Shows data access audit events for the authenticated user across PATIENT, DOCTOR, or ADMIN roles.
    """
    history = database.get_patient_access_history(current_user["user_id"])
    return {
        "user_id": current_user["user_id"],
        "total_records": len(history),
        "access_history": history
    }


@router.get("/patient/governance/data-export", status_code=status.HTTP_200_OK)
def export_my_account_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Data Export Endpoint.
    Returns JSON export of authenticated user's profile, health records, access history, and consultations.
    Excludes passwords, salts, tokens, and system secrets.
    """
    try:
        data = database.export_user_account_data(current_user["user_id"])
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/patient/governance/delete-request", status_code=status.HTTP_200_OK)
def submit_account_deletion_request(
    req: DeleteAccountRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Account Deletion Request Endpoint.
    Stores explicit deletion request without corrupting clinical audit trails.
    """
    res = database.request_account_deletion(
        user_id=current_user["user_id"],
        role=current_user["role"],
        reason=req.reason or ""
    )
    return res


# ------------------------------------------------------------------
# Admin Audit Console & Governance Endpoints
# ------------------------------------------------------------------

@router.get("/admin/audit", status_code=status.HTTP_200_OK)
@router.get("/admin/audit/logs", status_code=status.HTTP_200_OK)
def get_admin_audit_logs(
    role: Optional[str] = Query(None, description="Filter by actor role (PATIENT, DOCTOR, ADMIN)"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (SUCCESS, FAILED)"),
    search: Optional[str] = Query(None, description="Search term across actor/action/resource"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_user: Dict[str, Any] = Depends(require_admin_user)
):
    """
    Admin Audit Console Endpoint.
    Provides searchable, paginated audit records with outcome and role filtering.
    """
    res = database.query_admin_audit_logs(
        role=role, action=action, outcome=outcome, search=search, page=page, page_size=page_size
    )
    return res


@router.get("/admin/audit/integrity", status_code=status.HTTP_200_OK)
def verify_audit_ledger_integrity(admin_user: Dict[str, Any] = Depends(require_admin_user)):
    """
    Cryptographic Audit Ledger Verification Endpoint.
    Verifies SHA-256 append-only hash chaining across all stored audit records.
    Returns status: VALID or INVALID.
    """
    res = database.verify_audit_log_integrity()
    database.log_audit_event(
        actor_user_id=admin_user["user_id"],
        role="ADMIN",
        action="AUDIT_INTEGRITY_CHECK_PERFORMED",
        resource_type="SYSTEM_AUDIT_LEDGER",
        outcome=res["status"]
    )
    return res


@router.get("/admin/audit/export", status_code=status.HTTP_200_OK)
def export_admin_audit_logs(
    format: str = Query("json", description="Export format: 'json' or 'csv'"),
    role: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    admin_user: Dict[str, Any] = Depends(require_admin_user)
):
    """
    Export Admin Audit Logs as downloadable JSON or CSV format.
    Excludes internal secrets and passwords.
    """
    logs_data = database.query_admin_audit_logs(role=role, action=action, outcome=outcome, page=1, page_size=5000)
    items = logs_data["items"]

    database.log_audit_event(
        actor_user_id=admin_user["user_id"],
        role="ADMIN",
        action="AUDIT_LOGS_EXPORTED",
        resource_type="SYSTEM_AUDIT_LEDGER",
        context={"format": format, "count": len(items)}
    )

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["event_id", "actor_user_id", "role", "action", "resource_type", "resource_id", "outcome", "created_at", "event_hash"])
        for item in items:
            writer.writerow([
                item["event_id"], item["actor_user_id"], item["role"], item["action"],
                item["resource_type"], item["resource_id"], item["outcome"], item["created_at"], item["event_hash"]
            ])
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=telemed_audit_logs.csv"})

    return {
        "export_format": "json",
        "total_records": len(items),
        "audit_logs": items
    }
