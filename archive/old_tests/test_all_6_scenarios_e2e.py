"""
test_all_6_scenarios_e2e.py — Comprehensive End-to-End Verification across all 6 Modality Scenarios.

Verifies:
1. GUT-ONLY: Upload -> Quality -> confirmed_features (clinical: null) -> /predict blocked with 400
2. WEARABLE-ONLY: Upload -> Quality -> confirmed_features (clinical: null) -> /predict blocked with 400
3. C+G: Upload -> Quality -> confirmed_features -> /predict returns Pathway C+G
4. C+W: Upload -> Quality -> confirmed_features -> /predict returns Pathway C+W
5. W+G: Upload -> Quality -> confirmed_features -> /predict returns Pathway W+G
6. C+W+G: Upload -> Quality -> confirmed_features -> /predict returns Pathway C+W+G
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

# Login patient
reg = client.post("/api/v1/auth/register/patient", json={
    "email": "e2e_6scenarios_patient@telemed.ai", "password": "Password123!", "full_name": "E2E 6 Scenarios Patient"
})
if reg.status_code == 201:
    token = reg.json()["token"]
else:
    login = client.post("/api/v1/auth/login", json={
        "email": "e2e_6scenarios_patient@telemed.ai", "password": "Password123!"
    })
    token = login.json()["token"]

headers = {"Authorization": f"Bearer {token}"}

gut_pdf = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_gut_microbiome.pdf")
wear_pdf = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_wearable.pdf")
clin_pdf = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_clinical.pdf")


class TestAll6Scenarios(unittest.TestCase):

    def test_01_gut_only(self):
        with open(gut_pdf, "rb") as f:
            res = client.post("/api/v1/intake/upload", files=[("files", (gut_pdf.name, f, "application/pdf"))], headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        dq = data["data_quality_scores"]["score_breakdown"]
        cov = dq["coverage"]

        self.assertTrue(cov["gut"])
        self.assertFalse(cov["clinical"])
        self.assertFalse(cov["wearable"])
        self.assertEqual(dq["multimodal_coverage_pct"], 33.3)

        # /predict request with gut only MUST be blocked with 400
        pred_req = {
            "patient_id": "P_TEST_101",
            "clinical_data": None,
            "wearable_data": None,
            "gut_data": data["extracted_features"]["gut"]
        }
        res_p = client.post("/api/v3/predict", json=pred_req, headers=headers)
        self.assertEqual(res_p.status_code, 400)
        self.assertIn("Clinical anchor", str(res_p.json()))

    def test_02_wearable_only(self):
        with open(wear_pdf, "rb") as f:
            res = client.post("/api/v1/intake/upload", files=[("files", (wear_pdf.name, f, "application/pdf"))], headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        dq = data["data_quality_scores"]["score_breakdown"]
        cov = dq["coverage"]

        self.assertTrue(cov["wearable"])
        self.assertFalse(cov["clinical"])
        self.assertFalse(cov["gut"])
        self.assertEqual(dq["multimodal_coverage_pct"], 33.3)

        pred_req = {
            "patient_id": "P_TEST_101",
            "clinical_data": None,
            "wearable_data": data["extracted_features"]["wearable"],
            "gut_data": None
        }
        res_p = client.post("/api/v3/predict", json=pred_req, headers=headers)
        self.assertEqual(res_p.status_code, 400)
        self.assertIn("Clinical anchor", str(res_p.json()))

    def test_03_clinical_plus_gut(self):
        with open(clin_pdf, "rb") as fc, open(gut_pdf, "rb") as fg:
            res = client.post("/api/v1/intake/upload", files=[
                ("files", (clin_pdf.name, fc, "application/pdf")),
                ("files", (gut_pdf.name, fg, "application/pdf"))
            ], headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        dq = data["data_quality_scores"]["score_breakdown"]
        cov = dq["coverage"]

        self.assertTrue(cov["clinical"])
        self.assertTrue(cov["gut"])
        self.assertEqual(dq["multimodal_coverage_pct"], 66.7)

        pred_req = {
            "patient_id": "P_TEST_101",
            "clinical_data": data["extracted_features"]["clinical"],
            "wearable_data": None,
            "gut_data": data["extracted_features"]["gut"]
        }
        res_p = client.post("/api/v3/predict", json=pred_req, headers=headers)
        self.assertEqual(res_p.status_code, 200, res_p.text)
        self.assertEqual(res_p.json()["effective_pathway"], "C+G")

    def test_04_clinical_plus_wearable(self):
        with open(clin_pdf, "rb") as fc, open(wear_pdf, "rb") as fw:
            res = client.post("/api/v1/intake/upload", files=[
                ("files", (clin_pdf.name, fc, "application/pdf")),
                ("files", (wear_pdf.name, fw, "application/pdf"))
            ], headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        dq = data["data_quality_scores"]["score_breakdown"]
        cov = dq["coverage"]

        self.assertTrue(cov["clinical"])
        self.assertTrue(cov["wearable"])
        self.assertEqual(dq["multimodal_coverage_pct"], 66.7)

        pred_req = {
            "patient_id": "P_TEST_101",
            "clinical_data": data["extracted_features"]["clinical"],
            "wearable_data": data["extracted_features"]["wearable"],
            "gut_data": None
        }
        res_p = client.post("/api/v3/predict", json=pred_req, headers=headers)
        self.assertEqual(res_p.status_code, 200, res_p.text)
        self.assertEqual(res_p.json()["effective_pathway"], "C+W")

    def test_05_wearable_plus_gut(self):
        with open(wear_pdf, "rb") as fw, open(gut_pdf, "rb") as fg:
            res = client.post("/api/v1/intake/upload", files=[
                ("files", (wear_pdf.name, fw, "application/pdf")),
                ("files", (gut_pdf.name, fg, "application/pdf"))
            ], headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        dq = data["data_quality_scores"]["score_breakdown"]
        cov = dq["coverage"]

        self.assertTrue(cov["wearable"])
        self.assertTrue(cov["gut"])
        self.assertFalse(cov["clinical"])
        self.assertEqual(dq["multimodal_coverage_pct"], 66.7)

        pred_req = {
            "patient_id": "P_TEST_101",
            "clinical_data": None,
            "wearable_data": data["extracted_features"]["wearable"],
            "gut_data": data["extracted_features"]["gut"]
        }
        res_p = client.post("/api/v3/predict", json=pred_req, headers=headers)
        self.assertEqual(res_p.status_code, 200, res_p.text)
        self.assertEqual(res_p.json()["effective_pathway"], "W+G")

    def test_06_trimodal_clinical_wearable_gut(self):
        with open(clin_pdf, "rb") as fc, open(wear_pdf, "rb") as fw, open(gut_pdf, "rb") as fg:
            res = client.post("/api/v1/intake/upload", files=[
                ("files", (clin_pdf.name, fc, "application/pdf")),
                ("files", (wear_pdf.name, fw, "application/pdf")),
                ("files", (gut_pdf.name, fg, "application/pdf"))
            ], headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        dq = data["data_quality_scores"]["score_breakdown"]
        cov = dq["coverage"]

        self.assertTrue(cov["clinical"])
        self.assertTrue(cov["wearable"])
        self.assertTrue(cov["gut"])
        self.assertEqual(dq["multimodal_coverage_pct"], 100.0)

        pred_req = {
            "patient_id": "P_TEST_101",
            "clinical_data": data["extracted_features"]["clinical"],
            "wearable_data": data["extracted_features"]["wearable"],
            "gut_data": data["extracted_features"]["gut"]
        }
        res_p = client.post("/api/v3/predict", json=pred_req, headers=headers)
        self.assertEqual(res_p.status_code, 200, res_p.text)
        self.assertEqual(res_p.json()["effective_pathway"], "C+W+G")


if __name__ == "__main__":
    unittest.main()
