"""
run_phase5_pipeline.py — Master Execution Pipeline for Phase 5 Medical RAG.

Executes:
1. Knowledge Base Ingestion & Vector Index Building
2. Test Report Mode Execution
3. Test Q&A Mode Execution
4. Safety & Adversarial Tests
5. Execute 25-Scenario RAG Evaluation Suite
"""

import json
import logging
from pathlib import Path

from services.medical_rag import config
from services.medical_rag.evaluator import RAGEvaluator
from services.medical_rag.ingestion import process_all_documents
from services.medical_rag.rag_service import MedicalRAGService
from services.medical_rag.vector_store import SemanticVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("services.medical_rag.pipeline")


def run_phase5_pipeline():
    logger.info("=" * 70)
    logger.info("  PHASE 5: MEDICAL RAG ENGINE — FULL PIPELINE EXECUTION")
    logger.info("=" * 70)

    # ── Step 1: Ingestion & Vector Index ──
    logger.info("Processing raw document guidelines...")
    chunks = process_all_documents()
    vstore = SemanticVectorStore()
    vstore.build_index(chunks)
    logger.info("✓ Vector store index built with %d chunks.", len(chunks))

    # ── Step 2: Initialize RAG Service ──
    rag_service = MedicalRAGService()

    # ── Step 3: Test REPORT MODE ──
    logger.info("─" * 50)
    logger.info("TESTING REPORT MODE:")
    report_res = rag_service.generate_health_report(
        patient_id="P01429",
        patient_features=rag_service.sample_patient_payload,
    )
    logger.info("Report Mode Generated Response Length: %d chars", len(report_res["response_text"]))
    logger.info("Report Validation Passed: %s", report_res["validation_result"]["is_valid"])

    # ── Step 4: Test Q&A MODE ──
    logger.info("─" * 50)
    logger.info("TESTING Q&A MODE:")
    q_res = rag_service.answer_patient_question(
        user_question="What diet pattern is recommended for NAFLD and elevated ALT?",
        patient_id="P01429",
        patient_features=rag_service.sample_patient_payload,
    )
    logger.info("Q&A Response Length: %d chars", len(q_res["response_text"]))
    logger.info("Q&A Validation Passed: %s", q_res["validation_result"]["is_valid"])

    # ── Step 5: Execute 25-Scenario RAG Evaluation Suite ──
    evaluator = RAGEvaluator()
    eval_results = evaluator.evaluate_pipeline(rag_service)

    # Save Evaluation Results
    out_eval_path = config.REPORTS_DIR / "rag_evaluation_results.json"
    with open(out_eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)

    logger.info("=" * 70)
    logger.info("  PHASE 5 PIPELINE EXECUTION COMPLETE")
    logger.info("  Evaluation results saved to: %s", out_eval_path)
    logger.info("=" * 70)

    return eval_results


if __name__ == "__main__":
    run_phase5_pipeline()
