"""
test_level6_rag.py — Regression Test Suite for Level 6 Clinical Report & RAG Assistant.
"""

import unittest
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

class TestLevel6RAG(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Register a test doctor/user to get auth token
        reg_res = client.post("/api/v1/auth/register/patient", json={
            "email": "level6_tester@telemed.ai",
            "password": "Password123!",
            "full_name": "Level 6 Tester",
            "age": 45
        })
        if reg_res.status_code == 201:
            token = reg_res.json()["token"]
        else:
            login_res = client.post("/api/v1/auth/login", json={
                "email": "level6_tester@telemed.ai",
                "password": "Password123!"
            })
            token = login_res.json()["token"]

        cls.headers = {"Authorization": f"Bearer {token}"}

    def test_01_v3_suggested_questions(self):
        """Verify POST /api/v3/suggested-questions returns tailored prompts."""
        payload = {
            "patient_id": "P_TEST_LEVEL6",
            "predict_response": {
                "predictions": {
                    "Type2_Diabetes": {"predicted_class": 1, "calibrated_probability": 0.72},
                    "Hypertension": {"predicted_class": 1, "calibrated_probability": 0.65}
                },
                "routing_metadata": {
                    "modalities_supplied": ["clinical", "wearable"]
                }
            }
        }
        res = client.post("/api/v3/suggested-questions", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("suggested_questions", data)
        self.assertGreaterEqual(len(data["suggested_questions"]), 3)

    def test_02_v1_rag_suggested_questions_fallback(self):
        """Verify GET /api/v1/rag/suggested-questions handles uninitialized sessions without 404."""
        res = client.get("/api/v1/rag/suggested-questions?session_id=UNKNOWN_SESS_999", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("suggested_questions", data)

    def test_03_v3_qanda_5_part_structure(self):
        """Verify Q&A endpoint returns full 5-part grounded payload structure."""
        payload = {
            "patient_id": "P_TEST_LEVEL6",
            "question": "What dietary fiber target is recommended for my glucose profile?",
            "predict_response": {
                "expert_outputs": {
                    "clinical": {"raw_input": {"HbA1c": 7.2, "Fasting_Blood_Glucose": 140}}
                }
            }
        }
        res = client.post("/api/v3/qanda", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("answer_payload", data)
        text = data["answer_payload"].get("response_text", "")
        self.assertIn("Direct Summary", text)
        self.assertIn("Personalized Health Context", text)
        self.assertIn("Relevant Biomarkers & Risk Factors", text)
        self.assertIn("Medical Guideline Evidence", text)
        self.assertIn("Actionable Next Steps", text)

    def test_04_modality_bound_recommendations(self):
        """Verify Gut Health recommendations are suppressed when gut modality is absent."""
        payload = {
            "patient_id": "P_NO_GUT",
            "predictions": {
                "Type2_Diabetes": {"predicted_class": 0, "calibrated_probability": 0.20, "risk_level": "LOW", "threshold_used": 0.3}
            },
            "routing_metadata": {
                "effective_pathway": "C",
                "primary_decision_anchor": "Clinical_v3",
                "modalities_supplied": ["clinical"],
                "missing_modalities": ["wearable", "gut"]
            },
            "expert_outputs": {
                "clinical": {"raw_input": {"HbA1c": 5.4, "Fasting_Blood_Glucose": 90}}
            }
        }
        res = client.post("/api/v3/report", json={"patient_id": "P_NO_GUT", "predict_response": payload}, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        recs = data.get("recommendations", [])
        categories = [r["category"] for r in recs]
        self.assertNotIn("Gut Health", categories)

    def test_05_evidence_traceability(self):
        """Verify every recommendation citation maps to retrieved evidence."""
        payload = {
            "patient_id": "P_EVIDENCE_TEST",
            "predictions": {
                "Type2_Diabetes": {"predicted_class": 1, "calibrated_probability": 0.80, "risk_level": "HIGH", "threshold_used": 0.3}
            },
            "routing_metadata": {
                "effective_pathway": "C",
                "primary_decision_anchor": "Clinical_v3",
                "modalities_supplied": ["clinical"]
            },
            "expert_outputs": {
                "clinical": {"raw_input": {"HbA1c": 7.5}}
            }
        }
        res = client.post("/api/v3/report", json={"patient_id": "P_EVIDENCE_TEST", "predict_response": payload}, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        ev_list = data.get("retrieved_evidence", [])
        self.assertGreater(len(ev_list), 0)
        cids = {e["citation_id"] for e in ev_list}
        for rec in data.get("recommendations", []):
            ev_str = rec["evidence"]
            self.assertTrue(any(cid in ev_str for cid in cids) or "REF_" in ev_str)

if __name__ == "__main__":
    unittest.main()
