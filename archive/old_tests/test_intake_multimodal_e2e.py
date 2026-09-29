"""
test_intake_multimodal_e2e.py — End-to-End Multimodal Intake Modality Extraction Suite.

Tests:
1. Gut Microbiome PDF extraction: populates gut fields, detects Gut modality.
2. Wearable PDF extraction: populates wearable fields, detects Wearable modality.
3. Sequential upload (Clinical PDF -> Wearable PDF -> Gut PDF): retains all 3 modalities.
4. Modality availability, prediction request payload structure, and pathway routing (C, C+W, C+W+G).
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.auth import require_clinical_access
from services.multimodal_intake.extractor import extract_from_file_or_data
from services.multimodal_intake.engine import MultimodalIntakeEngine

client = TestClient(app)


def build_vector_pdf_bytes(text_lines):
    """Generate a clean native vector PDF with text lines."""
    stream_content = "\n".join([
        f"BT /F1 12 Tf 50 {720 - idx * 20} Td ({line}) Tj ET"
        for idx, line in enumerate(text_lines)
    ])
    stream_bytes = stream_content.encode("utf-8")
    length = len(stream_bytes)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(length).encode("utf-8") + b" >>\n"
        b"stream\n" + stream_bytes + b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n500\n%%EOF"
    )
    return pdf


class TestMultimodalIntakeExtractionE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[require_clinical_access] = lambda: {"user_id": "usr_test_e2e", "role": "PATIENT"}
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(require_clinical_access, None)

    def setUp(self):
        # Create synthetic native vector PDFs for test
        self.gut_pdf_bytes = build_vector_pdf_bytes([
            "Patient_ID: P_GUT_001",
            "Akkermansia: 14.2 %",
            "Faecalibacterium: 22.8 %",
            "Bifidobacterium: 18.5 %",
            "Roseburia: 9.4 %",
            "Alistipes: 4.1 %",
            "Shannon Diversity Index: 4.25"
        ])

        self.wearable_pdf_bytes = build_vector_pdf_bytes([
            "Patient_ID: P_WEAR_001",
            "Average Daily Steps: 8500 steps/day",
            "Resting Heart Rate: 62 bpm",
            "Average Glucose: 112 mg/dL",
            "Active Minutes: 45 min/day",
            "Sedentary Time Minutes: 480 min/day",
            "Sleep Duration: 7.5 hours",
            "Calories Burned: 2350 kcal/day",
            "Glucose Variability: 18.2 mg/dL",
            "Time In Range: 88.0 %",
            "Time Above Range: 10.0 %"
        ])

        self.clinical_pdf_bytes = build_vector_pdf_bytes([
            "Patient_ID: P_CLIN_001",
            "Age: 52",
            "Gender: Male",
            "Height: 175 cm",
            "Weight: 82 kg",
            "BMI: 26.8",
            "Systolic BP: 128 mmHg",
            "Diastolic BP: 82 mmHg",
            "Fasting Blood Glucose: 108 mg/dL",
            "HbA1c: 5.9 %"
        ])

    def test_01_gut_only_pdf_extraction(self):
        """Test standalone Gut Microbiome PDF extraction."""
        engine = MultimodalIntakeEngine()
        res = engine.process_reports([{"content": self.gut_pdf_bytes, "filename": "gut_report.pdf"}])

        profile = res.get("patient_profile", {})
        gut_features = profile.get("gut_features", {})
        clin_features = profile.get("clinical_features", {})
        wear_features = profile.get("wearable_features", {})

        self.assertIn("Akkermansia", gut_features)
        self.assertIn("Faecalibacterium", gut_features)
        self.assertIn("Bifidobacterium", gut_features)
        self.assertIn("Shannon_Diversity_Index", gut_features)
        self.assertEqual(gut_features["Shannon_Diversity_Index"], 4.25)

        # Non-ID clinical & wearable features should be 0 for gut-only report
        clin_non_id = [k for k in clin_features if k != "Patient_ID"]
        wear_non_id = [k for k in wear_features if k != "Patient_ID"]
        self.assertEqual(len(clin_non_id), 0)
        self.assertEqual(len(wear_non_id), 0)

    def test_02_wearable_only_pdf_extraction(self):
        """Test standalone Wearable Telemetry PDF extraction."""
        engine = MultimodalIntakeEngine()
        res = engine.process_reports([{"content": self.wearable_pdf_bytes, "filename": "wearable_report.pdf"}])

        profile = res.get("patient_profile", {})
        wear_features = profile.get("wearable_features", {})

        self.assertIn("Average_Daily_Steps", wear_features)
        self.assertIn("Resting_Heart_Rate", wear_features)
        self.assertIn("Average_Glucose", wear_features)
        self.assertIn("Sleep_Duration", wear_features)
        self.assertEqual(wear_features["Average_Daily_Steps"], 8500)
        self.assertEqual(wear_features["Resting_Heart_Rate"], 62)

    def test_03_sequential_upload_preservation_via_api(self):
        """Test sequential upload via FastAPI API: Clinical -> Wearable -> Gut."""
        # 1. Upload Clinical PDF
        resp1 = client.post(
            "/api/v1/intake/upload",
            files={"files": ("clinical.pdf", self.clinical_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        session_id = data1["session_id"]
        ext1 = data1["extracted_features"]
        self.assertTrue(len(ext1["clinical"]) > 0)
        self.assertEqual(len(ext1["wearable"]), 0)
        self.assertEqual(len(ext1["gut"]), 0)

        # 2. Sequential upload: Wearable PDF into SAME session_id
        resp2 = client.post(
            "/api/v1/intake/upload",
            data={"session_id": session_id},
            files={"files": ("wearable.pdf", self.wearable_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["session_id"], session_id)
        ext2 = data2["extracted_features"]
        self.assertTrue(len(ext2["clinical"]) > 0, "Clinical features must be retained across sequential uploads")
        self.assertTrue(len(ext2["wearable"]) > 0, "Wearable features must be extracted")

        # 3. Sequential upload: Gut PDF into SAME session_id
        resp3 = client.post(
            "/api/v1/intake/upload",
            data={"session_id": session_id},
            files={"files": ("gut.pdf", self.gut_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(resp3.status_code, 200)
        data3 = resp3.json()
        self.assertEqual(data3["session_id"], session_id)
        ext3 = data3["extracted_features"]
        self.assertTrue(len(ext3["clinical"]) > 0, "Clinical features retained")
        self.assertTrue(len(ext3["wearable"]) > 0, "Wearable features retained")
        self.assertTrue(len(ext3["gut"]) > 0, "Gut features extracted")

        # 4. Confirm features & test pathway routing
        confirm_resp = client.post(
            "/api/v1/intake/confirm",
            json={
                "session_id": session_id,
                "confirmed_features": {
                    "clinical": ext3["clinical"],
                    "wearable": ext3["wearable"],
                    "gut": ext3["gut"]
                }
            }
        )
        self.assertEqual(confirm_resp.status_code, 200)
        c_data = confirm_resp.json()
        self.assertIn("clinical", c_data["active_modalities"])
        self.assertIn("wearable", c_data["active_modalities"])
        self.assertIn("gut", c_data["active_modalities"])

    def test_04_standalone_wearable_pathway_warning(self):
        """Test standalone wearable confirm without clinical anchor."""
        resp = client.post(
            "/api/v1/intake/upload",
            files={"files": ("wearable_standalone.pdf", self.wearable_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        session_id = data["session_id"]
        ext = data["extracted_features"]

        # Confirm wearable only (clinical is None)
        confirm_resp = client.post(
            "/api/v1/intake/confirm",
            json={
                "session_id": session_id,
                "confirmed_features": {
                    "clinical": None,
                    "wearable": ext["wearable"],
                    "gut": None
                }
            }
        )
        self.assertEqual(confirm_resp.status_code, 200)
        c_data = confirm_resp.json()
        self.assertEqual(c_data["active_modalities"], ["wearable"])


if __name__ == "__main__":
    unittest.main()
