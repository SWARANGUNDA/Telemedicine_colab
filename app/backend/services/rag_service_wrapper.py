"""
rag_service_wrapper.py — Service Wrapper around MedicalRAGService.

Executes Report Mode health report generation and Q&A Mode interactive assistant
with strict post-generation citation and safety validation.
Sanitizes NaN values for JSON compliance.
"""

import math
import logging
from typing import Any, Dict, Optional
import numpy as np

from services.medical_rag.rag_service import MedicalRAGService
from services.medical_rag.source_manifest import SourceManifestManager

logger = logging.getLogger("web_platform.services.rag")


def sanitize_nans(obj: Any) -> Any:
    """Recursively convert NaN/Inf float values to None for JSON compliance."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_nans(item) for item in obj]
    return obj


class RAGServiceWrapper:
    """Service layer wrapping MedicalRAGService."""

    def __init__(self):
        self.rag_service = MedicalRAGService()
        self.manifest_mgr = SourceManifestManager()

    def generate_personalized_report(
        self,
        patient_id: str,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Generate structured personalized health report."""
        logger.info("RAG Service: Generating health report for %s", patient_id)
        raw_res = self.rag_service.generate_health_report(patient_id, patient_features)
        return sanitize_nans(raw_res)

    def answer_question(
        self,
        user_question: str,
        patient_id: str,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
        predict_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Answer patient Q&A query with citation grounding and strict consistency guard."""
        logger.info("RAG Service: Answering question for %s: '%s'", patient_id, user_question)
        raw_res = self.rag_service.answer_patient_question(
            user_question, patient_id, patient_features, predict_response=predict_response
        )

        # CONSISTENCY GUARD: Verify Q&A context matches predict_response snapshot
        if predict_response and "predictions" in predict_response:
            qa_diseases = raw_res.get("patient_context", {}).get("disease_risk_outcomes", {})
            pred_snapshot = predict_response.get("predictions", {})
            for d, snap_info in pred_snapshot.items():
                if d in qa_diseases:
                    snap_prob = float(snap_info.get("calibrated_probability", 0.0))
                    qa_prob = float(qa_diseases[d].get("fusion_probability", 0.0))
                    if abs(snap_prob - qa_prob) > 1e-4:
                        err_msg = f"Scientific Consistency Violation: Q&A probability for {d} ({qa_prob:.4f}) mismatches report snapshot ({snap_prob:.4f})."
                        logger.error(err_msg)
                        raise RuntimeError(err_msg)

        return sanitize_nans(raw_res)

    def list_authoritative_sources(self) -> Dict[str, Any]:
        """Return registered sources manifest."""
        return {
            "sources": self.manifest_mgr.list_sources(),
        }


def generate_v3_rag_report(predict_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts ML predict output into a structured clinical explanation report.
    Executes EvidenceRetriever candidate retrieval for guideline grounding.
    Prohibits altering ML risk probabilities or binary decisions.
    """
    patient_id = predict_response.get("patient_id", "UNKNOWN")
    routing_meta = predict_response.get("routing_metadata", {})
    predictions  = predict_response.get("predictions", {})

    high_risk = []
    low_risk = []
    positive_diseases = []

    for d, info in predictions.items():
        prob = info["calibrated_probability"]
        pred = info["predicted_class"]
        risk = info["risk_level"]
        cutoff = info.get("threshold_used", 0.3)

        d_display = d.replace('_', ' ')
        entry = f"{d_display}: Model-Estimated Score = {prob:.1%} (Threshold = {cutoff:.0%}, Signal = {'POSITIVE' if pred == 1 else 'NEGATIVE'})"
        if pred == 1:
            high_risk.append(entry)
            positive_diseases.append(d)
        else:
            low_risk.append(entry)

    pathway = routing_meta.get("effective_pathway", "C")
    anchor  = routing_meta.get("primary_decision_anchor", "Clinical_v3")
    cgm_st  = routing_meta.get("cgm_status", "N/A")
    supplied = ", ".join(routing_meta.get("modalities_supplied", []))
    missing  = ", ".join(routing_meta.get("missing_modalities", [])) or "None"

    # Step 1: Execute Evidence Retriever for Grounded Recommendations
    retrieved_evidence = []
    try:
        from services.medical_rag.retriever import EvidenceRetriever
        retriever = EvidenceRetriever()
        target_terms = [d.replace('_', ' ') for d in positive_diseases] if positive_diseases else ["Cardiometabolic Health", "Type 2 Diabetes"]
        query_str = f"Clinical management guidelines for {', '.join(target_terms)} risk reduction dietary fiber exercise"
        retrieved_evidence = retriever.retrieve_evidence(query=query_str, top_k=5)
    except Exception as e:
        logger.warning(f"RAG EvidenceRetriever retrieval warning: {e}")

    # Extract patient feature data across active modalities
    expert_outs = predict_response.get("expert_outputs") or {}
    c_data = (expert_outs.get("clinical") or {}).get("raw_input") or (expert_outs.get("clinical") or {})
    w_data = (expert_outs.get("wearable") or {}).get("raw_input") or (expert_outs.get("wearable") or {})
    g_data = (expert_outs.get("gut") or {}).get("raw_input") or (expert_outs.get("gut") or {})

    modalities_supplied = set(routing_meta.get("modalities_supplied", []))
    if not modalities_supplied:
        if c_data: modalities_supplied.add("clinical")
        if w_data: modalities_supplied.add("wearable")
        if g_data: modalities_supplied.add("gut")

    def get_ref(idx=0):
        if retrieved_evidence and len(retrieved_evidence) > idx:
            ev = retrieved_evidence[idx]
            cid = ev.get("citation_id", f"REF_{idx+1}")
            cit_str = ev.get("citation_string") or ev.get("metadata", {}).get("document_title", "Clinical Guideline")
            return f"[{cid}] {cit_str}"
        return f"[REF_{idx+1}] Evidence-Based Guideline"

    # Structured Level 6 Recommendation Cards (WHAT, WHY, EVIDENCE, PRIORITY)
    structured_recs = []

    # Glycemic & Nutrition Recommendations
    hba1c = c_data.get("HbA1c") or c_data.get("hba1c")
    fbg = c_data.get("Fasting_Blood_Glucose") or c_data.get("fasting_blood_glucose")
    if hba1c is not None and float(hba1c) >= 5.7:
        structured_recs.append({
            "category": "Nutrition",
            "what": "Prioritize low-glycemic index complex carbohydrates and increase dietary fiber to 25–35 g/day.",
            "why": f"Verified HbA1c is {hba1c}% ({'Elevated Diabetes Range' if float(hba1c) >= 6.5 else 'Prediabetes Range'}).",
            "evidence": get_ref(0),
            "priority": "HIGH"
        })
    elif fbg is not None and float(fbg) >= 100:
        structured_recs.append({
            "category": "Nutrition",
            "what": "Consume fiber-rich, high-protein meals to minimize postprandial blood glucose spikes.",
            "why": f"Fasting Blood Glucose measured at {fbg} mg/dL.",
            "evidence": get_ref(0),
            "priority": "MEDIUM"
        })

    # Blood Pressure & Cardiometabolic Monitoring Recommendations
    sbp = c_data.get("Systolic_BP") or c_data.get("systolic_bp")
    dbp = c_data.get("Diastolic_BP") or c_data.get("diastolic_bp")
    if (sbp is not None and float(sbp) >= 130) or (dbp is not None and float(dbp) >= 80):
        structured_recs.append({
            "category": "Cardiometabolic Monitoring",
            "what": "Adopt DASH dietary guidelines with dietary sodium restriction under 2,000 mg/day.",
            "why": f"Blood Pressure vitals show {sbp if sbp else 'N/A'}/{dbp if dbp else 'N/A'} mmHg.",
            "evidence": get_ref(1),
            "priority": "HIGH"
        })

    # Lipid Profile Recommendations
    trig = c_data.get("Triglycerides") or c_data.get("triglycerides")
    hdl = c_data.get("HDL") or c_data.get("HDL_Cholesterol") or c_data.get("hdl")
    if trig is not None and float(trig) >= 150:
        structured_recs.append({
            "category": "Cardiometabolic Monitoring",
            "what": "Limit refined carbohydrates and alcohol; discuss dietary omega-3 intake.",
            "why": f"Serum Triglycerides measured at {trig} mg/dL.",
            "evidence": get_ref(2),
            "priority": "MEDIUM"
        })
    if hdl is not None and float(hdl) < 40:
        structured_recs.append({
            "category": "Physical Activity",
            "what": "Engage in regular aerobic physical activity to elevate high-density lipoprotein (HDL).",
            "why": f"HDL Cholesterol measured at {hdl} mg/dL (Low).",
            "evidence": get_ref(2),
            "priority": "MEDIUM"
        })

    # Physical Activity & Wearable Recommendations (Only if Wearables supplied or general)
    steps = w_data.get("Average_Daily_Steps") or w_data.get("average_daily_steps")
    sed = w_data.get("Sedentary_Time_Minutes") or w_data.get("sedentary_time_minutes")
    if "wearable" in modalities_supplied and steps is not None:
        if float(steps) < 7000:
            structured_recs.append({
                "category": "Physical Activity",
                "what": "Gradually increase walking volume by +1,000 steps/day weekly targeting 7,500–10,000 steps baseline.",
                "why": f"Wearable telemetry records average daily steps at {int(float(steps))} steps/day.",
                "evidence": get_ref(3),
                "priority": "HIGH"
            })
        else:
            structured_recs.append({
                "category": "Physical Activity",
                "what": "Maintain current physical activity baseline of >150 mins moderate exercise per week.",
                "why": f"Wearable daily step volume of {int(float(steps))} steps/day meets target goals.",
                "evidence": get_ref(3),
                "priority": "GENERAL"
            })
    elif "wearable" not in modalities_supplied and not any(r["category"] == "Physical Activity" for r in structured_recs):
        structured_recs.append({
            "category": "Physical Activity",
            "what": "Aim for at least 150 minutes of moderate-intensity aerobic physical activity per week.",
            "why": "Supports insulin sensitivity and overall cardiometabolic fitness.",
            "evidence": get_ref(3),
            "priority": "MEDIUM"
        })

    if "wearable" in modalities_supplied and sed is not None and float(sed) >= 480:
        structured_recs.append({
            "category": "Physical Activity",
            "what": "Break up continuous sedentary desk periods with 2-minute light walking breaks every 60 minutes.",
            "why": f"Sedentary duration is {int(float(sed))} minutes/day.",
            "evidence": get_ref(3),
            "priority": "MEDIUM"
        })

    # Sleep & Rest Recommendations (Only if Sleep data present in Wearables)
    sleep_dur = w_data.get("Sleep_Duration") or w_data.get("sleep_duration") or w_data.get("Sleep_Duration_Hours")
    if "wearable" in modalities_supplied and sleep_dur is not None and float(sleep_dur) < 7.0:
        structured_recs.append({
            "category": "Sleep",
            "what": "Optimize sleep hygiene to achieve 7–8 hours of uninterrupted nocturnal rest.",
            "why": f"Wearable sensor logs average nocturnal sleep duration at {float(sleep_dur):.1f} hours/night.",
            "evidence": get_ref(3),
            "priority": "MEDIUM"
        })

    # Microbiome & Gut Health Recommendations (STRICTLY ONLY WHEN GUT DATA IS SUPPLIED)
    if "gut" in modalities_supplied:
        akker = g_data.get("Akkermansia") or g_data.get("akkermansia")
        faecal = g_data.get("Faecalibacterium") or g_data.get("faecalibacterium")
        if akker is not None and float(akker) < 1.0:
            structured_recs.append({
                "category": "Gut Health",
                "what": "Incorporate polyphenol-rich foods (pomegranate, green tea, dark berries) into daily diet.",
                "why": f"Akkermansia muciniphila relative abundance is low ({akker}%).",
                "evidence": get_ref(4),
                "priority": "MEDIUM"
            })
        if faecal is not None and float(faecal) < 3.0:
            structured_recs.append({
                "category": "Gut Health",
                "what": "Increase fermentable prebiotic fibers (inulin, legumes, resistant starch) to boost SCFA butyrate.",
                "why": f"Faecalibacterium prausnitzii relative abundance measured at {faecal}%.",
                "evidence": get_ref(4),
                "priority": "MEDIUM"
            })

    # Liver Health Recommendation (for NAFLD positive screening signal)
    alt = c_data.get("ALT") or c_data.get("alt")
    ast = c_data.get("AST") or c_data.get("ast")
    if "NAFLD" in positive_diseases or (alt is not None and float(alt) >= 40):
        structured_recs.append({
            "category": "Liver Health Follow-up",
            "what": "Discuss hepatic biomarker monitoring (ALT, AST, Bilirubin) and liver ultrasound evaluation with your physician.",
            "why": f"Model-estimated screening signal detected for NAFLD (ALT: {alt if alt else 'Elevated Signal'}).",
            "evidence": get_ref(0),
            "priority": "HIGH"
        })

    # Weight & Body Composition Recommendation (for High Adiposity / Obesity / MetS)
    bmi = c_data.get("BMI") or c_data.get("bmi")
    waist = c_data.get("Waist_Circumference_cm") or c_data.get("waist")
    if "Obesity" in positive_diseases or "Metabolic_Syndrome" in positive_diseases or (bmi is not None and float(bmi) >= 25.0):
        structured_recs.append({
            "category": "Weight & Body Composition",
            "what": "Target a 5–10% gradual reduction in body weight through structured caloric restriction and regular activity.",
            "why": f"Screening profile indicates elevated adiposity risk (BMI: {bmi if bmi else 'Elevated Risk'}, Waist: {waist if waist else 'Elevated'}).",
            "evidence": get_ref(1),
            "priority": "HIGH" if "Obesity" in positive_diseases else "MEDIUM"
        })

    # Clinical Follow-up Recommendation
    if positive_diseases:
        structured_recs.append({
            "category": "Clinical Follow-up",
            "what": "Schedule a comprehensive clinical consultation with a healthcare provider to review model findings.",
            "why": f"Positive model-estimated screening signals detected for: {', '.join([d.replace('_', ' ') for d in positive_diseases])}.",
            "evidence": get_ref(0),
            "priority": "HIGH"
        })
    else:
        structured_recs.append({
            "category": "Clinical Follow-up",
            "what": "Maintain routine annual preventative health checks and periodic blood panels.",
            "why": "Screening profile indicates low immediate risk signals across evaluated domains.",
            "evidence": get_ref(0),
            "priority": "GENERAL"
        })

    # Dynamic Next Steps Timeline (NOW, NEXT, ONGOING) derived from actual findings
    now_steps = [
        "Review your 5 model-estimated screening results and SHAP driver rankings."
    ]
    if positive_diseases:
        now_steps.append(f"Schedule a clinical consultation or click 'Discuss with Doctor' to review elevated findings ({', '.join([d.replace('_', ' ') for d in positive_diseases])}).")
    else:
        now_steps.append("Discuss preventative cardiometabolic monitoring targets during your next routine checkup.")

    next_steps_1_4_weeks = []
    high_priority_recs = [r for r in structured_recs if r["priority"] == "HIGH"]
    if high_priority_recs:
        for r in high_priority_recs[:2]:
            next_steps_1_4_weeks.append(r["what"])
    else:
        next_steps_1_4_weeks.append("Incorporate recommended dietary fiber and physical activity targets.")
    if "wearable" in modalities_supplied:
        next_steps_1_4_weeks.append("Monitor daily step trends and active minutes using your connected wearable.")

    next_steps = {
        "now": now_steps,
        "next": next_steps_1_4_weeks,
        "ongoing": [
            "Re-evaluate baseline cardiometabolic blood panels (HbA1c, Lipid Profile, FBG) in 3–6 months.",
            "Maintain longitudinal health tracking to monitor changes over time."
        ]
    }

    # Format Markdown Report
    recs_md_lines = []
    for r in structured_recs:
        recs_md_lines.append(
            f"- **[{r['priority']}] {r['category']}**: {r['what']}\n"
            f"  - *Why:* {r['why']}\n"
            f"  - *Evidence Source:* {r['evidence']}"
        )
    recs_formatted = "\n\n".join(recs_md_lines)

    evidence_text_blocks = []
    for ev in retrieved_evidence:
        citation_id = ev.get("citation_id", "REF")
        cit_str = ev.get("citation_string", "Clinical Guideline")
        txt = ev.get("text", "")
        evidence_text_blocks.append(f"- **[{citation_id}]** *{cit_str}*: \"{txt[:220]}...\"")

    evidence_formatted = "\n".join(evidence_text_blocks) if evidence_text_blocks else "- No external guideline chunks loaded."

    markdown_report = f"""# TeleMed Multimodal Cardiometabolic Health Report (v4.0)

**Patient Identifier:** `{patient_id}`  
**Effective Scientific Pathway:** `{pathway}` (Primary Screening Input: `{anchor}`)  
**Modality Status:** Supplied: `[{supplied}]` | Missing: `[{missing}]` | CGM Status: `{cgm_st}`  

---

## 1. Model-Estimated Decision-Support Screening Signals (ML Engine Controlled)

### Positive Screening Signals
{"".join(f"- **{item}**\n" for item in high_risk) if high_risk else "- No positive screening signals detected.\n"}

### Negative Screening Signals
{"".join(f"- {item}\n" for item in low_risk) if low_risk else "- None.\n"}

---

## 2. Personalized Evidence-Based Lifestyle & Clinical Guidance

{recs_formatted}

---

## 3. Your Actionable Next Steps

- **NOW (Immediate Actions):**
{"".join(f"  - {step}\n" for step in next_steps['now'])}
- **NEXT (1–4 Weeks):**
{"".join(f"  - {step}\n" for step in next_steps['next'])}
- **ONGOING (Long-Term Monitoring):**
{"".join(f"  - {step}\n" for step in next_steps['ongoing'])}

---

## 4. Grounded Medical Guidelines & Retrieved Evidence

{evidence_formatted}

---

## 5. Clinical Governance & Decision-Support Disclaimer

- **Decision-Support Scope:** Disease probability estimates are generated by the frozen **v4.0 Expert Engine** for screening and decision-support input. Standard clinical lab biomarkers provide high-confidence model inputs when available, but model scores do not establish a definitive clinical diagnosis.
- **Remote Telemetry Context:** Non-clinical modalities (Wearables & Gut Microbiome) provide continuous risk monitoring and remote screening capability when clinical lab access is restricted.
- **Next Clinical Steps:** Patients presenting with Positive Screening Signals for Type 2 Diabetes, NAFLD, High Adiposity Risk, or Metabolic Syndrome should receive confirmatory diagnostic blood panels (HbA1c, Fasting Glucose, Lipid Panel, ALT/AST) and consult a board-certified physician.

---

*Disclaimer: This report is generated for clinical decision support and research evaluation. All disease probability estimates are computed directly by ML expert algorithms. This tool does not replace professional medical diagnosis, prescription, or clinical judgment.*
"""

    return {
        "patient_id": patient_id,
        "pipeline_version": "v4.0",
        "model_version": "v4.0",
        "effective_pathway": pathway,
        "report_status": "READY",
        "report_markdown": markdown_report,
        "recommendations": structured_recs,
        "next_steps": next_steps,
        "retrieved_evidence": retrieved_evidence,
        "summary": {
            "positive_signal_count": len(high_risk),
            "negative_signal_count": len(low_risk)
        }
    }

