"""
v3_routes.py — Dedicated FastAPI REST Router for Unified Multimodal v3.3.

Endpoints:
- POST /api/v3/predict  : Run dynamic modality routing & expert inference.
- POST /api/v3/xai      : Generate SHAP statistical feature contributions.
- POST /api/v3/report   : Generate LLM clinical explanation report.

Strictly isolated under /api/v3/* without automatic v2 fallback.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from ai.inference.v3_inference_engine import V3InferenceEngine
from services.multimodal_intake.v3_schema_validator import V3SchemaValidator
from ai.inference.v3_scientific_router import V3ScientificRouter
from app.backend.services.xai_service import generate_v3_xai_attribution
from app.backend.services.rag_service_wrapper import generate_v3_rag_report
from app.backend.auth import require_clinical_access

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("v3_routes")

router = APIRouter(prefix="/api/v3", tags=["V3 Unified Multimodal Baseline"])

# Shared engine instance
_engine = V3InferenceEngine()
_scientific_router = V3ScientificRouter(_engine)

class V3PredictRequest(BaseModel):
    patient_id: str = Field(default="P_TEST_001")
    clinical_data: Optional[Dict[str, Any]] = None
    wearable_data: Optional[Dict[str, Any]] = None
    gut_data: Optional[Dict[str, Any]] = None

class V3XAIRequest(BaseModel):
    patient_id: str = Field(default="P_TEST_001")
    clinical_data: Optional[Dict[str, Any]] = None
    wearable_data: Optional[Dict[str, Any]] = None
    gut_data: Optional[Dict[str, Any]] = None
    disease: str = Field(default="Type2_Diabetes")
    predict_response: Optional[Dict[str, Any]] = None

class V3ReportRequest(BaseModel):
    patient_id: str = Field(default="P_TEST_001")
    predict_response: Dict[str, Any] = Field(...)

@router.post("/predict", status_code=status.HTTP_200_OK)
def predict_v3(
    request: V3PredictRequest,
    current_user: dict = Depends(require_clinical_access)
):
    """
    Executes v3 prediction pipeline with dynamic modality routing.
    Does NOT fall back to v2 on failure.
    """
    try:
        raw_payload = request.model_dump()
        validated_intake = V3SchemaValidator.validate_and_inspect_payload(raw_payload)
        
        if validated_intake.get("gut_validation_error"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Gut Validation Failed: {validated_intake['gut_validation_error']}"
            )

        if validated_intake["modality_mask"] == "NONE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request: At least one modality (clinical, wearable, or gut) must contain valid features."
            )

        result = _scientific_router.route_and_predict(validated_intake)
        result["effective_pathway"] = result.get("routing_metadata", {}).get("effective_pathway", "C")
        result["pathway_used"] = result.get("routing_metadata", {}).get("effective_pathway", "C")
        result["active_modalities"] = result.get("routing_metadata", {}).get("modalities_supplied", ["clinical"])

        user_id = current_user.get("user_id")
        if user_id:
            try:
                from .. import database
                record = database.upsert_health_record(
                    user_id=user_id,
                    source_session_id=f"sess_{request.patient_id}",
                    effective_pathway=result["effective_pathway"],
                    data_quality_score=0.92,
                    active_modalities=", ".join(result["active_modalities"]),
                    confirmed_features={"clinical": raw_payload.get("clinical_data"), "wearable": raw_payload.get("wearable_data"), "gut": raw_payload.get("gut_data")},
                    prediction_snapshot=result,
                    status="ANALYZED"
                )
                result["record_id"] = record.get("record_id")
            except Exception as db_err:
                logger.warning(f"Non-blocking health record persistence error: {db_err}")

        return result

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"V3 Inference Failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"v3_inference_failure: {str(e)}"
        )

@router.post("/xai", status_code=status.HTTP_200_OK)
def xai_v3(
    request: V3XAIRequest,
    current_user: dict = Depends(require_clinical_access)
):
    """
    Generates TreeSHAP statistical model feature contributions for active v3 experts.
    Outputs are explicitly labeled 'Statistical Predictor Contributions'.
    """
    try:
        raw_payload = request.model_dump()
        if request.predict_response:
            pred_resp = request.predict_response
            exp_outs = pred_resp.get("expert_outputs") or {}
            conf_feats = pred_resp.get("confirmed_features") or {}

            if not raw_payload.get("clinical_data"):
                raw_payload["clinical_data"] = (exp_outs.get("clinical") or {}).get("raw_input") or (exp_outs.get("clinical") or {}) or conf_feats.get("clinical")
            if not raw_payload.get("wearable_data"):
                raw_payload["wearable_data"] = (exp_outs.get("wearable") or {}).get("raw_input") or (exp_outs.get("wearable") or {}) or conf_feats.get("wearable")
            if not raw_payload.get("gut_data"):
                raw_payload["gut_data"] = (exp_outs.get("gut") or {}).get("raw_input") or (exp_outs.get("gut") or {}) or conf_feats.get("gut")

        validated_intake = V3SchemaValidator.validate_and_inspect_payload(raw_payload)
        
        if validated_intake["modality_mask"] == "NONE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request: No valid modality data provided for XAI analysis."
            )

        xai_res = generate_v3_xai_attribution(_engine, validated_intake, request.disease)
        
        user_id = current_user.get("user_id")
        if user_id:
            try:
                from .. import database
                database.attach_xai_snapshot_to_record(f"sess_{request.patient_id}", xai_res)
            except Exception as db_err:
                logger.warning(f"Non-blocking XAI snapshot persistence error: {db_err}")

        return xai_res

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"V3 XAI Failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"v3_xai_failure: {str(e)}"
        )

@router.post("/report", status_code=status.HTTP_200_OK)
def report_v3(
    request: V3ReportRequest,
    current_user: dict = Depends(require_clinical_access)
):
    """
    Generates RAG + LLM clinical explanation report.
    Prohibits LLM from modifying ML probabilities or binary predictions.
    """
    try:
        report_res = generate_v3_rag_report(request.predict_response)
        
        user_id = current_user.get("user_id")
        if user_id:
            try:
                from .. import database
                patient_id = request.predict_response.get("patient_id", request.patient_id)
                database.attach_report_snapshot_to_record(f"sess_{patient_id}", report_res)
            except Exception as db_err:
                logger.warning(f"Non-blocking RAG report snapshot persistence error: {db_err}")

        return report_res

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"V3 Report Failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"v3_report_failure: {str(e)}"
        )

class V3QARequest(BaseModel):
    patient_id: str = Field(default="P_TEST_001")
    predict_response: Optional[Dict[str, Any]] = None
    question: str = Field(...)

@router.post("/qanda", status_code=status.HTTP_200_OK)
@router.post("/ask", status_code=status.HTTP_200_OK)
def qanda_v3(
    request: V3QARequest,
    current_user: dict = Depends(require_clinical_access)
):
    """
    Answers patient Q&A query grounded in evidence-based guidelines.
    Does NOT alter ML model state or probabilities.
    """
    try:
        from app.backend.services.rag_service_wrapper import RAGServiceWrapper
        wrapper = RAGServiceWrapper()
        patient_features = {}
        if request.predict_response:
            expert_outs = request.predict_response.get("expert_outputs", {})
            patient_features = {
                "clinical": (expert_outs.get("clinical") or {}).get("raw_input") or (expert_outs.get("clinical") or {}),
                "wearable": (expert_outs.get("wearable") or {}).get("raw_input") or (expert_outs.get("wearable") or {}),
                "gut": (expert_outs.get("gut") or {}).get("raw_input") or (expert_outs.get("gut") or {}),
            }

        qa_res = wrapper.answer_question(
            request.question,
            request.patient_id,
            patient_features,
            predict_response=request.predict_response
        )
        return {
            "patient_id": request.patient_id,
            "question": request.question,
            "answer_payload": qa_res
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"V3 Q&A Failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"v3_qanda_failure: {str(e)}"
        )


class V3SuggestedQuestionsRequest(BaseModel):
    patient_id: Optional[str] = "P_TEST_001"
    predict_response: Optional[Dict[str, Any]] = None


@router.get("/suggested-questions", status_code=status.HTTP_200_OK)
@router.post("/suggested-questions", status_code=status.HTTP_200_OK)
def suggested_questions_v3(
    request: Optional[V3SuggestedQuestionsRequest] = None,
    patient_id: Optional[str] = None,
    current_user: dict = Depends(require_clinical_access)
):
    """Generates dynamic suggested clinical questions from v3 predict response or patient profile."""
    pid = (request.patient_id if request else patient_id) or "P_USER_001"
    pred_res = (request.predict_response if request else None) or {}
    preds = pred_res.get("predictions", {})
    routing = pred_res.get("routing_metadata", {})
    supplied = set(routing.get("modalities_supplied", ["clinical"]))

    elevated = [d for d, info in preds.items() if info.get("predicted_class", 0) == 1 or info.get("calibrated_probability", 0) >= 0.40]

    prompts = []
    if "Type2_Diabetes" in elevated or "Prediabetes" in elevated:
        prompts.append("What dietary fiber targets (g/day) help optimize glycemic control?")
    if "Metabolic_Syndrome" in elevated or "Hypertension" in elevated:
        prompts.append("How does DASH sodium restriction (<2000 mg/day) support blood pressure management?")
    if "NAFLD" in elevated or "Obesity" in elevated:
        prompts.append("What lifestyle strategies support liver fat reduction and weight management?")

    if "wearable" in supplied:
        prompts.append("How do my wearable steps and sedentary duration affect blood glucose variability?")
    else:
        prompts.append("What physical activity baseline is recommended for my risk profile?")

    if "gut" in supplied:
        prompts.append("How does my gut microbiome relative abundance impact SCFA butyrate production?")

    prompts.extend([
        "What dietary modifications reduce my overall cardiometabolic risk?",
        "What follow-up blood tests should I discuss during my next doctor consultation?"
    ])

    return {
        "patient_id": pid,
        "suggested_questions": prompts[:4]
    }

