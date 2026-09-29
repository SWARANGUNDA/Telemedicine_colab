"""
intake_routes.py — FastAPI Endpoints for Document Upload, IMDIE Extraction, and Feature Confirmation.
Dynamic Data Quality Re-evaluation & Data Quality Score API Mapping Fix.
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from pydantic import BaseModel

from ..config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, SessionState, UPLOAD_DIR
from ..session_manager import SessionManager, PatientSession
from ..services.intake_service import IntakeService
from ..auth import require_clinical_access
from services.multimodal_intake.quality_scorer import calculate_data_quality_scores
from services.multimodal_intake.validator import validate_feature_dict

router = APIRouter(prefix="/api/v1/intake", tags=["Intake & Extraction"])

intake_service = IntakeService()


class FeatureConfirmRequest(BaseModel):
    session_id: str
    confirmed_features: Dict[str, Any]


def format_quality_scores(raw_scores: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure data quality scores dictionary has standardized keys and score breakdown."""
    ov = raw_scores.get("overall_score", raw_scores.get("overall_quality_score", 0.0))
    if ov <= 1.0 and ov > 0:
        ov = round(ov * 100.0, 1)

    return {
        "overall_quality_score": ov,
        "overall_score": ov,
        "clinical_score": raw_scores.get("clinical_score", 0.0),
        "wearable_score": raw_scores.get("wearable_score", 0.0),
        "gut_score": raw_scores.get("gut_score", 0.0),
        "score_breakdown": raw_scores.get("score_breakdown", {}),
    }


@router.post("/upload")
async def upload_reports(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
    session_mgr: SessionManager = Depends(lambda: router.session_mgr),
    current_user: Dict[str, Any] = Depends(require_clinical_access)
):
    """Upload report files (PDF, TXT, CSV, JSON) and execute IMDIE extraction."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    session = None
    if session_id:
        try:
            session = session_mgr.get_session(session_id)
        except KeyError:
            session = None

    if not session:
        session = session_mgr.create_session(user_id=current_user.get("user_id"))

    saved_file_paths = []

    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            if not session_id:
                session_mgr.delete_session(session.session_id)
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            if not session_id:
                session_mgr.delete_session(session.session_id)
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' exceeds maximum allowed size of 10MB."
            )

        safe_filename = f"{uuid.uuid4().hex}{ext}"
        saved_path = UPLOAD_DIR / safe_filename
        with open(saved_path, "wb") as f:
            f.write(content)
        saved_file_paths.append(saved_path)

    session.uploaded_files.extend(saved_file_paths)

    try:
        imdie_result = intake_service.process_uploaded_reports(session.uploaded_files)
        session.imdie_output = imdie_result

        raw_quality = imdie_result.get("data_quality_scores", {})
        formatted_quality = format_quality_scores(raw_quality)
        session.quality_scores = formatted_quality

        profile = imdie_result.get("patient_profile", {})
        extracted_features = {
            "clinical": profile.get("clinical_features", {}),
            "wearable": profile.get("wearable_features", {}),
            "gut": profile.get("gut_features", {}),
        }

        session.transition_to(SessionState.EXTRACTED)

        return {
            "session_id": session.session_id,
            "status": "EXTRACTED",
            "extracted_features": extracted_features,
            "patient_profile": profile,
            "data_quality_scores": formatted_quality,
            "verify_flags": imdie_result.get("verify_flags", {}),
            "conflict_map": imdie_result.get("conflict_map", {}),
            "different_patient_warning": imdie_result.get("different_patient_warning"),
            "processed_reports_metadata": imdie_result.get("processed_reports_metadata", []),
            "provenance": imdie_result.get("provenance", {}),
            "missing_feature_assistant": imdie_result.get("missing_feature_assistant", {}),
            "expert_availability": imdie_result.get("expert_availability", {}),
            "adaptive_prediction_strategy": imdie_result.get("adaptive_prediction_strategy", {}),
        }
    except Exception as e:
        session_mgr.delete_session(session.session_id)
        raise HTTPException(status_code=500, detail=f"IMDIE extraction failure: {str(e)}")


@router.post("/confirm")
def confirm_features(
    req: FeatureConfirmRequest,
    session_mgr: SessionManager = Depends(lambda: router.session_mgr),
    current_user: Dict[str, Any] = Depends(require_clinical_access)
):
    """Mandatory Step: Confirm/Edit extracted feature values before ML inference.
    Validates manual entries and recalculates Data Quality Score dynamically based on confirmed features.
    """
    try:
        session = session_mgr.get_session(req.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if current_user.get("role") == "PATIENT" and session.user_id and session.user_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=403,
            detail="Patient is not authorized to access or modify a clinical session belonging to another user."
        )

    allowed_states = [
        SessionState.EXTRACTED,
        SessionState.CONFIRMED,
        SessionState.ANALYZED,
        SessionState.XAI_READY,
        SessionState.REPORT_READY
    ]
    if session.state not in allowed_states:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm features in state '{session.state}'."
        )

    clinical_feat = req.confirmed_features.get("clinical") or {}
    wearable_feat = req.confirmed_features.get("wearable") or {}
    gut_feat = req.confirmed_features.get("gut") or {}

    # Validate confirmed feature entries
    all_validation_errors = []
    clean_clinical, err_c, _, vf_c = validate_feature_dict(clinical_feat)
    all_validation_errors.extend(err_c)
    clean_wearable, err_w, _, vf_w = validate_feature_dict(wearable_feat)
    all_validation_errors.extend(err_w)
    clean_gut, err_g, _, vf_g = validate_feature_dict(gut_feat)
    all_validation_errors.extend(err_g)

    if all_validation_errors:
        raise HTTPException(
            status_code=400,
            detail=f"Feature validation failed for confirmed values: {'; '.join(all_validation_errors)}"
        )

    validated_confirmed = {
        "clinical": clean_clinical if clinical_feat else None,
        "wearable": clean_wearable if wearable_feat else None,
        "gut": clean_gut if gut_feat else None,
    }

    session.confirmed_features = validated_confirmed

    # Recalculate Data Quality Score dynamically
    recalculated_raw = calculate_data_quality_scores(clean_clinical, clean_wearable, clean_gut)
    updated_quality = format_quality_scores(recalculated_raw)
    session.quality_scores = updated_quality

    # Detect active modalities
    active = []
    missing = []
    for mod_key in ["clinical", "wearable", "gut"]:
        feat_dict = validated_confirmed.get(mod_key)
        if feat_dict and any(v is not None for k, v in feat_dict.items() if k != "Patient_ID"):
            active.append(mod_key)
        else:
            missing.append(mod_key)

    if not active:
        raise HTTPException(
            status_code=400,
            detail="At least one modality (Clinical, Wearable, or Gut) must contain confirmed feature data."
        )

    session.active_modalities = active
    session.missing_modalities = missing

    session.transition_to(SessionState.CONFIRMED)

    return {
        "session_id": session.session_id,
        "status": "CONFIRMED",
        "active_modalities": active,
        "missing_modalities": missing,
        "confirmed_features": session.confirmed_features,
        "data_quality_scores": updated_quality,
        "message": "Extracted feature review and confirmation complete. Ready for ML analysis.",
    }
