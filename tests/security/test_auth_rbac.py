"""
test_auth_rbac.py — Level 1 Hardened Security & RBAC Verification Test Suite.

Tests:
1. Patient registration, login, logout, /me & token revocation
2. Doctor registration (defaults to PENDING) & verification status
3. Direct unauthenticated API call rejection (401)
4. Patient access control (Patient blocked from Admin APIs with 403)
5. Pending Doctor access control (Blocked from clinical patient APIs with 403)
6. Verified Doctor access control (Blocked from unassigned patient clinical APIs with 403)
7. Admin access control (Allowed on Admin APIs, blocked from clinical patient APIs with 403)
8. Patient authenticated clinical workspace workflow
9. Admin bootstrap disabled in default runtime (403)
10. Repeated admin bootstrap rejection when admin already exists (403)
11. Password hash & salt exposure prevention across all endpoints
12. Duplicate email registration rejection (400)
13. Cross-patient resource isolation (Patient B blocked from Patient A session with 403)
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
logger = logging.getLogger("auth_rbac_tests")


import tempfile
import shutil

class TestAuthAndRBAC(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_telemed_auth_rbac.db")
        config.DB_PATH = cls.db_path
        database.DB_PATH = cls.db_path
        database.init_db()
        # Bootstrap default admin for tests
        config.ALLOW_ADMIN_BOOTSTRAP = True
        database.bootstrap_admin()
        config.ALLOW_ADMIN_BOOTSTRAP = False

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        self.client = TestClient(app)

    def test_01_patient_registration_login_me_logout(self):
        logger.info("--- TEST 1: Patient Registration, Login, /me & Logout ---")
        email = f"patient_{uuid.uuid4().hex[:8]}@telemed.ai"
        
        # 1. Register Patient
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Jane Patient",
            "age": 35,
            "gender": "Female",
            "height_cm": 165.0,
            "weight_kg": 62.0,
            "contact_number": "+1555123456"
        })
        self.assertEqual(reg_res.status_code, 201)
        reg_data = reg_res.json()
        self.assertEqual(reg_data["user"]["role"], "PATIENT")
        token = reg_data["token"]

        # 2. GET /me with Bearer token
        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["user"]["email"], email)

        # 3. Login Patient
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "Password123!"
        })
        self.assertEqual(login_res.status_code, 200)
        login_token = login_res.json()["token"]

        # 4. Logout
        logout_res = self.client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {login_token}"})
        self.assertEqual(logout_res.status_code, 200)

        # 5. Verify token revoked
        revoked_me = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login_token}"})
        self.assertEqual(revoked_me.status_code, 401)

    def test_02_doctor_registration_defaults_to_pending(self):
        logger.info("--- TEST 2: Doctor Registration Defaults to PENDING ---")
        email = f"doctor_{uuid.uuid4().hex[:8]}@telemed.ai"

        reg_res = self.client.post("/api/v1/auth/register/doctor", json={
            "email": email,
            "password": "DoctorPass123!",
            "full_name": "Dr. John Smith",
            "specialization": "Endocrinology",
            "registration_number": f"MED-{uuid.uuid4().hex[:6]}",
            "experience_years": 10,
            "hospital_affiliation": "General Hospital"
        })
        self.assertEqual(reg_res.status_code, 201)
        user_data = reg_res.json()["user"]
        self.assertEqual(user_data["role"], "DOCTOR")
        self.assertEqual(user_data["doctor_profile"]["verification_status"], "PENDING")

    def test_03_unauthenticated_api_rejection(self):
        logger.info("--- TEST 3: Direct Unauthenticated API Call Rejection (401) ---")
        res = self.client.post("/api/v1/predict/analyze", json={"session_id": "sess_fake_123"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Authentication required", res.json()["message"])

    def test_04_patient_blocked_from_admin_apis(self):
        logger.info("--- TEST 4: Patient Blocked from Admin APIs (403) ---")
        email = f"pat_blocked_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Blocked Patient"
        })
        token = reg_res.json()["token"]

        admin_res = self.client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(admin_res.status_code, 403)

    def test_05_pending_doctor_blocked_from_clinical_patient_data(self):
        logger.info("--- TEST 5: Pending Doctor Blocked from Clinical Data (403) ---")
        email = f"doc_pending_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/doctor", json={
            "email": email, "password": "DoctorPass123!", "full_name": "Dr. Pending",
            "specialization": "Cardiology", "registration_number": f"REG-{uuid.uuid4().hex[:6]}"
        })
        doc_token = reg_res.json()["token"]

        pred_res = self.client.post(
            "/api/v1/predict/analyze",
            json={"session_id": "sess_fake"},
            headers={"Authorization": f"Bearer {doc_token}"}
        )
        self.assertEqual(pred_res.status_code, 403)
        self.assertIn("Doctor account status is 'PENDING'", pred_res.json()["message"])

    def test_06_verified_doctor_blocked_from_unassigned_patient_data(self):
        logger.info("--- TEST 6: Verified Doctor Blocked from Unassigned Patient Data (403) ---")
        email = f"doc_verified_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/doctor", json={
            "email": email, "password": "DoctorPass123!", "full_name": "Dr. Verified",
            "specialization": "Internal Medicine", "registration_number": f"REG-{uuid.uuid4().hex[:6]}"
        })
        doc_user = reg_res.json()["user"]
        doc_token = reg_res.json()["token"]
        doc_id = doc_user["doctor_profile"]["doctor_id"]

        # Admin logs in and updates doctor status to VERIFIED
        admin_login = self.client.post("/api/v1/auth/login", json={
            "email": config.DEMO_ADMIN_EMAIL, "password": config.DEMO_ADMIN_PASSWORD
        })
        admin_token = admin_login.json()["token"]
        admin_user_id = admin_login.json()["user"]["user_id"]

        database.update_doctor_verification_status(admin_user_id, doc_id, "UNDER_REVIEW", "Application submitted")
        database.update_doctor_verification_status(admin_user_id, doc_id, "VERIFIED", "Verified credentials")

        # Verified Doctor tries calling clinical v3 predict
        v3_res = self.client.post(
            "/api/v3/predict",
            json={"patient_id": "P_TEST", "clinical_data": {"Age": 45, "Glucose": 110}},
            headers={"Authorization": f"Bearer {doc_token}"}
        )
        self.assertEqual(v3_res.status_code, 403)
        self.assertIn("Verified doctor is not explicitly assigned", v3_res.json()["message"])

    def test_07_admin_role_capabilities_and_clinical_restriction(self):
        logger.info("--- TEST 7: Admin Role Capabilities & Clinical Restriction ---")
        admin_login = self.client.post("/api/v1/auth/login", json={
            "email": config.DEMO_ADMIN_EMAIL, "password": config.DEMO_ADMIN_PASSWORD
        })
        admin_token = admin_login.json()["token"]

        # 1. Admin gets stats -> 200 OK
        stats_res = self.client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(stats_res.status_code, 200)
        self.assertIn("total_users", stats_res.json()["stats"])

        # 2. Admin lists users -> 200 OK
        users_res = self.client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(users_res.status_code, 200)

        # 3. Admin lists doctors -> 200 OK
        docs_res = self.client.get("/api/v1/admin/doctors", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(docs_res.status_code, 200)

        # 4. Admin tries calling clinical predict endpoint -> 403 Forbidden
        clin_res = self.client.post(
            "/api/v1/predict/analyze",
            json={"session_id": "sess_fake"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(clin_res.status_code, 403)
        self.assertIn("Admin accounts are restricted to administrative management operations", clin_res.json()["message"])

    def test_08_patient_authenticated_clinical_workflow(self):
        logger.info("--- TEST 8: Patient Authenticated Clinical Workspace Workflow ---")
        email = f"patient_workflow_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Workflow Patient"
        })
        pat_token = reg_res.json()["token"]

        # Patient calls health check (public)
        health_res = self.client.get("/api/v1/health")
        self.assertEqual(health_res.status_code, 200)

        # Patient uploads report with auth token
        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up_res = self.client.post(
                "/api/v1/intake/upload",
                files=[("files", ("clinical.txt", f, "text/plain"))],
                headers={"Authorization": f"Bearer {pat_token}"}
            )
        self.assertEqual(up_res.status_code, 200)
        self.assertEqual(up_res.json()["status"], "EXTRACTED")

    def test_09_admin_bootstrap_disabled_in_default_runtime(self):
        logger.info("--- TEST 9: Admin Bootstrap Disabled in Default Runtime (403) ---")
        config.ALLOW_ADMIN_BOOTSTRAP = False
        config.ADMIN_BOOTSTRAP_KEY = ""
        boot_res = self.client.post("/api/v1/auth/bootstrap-admin", json={
            "email": "hacker_admin@telemed.ai", "password": "HackPassword123!"
        })
        self.assertEqual(boot_res.status_code, 403)
        res_text = str(boot_res.json())
        self.assertIn("Admin bootstrap endpoint is disabled", res_text)

    def test_10_repeated_bootstrap_rejected(self):
        logger.info("--- TEST 10: Repeated Admin Bootstrap Rejected When Admin Exists (403) ---")
        config.ALLOW_ADMIN_BOOTSTRAP = True
        boot_res = self.client.post("/api/v1/auth/bootstrap-admin", json={
            "email": "second_admin@telemed.ai", "password": "SecondAdmin123!"
        })
        self.assertEqual(boot_res.status_code, 403)
        res_text = str(boot_res.json())
        self.assertIn("Initial admin account already exists", res_text)
        config.ALLOW_ADMIN_BOOTSTRAP = False

    def test_11_password_and_salt_never_returned(self):
        logger.info("--- TEST 11: Password Hash & Salt Exposure Prevention ---")
        email = f"pat_sec_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "SecurePassword123!", "full_name": "Sec Patient"
        })
        user_data = reg_res.json()["user"]
        self.assertNotIn("password_hash", user_data)
        self.assertNotIn("salt", user_data)

        # Check /me
        token = reg_res.json()["token"]
        me_data = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["user"]
        self.assertNotIn("password_hash", me_data)
        self.assertNotIn("salt", me_data)

    def test_12_duplicate_email_rejected(self):
        logger.info("--- TEST 12: Duplicate Email Registration Rejection (400) ---")
        email = f"dup_{uuid.uuid4().hex[:8]}@telemed.ai"
        self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Patient One"
        })
        dup_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Patient Two"
        })
        self.assertEqual(dup_res.status_code, 400)
        res_text = str(dup_res.json())
        self.assertIn("already exists", res_text)

    def test_13_patient_resource_isolation_cross_patient_blocked(self):
        logger.info("--- TEST 13: Cross-Patient Resource Isolation (403) ---")
        # Patient 1 creates session
        email1 = f"pat1_{uuid.uuid4().hex[:8]}@telemed.ai"
        p1_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email1, "password": "Password123!", "full_name": "Patient One"
        })
        p1_token = p1_res.json()["token"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up1 = self.client.post(
                "/api/v1/intake/upload",
                files=[("files", ("clinical.txt", f, "text/plain"))],
                headers={"Authorization": f"Bearer {p1_token}"}
            )
        sid = up1.json()["session_id"]

        # Patient 2 registers and attempts to access Patient 1's session
        email2 = f"pat2_{uuid.uuid4().hex[:8]}@telemed.ai"
        p2_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": email2, "password": "Password123!", "full_name": "Patient Two"
        })
        p2_token = p2_res.json()["token"]

        # Patient 2 calls confirm on Patient 1's session
        conf2 = self.client.post(
            "/api/v1/intake/confirm",
            json={"session_id": sid, "confirmed_features": {"clinical": {"Age": 40}}},
            headers={"Authorization": f"Bearer {p2_token}"}
        )
        self.assertEqual(conf2.status_code, 403)
        res_text = str(conf2.json())
        self.assertIn("belonging to another user", res_text)


if __name__ == "__main__":
    unittest.main()
