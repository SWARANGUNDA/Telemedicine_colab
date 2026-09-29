"""
test_level6_consistency_e2e.py — Level 6 Scientific Consistency & Data-Flow E2E Test Suite.
"""

import unittest
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

class TestLevel6ConsistencyE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Register a test doctor/user to obtain auth bearer token
        reg_res = client.post("/api/v1/auth/register/patient", json={
            "email": "consistency_tester@telemed.ai",
            "password": "Password123!",
            "full_name": "Scientific Consistency Tester",
            "age": 52
        })
        if reg_res.status_code == 201:
            token = reg_res.json()["token"]
        else:
            login_res = client.post("/api/v1/auth/login", json={
                "email": "consistency_tester@telemed.ai",
                "password": "Password123!"
            })
            token = login_res.json()["token"]

        cls.headers = {"Authorization": f"Bearer {token}"}

    def test_01_e2e_test_c002_single_source_of_truth(self):
        """E2E Test on TEST_C002: Verify 100% probability and signal alignment between Report and Q&A."""
        # 1. Run v3 predict for TEST_C002 (High-risk Pathway C payload)
        c002_payload = {
            "patient_id": "TEST_C002",
            "clinical_data": {
                "Age": 55, "Gender": "Male", "Height_cm": 175, "Weight_kg": 95, "BMI": 31.0,
                "Waist_Circumference_cm": 102, "Systolic_BP": 140, "Diastolic_BP": 90,
                "Fasting_Blood_Glucose": 145, "HbA1c": 7.5, "LDL_Cholesterol": 160,
                "HDL_Cholesterol": 38, "Triglycerides": 220, "ALT": 55, "AST": 42,
                "Family_History_Diabetes": 1, "Family_History_Obesity": 1,
                "Family_History_Hypertension": 1, "Family_History_NAFLD": 1
            }
        }
        pred_res = client.post("/api/v3/predict", json=c002_payload, headers=self.headers)
        self.assertEqual(pred_res.status_code, 200)
        pred_data = pred_res.json()

        pred_t2d = pred_data["predictions"]["Type2_Diabetes"]["calibrated_probability"]
        self.assertGreaterEqual(pred_t2d, 0.85)

        # 2. Generate Report
        report_res = client.post("/api/v3/report", json={"patient_id": "TEST_C002", "predict_response": pred_data}, headers=self.headers)
        self.assertEqual(report_res.status_code, 200)

        # 3. Call RAG Q&A passing exact predict_response snapshot
        qa_req = {
            "patient_id": "TEST_C002",
            "predict_response": pred_data,
            "question": "What physical activity goals should I target for my current profile?"
        }
        qa_res = client.post("/api/v3/qanda", json=qa_req, headers=self.headers)
        self.assertEqual(qa_res.status_code, 200)
        qa_data = qa_res.json()
        qa_payload = qa_data["answer_payload"]
        qa_context = qa_payload["patient_context"]["disease_risk_outcomes"]

        # ASSERTION 1: 100% Probability Alignment between Report & Q&A
        for d, info in pred_data["predictions"].items():
            self.assertIn(d, qa_context)
            snap_prob = info["calibrated_probability"]
            qa_prob = qa_context[d]["fusion_probability"]
            self.assertAlmostEqual(snap_prob, qa_prob, places=4, msg=f"Mismatch in {d} probability between predict snapshot ({snap_prob}) and Q&A context ({qa_prob})")

        # ASSERTION 2: Positive screening signals match Elevated Risk in Q&A
        ans_text = qa_payload["response_text"]
        self.assertIn("Elevated Risk", ans_text)
        self.assertIn("Type2 Diabetes", ans_text)

        # ASSERTION 3: Pathway C Modality Isolation (No Wearable/Gut claims when missing)
        self.assertIn("missing_modalities", qa_payload["patient_context"])
        self.assertIn("wearable", qa_payload["patient_context"]["missing_modalities"])
        self.assertNotIn("using your connected wearable", ans_text.lower())

    def test_02_blood_test_question_evidence_relevance(self):
        """Verify 'What follow-up blood tests...' retrieves laboratory panel evidence."""
        c002_payload = {
            "patient_id": "TEST_C002",
            "clinical_data": {"HbA1c": 7.5, "Fasting_Blood_Glucose": 145, "Systolic_BP": 140, "Diastolic_BP": 90, "ALT": 55, "AST": 42}
        }
        pred_res = client.post("/api/v3/predict", json=c002_payload, headers=self.headers).json()

        qa_req = {
            "patient_id": "TEST_C002",
            "predict_response": pred_res,
            "question": "What follow-up blood tests should I discuss with my doctor?"
        }
        qa_res = client.post("/api/v3/qanda", json=qa_req, headers=self.headers)
        self.assertEqual(qa_res.status_code, 200)
        qa_payload = qa_res.json()["answer_payload"]
        evidence = qa_payload.get("retrieved_evidence", [])

        # ASSERTION: Evidence list contains blood/lab test relevant keywords
        found_lab_evidence = False
        for ev in evidence:
            txt = (ev.get("text", "") + " " + ev.get("citation_string", "")).lower()
            if any(kw in txt for kw in ["blood", "hba1c", "glucose", "lipid", "alt", "ast", "panel", "diagnostic", "laboratory", "test"]):
                found_lab_evidence = True
                break
        self.assertTrue(found_lab_evidence, "Blood test query failed to retrieve lab/diagnostic evidence.")

    def test_03_no_diagnostic_authority_phrasing(self):
        """Verify removal of diagnostic authority claims from patient-facing text."""
        c002_payload = {
            "patient_id": "TEST_C002",
            "clinical_data": {"HbA1c": 7.5, "Fasting_Blood_Glucose": 145}
        }
        pred_res = client.post("/api/v3/predict", json=c002_payload, headers=self.headers).json()
        report_res = client.post("/api/v3/report", json={"patient_id": "TEST_C002", "predict_response": pred_res}, headers=self.headers).json()

        md = report_res.get("report_markdown", "")
        self.assertNotIn("primary diagnostic anchor", md.lower())
        self.assertNotIn(">99.9% of maximum achievable roc-auc", md.lower())
        self.assertIn("screening", md.lower())

    def test_04_sequential_multi_patient_isolation(self):
        """Verify sequential patient assessments do not leak risk scores across sessions."""
        # Patient A: High Risk
        high_payload = {"patient_id": "P_HIGH", "clinical_data": {"HbA1c": 8.5, "Fasting_Blood_Glucose": 180}}
        pred_high = client.post("/api/v3/predict", json=high_payload, headers=self.headers).json()
        qa_high = client.post("/api/v3/qanda", json={"patient_id": "P_HIGH", "predict_response": pred_high, "question": "What is my diabetes risk?"}, headers=self.headers).json()
        prob_high = qa_high["answer_payload"]["patient_context"]["disease_risk_outcomes"]["Type2_Diabetes"]["fusion_probability"]
        self.assertGreaterEqual(prob_high, 0.85)

        # Patient B: Low Risk
        low_payload = {"patient_id": "P_LOW", "clinical_data": {"HbA1c": 5.0, "Fasting_Blood_Glucose": 85, "BMI": 21.0, "Systolic_BP": 115, "Diastolic_BP": 75, "Triglycerides": 90, "HDL_Cholesterol": 60, "ALT": 18, "AST": 16}}
        pred_low = client.post("/api/v3/predict", json=low_payload, headers=self.headers).json()
        qa_low = client.post("/api/v3/qanda", json={"patient_id": "P_LOW", "predict_response": pred_low, "question": "What is my diabetes risk?"}, headers=self.headers).json()
        prob_low = qa_low["answer_payload"]["patient_context"]["disease_risk_outcomes"]["Type2_Diabetes"]["fusion_probability"]
        self.assertLess(prob_low, 0.35)

        # Confirm zero cross-session leakage
        self.assertNotEqual(prob_high, prob_low)

if __name__ == "__main__":
    unittest.main()
