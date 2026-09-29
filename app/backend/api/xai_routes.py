"""
xai_routes.py — FastAPI Endpoints for SHAP Attributions & Decision Weights.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..config import SessionState
from ..session_manager import SessionManager
from ..services.xai_service import XAIService
from ..auth import require_clinical_access
from .. import database

router = APIRouter(prefix="/api/v1/xai", tags=["Explainable AI"])
xai_service = XAIService()

class XAIRequest(BaseModel):
    session_id: str
    top_k_drivers: int = 5


@router.post("/explain")
def generate_xai_explanation(
    req: XAIRequest,
    session_mgr: SessionManager = Depends(lambda: router.session_mgr),
    current_user: dict = Depends(require_clinical_access)
):
    """Retrieve rank-ordered SHAP drivers and fusion decision weights."""
    try:
        session = session_mgr.get_session(req.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if current_user.get("role") == "PATIENT" and session.user_id and session.user_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=403,
            detail="Patient is not authorized to access or modify a clinical session belonging to another user."
        )

    if session.state not in [SessionState.ANALYZED, SessionState.XAI_READY, SessionState.REPORT_READY]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate XAI in state '{session.state}'. ML prediction must be completed first."
        )

    try:
        patient_features = {
            "clinical": session.confirmed_features.get("clinical") if session.confirmed_features else None,
            "wearable": session.confirmed_features.get("wearable") if session.confirmed_features else None,
            "gut": session.confirmed_features.get("gut") if session.confirmed_features else None,
        }

        xai_payload = xai_service.generate_xai_explanations(patient_features, top_k_drivers=req.top_k_drivers)
        session.xai_output = xai_payload

        if session.state == SessionState.ANALYZED:
            session.transition_to(SessionState.XAI_READY)

        # Attach snapshot to database health record if available
        database.attach_xai_snapshot_to_record(session.session_id, xai_payload)

        return {
            "session_id": session.session_id,
            "status": session.state,
            "xai_payload": xai_payload,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XAI Engine generation failure: {str(e)}")
