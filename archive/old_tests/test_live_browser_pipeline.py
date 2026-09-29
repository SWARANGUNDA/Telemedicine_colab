"""
test_live_browser_pipeline.py — Live Browser-Equivalent API Contract & Pathway Routing Integration Test.

Simulates exact browser frontend HTTP requests sent by IntakePage.jsx & App.jsx across:
1. Clinical Only (Pathway C)
2. Clinical + Wearable (Pathway C+W)
3. Wearable + Gut (Pathway W+G)
4. Clinical + Wearable + Gut (Pathway C+W+G)
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.backend.main import app

client = TestClient(app)

# Register & Login Test Patient
reg = client.post("/api/v1/auth/register/patient", json={
    "email": "browser_e2e_patient@telemed.ai", "password": "Password123!", "full_name": "Browser E2E Patient"
})
if reg.status_code == 201:
    token = reg.json()["token"]
else:
    login = client.post("/api/v1/auth/login", json={
        "email": "browser_e2e_patient@telemed.ai", "password": "Password123!"
    })
    token = login.json()["token"]

client.headers.update({"Authorization": f"Bearer {token}"})

PDF_DIR = Path("TeleMed_5_Patient_Sets_15_PDFs")


class TestLiveBrowserPipeline(unittest.TestCase):

    def test_01_clinical_only_c_pathway(self):
        """Browser flow for Clinical PDF alone -> Pathway C."""
        clin_file = PDF_DIR / "P_TEST_101_clinical.pdf"
        with open(clin_file, "rb") as f:
            b_c = f.read()

        # Step 1: Upload
        r_up = client.post("/api/v1/intake/upload", files={"files": (clin_file.name, b_c, "application/pdf")})
        self.assertEqual(r_up.status_code, 200)
        sid = r_up.json()["session_id"]
        ext = r_up.json()["extracted_features"]
        self.assertGreaterEqual(len(ext["clinical"]), 10)

        # Step 2: Confirm
        r_conf = client.post("/api/v1/intake/confirm", json={
            "session_id": sid,
            "confirmed_features": {"clinical": ext["clinical"], "wearable": None, "gut": None}
        })
        self.assertEqual(r_conf.status_code, 200)
        self.assertEqual(r_conf.json()["active_modalities"], ["clinical"])

        # Step 3: Analyze V1
        r_an = client.post("/api/v1/predict/analyze", json={"session_id": sid})
        self.assertEqual(r_an.status_code, 200)
        self.assertEqual(r_an.json()["pathway_used"], "C")

        # Step 4: Predict V3
        r_v3 = client.post("/api/v3/predict", json={
            "patient_id": "P_TEST_101",
            "clinical_data": ext["clinical"], "wearable_data": None, "gut_data": None
        })
        self.assertEqual(r_v3.status_code, 200)
        pathway = r_v3.json()["routing_metadata"]["effective_pathway"]
        self.assertEqual(pathway, "C")

    def test_02_clinical_plus_wearable_cw_pathway(self):
        """Browser flow for Clinical + Wearable sequential upload -> Pathway C+W."""
        clin_file = PDF_DIR / "P_TEST_101_clinical.pdf"
        wear_file = PDF_DIR / "P_TEST_101_wearable.pdf"

        with open(clin_file, "rb") as f:
            b_c = f.read()
        with open(wear_file, "rb") as f:
            b_w = f.read()

        # 1. Upload Clinical
        r_up1 = client.post("/api/v1/intake/upload", files={"files": (clin_file.name, b_c, "application/pdf")})
        sid = r_up1.json()["session_id"]

        # 2. Upload Wearable into SAME session
        r_up2 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (wear_file.name, b_w, "application/pdf")})
        ext = r_up2.json()["extracted_features"]
        self.assertGreaterEqual(len(ext["clinical"]), 10)
        self.assertGreaterEqual(len(ext["wearable"]), 8)

        # 3. Confirm
        r_conf = client.post("/api/v1/intake/confirm", json={
            "session_id": sid,
            "confirmed_features": {"clinical": ext["clinical"], "wearable": ext["wearable"], "gut": None}
        })
        self.assertEqual(r_conf.status_code, 200)
        self.assertEqual(set(r_conf.json()["active_modalities"]), {"clinical", "wearable"})

        # 4. Analyze V1
        r_an = client.post("/api/v1/predict/analyze", json={"session_id": sid})
        self.assertEqual(r_an.status_code, 200)
        self.assertEqual(r_an.json()["pathway_used"], "C+W")

        # 5. Predict V3
        r_v3 = client.post("/api/v3/predict", json={
            "patient_id": "P_TEST_101",
            "clinical_data": ext["clinical"], "wearable_data": ext["wearable"], "gut_data": None
        })
        self.assertEqual(r_v3.status_code, 200)
        pathway = r_v3.json()["routing_metadata"]["effective_pathway"]
        self.assertEqual(pathway, "C+W")

    def test_03_wearable_plus_gut_wg_pathway(self):
        """Browser flow for Wearable + Gut sequential upload without Clinical -> Pathway W+G."""
        wear_file = PDF_DIR / "P_TEST_101_wearable.pdf"
        gut_file = PDF_DIR / "P_TEST_101_gut_microbiome.pdf"

        with open(wear_file, "rb") as f:
            b_w = f.read()
        with open(gut_file, "rb") as f:
            b_g = f.read()

        # 1. Upload Wearable
        r_up1 = client.post("/api/v1/intake/upload", files={"files": (wear_file.name, b_w, "application/pdf")})
        sid = r_up1.json()["session_id"]

        # 2. Upload Gut into SAME session
        r_up2 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (gut_file.name, b_g, "application/pdf")})
        ext = r_up2.json()["extracted_features"]
        self.assertGreaterEqual(len(ext["wearable"]), 8)
        self.assertGreaterEqual(len(ext["gut"]), 8)

        # 3. Confirm
        r_conf = client.post("/api/v1/intake/confirm", json={
            "session_id": sid,
            "confirmed_features": {"clinical": None, "wearable": ext["wearable"], "gut": ext["gut"]}
        })
        self.assertEqual(r_conf.status_code, 200)
        self.assertEqual(set(r_conf.json()["active_modalities"]), {"wearable", "gut"})

        # 4. Analyze V1
        r_an = client.post("/api/v1/predict/analyze", json={"session_id": sid})
        self.assertEqual(r_an.status_code, 200)
        self.assertEqual(r_an.json()["pathway_used"], "W+G")

        # 5. Predict V3
        r_v3 = client.post("/api/v3/predict", json={
            "patient_id": "P_TEST_101",
            "clinical_data": None, "wearable_data": ext["wearable"], "gut_data": ext["gut"]
        })
        self.assertEqual(r_v3.status_code, 200)
        pathway = r_v3.json()["routing_metadata"]["effective_pathway"]
        self.assertEqual(pathway, "W+G")

    def test_04_tri_modal_cwg_pathway(self):
        """Browser flow for Clinical + Wearable + Gut sequential upload -> Pathway C+W+G."""
        clin_file = PDF_DIR / "P_TEST_101_clinical.pdf"
        wear_file = PDF_DIR / "P_TEST_101_wearable.pdf"
        gut_file = PDF_DIR / "P_TEST_101_gut_microbiome.pdf"

        with open(clin_file, "rb") as f:
            b_c = f.read()
        with open(wear_file, "rb") as f:
            b_w = f.read()
        with open(gut_file, "rb") as f:
            b_g = f.read()

        r_up1 = client.post("/api/v1/intake/upload", files={"files": (clin_file.name, b_c, "application/pdf")})
        sid = r_up1.json()["session_id"]
        r_up2 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (wear_file.name, b_w, "application/pdf")})
        r_up3 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (gut_file.name, b_g, "application/pdf")})
        ext = r_up3.json()["extracted_features"]

        r_conf = client.post("/api/v1/intake/confirm", json={
            "session_id": sid,
            "confirmed_features": {"clinical": ext["clinical"], "wearable": ext["wearable"], "gut": ext["gut"]}
        })
        self.assertEqual(r_conf.status_code, 200)
        self.assertEqual(set(r_conf.json()["active_modalities"]), {"clinical", "wearable", "gut"})

        r_an = client.post("/api/v1/predict/analyze", json={"session_id": sid})
        self.assertEqual(r_an.status_code, 200)
        self.assertEqual(r_an.json()["pathway_used"], "C+W+G")

        r_v3 = client.post("/api/v3/predict", json={
            "patient_id": "P_TEST_101",
            "clinical_data": ext["clinical"], "wearable_data": ext["wearable"], "gut_data": ext["gut"]
        })
        self.assertEqual(r_v3.status_code, 200)
        pathway = r_v3.json()["routing_metadata"]["effective_pathway"]
        self.assertEqual(pathway, "C+W+G")


if __name__ == "__main__":
    unittest.main()
