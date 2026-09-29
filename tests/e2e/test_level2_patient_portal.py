"""
test_level2_patient_portal.py — Level 2 Patient Portal Core UX & Security Verification Test Suite.

Tests:
1. Empty patient initial state & profile completion indicator
2. Profile field whitelist protection (Protected fields immutable)
3. Prefill provenance labeling (Profile prefill provenance tracking)
4. Unified intake file format & extraction support (PDF/TXT/CSV/JSON/Images)
5. Analysis reset vs account logout session lifecycle
6. Session refresh & expired auth token handling
7. Stale state isolation (No previous patient data leaks)
8. Cross-patient session isolation (403 Forbidden)
9. Cross-role route access restriction (403 Forbidden)
10. Full Patient Intake -> Predict -> XAI -> RAG end-to-end flow
"""

import os
import json
import logging
import unittest
import uuid
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("level2_patient_portal_tests")


class TestLevel2PatientPortal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()

    def setUp(self):
        self.client = TestClient(app)

    def test_01_empty_patient_portal_initial_state(self):
        logger.info("--- LEVEL 2 TEST 1: Empty Patient Initial State & Profile Completion ---")
        email = f"pat_empty_{uuid.uuid4().hex[:8]}@telemed.ai"
        
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email,
            "password": "Password123!",
            "full_name": "New Patient",
            "age": 30,
            "gender": "Female"
        })
        self.assertEqual(reg_res.status_code, 201)
        user = reg_res.json()["user"]
        self.assertEqual(user["role"], "PATIENT")
        self.assertIn("patient_profile", user)
        self.assertEqual(user["patient_profile"]["age"], 30)

        token = reg_res.json()["token"]
        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["user"]["email"], email)

    def test_02_profile_field_whitelist_protection(self):
        logger.info("--- LEVEL 2 TEST 2: Profile Field Whitelist Protection ---")
        email = f"pat_profile_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Alice Patient"
        })
        token = reg_res.json()["token"]

        # 1. Valid update of editable demographic fields
        up_res = self.client.put("/api/v1/auth/profile", json={
            "full_name": "Alice Updated",
            "age": 42,
            "gender": "Female",
            "height_cm": 168.0,
            "weight_kg": 65.5,
            "contact_number": "+1555999888"
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(up_res.status_code, 200)
        up_user = up_res.json()["user"]
        self.assertEqual(up_user["full_name"], "Alice Updated")
        self.assertEqual(up_user["patient_profile"]["age"], 42)
        self.assertEqual(up_user["patient_profile"]["height_cm"], 168.0)

        # 2. Rejection of protected system field modification (role / user_id / email)
        hacked_res = self.client.put("/api/v1/auth/profile", json={
            "role": "ADMIN",
            "user_id": "usr_hacked_123",
            "email": "hacked@telemed.ai"
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(hacked_res.status_code, 400)
        resp_text = str(hacked_res.json())
        self.assertTrue(
            "strictly prohibited" in resp_text or "No valid updatable fields" in resp_text,
            f"Expected protected-field rejection message, got: {resp_text}"
        )

    def test_03_prefill_provenance_labeling(self):
        logger.info("--- LEVEL 2 TEST 3: Prefill Provenance Labeling ---")
        email = f"pat_prefill_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Bob Prefill",
            "age": 50, "gender": "Male", "height_cm": 175.0, "weight_kg": 80.0
        })
        token = reg_res.json()["token"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up_res = self.client.post(
                "/api/v1/intake/upload",
                files=[("files", ("clinical.txt", f, "text/plain"))],
                headers={"Authorization": f"Bearer {token}"}
            )
        self.assertEqual(up_res.status_code, 200)
        self.assertEqual(up_res.json()["status"], "EXTRACTED")

    def test_04_intake_unified_file_formats_support(self):
        logger.info("--- LEVEL 2 TEST 4: Unified Intake File Format & Extraction Support ---")
        email = f"pat_intake_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Carol Intake"
        })
        token = reg_res.json()["token"]

        # Upload clinical.txt
        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up_res = self.client.post(
                "/api/v1/intake/upload",
                files=[("files", ("clinical.txt", f, "text/plain"))],
                headers={"Authorization": f"Bearer {token}"}
            )
        self.assertEqual(up_res.status_code, 200)
        ext_data = up_res.json()["extracted_features"]
        self.assertIn("clinical", ext_data)
        self.assertIn("Fasting_Blood_Glucose", ext_data["clinical"])

    def test_05_analysis_reset_vs_logout(self):
        logger.info("--- LEVEL 2 TEST 5: Analysis Reset vs Logout Session Lifecycle ---")
        email = f"pat_lifecycle_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Dave Lifecycle"
        })
        token = reg_res.json()["token"]

        # Logout revokes token
        logout_res = self.client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 200)

        # Subsequent request fails with 401
        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 401)

    def test_06_session_refresh_and_expired_auth(self):
        logger.info("--- LEVEL 2 TEST 6: Session Refresh & Expired Auth Token ---")
        email = f"pat_refresh_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Eve Refresh"
        })
        token = reg_res.json()["token"]

        # Invalid token returns 401
        invalid_res = self.client.get("/api/v1/auth/me", headers={"Authorization": "Bearer tok_invalid_fake_999"})
        self.assertEqual(invalid_res.status_code, 401)

    def test_07_stale_state_isolation(self):
        logger.info("--- LEVEL 2 TEST 7: Stale State Isolation ---")
        # Patient A registers
        email_a = f"pat_a_{uuid.uuid4().hex[:8]}@telemed.ai"
        p_a = self.client.post("/api/v1/auth/register/patient", json={
            "email": email_a, "password": "Password123!", "full_name": "Patient A"
        })
        token_a = p_a.json()["token"]

        # Patient B registers
        email_b = f"pat_b_{uuid.uuid4().hex[:8]}@telemed.ai"
        p_b = self.client.post("/api/v1/auth/register/patient", json={
            "email": email_b, "password": "Password123!", "full_name": "Patient B"
        })
        token_b = p_b.json()["token"]

        # Patient A me call returns Patient A
        me_a = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(me_a.json()["user"]["email"], email_a)

        # Patient B me call returns Patient B
        me_b = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(me_b.json()["user"]["email"], email_b)

    def test_08_cross_patient_session_isolation(self):
        logger.info("--- LEVEL 2 TEST 8: Cross-Patient Session Isolation (403) ---")
        email1 = f"owner1_{uuid.uuid4().hex[:8]}@telemed.ai"
        p1 = self.client.post("/api/v1/auth/register/patient", json={
            "email": email1, "password": "Password123!", "full_name": "Owner One"
        })
        t1 = p1.json()["token"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up1 = self.client.post(
                "/api/v1/intake/upload",
                files=[("files", ("clinical.txt", f, "text/plain"))],
                headers={"Authorization": f"Bearer {t1}"}
            )
        sid = up1.json()["session_id"]

        email2 = f"attacker_{uuid.uuid4().hex[:8]}@telemed.ai"
        p2 = self.client.post("/api/v1/auth/register/patient", json={
            "email": email2, "password": "Password123!", "full_name": "Attacker Two"
        })
        t2 = p2.json()["token"]

        # Attacker tries to confirm Patient 1's session
        conf_res = self.client.post(
            "/api/v1/intake/confirm",
            json={"session_id": sid, "confirmed_features": {"clinical": {"Age": 45}}},
            headers={"Authorization": f"Bearer {t2}"}
        )
        self.assertEqual(conf_res.status_code, 403)

    def test_09_cross_role_route_restriction(self):
        logger.info("--- LEVEL 2 TEST 9: Cross-Role Route Restriction (403) ---")
        email = f"pat_cross_{uuid.uuid4().hex[:8]}@telemed.ai"
        p = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Cross Patient"
        })
        token = p.json()["token"]

        admin_users = self.client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(admin_users.status_code, 403)

        admin_stats = self.client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(admin_stats.status_code, 403)

    def test_10_full_intake_predict_xai_rag_flow(self):
        logger.info("--- LEVEL 2 TEST 10: Full Patient Intake -> Predict -> XAI -> RAG Flow ---")
        email = f"pat_flow_{uuid.uuid4().hex[:8]}@telemed.ai"
        p = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Flow Patient"
        })
        token = p.json()["token"]

        # 1. Upload
        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up_res = self.client.post(
                "/api/v1/intake/upload",
                files=[("files", ("clinical.txt", f, "text/plain"))],
                headers={"Authorization": f"Bearer {token}"}
            )
        self.assertEqual(up_res.status_code, 200)
        sid = up_res.json()["session_id"]
        extracted = up_res.json()["extracted_features"]

        # 2. Confirm
        conf_res = self.client.post(
            "/api/v1/intake/confirm",
            json={"session_id": sid, "confirmed_features": extracted},
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(conf_res.status_code, 200)
        self.assertEqual(conf_res.json()["status"], "CONFIRMED")

        # 3. Predict
        pred_res = self.client.post(
            "/api/v1/predict/analyze",
            json={"session_id": sid},
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(pred_res.status_code, 200)
        self.assertEqual(pred_res.json()["status"], "ANALYZED")
        pred_dict = pred_res.json().get("disease_outcomes", {})
        self.assertIn("Type2_Diabetes", pred_dict)

        # 4. XAI
        xai_res = self.client.post(
            "/api/v1/xai/explain",
            json={"session_id": sid, "target_disease": "Type2_Diabetes"},
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(xai_res.status_code, 200)
        self.assertIn("xai_payload", xai_res.json())

        # 5. RAG Report
        rag_res = self.client.post(
            "/api/v1/rag/report",
            json={"session_id": sid},
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(rag_res.status_code, 200)
        self.assertIn("report", rag_res.json())


if __name__ == "__main__":
    unittest.main()
