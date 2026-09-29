"""
admin_routes.py — FastAPI Endpoints for System Administration, Role & Doctor Verification Management.
Enforces strictly ADMIN role authorization on all endpoints.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import database
from ..auth import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Portal & Verification Management"])


class UpdateDoctorStatusRequest(BaseModel):
    status: str = Field(..., description="Target status: PENDING, UNDER_REVIEW, VERIFIED, REJECTED, RESUBMISSION_REQUIRED, SUSPENDED")
    notes: Optional[str] = Field(None, description="Admin verification notes / audit log details")
    reason: Optional[str] = Field(None, description="Detailed reason for rejection or resubmission request")


@router.get("/stats", status_code=status.HTTP_200_OK)
def get_admin_dashboard_stats(admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))):
    """Retrieve system overview metrics for Admin Dashboard."""
    stats = database.get_admin_stats()
    return {
        "admin_user": admin_user["email"],
        "stats": stats
    }


@router.get("/users", status_code=status.HTTP_200_OK)
def list_system_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))
):
    """List registered users with optional role and search filtering."""
    users = database.list_users(role=role, search=search)
    return {
        "count": len(users),
        "users": users
    }


@router.get("/doctors", status_code=status.HTTP_200_OK)
@router.get("/doctor-applications", status_code=status.HTTP_200_OK)
def list_doctor_applications(
    verification_status: Optional[str] = None,
    specialization: Optional[str] = None,
    search: Optional[str] = None,
    admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))
):
    """List doctor applications with status, specialization, and search filtering."""
    applications = database.list_doctor_applications(
        status_filter=verification_status,
        specialization_filter=specialization,
        search_query=search
    )
    return {
        "count": len(applications),
        "applications": applications,
        "doctors": applications
    }


@router.get("/doctor-applications/{doctor_id}", status_code=status.HTTP_200_OK)
def get_doctor_application_detail(
    doctor_id: str,
    admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))
):
    """Fetch complete detail snapshot of a doctor application including credentials & audit history."""
    detail = database.get_doctor_application_detail(doctor_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor application '{doctor_id}' not found.")
    return {
        "status": "SUCCESS",
        "application": detail
    }


@router.put("/doctors/{doctor_id}/status", status_code=status.HTTP_200_OK)
@router.post("/doctor-applications/{doctor_id}/transition", status_code=status.HTTP_200_OK)
def update_doctor_verification_status(
    doctor_id: str,
    req: UpdateDoctorStatusRequest,
    admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))
):
    """
    Execute admin state transition for doctor application (VERIFIED, REJECTED, RESUBMISSION_REQUIRED, SUSPENDED).
    Validates state machine and logs an explicit audit trail.
    """
    try:
        new_status_clean = req.status.strip().upper()
        existing_doc = database.get_doctor_application_detail(doctor_id)
        if existing_doc and existing_doc.get("verification_status") == new_status_clean:
            return {
                "message": f"Doctor verification status is already '{new_status_clean}'.",
                "verification_status": new_status_clean,
                "doctor": existing_doc,
                "application": existing_doc
            }

        reason_text = req.reason or req.notes
        updated_detail = database.update_doctor_verification_status(
            admin_user_id=admin_user["user_id"],
            doctor_id=doctor_id,
            new_status=new_status_clean,
            reason=reason_text
        )

        return {
            "message": f"Doctor verification status successfully updated to '{req.status.upper()}'.",
            "verification_status": updated_detail["verification_status"],
            "doctor": updated_detail,
            "application": updated_detail
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class UpdateSystemSettingsRequest(BaseModel):
    settings: Dict[str, str] = Field(..., description="Map of non-scientific operational settings")


@router.get("/system/health", status_code=status.HTTP_200_OK)
def get_system_operations_health(admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))):
    """
    Retrieve real-time operational system health, subsystem status, pipeline immutability metadata,
    and DB volume metrics for Admin System Operations Dashboard.
    """
    return database.get_detailed_system_health()


@router.get("/system/settings", status_code=status.HTTP_200_OK)
def get_system_settings(admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))):
    """Retrieve operational system settings."""
    return {"settings": database.get_system_settings()}

@router.post("/system/settings", status_code=status.HTTP_200_OK)
def update_system_settings(
    req: UpdateSystemSettingsRequest,
    admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))
):
    """
    Update non-scientific system configuration (maintenance banner, support text).
    Rejects any attempts to modify scientific ML model parameters.
    """
    try:
        updated = database.update_system_settings(admin_user["user_id"], req.settings)
        return {
            "status": "SUCCESS",
            "message": "Operational system settings updated successfully.",
            "settings": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/doctor-credentials/{document_id}/file", status_code=status.HTTP_200_OK)
def view_doctor_credential_file(
    document_id: str,
    admin_user: Dict[str, Any] = Depends(require_role(["ADMIN"]))
):
    """Serve credential document file directly for Admin Review Workspace."""
    from pathlib import Path
    from fastapi.responses import FileResponse

    cred = database.get_doctor_credential_by_id(document_id)
    if not cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Credential document '{document_id}' not found.")
    
    file_path = Path(cred.get("file_path", ""))
    if not file_path.exists():
        filename = cred.get("stored_filename", "")
        file_path = Path(__file__).parent.parent / "uploads" / "doctor_credentials" / filename

    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored document file missing on server disk.")

    return FileResponse(
        path=str(file_path),
        filename=cred.get("original_filename", "credential.pdf"),
        media_type=cred.get("mime_type", "application/pdf")
    )
