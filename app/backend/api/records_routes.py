"""
records_routes.py — REST API Endpoints for Persistent Health Records & History.

Endpoints:
- GET /api/v1/records : List all health records owned by authenticated patient
- GET /api/v1/records/{record_id} : Get single record detail snapshot (IDOR protected)
- GET /api/v1/records/{record_id}/export : Download structured JSON record summary
- DELETE /api/v1/records/{record_id} : Delete patient-owned health record (IDOR protected)
"""

import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..auth import require_clinical_access, get_current_user
from .. import database

router = APIRouter(prefix="/api/v1/records", tags=["Persistent Health Records"])


@router.get("")
@router.get("/")
def list_patient_records(current_user: dict = Depends(require_clinical_access)):
    """List all persistent health records accessible to authenticated patient.
    
    RBAC enforcement via require_clinical_access:
    - PATIENT: Allowed (returns owned records).
    - DOCTOR (VERIFIED): Allowed (returns assigned patient records).
    - DOCTOR (PENDING/SUSPENDED/REJECTED): Blocked with 403 Forbidden.
    - ADMIN: Blocked with 403 Forbidden.
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    
    try:
        records = database.list_patient_health_records(user_id)
    except Exception:
        records = []

    return {
        "user_id": user_id,
        "total_records": len(records),
        "records": records
    }


@router.get("/{record_id}")
def get_record_detail(
    record_id: str,
    current_user: dict = Depends(require_clinical_access)
):
    """Retrieve detailed snapshot of a single health record with strict server-side ownership verification."""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")

    record = database.get_patient_health_record(user_id, record_id)
    if not record:
        # Return generic 404 to prevent IDOR record ID enumeration/information leakage
        raise HTTPException(
            status_code=404,
            detail="Health record not found or access denied."
        )

    return {
        "status": "SUCCESS",
        "record": record
    }


@router.get("/{record_id}/export")
def export_record_summary(
    record_id: str,
    current_user: dict = Depends(require_clinical_access)
):
    """
    Download safe structured JSON export of a single analysis record summary.
    Includes metadata, verified input snapshot, prediction snapshot, XAI/report snapshots,
    provenance, versions, timestamp, and research disclaimer.
    Excludes auth tokens, password hashes, salts, internal paths, and secrets.
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")

    record = database.get_patient_health_record(user_id, record_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Health record not found or access denied."
        )

    export_payload = {
        "export_metadata": {
            "export_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "exported_by_user_id": user_id,
            "patient_name": current_user.get("full_name", "TeleMed Patient"),
            "disclaimer": "Research Prototype System trained on synthetic multimodal data. This exported document contains model-estimated screening indicators and does NOT constitute a clinical diagnosis or medical prescription."
        },
        "health_record": {
            "record_id": record["record_id"],
            "source_session_id": record["source_session_id"],
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
            "pipeline_version": record["pipeline_version"],
            "schema_version": record["schema_version"],
            "effective_pathway": record["effective_pathway"],
            "data_quality_score": record["data_quality_score"],
            "active_modalities": record["active_modalities"],
            "status": record["status"]
        },
        "input_features_snapshot": record["confirmed_features"],
        "prediction_snapshot": record["prediction_snapshot"],
        "xai_snapshot": record["xai_snapshot"] if record["xai_snapshot"] else "NOT GENERATED",
        "report_snapshot": record["report_snapshot"] if record["report_snapshot"] else "NOT GENERATED"
    }

    return JSONResponse(
        content=export_payload,
        headers={"Content-Disposition": f'attachment; filename="TeleMed_HealthRecord_{record_id}.json"'}
    )


@router.delete("/{record_id}")
def delete_patient_record(
    record_id: str,
    current_user: dict = Depends(require_clinical_access)
):
    """
    Delete a health record owned by the requesting patient.
    Requires server-side user_id ownership check. Returns generic 404 if not found/unauthorized.
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")

    deleted = database.delete_patient_health_record(user_id, record_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Health record not found or access denied."
        )

    return {
        "status": "SUCCESS",
        "message": f"Health record '{record_id}' deleted successfully.",
        "record_id": record_id
    }
