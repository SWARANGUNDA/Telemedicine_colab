"""
rag_service.py — High-Level Medical RAG Service API.

Orchestrates:
1. REPORT MODE: Structured Personalized Health Report
2. Q&A MODE: Interactive Health Q&A Assistant

Connects Patient Context Contract Builder, Multi-Stage Retriever,
Grounded Generator, and Post-Generation Validator.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from ai.explainability.unified_xai_engine import UnifiedXAIEngine
except (ImportError, ValueError):
    from ai.explainability.unified_xai_engine import UnifiedXAIEngine
from . import config
from .generator import GroundedRAGGenerator
from .post_validator import RAGPostValidator
from .rag_patient_contract import build_rag_patient_context
from .retriever import EvidenceRetriever

logger = logging.getLogger("services.medical_rag.rag_service")


class MedicalRAGService:
    """High-Level Medical RAG Service supporting Report Mode and Q&A Mode."""

    def __init__(self):
        self.xai_engine = UnifiedXAIEngine().load()
        self.retriever = EvidenceRetriever()
        self.generator = GroundedRAGGenerator()
        self.post_validator = RAGPostValidator()

        # Sample patient payload for evaluation/testing
        self.sample_patient_payload = {
            "clinical": {
                'Age': 55, 'Gender': 'Male', 'Height_cm': 175, 'Weight_kg': 95, 'BMI': 31.0,
                'Waist_Circumference_cm': 102, 'Systolic_BP': 145, 'Diastolic_BP': 92,
                'Fasting_Blood_Glucose': 130, 'HbA1c': 7.2, 'LDL_Cholesterol': 160,
                'HDL_Cholesterol': 38, 'Triglycerides': 220, 'ALT': 55, 'AST': 42,
                'Family_History_Diabetes': 1, 'Family_History_Obesity': 1,
                'Family_History_Hypertension': 1, 'Family_History_NAFLD': 0
            },
            "wearable": {
                'Average_Daily_Steps': 3500, 'Active_Minutes': 15, 'Sedentary_Time_Minutes': 660,
                'Resting_Heart_Rate': 82, 'Sleep_Duration': 5.5, 'Calories_Burned': 1800,
                'Average_Glucose': 145, 'Glucose_Variability': 35, 'Time_In_Range': 55,
                'Time_Above_Range': 38
            },
            "gut": {
                'Akkermansia': 0.5, 'Faecalibacterium': 2.0, 'Bifidobacterium': 1.5,
                'Roseburia': 1.0, 'Alistipes': 0.8, 'Escherichia_Shigella': 5.0,
                'Collinsella': 3.0, 'Prevotella': 2.5, 'Blautia': 1.2,
                'Shannon_Diversity_Index': 2.0
            }
        }

    def generate_health_report(
        self,
        patient_id: str,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
        top_k_evidence: int = config.DEFAULT_TOP_K,
        predict_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """REPORT MODE: Generate structured personalized health report."""
        logger.info("REPORT MODE: Generating report for patient %s", patient_id)

        # Step 1: Build RAG Patient Context Contract using immutable predict_response
        patient_context = build_rag_patient_context(patient_id, patient_features, self.xai_engine, predict_response=predict_response)
        
        # ...
        elevated_diseases = [
            d for d, info in patient_context["disease_risk_outcomes"].items()
            if info.get("fusion_probability", 0) >= 0.35 or info.get("prediction", 0) == 1
        ]

        query = f"Clinical management guidelines for {', '.join(elevated_diseases)} risk reduction dietary fiber exercise"
        evidence = self.retriever.retrieve_evidence(
            query=query,
            top_k=top_k_evidence,
            disease_filter=elevated_diseases if elevated_diseases else None,
        )

        raw_response = self.generator.generate_report(patient_context, evidence)
        val_result = self.post_validator.validate_llm_response(raw_response, patient_context, evidence)
        cleaned_response = val_result.get("cleaned_response", raw_response)

        verified_refs = set(val_result.get("verified_citations", []))
        display_evidence = [ev for ev in evidence if ev["citation_id"] in verified_refs] if verified_refs else evidence

        return {
            "mode": "REPORT",
            "patient_id": patient_id,
            "report_status": "READY",
            "response_text": cleaned_response,
            "report_markdown": cleaned_response,
            "patient_context": patient_context,
            "retrieved_evidence": display_evidence,
            "validation_result": val_result,
        }

    def answer_patient_question(
        self,
        user_question: str,
        patient_id: str,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
        top_k_evidence: int = config.DEFAULT_TOP_K,
        predict_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Q&A MODE: Answer patient question using evidence retrieval across all domains."""
        logger.info("Q&A MODE: Answering question for patient %s: '%s'", patient_id, user_question)

        # Step 1: Build RAG Patient Context Contract using immutable predict_response
        patient_context = build_rag_patient_context(patient_id, patient_features, self.xai_engine, predict_response=predict_response)

        # Step 2: Multi-Domain Evidence Retrieval (Query-Aware)
        evidence = self.retriever.retrieve_evidence(
            query=user_question,
            top_k=top_k_evidence,
            disease_filter=None,
        )

        # Step 3: Grounded Generation
        raw_response = self.generator.generate_qanda_answer(user_question, patient_context, evidence)

        # Step 4: Post-Generation Validation
        val_result = self.post_validator.validate_llm_response(raw_response, patient_context, evidence)
        cleaned_response = val_result.get("cleaned_response", raw_response)

        # Filter evidence to only chunks actually cited in the final response
        verified_refs = set(val_result.get("verified_citations", []))
        display_evidence = [ev for ev in evidence if ev["citation_id"] in verified_refs] if verified_refs else []

        return {
            "mode": "QANDA",
            "user_question": user_question,
            "patient_id": patient_id,
            "response_text": cleaned_response,
            "patient_context": patient_context,
            "retrieved_evidence": display_evidence,
            "validation_result": val_result,
        }
