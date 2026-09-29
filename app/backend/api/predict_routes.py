"""
predict_routes.py — FastAPI Endpoints for Multimodal ML & Fusion Prediction.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..config import SessionState
from ..session_manager import SessionManager
from ..services.inference_service import InferenceService
from ..auth import require_clinical_access
from .. import database

router = APIRouter(prefix="/api/v1/predict", tags=["Prediction & Fusion"])
inference_service = InferenceService()

class AnalyzeRequest(BaseModel):
    session_id: str


@router.post("/analyze")
def run_multimodal_analysis(
    req: AnalyzeRequest,
    session_mgr: SessionManager = Depends(lambda: router.session_mgr),
    current_user: dict = Depends(require_clinical_access)
):
    """
    Run multimodal ML fusion engine inference for a confirmed patient session.
    """
    try:
        session = session_mgr.get_session(req.session_id)
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{req.session_id}' not found or expired. Please upload reports to start a new session."
        )

    # Ownership check
    if current_user["role"] == "PATIENT" and session.user_id and session.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Patient is not authorized to access or modify a clinical session belonging to another user."
        )

    if session.state not in (SessionState.CONFIRMED, SessionState.ANALYZED, SessionState.XAI_READY, SessionState.REPORT_READY):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run ML analysis in session state '{session.state}'. Features must be CONFIRMED first."
        )

    try:
        # Prepare input dict for FusionInferenceEngine
        patient_features = {
            "clinical": session.confirmed_features.get("clinical") if "clinical" in session.active_modalities else None,
            "wearable": session.confirmed_features.get("wearable") if "wearable" in session.active_modalities else None,
            "gut": session.confirmed_features.get("gut") if "gut" in session.active_modalities else None,
        }

        result = inference_service.run_prediction(patient_features)
        session.prediction_output = result

        # Transition state to ANALYZED
        session.transition_to(SessionState.ANALYZED)

        record_id = None
        user_id = session.user_id or current_user.get("user_id")
        if user_id:
            dq_val = session.quality_scores.get("overall_quality_score") if session.quality_scores else None
            rec = database.upsert_health_record(
                user_id=user_id,
                source_session_id=session.session_id,
                effective_pathway=result["pathway_used"],
                data_quality_score=dq_val,
                active_modalities=session.active_modalities,
                confirmed_features=session.confirmed_features,
                prediction_snapshot=result,
                status="ANALYZED"
            )
            record_id = rec.get("record_id")

        return {
            "session_id": session.session_id,
            "record_id": record_id,
            "status": "ANALYZED",
            "pathway_used": result["pathway_used"],
            "active_modalities": session.active_modalities,
            "missing_modalities": session.missing_modalities,
            "data_quality_scores": session.quality_scores,
            "disease_outcomes": result["disease_outcomes"],
            "disclaimer": "Research Prototype System trained on synthetic multimodal data. Predictions do NOT constitute clinical diagnosis.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multimodal Fusion inference failure: {str(e)}")
