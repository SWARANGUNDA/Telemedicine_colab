"""
verify_e2e_c001_full_pipeline.py — Live End-to-End Verification of TEST_C001 across Predict, XAI, RAG Report & Q&A
"""

import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

c001_payload = {
    "patient_id": "TEST_C001",
    "clinical_data": {
        "Age": 48,
        "Gender": 1,
        "Height": 170.0,
        "Weight": 87.0,
        "BMI": 30.1,
        "Waist_Circumference": 102.0,
        "Systolic_BP": 142.0,
        "Diastolic_BP": 91.0,
        "Fasting_Blood_Glucose": 132.0,
        "HbA1c": 6.8,
        "LDL": 145.0,
        "HDL": 38.0,
        "Triglycerides": 210.0,
        "ALT": 58.0,
        "AST": 41.0
    }
}

def post_json(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

print("=== STEP 1: PREDICT LIVE VERIFICATION ===")
st, pred_res = post_json("/api/v3/predict", c001_payload)
print(f"Status: {st}")
print("Predictions:", json.dumps(pred_res["predictions"], indent=2))

print("\n=== STEP 2: XAI / SHAP VERIFICATION FOR ALL 5 TARGETS ===")
diseases = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
for d in diseases:
    xai_req = {**c001_payload, "disease": d}
    st_x, xai_res = post_json("/api/v3/xai", xai_req)
    clinical_drivers = xai_res.get("attributions", {}).get("clinical", {}).get("top_risk_drivers", [])
    top_driver = clinical_drivers[0]["feature_name"] if clinical_drivers else "None"
    top_val = clinical_drivers[0]["value"] if clinical_drivers else "N/A"
    top_shap = clinical_drivers[0]["shap_attribution"] if clinical_drivers else "N/A"
    print(f"Target: {d:<22} | Top Driver: {top_driver:<22} (Value: {top_val}, SHAP: +{top_shap})")

print("\n=== STEP 3: RAG CLINICAL REPORT & EVIDENCE RETRIEVAL ===")
report_req = {"patient_id": "TEST_C001", "predict_response": pred_res}
st_r, report_res = post_json("/api/v3/report", report_req)
print(f"Status: {st_r}")
print("Retrieved Evidence Count:", len(report_res.get("retrieved_evidence", [])))
for ev in report_res.get("retrieved_evidence", [])[:2]:
    print(f"  - Citation [{ev['citation_id']}]: {ev['citation_string']} (Score: {ev['similarity_score']:.4f})")

print("\n=== STEP 4: GROUNDED RAG Q&A ASSISTANT ===")
qa_req = {
    "patient_id": "TEST_C001",
    "predict_response": pred_res,
    "question": "What dietary changes will reduce my overall metabolic risk?"
}
st_q, qa_res = post_json("/api/v3/qanda", qa_req)
print(f"Status: {st_q}")
ans = qa_res.get("answer_payload", {})
print("Response Text:", ans.get("response_text", "")[:250], "...")
print("Citations Verified:", ans.get("verified_citations", []))
