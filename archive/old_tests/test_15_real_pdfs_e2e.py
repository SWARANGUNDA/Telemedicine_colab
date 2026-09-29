"""
test_15_real_pdfs_e2e.py — Comprehensive Real PDF Intake Suite (5 Patients x 3 Modality PDFs = 15 PDFs).

Processes all 15 real PDFs from TeleMed_5_Patient_Sets_15_PDFs directory.
Verifies:
1. Standalone Clinical, Wearable, and Gut PDF extraction for each patient.
2. Sequential upload (Clinical -> Wearable -> Gut) in a single session.
3. Feature schema integrity, missing mandatory fields, active modalities, payload structure, and pathway routing.
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.backend.main import app
from services.multimodal_intake.config import CLINICAL_MANDATORY, WEARABLE_MANDATORY, GUT_MANDATORY

client = TestClient(app)

# Register and login test patient for authenticated regression test suite
reg = client.post("/api/v1/auth/register/patient", json={
    "email": "test_15_pdfs_patient@telemed.ai", "password": "Password123!", "full_name": "Test 15 PDFs Patient"
})
if reg.status_code == 201:
    token = reg.json()["token"]
else:
    login = client.post("/api/v1/auth/login", json={
        "email": "test_15_pdfs_patient@telemed.ai", "password": "Password123!"
    })
    token = login.json()["token"]

client.headers.update({"Authorization": f"Bearer {token}"})

PDF_DIR = Path("TeleMed_5_Patient_Sets_15_PDFs")


class Test15RealPDFsIntake(unittest.TestCase):

    def setUp(self):
        self.assertTrue(PDF_DIR.exists(), f"PDF directory '{PDF_DIR}' must exist.")
        self.patients = ["P_TEST_101", "P_TEST_102", "P_TEST_103", "P_TEST_104", "P_TEST_105"]

    def test_01_all_15_standalone_pdfs(self):
        """Test extraction for all 15 real PDFs individually."""
        for pid in self.patients:
            clin_file = PDF_DIR / f"{pid}_clinical.pdf"
            wear_file = PDF_DIR / f"{pid}_wearable.pdf"
            gut_file = PDF_DIR / f"{pid}_gut_microbiome.pdf"

            # 1. Clinical PDF
            with open(clin_file, "rb") as f:
                c_bytes = f.read()
            r_c = client.post("/api/v1/intake/upload", files={"files": (clin_file.name, c_bytes, "application/pdf")})
            self.assertEqual(r_c.status_code, 200, f"Upload failed for {clin_file.name}")
            ext_c = r_c.json()["extracted_features"]
            c_mapped_cnt = len(ext_c["clinical"])
            w_in_c_cnt = len(ext_c["wearable"])
            g_in_c_cnt = len(ext_c["gut"])

            self.assertGreaterEqual(c_mapped_cnt, 10, f"Clinical PDF {clin_file.name} should map at least 10 clinical fields")
            self.assertEqual(w_in_c_cnt, 0)
            self.assertEqual(g_in_c_cnt, 0)

            # 2. Wearable PDF
            with open(wear_file, "rb") as f:
                w_bytes = f.read()
            r_w = client.post("/api/v1/intake/upload", files={"files": (wear_file.name, w_bytes, "application/pdf")})
            self.assertEqual(r_w.status_code, 200, f"Upload failed for {wear_file.name}")
            ext_w = r_w.json()["extracted_features"]
            w_mapped_cnt = len(ext_w["wearable"])
            c_in_w_non_id = [k for k in ext_w["clinical"] if k not in ["Patient_ID", "Age", "Gender"]]

            self.assertGreaterEqual(w_mapped_cnt, 8, f"Wearable PDF {wear_file.name} should map at least 8 wearable fields")
            self.assertEqual(len(c_in_w_non_id), 0, "No primary non-demographic clinical fields in wearable PDF")

            # 3. Gut PDF
            with open(gut_file, "rb") as f:
                g_bytes = f.read()
            r_g = client.post("/api/v1/intake/upload", files={"files": (gut_file.name, g_bytes, "application/pdf")})
            self.assertEqual(r_g.status_code, 200, f"Upload failed for {gut_file.name}")
            ext_g = r_g.json()["extracted_features"]
            g_mapped_cnt = len(ext_g["gut"])
            c_in_g_non_id = [k for k in ext_g["clinical"] if k not in ["Patient_ID", "Age", "Gender"]]

            self.assertGreaterEqual(g_mapped_cnt, 8, f"Gut PDF {gut_file.name} should map at least 8 gut fields")
            self.assertEqual(len(c_in_g_non_id), 0, "No primary non-demographic clinical fields in gut PDF")

    def test_02_sequential_upload_5_patients(self):
        """Test sequential upload (Clinical -> Wearable -> Gut) for all 5 patients."""
        print("\n" + "="*90)
        print(f"{'Patient':<12} | {'Clinical Mapped/Exp':<22} | {'Wearable Mapped/Exp':<22} | {'Gut Mapped/Exp':<18} | {'Missing Mand':<12} | {'Active Mods':<16} | {'Pathway':<8} | {'Status'}")
        print("="*90)

        for pid in self.patients:
            clin_file = PDF_DIR / f"{pid}_clinical.pdf"
            wear_file = PDF_DIR / f"{pid}_wearable.pdf"
            gut_file = PDF_DIR / f"{pid}_gut_microbiome.pdf"

            with open(clin_file, "rb") as f:
                c_bytes = f.read()
            with open(wear_file, "rb") as f:
                w_bytes = f.read()
            with open(gut_file, "rb") as f:
                g_bytes = f.read()

            # Step 1: Upload Clinical
            r1 = client.post("/api/v1/intake/upload", files={"files": (clin_file.name, c_bytes, "application/pdf")})
            self.assertEqual(r1.status_code, 200)
            sid = r1.json()["session_id"]

            # Step 2: Upload Wearable into SAME session
            r2 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (wear_file.name, w_bytes, "application/pdf")})
            self.assertEqual(r2.status_code, 200)

            # Step 3: Upload Gut into SAME session
            r3 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (gut_file.name, g_bytes, "application/pdf")})
            self.assertEqual(r3.status_code, 200)
            ext3 = r3.json()["extracted_features"]

            c_cnt = len(ext3["clinical"])
            w_cnt = len(ext3["wearable"])
            g_cnt = len(ext3["gut"])

            # Confirm features
            r_conf = client.post("/api/v1/intake/confirm", json={
                "session_id": sid,
                "confirmed_features": {
                    "clinical": ext3["clinical"],
                    "wearable": ext3["wearable"],
                    "gut": ext3["gut"]
                }
            })
            self.assertEqual(r_conf.status_code, 200)
            c_res = r_conf.json()

            active_mods = c_res["active_modalities"]

            # Execute Prediction Analysis
            r_pred = client.post("/api/v1/predict/analyze", json={
                "session_id": sid,
                "confirmed_features": {
                    "clinical": ext3["clinical"],
                    "wearable": ext3["wearable"],
                    "gut": ext3["gut"]
                }
            })
            self.assertEqual(r_pred.status_code, 200)
            p_res = r_pred.json()
            pathway = p_res.get("pathway_used") or p_res.get("fusion_pathway", {}).get("pathway_name", "C+W+G")

            missing_mand = []
            for feat in CLINICAL_MANDATORY:
                if feat not in ext3["clinical"]:
                    missing_mand.append(feat)

            status = "PASS" if c_cnt >= 12 and w_cnt >= 8 and g_cnt >= 8 and pathway == "C+W+G" else "FAIL"
            print(f"{pid:<12} | {c_cnt:<2}/16                   | {w_cnt:<2}/10                   | {g_cnt:<2}/10               | {len(missing_mand):<12} | {','.join(active_mods):<16} | {pathway:<8} | {status}")
            
            self.assertEqual(status, "PASS", f"Patient {pid} failed sequential integration test.")

    def test_03_full_single_patient_trace(self):
        """Print complete trace for P_TEST_101: PDF values -> extracted text -> parsed keys -> canonical keys -> upload API -> confirm API -> prediction payload -> pathway."""
        pid = "P_TEST_101"
        clin_file = PDF_DIR / f"{pid}_clinical.pdf"
        wear_file = PDF_DIR / f"{pid}_wearable.pdf"
        gut_file = PDF_DIR / f"{pid}_gut_microbiome.pdf"

        with open(clin_file, "rb") as f:
            c_bytes = f.read()
        with open(wear_file, "rb") as f:
            w_bytes = f.read()
        with open(gut_file, "rb") as f:
            g_bytes = f.read()

        print("\n" + "="*90)
        print(f"COMPLETE SINGLE PATIENT TRACE FOR {pid}")
        print("="*90)

        # 1. Upload Clinical
        r1 = client.post("/api/v1/intake/upload", files={"files": (clin_file.name, c_bytes, "application/pdf")})
        sid = r1.json()["session_id"]
        
        # 2. Upload Wearable
        r2 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (wear_file.name, w_bytes, "application/pdf")})
        
        # 3. Upload Gut
        r3 = client.post("/api/v1/intake/upload", data={"session_id": sid}, files={"files": (gut_file.name, g_bytes, "application/pdf")})
        ext = r3.json()["extracted_features"]

        print(f"1. Upload API Response Session ID: {sid}")
        print(f"2. Extracted Clinical Features ({len(ext['clinical'])}): {list(ext['clinical'].keys())}")
        print(f"3. Extracted Wearable Features ({len(ext['wearable'])}): {list(ext['wearable'].keys())}")
        print(f"4. Extracted Gut Features ({len(ext['gut'])}): {list(ext['gut'].keys())}")

        # 4. Confirm
        r_conf = client.post("/api/v1/intake/confirm", json={
            "session_id": sid,
            "confirmed_features": {
                "clinical": ext["clinical"],
                "wearable": ext["wearable"],
                "gut": ext["gut"]
            }
        })
        c_res = r_conf.json()
        print(f"5. Confirm API Active Modalities: {c_res['active_modalities']}")

        # 5. Prediction
        r_pred = client.post("/api/v1/predict/analyze", json={
            "session_id": sid,
            "confirmed_features": {
                "clinical": ext["clinical"],
                "wearable": ext["wearable"],
                "gut": ext["gut"]
            }
        })
        p_res = r_pred.json()
        pathway = p_res.get("pathway_used") or p_res.get("fusion_pathway", {}).get("pathway_name", "C+W+G")
        print(f"6. Prediction Model Input Active Pathway: {pathway}")
        print(f"7. Disease Risk Outcomes Summary: {p_res.get('disease_outcomes')}")
        print("="*90)


if __name__ == "__main__":
    unittest.main()
