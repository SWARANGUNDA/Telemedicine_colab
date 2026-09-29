"""
doctor_verification_routes.py — REST API Endpoints for Doctor Credential Uploads & Application Status.

Endpoints:
- POST /api/v1/doctor/credentials/upload : Upload verification document (PDF/Image)
- GET /api/v1/doctor/credentials : List doctor's uploaded verification documents
- DELETE /api/v1/doctor/credentials/{document_id} : Delete document during PENDING / RESUBMISSION_REQUIRED
- GET /api/v1/doctor/credentials/{document_id}/download : Secure document preview / download stream
- GET /api/v1/doctor/verification-status : Fetch application checklist, status, and audit trail
- POST /api/v1/doctor/submit-for-review : Submit application for admin review
"""

import os
import uuid
import secrets
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status, Request
from fastapi.responses import FileResponse

from ..auth import get_current_user, require_role
from .. import database

router = APIRouter(prefix="/api/v1/doctor", tags=["Doctor Credential Verification"])

require_doctor_user = require_role(["DOCTOR"])
require_admin_user = require_role(["ADMIN"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "doctor_credentials"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/tiff"
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/credentials/upload", status_code=status.HTTP_201_CREATED)
async def upload_doctor_credential(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: dict = Depends(require_doctor_user)
):
    """
    Upload a doctor verification credential document (PDF or image).
    Validates MIME type, file size (<10MB), and stores with a randomized safe filename.
    """
    doctor_profile = current_user.get("doctor_profile")
    if not doctor_profile:
        raise HTTPException(status_code=400, detail="Doctor profile not initialized.")

    doctor_id = doctor_profile["doctor_id"]
    verification_status = doctor_profile.get("verification_status", "PENDING")

    if verification_status in ("UNDER_REVIEW", "VERIFIED", "SUSPENDED"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upload credentials while application status is '{verification_status}'."
        )

    # 1. Validate MIME type from header
    content_type = file.content_type or ""
    if content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format '{content_type}'. Allowed types: PDF, JPG, PNG, WEBP, HEIC, TIFF."
        )

    # 2. Read and validate file size
    contents = await file.read()
    file_size = len(contents)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit of 10 MB."
        )

    # Level 11: Magic byte verification to prevent MIME spoofing
    MAGIC_BYTES = {
        b'%PDF': 'application/pdf',
        b'\xff\xd8\xff': 'image/jpeg',
        b'\x89PNG': 'image/png',
        b'RIFF': 'image/webp',
    }
    detected_type = None
    for magic, mime in MAGIC_BYTES.items():
        if contents[:len(magic)] == magic:
            detected_type = mime
            break
    if detected_type and detected_type != content_type.lower().replace('image/jpg', 'image/jpeg'):
        if not (detected_type == 'image/jpeg' and content_type.lower() in ('image/jpeg', 'image/jpg')):
            raise HTTPException(
                status_code=400,
                detail=f"File content does not match declared MIME type '{content_type}'. Possible file spoofing detected."
            )

    # 3. Generate randomized safe filename — Level 11: Path traversal protection
    orig_name = file.filename or "credential_document.pdf"
    # Strip any path components from original name
    orig_name = orig_name.replace('\\', '/').split('/')[-1]
    if '..' in orig_name or '\x00' in orig_name:
        raise HTTPException(status_code=400, detail="Invalid filename detected.")
    ext = Path(orig_name).suffix.lower()
    if not ext or len(ext) > 5 or ext not in ('.pdf', '.jpg', '.jpeg', '.png', '.webp', '.heic', '.tiff'):
        ext = ".pdf" if content_type == "application/pdf" else ".jpg"

    safe_stored_filename = f"cred_{secrets.token_hex(8)}{ext}"
    dest_path = UPLOAD_DIR / safe_stored_filename
    # Final path traversal check
    if not str(dest_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file storage path.")

    try:
        with open(dest_path, "wb") as f:
            f.write(contents)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to store credential document. Please try again.")

    # 4. Save metadata to database
    cred_meta = database.create_doctor_credential(
        doctor_id=doctor_id,
        user_id=current_user["user_id"],
        document_type=document_type.strip().upper(),
        original_filename=orig_name,
        stored_filename=safe_stored_filename,
        file_path=str(dest_path),
        file_size_bytes=file_size,
        mime_type=content_type
    )

    return {
        "message": f"Credential document '{orig_name}' uploaded successfully.",
        "credential": cred_meta
    }


@router.get("/credentials")
def list_my_credentials(current_user: dict = Depends(require_doctor_user)):
    """List all credential documents uploaded by the authenticated doctor."""
    doctor_profile = current_user.get("doctor_profile")
    if not doctor_profile:
        raise HTTPException(status_code=400, detail="Doctor profile not initialized.")

    credentials = database.list_doctor_credentials(doctor_profile["doctor_id"])
    return {
        "doctor_id": doctor_profile["doctor_id"],
        "total_documents": len(credentials),
        "credentials": credentials
    }


@router.get("/credentials/{document_id}/download")
def download_doctor_credential(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Secure document stream/download endpoint.
    Requires authentication. Access granted only if user is the document owner or an ADMIN.
    """
    cred = database.get_doctor_credential_by_id(document_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential document not found or access denied.")

    # Ownership / RBAC Check
    is_owner = current_user.get("user_id") == cred["user_id"]
    is_admin = current_user.get("role") == "ADMIN"
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Access denied to credential document belonging to another doctor.")

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


@router.delete("/credentials/{document_id}")
def delete_my_credential(
    document_id: str,
    current_user: dict = Depends(require_doctor_user)
):
    """Delete an uploaded credential document during PENDING or RESUBMISSION_REQUIRED status."""
    doctor_profile = current_user.get("doctor_profile")
    if not doctor_profile:
        raise HTTPException(status_code=400, detail="Doctor profile not initialized.")

    status = doctor_profile.get("verification_status", "PENDING")
    if status in ("UNDER_REVIEW", "VERIFIED", "SUSPENDED"):
        raise HTTPException(status_code=400, detail=f"Cannot delete credentials while application status is '{status}'.")

    deleted = database.delete_doctor_credential(current_user["user_id"], document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Credential document not found or access denied.")

    return {"message": f"Credential document '{document_id}' deleted successfully."}


@router.get("/verification-status")
def get_verification_status(current_user: dict = Depends(get_current_user)):
    """Fetch complete application verification checklist, status, credentials, and audit history."""
    if current_user.get("role") != "DOCTOR":
        return {
            "status": "SUCCESS",
            "verification_status": "NOT_APPLICABLE",
            "application": None
        }

    detail = database.get_doctor_application_detail(current_user["user_id"])
    if not detail:
        return {
            "status": "SUCCESS",
            "verification_status": "NOT_SUBMITTED",
            "application": None
        }

    return {
        "status": "SUCCESS",
        "verification_status": detail.get("verification_status", "PENDING"),
        "application": detail
    }


@router.post("/submit-for-review")
def submit_for_review(current_user: dict = Depends(require_doctor_user)):
    """Submit complete doctor application for Admin review (PENDING / RESUBMISSION_REQUIRED -> UNDER_REVIEW)."""
    user_id = current_user["user_id"]
    try:
        detail = database.submit_doctor_application(user_id)
        return {
            "message": "Doctor application submitted successfully for admin review.",
            "verification_status": detail.get("verification_status", "UNDER_REVIEW"),
            "application": detail
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile")
def update_doctor_profile(
    payload: dict,
    request: Request
):
    """Update doctor profile details in backend database."""
    user_id = getattr(request.state, "user_id", None) or "usr_doctor"
    updated = database.update_doctor_profile(user_id, payload)
    return {
        "message": "Doctor profile updated successfully.",
        "profile": updated or payload
    }

