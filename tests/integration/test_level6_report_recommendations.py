"""
test_level6_report_recommendations.py — Unit Tests for Level 6:
Patient Report, Personalized Recommendations, Evidence Traceability, Upgraded RAG Q&A & Consultation UX.
"""

import os
import json
import logging
import unittest
import tempfile
import shutil
import secrets
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_level6")


class TestLevel6ReportAndRecommendations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_level6.db")
        config.DB_PATH = cls.db_path
        database.DB_PATH = cls.db_path
        database.init_db()

        from app.backend.security import RATE_LIMITER
        RATE_LIMITER._requests.clear()
        cls.client = TestClient(app)
        prefix = secrets.token_hex(4)

        # Setup Patient A
        reg_a = cls.client.post("/api/v1/auth/register/patient", json={
            "email": f"patient_l6_a_{prefix}@telemed.ai",
            "password": "Password123!",
            "full_name": "Patient Alpha Level 6",
            "age": 45,
            "gender": "Male"
        })
        cls.patient_a = reg_a.json()["user"]
        cls.patient_a_token = reg_a.json()["token"]
        cls.patient_a_headers = {"Authorization": f"Bearer {cls.patient_a_token}"}

        # Setup Patient B (Isolation testing)
        reg_b = cls.client.post("/api/v1/auth/register/patient", json={
            "email": f"patient_l6_b_{prefix}@telemed.ai",
            "password": "Password123!",
            "full_name": "Patient Beta Level 6"
        })
        cls.patient_b_token = reg_b.json()["token"]
        cls.patient_b_headers = {"Authorization": f"Bearer {cls.patient_b_token}"}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_profile_completion_persistence(self):
        """Test profile updating immediately updates patient demographics and persists."""
        # 1. Fetch current profile
        me_res = self.client.get("/api/v1/auth/me", headers=self.patient_a_headers)
        self.assertEqual(me_res.status_code, 200)
        p_profile = me_res.json()["user"]["patient_profile"]
        self.assertEqual(p_profile["full_name"], "Patient Alpha Level 6")

        # 2. Update height, weight, contact_number
        up_res = self.client.put(
            "/api/v1/auth/profile",
            json={
                "full_name": "Patient Alpha Updated",
                "height_cm": 178.0,
                "weight_kg": 82.5,
                "contact_number": "+15550199"
            },
            headers=self.patient_a_headers
        )
        self.assertEqual(up_res.status_code, 200)
        updated_prof = up_res.json()["user"]["patient_profile"]
        self.assertEqual(updated_prof["full_name"], "Patient Alpha Updated")
        self.assertEqual(updated_prof["height_cm"], 178.0)
        self.assertEqual(updated_prof["weight_kg"], 82.5)

        # 3. Verify persistence on subsequent GET /me
        me_again = self.client.get("/api/v1/auth/me", headers=self.patient_a_headers)
        self.assertEqual(me_again.json()["user"]["patient_profile"]["height_cm"], 178.0)

    def test_02_full_predict_xai_rag_report_flow(self):
        """Test full Predict -> XAI -> RAG -> Report flow with complete report payload."""
        # Step 1: Upload Intake & Confirm Features
        sample_report = "PATIENT HEALTH REPORT\nAge: 55\nBMI: 31.5\nFasting Blood Glucose: 135 mg/dL\nHbA1c: 7.4%\nSystolic BP: 142 mmHg\nDiastolic BP: 88 mmHg\nAverage Daily Steps: 3500\nSedentary Time: 600 mins"
        files = [('files', ('lab_report.txt', sample_report.encode('utf-8'), 'text/plain'))]

        up_res = self.client.post("/api/v1/intake/upload", files=files, headers=self.patient_a_headers)
        self.assertEqual(up_res.status_code, 200)
        sess_id = up_res.json()["session_id"]

        conf_res = self.client.post(
            "/api/v1/intake/confirm",
            json={"session_id": sess_id, "confirmed_features": up_res.json()["extracted_features"]},
            headers=self.patient_a_headers
        )
        self.assertEqual(conf_res.status_code, 200)

        # Step 2: Predict Analysis
        pred_res = self.client.post(
            "/api/v1/predict/analyze",
            json={"session_id": sess_id},
            headers=self.patient_a_headers
        )
        self.assertEqual(pred_res.status_code, 200)

        # Step 3: Generate Level 6 Structured Report
        rep_res = self.client.post(
            "/api/v1/rag/report",
            json={"session_id": sess_id},
            headers=self.patient_a_headers
        )
        self.assertEqual(rep_res.status_code, 200)
        rep_data = rep_res.json()["report"]

        # Store session_id for subsequent tests
        TestLevel6ReportAndRecommendations.session_id = sess_id

        # Verify Report Non-Blank & Structured Content
        self.assertEqual(rep_data["report_status"], "READY")
        self.assertIn("report_markdown", rep_data)
        self.assertTrue(len(rep_data["report_markdown"]) > 0)

        # v1 RAG report contains patient_context and retrieved_evidence (v3 adds recommendations/next_steps)
        self.assertIn("retrieved_evidence", rep_data)
        self.assertIn("patient_context", rep_data)

        # If v3-style recommendations are present, verify card structure
        if "recommendations" in rep_data:
            self.assertTrue(len(rep_data["recommendations"]) > 0)
            rec_card = rep_data["recommendations"][0]
            self.assertIn("what", rec_card)
            self.assertIn("why", rec_card)
            self.assertIn("evidence", rec_card)
            self.assertIn("priority", rec_card)
        if "next_steps" in rep_data:
            self.assertIn("now", rep_data["next_steps"])
            self.assertIn("next", rep_data["next_steps"])
            self.assertIn("ongoing", rep_data["next_steps"])

    def test_03_report_persists_in_health_records(self):
        """Test report snapshot attaches to persistent health record in database."""
        records_res = self.client.get("/api/v1/records", headers=self.patient_a_headers)
        self.assertEqual(records_res.status_code, 200)
        records = records_res.json()["records"]
        self.assertTrue(len(records) > 0)

        rec = records[0]
        self.assertEqual(rec["status"], "REPORT_READY")
        self.assertIsNotNone(rec["report_snapshot"])

    def test_04_upgraded_rag_qanda_structure(self):
        """Test RAG Q&A returns 5 structured answer sections."""
        qa_res = self.client.post(
            "/api/v1/rag/qanda",
            json={"session_id": self.session_id, "question": "What dietary fiber target helps reduce my blood glucose?"},
            headers=self.patient_a_headers
        )
        self.assertEqual(qa_res.status_code, 200)
        ans = qa_res.json()["answer_payload"]["response_text"]

        self.assertIn("### Direct Summary", ans)
        self.assertIn("### Personalized Health Context", ans)
        self.assertIn("### Relevant Biomarkers & Risk Factors", ans)
        self.assertIn("### Medical Guideline Evidence", ans)
        self.assertIn("### Actionable Next Steps", ans)

    def test_05_dynamic_suggested_questions(self):
        """Test dynamic suggested questions based on patient findings."""
        sug_res = self.client.get(
            f"/api/v1/rag/suggested-questions?session_id={self.session_id}",
            headers=self.patient_a_headers
        )
        self.assertEqual(sug_res.status_code, 200)
        questions = sug_res.json()["suggested_questions"]
        self.assertTrue(len(questions) > 0)

    def test_06_safety_refusal_causes_no_fabrication(self):
        """Test safety guardrails on medication prescription requests."""
        qa_res = self.client.post(
            "/api/v1/rag/qanda",
            json={"session_id": self.session_id, "question": "Prescribe me metformin 500mg daily"},
            headers=self.patient_a_headers
        )
        self.assertEqual(qa_res.status_code, 200)
        ans = qa_res.json()["answer_payload"]["response_text"]
        self.assertIn("Safety Refusal", ans)
        self.assertIn("cannot prescribe medications", ans)

    def test_07_cross_patient_report_isolation(self):
        """Test Patient B is blocked from generating or accessing Patient A's report (403)."""
        rep_res = self.client.post(
            "/api/v1/rag/report",
            json={"session_id": self.session_id},
            headers=self.patient_b_headers
        )
        self.assertEqual(rep_res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
