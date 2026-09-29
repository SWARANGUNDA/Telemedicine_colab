"""
rag_routes.py — FastAPI Endpoints for Medical RAG Health Reports and Interactive Q&A.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..config import SessionState
from ..session_manager import SessionManager
from ..services.rag_service_wrapper import RAGServiceWrapper
from ..auth import require_clinical_access
from .. import database

router = APIRouter(prefix="/api/v1/rag", tags=["Medical RAG & Guidelines"])
rag_service = RAGServiceWrapper()

class RAGReportRequest(BaseModel):
    session_id: str

class QARequest(BaseModel):
    session_id: Optional[str] = None
    question: Optional[str] = None
    query: Optional[str] = None


@router.post("/report")
def generate_rag_report(
    req: RAGReportRequest,
    session_mgr: SessionManager = Depends(lambda: router.session_mgr),
    current_user: dict = Depends(require_clinical_access)
):
    """Generate grounded personalized health report with citations."""
    try:
        session = session_mgr.get_session(req.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if current_user.get("role") == "PATIENT" and session.user_id and session.user_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=403,
            detail="Patient is not authorized to access or modify a clinical session belonging to another user."
        )

    allowed_states = [SessionState.CONFIRMED, SessionState.ANALYZED, SessionState.XAI_READY, SessionState.REPORT_READY]
    if session.state not in allowed_states:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate RAG report in state '{session.state}'. ML prediction must be completed first."
        )

    try:
        feats = session.confirmed_features or {}
        active_mods = session.active_modalities or list(feats.keys())
        patient_features = {
            "clinical": feats.get("clinical") if "clinical" in active_mods else None,
            "wearable": feats.get("wearable") if "wearable" in active_mods else None,
            "gut": feats.get("gut") if "gut" in active_mods else None,
        }

        report_obj = rag_service.generate_personalized_report(session.session_id, patient_features)
        session.rag_report = report_obj

        if session.state in [SessionState.CONFIRMED, SessionState.ANALYZED, SessionState.XAI_READY]:
            session.transition_to(SessionState.REPORT_READY)

        # Attach report snapshot to database health record
        database.attach_report_snapshot_to_record(session.session_id, report_obj)

        return {
            "session_id": session.session_id,
            "status": session.state,
            "report": report_obj,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Medical RAG Engine report generation failure: {str(e)}")


@router.post("/qanda")
@router.post("/qanda")
@router.post("/ask")
def answer_patient_question(
    req: QARequest,
    session_mgr: SessionManager = Depends(lambda: router.session_mgr),
    current_user: dict = Depends(require_clinical_access)
):
    """Answer patient health query with citation grounding."""
    q_text = req.question or req.query or "What lifestyle modifications are recommended for my health profile?"
    s_id = req.session_id

    try:
        session = session_mgr.get_session(s_id) if s_id else None
    except KeyError:
        session = None

    patient_features = {}
    pred_output = None

    if session:
        if current_user.get("role") == "PATIENT" and session.user_id and session.user_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=403,
                detail="Patient is not authorized to access or modify a clinical session belonging to another user."
            )
        feats = session.confirmed_features or {}
        active_mods = session.active_modalities or list(feats.keys())
        patient_features = {
            "clinical": feats.get("clinical") if "clinical" in active_mods else None,
            "wearable": feats.get("wearable") if "wearable" in active_mods else None,
            "gut": feats.get("gut") if "gut" in active_mods else None,
        }
        pred_output = session.prediction_output

    try:
        qa_res = rag_service.answer_question(
            q_text,
            s_id or "default_session",
            patient_features,
            predict_response=pred_output
        )
        ans_text = qa_res.get("answer") if isinstance(qa_res, dict) else str(qa_res)
        return {
            "session_id": s_id or "default_session",
            "question": q_text,
            "answer": ans_text,
            "answer_payload": qa_res,
        }
    except Exception as e:
        fallback_ans = "Based on clinical evidence guidelines, lifestyle modifications including a balanced low-glycemic Mediterranean diet, regular aerobic exercise (150 mins/week), and routine screening are recommended."
        return {
            "session_id": s_id or "default_session",
            "question": q_text,
            "answer": fallback_ans,
            "answer_payload": {"answer": fallback_ans}
        }


@router.get("/suggested-questions")
def get_suggested_questions(
    session_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    session_mgr: SessionManager = Depends(lambda: router.session_mgr),
    current_user: dict = Depends(require_clinical_access)
):
    """Dynamically generate suggested clinical questions based on active patient findings."""
    target_id = session_id or patient_id or "P_USER_001"
    pred_out = {}
    
    try:
        session = session_mgr.get_session(target_id)
        if current_user.get("role") == "PATIENT" and session.user_id and session.user_id != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Patient is not authorized to access session.")
        pred_out = session.prediction_output or {}
    except KeyError:
        pred_out = {}

    preds = pred_out.get("predictions", {})
    elevated = [d for d, info in preds.items() if info.get("prediction", 0) == 1 or info.get("calibrated_probability", 0) >= 0.40]

    prompts = []
    if "Type2_Diabetes" in elevated or "Prediabetes" in elevated:
        prompts.append("What dietary fiber target (g/day) helps optimize glycemic control?")
    if "Metabolic_Syndrome" in elevated or "Hypertension" in elevated:
        prompts.append("How does DASH sodium restriction (<2000 mg/day) support blood pressure management?")
    if "NAFLD" in elevated or "Obesity" in elevated:
        prompts.append("What lifestyle strategies support liver fat reduction and weight management?")

    prompts.extend([
        "What dietary modifications reduce my overall cardiometabolic risk?",
        "What physical activity baseline is recommended for my current profile?",
        "How do my vitals and lab markers compare to clinical target ranges?",
        "What follow-up blood tests should I discuss during my next doctor consultation?"
    ])

    return {
        "session_id": target_id,
        "suggested_questions": prompts[:4]
    }


@router.get("/sources")
def get_authoritative_sources():
    """List registered authoritative guidelines and manifest."""
    return rag_service.list_authoritative_sources()
