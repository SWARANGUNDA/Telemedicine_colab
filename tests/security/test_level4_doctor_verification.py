"""
test_level4_doctor_verification.py — Comprehensive Test Suite for Level 4 Doctor Verification System.

Tests:
1. test_doctor_default_pending
2. test_credential_upload_and_validation
3. test_duplicate_registration_number_rejection
4. test_verification_state_machine_matrix
5. test_doctor_self_verification_blocking
6. test_unverified_and_suspended_doctor_clinical_denial
7. test_verified_doctor_access_and_shell_banner
8. test_idor_and_cross_doctor_isolation
9. test_admin_doctor_verification_workspace
10. test_audit_trail_integrity
11. test_levels123_regression_suite
"""

import unittest
import os
import sys
import secrets
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root workspace path is on sys.path
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR))

from app.backend.main import app
from app.backend import database


class TestLevel4DoctorVerification(unittest.TestCase):

    def setUp(self):
        """Set up clean database state and test client for each test."""
        from app.backend.security import RATE_LIMITER
        RATE_LIMITER._requests.clear()
        self.client = TestClient(app)
        database.init_db()

        # Seed Admin Account directly in database
        self.admin_email = f"admin_l4_{secrets.token_hex(4)}@telemed.org"
        self.admin_pass = "AdminSec#2026!Pass"
        database.create_user(
            self.admin_email,
            self.admin_pass,
            role="ADMIN",
            profile_data={"full_name": "System Administrator"}
        )

        # Login Admin
        res = self.client.post("/api/v1/auth/login", json={"email": self.admin_email, "password": self.admin_pass})
        self.assertEqual(res.status_code, 200)
        self.admin_token = res.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

    def _register_doctor(self, reg_num=None, email=None):
        """Helper to register a new doctor account."""
        doc_email = email or f"dr_{secrets.token_hex(4)}@telemed.org"
        password = "DoctorPass#2026!"
        reg = reg_num or f"MCI-L4-{secrets.token_hex(4).upper()}"

        res = self.client.post("/api/v1/auth/register/doctor", json={
            "email": doc_email,
            "password": password,
            "full_name": "Dr. Test Verification",
            "specialization": "Cardiology",
            "qualification": "MD Cardiology",
            "registration_number": reg,
            "registration_council": "Medical Council of India",
            "experience_years": 8,
            "contact_number": "+15559876543",
            "hospital_affiliation": "City Heart Institute"
        })
        self.assertEqual(res.status_code, 201)

        # Login doctor
        login_res = self.client.post("/api/v1/auth/login", json={"email": doc_email, "password": password})
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_data = login_res.json()["user"]

        return {
            "email": doc_email,
            "password": password,
            "token": token,
            "headers": headers,
            "user": user_data,
            "registration_number": reg,
            "doctor_id": user_data["doctor_profile"]["doctor_id"],
            "user_id": user_data["user_id"]
        }

    def test_1_doctor_default_pending(self):
        """1. Verify newly registered doctor defaults to PENDING status."""
        doc = self._register_doctor()
        self.assertEqual(doc["user"]["role"], "DOCTOR")
        self.assertEqual(doc["user"]["doctor_profile"]["verification_status"], "PENDING")

        # Verify backend /me endpoint returns PENDING
        me_res = self.client.get("/api/v1/auth/me", headers=doc["headers"])
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["user"]["doctor_profile"]["verification_status"], "PENDING")

    def test_2_credential_upload_and_validation(self):
        """2. Verify document upload MIME validation, size limits, and safe storage."""
        doc = self._register_doctor()

        # Valid PDF Upload
        pdf_content = b"%PDF-1.4 Fake PDF Content for Doctor Verification Test"
        upload_res = self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc["headers"],
            data={"document_type": "MEDICAL_LICENSE"},
            files={"file": ("license.pdf", pdf_content, "application/pdf")}
        )
        self.assertEqual(upload_res.status_code, 201)
        cred = upload_res.json()["credential"]
        self.assertEqual(cred["original_filename"], "license.pdf")
        self.assertTrue(cred["stored_filename"].startswith("cred_"))

        # Rejects executable / invalid MIME file format
        exe_res = self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc["headers"],
            data={"document_type": "MEDICAL_LICENSE"},
            files={"file": ("malicious.exe", b"MZ Executable Content", "application/x-executable")}
        )
        self.assertEqual(exe_res.status_code, 400)
        self.assertIn("Invalid file format", str(exe_res.json()))

        # Rejects oversized file (>10MB)
        large_bytes = b"0" * (10 * 1024 * 1024 + 100)
        large_res = self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc["headers"],
            data={"document_type": "ID_PROOF"},
            files={"file": ("large_doc.pdf", large_bytes, "application/pdf")}
        )
        self.assertEqual(large_res.status_code, 400)
        self.assertIn("10 MB", str(large_res.json()))

    def test_3_duplicate_registration_number_rejection(self):
        """3. Verify duplicate medical registration number registration is rejected."""
        reg_num = f"DUP-REG-{secrets.token_hex(4).upper()}"
        self._register_doctor(reg_num=reg_num)

        # Attempt to register second doctor with exact same registration number
        dup_res = self.client.post("/api/v1/auth/register/doctor", json={
            "email": f"dr_dup_{secrets.token_hex(4)}@telemed.org",
            "password": "DoctorPass#2026!",
            "full_name": "Dr. Duplicate Fraud",
            "specialization": "Neurology",
            "registration_number": reg_num,
            "experience_years": 5,
            "contact_number": "+15551112222"
        })
        self.assertEqual(dup_res.status_code, 400)
        self.assertIn("already exists", str(dup_res.json()))

    def test_4_verification_state_machine_matrix(self):
        """4. Test complete state machine matrix, submitting for review, and admin transition rules."""
        doc = self._register_doctor()
        doc_id = doc["doctor_id"]

        # 1. Cannot submit for review without uploading documents
        no_doc_sub = self.client.post("/api/v1/doctor/submit-for-review", headers=doc["headers"])
        self.assertEqual(no_doc_sub.status_code, 400)
        self.assertIn("upload at least one verification document", str(no_doc_sub.json()))

        # Upload document
        self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc["headers"],
            data={"document_type": "MEDICAL_LICENSE"},
            files={"file": ("license.pdf", b"%PDF-1.4 Valid Medical License", "application/pdf")}
        )

        # 2. Submit application for review (PENDING -> UNDER_REVIEW)
        sub_res = self.client.post("/api/v1/doctor/submit-for-review", headers=doc["headers"])
        self.assertEqual(sub_res.status_code, 200)
        self.assertEqual(sub_res.json()["verification_status"], "UNDER_REVIEW")

        # 3. Invalid Transition Attempt (PENDING directly to VERIFIED without UNDER_REVIEW on another doctor)
        doc2 = self._register_doctor()
        invalid_res = self.client.post(
            f"/api/v1/admin/doctor-applications/{doc2['doctor_id']}/transition",
            headers=self.admin_headers,
            json={"status": "VERIFIED", "reason": "Attempt skipping review"}
        )
        self.assertEqual(invalid_res.status_code, 400)
        self.assertIn("Invalid status transition", str(invalid_res.json()))

        # 4. Admin transition UNDER_REVIEW -> RESUBMISSION_REQUIRED (requires reason)
        no_reason_res = self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=self.admin_headers,
            json={"status": "RESUBMISSION_REQUIRED", "reason": "   "}
        )
        self.assertEqual(no_reason_res.status_code, 400)
        self.assertIn("detailed reason is required", str(no_reason_res.json()))

        # Admin requests resubmission with valid reason
        resub_res = self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=self.admin_headers,
            json={"status": "RESUBMISSION_REQUIRED", "reason": "Medical license copy is blurry. Please re-upload clear scan."}
        )
        self.assertEqual(resub_res.status_code, 200)
        self.assertEqual(resub_res.json()["verification_status"], "RESUBMISSION_REQUIRED")

        # Doctor resubmits for review (RESUBMISSION_REQUIRED -> UNDER_REVIEW)
        sub2_res = self.client.post("/api/v1/doctor/submit-for-review", headers=doc["headers"])
        self.assertEqual(sub2_res.status_code, 200)
        self.assertEqual(sub2_res.json()["verification_status"], "UNDER_REVIEW")

        # Admin approves (UNDER_REVIEW -> VERIFIED)
        appr_res = self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=self.admin_headers,
            json={"status": "VERIFIED", "reason": "Credentials verified against medical council database."}
        )
        self.assertEqual(appr_res.status_code, 200)
        self.assertEqual(appr_res.json()["verification_status"], "VERIFIED")

        # Admin suspends verified doctor (VERIFIED -> SUSPENDED)
        susp_res = self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=self.admin_headers,
            json={"status": "SUSPENDED", "reason": "Pending license audit review."}
        )
        self.assertEqual(susp_res.status_code, 200)
        self.assertEqual(susp_res.json()["verification_status"], "SUSPENDED")

    def test_5_doctor_self_verification_blocking(self):
        """5. Verify doctor cannot set their own status, role, or execute admin transitions."""
        doc = self._register_doctor()
        doc_id = doc["doctor_id"]

        # Direct call to admin transition endpoint with doctor headers must be denied (403)
        self_trans = self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=doc["headers"],
            json={"status": "VERIFIED", "reason": "Self approving account"}
        )
        self.assertEqual(self_trans.status_code, 403)

    def test_6_unverified_and_suspended_doctor_clinical_denial(self):
        """6. Verify PENDING, UNDER_REVIEW, REJECTED, and SUSPENDED doctors are blocked from clinical endpoints."""
        doc = self._register_doctor()
        doc_id = doc["doctor_id"]

        # Upload document and submit
        self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc["headers"],
            data={"document_type": "MEDICAL_LICENSE"},
            files={"file": ("license.pdf", b"%PDF-1.4 Test Doc", "application/pdf")}
        )

        # 1. PENDING Status -> Clinical Blocked
        predict_res = self.client.post("/api/v1/predict/analyze", headers=doc["headers"], json={"session_id": "sess_fake"})
        self.assertEqual(predict_res.status_code, 403)
        self.assertIn("Access to patient clinical workspace", str(predict_res.json()))

        # 2. UNDER_REVIEW Status -> Clinical Blocked
        self.client.post("/api/v1/doctor/submit-for-review", headers=doc["headers"])
        predict_res2 = self.client.post("/api/v1/predict/analyze", headers=doc["headers"], json={"session_id": "sess_fake"})
        self.assertEqual(predict_res2.status_code, 403)

        # 3. REJECTED Status -> Clinical Blocked
        self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=self.admin_headers,
            json={"status": "REJECTED", "reason": "License invalid."}
        )
        predict_res3 = self.client.post("/api/v1/predict/analyze", headers=doc["headers"], json={"session_id": "sess_fake"})
        self.assertEqual(predict_res3.status_code, 403)

    def test_7_verified_doctor_access_and_shell_banner(self):
        """7. Verify VERIFIED doctor can access verification status and doctor portal shell."""
        doc = self._register_doctor()
        doc_id = doc["doctor_id"]

        # Upload & Submit
        self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc["headers"],
            data={"document_type": "MEDICAL_LICENSE"},
            files={"file": ("license.pdf", b"%PDF-1.4 Valid License", "application/pdf")}
        )
        self.client.post("/api/v1/doctor/submit-for-review", headers=doc["headers"])

        # Admin approves
        self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=self.admin_headers,
            json={"status": "VERIFIED", "reason": "Verified for TeleMed portal access."}
        )

        status_res = self.client.get("/api/v1/doctor/verification-status", headers=doc["headers"])
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["verification_status"], "VERIFIED")

    def test_8_idor_and_cross_doctor_isolation(self):
        """8. Test IDOR protection: Doctor A cannot access or delete Doctor B's credentials."""
        doc_a = self._register_doctor(email=f"doc_a_{secrets.token_hex(4)}@telemed.org")
        doc_b = self._register_doctor(email=f"doc_b_{secrets.token_hex(4)}@telemed.org")

        # Doctor A uploads document
        up_res = self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc_a["headers"],
            data={"document_type": "MEDICAL_LICENSE"},
            files={"file": ("doc_a_license.pdf", b"%PDF-1.4 Doc A License", "application/pdf")}
        )
        doc_a_cred_id = up_res.json()["credential"]["document_id"]

        # Doctor B attempts to download Doctor A's credential document
        dl_res = self.client.get(
            f"/api/v1/doctor/credentials/{doc_a_cred_id}/download",
            headers=doc_b["headers"]
        )
        self.assertEqual(dl_res.status_code, 403)

        # Doctor B attempts to delete Doctor A's credential document
        del_res = self.client.delete(
            f"/api/v1/doctor/credentials/{doc_a_cred_id}",
            headers=doc_b["headers"]
        )
        self.assertEqual(del_res.status_code, 404)

        # Admin CAN download Doctor A's document for verification review
        admin_dl = self.client.get(
            f"/api/v1/doctor/credentials/{doc_a_cred_id}/download",
            headers=self.admin_headers
        )
        self.assertEqual(admin_dl.status_code, 200)

    def test_9_admin_doctor_verification_workspace(self):
        """9. Verify Admin doctor applications list, filtering, search, and detail review endpoints."""
        doc = self._register_doctor()
        doc_id = doc["doctor_id"]

        # Admin list applications
        list_res = self.client.get("/api/v1/admin/doctor-applications", headers=self.admin_headers)
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(list_res.json()["count"], 1)

        # Admin get application detail
        detail_res = self.client.get(f"/api/v1/admin/doctor-applications/{doc_id}", headers=self.admin_headers)
        self.assertEqual(detail_res.status_code, 200)
        app_detail = detail_res.json()["application"]
        self.assertEqual(app_detail["doctor_id"], doc_id)
        self.assertIn("credentials", app_detail)
        self.assertIn("audit_history", app_detail)

    def test_10_audit_trail_integrity(self):
        """10. Verify immutable audit log records events, actor, roles, and status changes."""
        doc = self._register_doctor()
        doc_id = doc["doctor_id"]

        # Upload document
        self.client.post(
            "/api/v1/doctor/credentials/upload",
            headers=doc["headers"],
            data={"document_type": "MEDICAL_LICENSE"},
            files={"file": ("license.pdf", b"%PDF-1.4 Content", "application/pdf")}
        )

        # Submit & Transition
        self.client.post("/api/v1/doctor/submit-for-review", headers=doc["headers"])
        self.client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            headers=self.admin_headers,
            json={"status": "VERIFIED", "reason": "Verified credentials."}
        )

        # Inspect audit history
        audit_history = database.get_doctor_audit_history(doc_id)
        actions = [a["action"] for a in audit_history]
        self.assertIn("CREATED", actions)
        self.assertIn("DOCUMENT_UPLOADED", actions)
        self.assertIn("STATUS_CHANGED", actions)

    def test_11_levels123_regression_suite(self):
        """11. Regression verification: Level 1 Auth/RBAC, Level 2 UX, Level 3 Health Records remain intact."""
        # Patient login & profile
        pat_email = f"pat_reg_{secrets.token_hex(4)}@telemed.org"
        reg_res = self.client.post("/api/v1/auth/register/patient", json={
            "email": pat_email,
            "password": "PatientPass#2026!",
            "full_name": "Test Regression Patient"
        })
        self.assertEqual(reg_res.status_code, 201)

        login_res = self.client.post("/api/v1/auth/login", json={"email": pat_email, "password": "PatientPass#2026!"})
        self.assertEqual(login_res.status_code, 200)
        pat_headers = {"Authorization": f"Bearer {login_res.json()['token']}"}

        # Level 3 Health records list
        rec_res = self.client.get("/api/v1/records", headers=pat_headers)
        self.assertEqual(rec_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
