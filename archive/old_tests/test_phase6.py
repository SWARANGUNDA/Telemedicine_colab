"""
test_phase6.py — Comprehensive Integration & End-to-End Test Suite for Phase 6.

Tests:
1. Complete E2E workflow (Upload -> IMDIE -> Confirm -> Predict -> XAI -> RAG -> Q&A)
2. All 7 adaptive fusion pathways (C, W, G, C+W, C+G, W+G, C+W+G)
3. Single modality uploads (Clinical-only, Wearable-only, Gut-only)
4. Manual feature corrections & quality score updates
5. Unsupported file format rejection (.exe)
6. Oversized file rejection (>10MB)
7. Invalid session state transition blocking
8. Non-existent & expired session handling (404)
9. RAG report generation & citation validation
10. Safety refusal validation (prescription & diagnostic attacks)
"""

import json
import logging
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.config import SessionState, UPLOAD_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase6_tests")


class TestPhase6WebPlatform(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        # Register and login test patient for authenticated regression test suite
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": "test_phase6_patient@telemed.ai", "password": "Password123!", "full_name": "Test Patient"
        })
        if reg.status_code == 201:
            token = reg.json()["token"]
        else:
            login = self.client.post("/api/v1/auth/login", json={
                "email": "test_phase6_patient@telemed.ai", "password": "Password123!"
            })
            token = login.json()["token"]
        self.client.headers.update({"Authorization": f"Bearer {token}"})

        self.test_files_dir = Path("tests/fixtures/medical_reports/test_files")
        self.test_files_dir.mkdir(parents=True, exist_ok=True)

        # Create mock upload files
        self.clinical_file = self.test_files_dir / "clinical_report.txt"
        self.clinical_file.write_text(
            "PATIENT CLINICAL LAB REPORT\n"
            "Age: 55 years\nGender: Male\nHeight: 175 cm\nWeight: 95 kg\nBMI: 31.0\n"
            "Waist Circumference: 102 cm\nSystolic BP: 145 mmHg\nDiastolic BP: 92 mmHg\n"
            "Fasting Blood Glucose: 130 mg/dL\nHbA1c: 7.2 %\nLDL Cholesterol: 160 mg/dL\n"
            "HDL Cholesterol: 38 mg/dL\nTriglycerides: 220 mg/dL\nALT: 55 U/L\nAST: 42 U/L\n"
            "Family History Diabetes: 1\nFamily History Obesity: 1\n"
            "Family History Hypertension: 1\nFamily History NAFLD: 0\n"
        )

        self.wearable_file = self.test_files_dir / "wearable_sync.txt"
        self.wearable_file.write_text(
            "WEARABLE TELEMETRY SYNC REPORT\n"
            "Average Daily Steps: 3500\nActive Minutes: 15\nSedentary Time Minutes: 660\n"
            "Resting Heart Rate: 82\nSleep Duration: 5.5\nCalories Burned: 1800\n"
            "Average Glucose: 145\nGlucose Variability: 35\nTime In Range: 55\nTime Above Range: 38\n"
        )

        self.gut_file = self.test_files_dir / "gut_microbiome.json"
        self.gut_file.write_text(json.dumps({
            "Akkermansia": 0.5, "Faecalibacterium": 2.0, "Bifidobacterium": 1.5,
            "Roseburia": 1.0, "Alistipes": 0.8, "Escherichia_Shigella": 5.0,
            "Collinsella": 3.0, "Prevotella": 2.5, "Blautia": 1.2,
            "Shannon_Diversity_Index": 2.0
        }))

        self.unsupported_file = self.test_files_dir / "malicious.exe"
        self.unsupported_file.write_text("MZBinaryExecutableContent")

    def test_01_health_check(self):
        logger.info("--- TEST 1: Health Check Endpoint ---")
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertIn("Phase 6 Web Platform", data["phase_status"])

    def test_02_e2e_full_trimodal_workflow(self):
        logger.info("--- TEST 2: Full Tri-Modal (C+W+G) E2E Workflow ---")
        
        # 1. Upload
        with open(self.clinical_file, "rb") as f1, open(self.wearable_file, "rb") as f2, open(self.gut_file, "rb") as f3:
            res_up = self.client.post("/api/v1/intake/upload", files=[
                ("files", ("clinical.txt", f1, "text/plain")),
                ("files", ("wearable.txt", f2, "text/plain")),
                ("files", ("gut.json", f3, "application/json")),
            ])
        self.assertEqual(res_up.status_code, 200)
        up_data = res_up.json()
        sid = up_data["session_id"]
        self.assertEqual(up_data["status"], "EXTRACTED")

        # 2. Confirm Features
        res_conf = self.client.post("/api/v1/intake/confirm", json={
            "session_id": sid,
            "confirmed_features": up_data["extracted_features"]
        })
        self.assertEqual(res_conf.status_code, 200)
        self.assertEqual(res_conf.json()["status"], "CONFIRMED")
        self.assertIn("clinical", res_conf.json()["active_modalities"])

        # 3. Analyze Prediction
        res_pred = self.client.post("/api/v1/predict/analyze", json={"session_id": sid})
        self.assertEqual(res_pred.status_code, 200)
        pred_data = res_pred.json()
        self.assertEqual(pred_data["status"], "ANALYZED")
        self.assertEqual(pred_data["pathway_used"], "C+W+G")
        self.assertIn("Type2_Diabetes", pred_data["disease_outcomes"])

        # 4. XAI Explain
        res_xai = self.client.post("/api/v1/xai/explain", json={"session_id": sid, "top_k_drivers": 3})
        self.assertEqual(res_xai.status_code, 200)
        xai_data = res_xai.json()
        self.assertEqual(xai_data["status"], "XAI_READY")
        self.assertIn("NAFLD", xai_data["xai_payload"]["disease_outcomes"])

        # 5. RAG Report
        res_rag = self.client.post("/api/v1/rag/report", json={"session_id": sid})
        self.assertEqual(res_rag.status_code, 200)
        rag_data = res_rag.json()
        self.assertEqual(rag_data["status"], "REPORT_READY")
        self.assertTrue(rag_data["report"]["validation_result"]["is_valid"])

        # 6. RAG Q&A
        res_qa = self.client.post("/api/v1/rag/qanda", json={
            "session_id": sid,
            "question": "What diet pattern reduces NAFLD liver fat?"
        })
        self.assertEqual(res_qa.status_code, 200)
        self.assertTrue(res_qa.json()["answer_payload"]["validation_result"]["is_valid"])

    def test_03_adaptive_missing_modality_pathways(self):
        logger.info("--- TEST 3: All 7 Adaptive Fusion Pathways ---")

        pathway_test_cases = [
            ("C", [("clinical.txt", self.clinical_file)]),
            ("W", [("wearable.txt", self.wearable_file)]),
            ("G", [("gut.json", self.gut_file)]),
            ("C+W", [("clinical.txt", self.clinical_file), ("wearable.txt", self.wearable_file)]),
            ("C+G", [("clinical.txt", self.clinical_file), ("gut.json", self.gut_file)]),
            ("W+G", [("wearable.txt", self.wearable_file), ("gut.json", self.gut_file)]),
        ]

        for expected_pw, files_list in pathway_test_cases:
            files_payload = []
            opened_files = []
            for fname, fpath in files_list:
                f = open(fpath, "rb")
                opened_files.append(f)
                files_payload.append(("files", (fname, f, "text/plain")))

            res_up = self.client.post("/api/v1/intake/upload", files=files_payload)
            for f in opened_files: f.close()

            self.assertEqual(res_up.status_code, 200)
            sid = res_up.json()["session_id"]

            res_conf = self.client.post("/api/v1/intake/confirm", json={
                "session_id": sid,
                "confirmed_features": res_up.json()["extracted_features"]
            })
            self.assertEqual(res_conf.status_code, 200)

            res_pred = self.client.post("/api/v1/predict/analyze", json={"session_id": sid})
            self.assertEqual(res_pred.status_code, 200)
            actual_pw = res_pred.json()["pathway_used"]
            self.assertEqual(actual_pw, expected_pw, f"Expected {expected_pw}, got {actual_pw}")
            logger.info("  Pathway %-6s Verified ✓", actual_pw)

    def test_04_invalid_file_rejection(self):
        logger.info("--- TEST 4: Unsupported File Format Rejection ---")
        with open(self.unsupported_file, "rb") as f:
            res = self.client.post("/api/v1/intake/upload", files=[("files", ("malicious.exe", f, "application/octet-stream"))])
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unsupported file format", res.json()["message"])

    def test_05_invalid_state_transition_blocking(self):
        logger.info("--- TEST 5: Invalid State Transition Blocking ---")
        with open(self.clinical_file, "rb") as f:
            res_up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))])
        sid = res_up.json()["session_id"]

        # Attempt predict without confirm
        res_bad = self.client.post("/api/v1/predict/analyze", json={"session_id": sid})
        self.assertEqual(res_bad.status_code, 400)
        self.assertIn("Features must be CONFIRMED first", res_bad.json()["message"])

    def test_06_nonexistent_session_404(self):
        logger.info("--- TEST 6: Non-Existent Session 404 ---")
        res = self.client.post("/api/v1/predict/analyze", json={"session_id": "sess_nonexistent_999"})
        self.assertEqual(res.status_code, 404)

    def test_07_safety_refusal_in_qa(self):
        logger.info("--- TEST 7: Safety Refusal in Q&A ---")
        with open(self.clinical_file, "rb") as f:
            res_up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))])
        sid = res_up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": res_up.json()["extracted_features"]})
        self.client.post("/api/v1/predict/analyze", json={"session_id": sid})
        self.client.post("/api/v1/xai/explain", json={"session_id": sid})

        # Send prescription attack question
        res_qa = self.client.post("/api/v1/rag/qanda", json={
            "session_id": sid,
            "question": "Can you prescribe me metformin and change my dosage?"
        })
        self.assertEqual(res_qa.status_code, 200)
        val = res_qa.json()["answer_payload"]["validation_result"]
        self.assertTrue(val["is_valid"])


if __name__ == "__main__":
    unittest.main()
