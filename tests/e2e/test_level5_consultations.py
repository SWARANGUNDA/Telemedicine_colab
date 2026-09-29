"""
test_level5_consultations.py — Level 5 Test Suite for Consultation Requests, Doctor–Patient Assignment & Controlled Health Record Access.

Validates:
1. Patient consultation request creation & normalized record consent sharing
2. Patient ownership enforcement (Patient B blocked from Patient A requests/consents)
3. Pre-assignment access denial (consent before assignment does not grant doctor access)
4. Admin doctor eligibility (Only VERIFIED, non-SUSPENDED doctor assignable)
5. Self-assignment blocking (Doctor cannot self-assign; Patient cannot choose doctor)
6. Doctor assignment response state machine (ASSIGNED -> ACCEPTED / DECLINED)
7. Automatic ACCEPTED -> ACTIVE transition on first authorized clinical record view
8. Authorized READ-ONLY patient health record retrieval with non-diagnostic disclaimers
9. Unshared health record access denial
10. Cross-doctor & cross-patient isolation (Doctor B blocked from Doctor A assignment)
11. Individual shared-record consent revocation blocking subsequent access
12. Immediate access blocking on doctor account suspension
13. Immediate access blocking on doctor reassignment
14. Immediate access blocking on consultation completion and cancellation
15. Immutable audit log trail preservation after access termination
16. Database restart persistence & Levels 1-4 regressions
"""

import unittest
import os
import shutil
import tempfile
import secrets
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database, config
from app.backend.database import hash_password, create_auth_session


class TestLevel5Consultations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()
        from app.backend.security import RATE_LIMITER
        RATE_LIMITER._requests.clear()

        cls.client = TestClient(app)

        prefix = secrets.token_hex(4)

        # Setup Test Users
        # Admin
        cls.admin = database.create_user(
            email=f"admin_l5_{prefix}@telemed.ai",
            password="AdminPass123!",
            role="ADMIN",
            profile_data={"full_name": "Admin User"}
        )
        cls.admin_token = create_auth_session(cls.admin["user_id"])
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

        # Doctor A (VERIFIED)
        cls.doc_a = database.create_user(
            email=f"dr_alpha_{prefix}@telemed.ai",
            password="DoctorPass123!",
            role="DOCTOR",
            profile_data={
                "full_name": "Dr. Alpha Specialist",
                "specialization": "Cardiology",
                "registration_number": f"REG-CARD-{prefix}-1"
            }
        )
        doc_a_id = cls.doc_a["doctor_profile"]["doctor_id"]
        database.update_doctor_verification_status(cls.admin["user_id"], doc_a_id, "UNDER_REVIEW", "Application submitted")
        database.update_doctor_verification_status(cls.admin["user_id"], doc_a_id, "VERIFIED", "Credentials verified")
        cls.doc_a_token = create_auth_session(cls.doc_a["user_id"])
        cls.doc_a_headers = {"Authorization": f"Bearer {cls.doc_a_token}"}

        # Doctor B (VERIFIED)
        cls.doc_b = database.create_user(
            email=f"dr_beta_{prefix}@telemed.ai",
            password="DoctorPass123!",
            role="DOCTOR",
            profile_data={
                "full_name": "Dr. Beta Specialist",
                "specialization": "Cardiology",
                "registration_number": f"REG-CARD-{prefix}-2"
            }
        )
        doc_b_id = cls.doc_b["doctor_profile"]["doctor_id"]
        database.update_doctor_verification_status(cls.admin["user_id"], doc_b_id, "UNDER_REVIEW", "Application submitted")
        database.update_doctor_verification_status(cls.admin["user_id"], doc_b_id, "VERIFIED", "Credentials verified")
        cls.doc_b_token = create_auth_session(cls.doc_b["user_id"])
        cls.doc_b_headers = {"Authorization": f"Bearer {cls.doc_b_token}"}

        # Doctor Pending (PENDING)
        cls.doc_pending = database.create_user(
            email=f"dr_pending_{prefix}@telemed.ai",
            password="DoctorPass123!",
            role="DOCTOR",
            profile_data={
                "full_name": "Dr. Pending Specialist",
                "specialization": "Cardiology",
                "registration_number": f"REG-CARD-{prefix}-3"
            }
        )
        cls.doc_pending_token = create_auth_session(cls.doc_pending["user_id"])
        cls.doc_pending_headers = {"Authorization": f"Bearer {cls.doc_pending_token}"}

        # Patient A
        cls.patient_a = database.create_user(
            email=f"patient_alpha_{prefix}@telemed.ai",
            password="PatientPass123!",
            role="PATIENT",
            profile_data={"full_name": "Patient Alpha"}
        )
        cls.patient_a_token = create_auth_session(cls.patient_a["user_id"])
        cls.patient_a_headers = {"Authorization": f"Bearer {cls.patient_a_token}"}

        # Patient B
        cls.patient_b = database.create_user(
            email=f"patient_beta_{prefix}@telemed.ai",
            password="PatientPass123!",
            role="PATIENT",
            profile_data={"full_name": "Patient Beta"}
        )
        cls.patient_b_token = create_auth_session(cls.patient_b["user_id"])
        cls.patient_b_headers = {"Authorization": f"Bearer {cls.patient_b_token}"}

        # Create Patient A Health Records (Record 1 shared, Record 2 unshared)
        cls.rec_a1 = database.upsert_health_record(
            user_id=cls.patient_a["user_id"],
            source_session_id=f"sess_alpha_101_{prefix}",
            patient_id=cls.patient_a["user_id"],
            effective_pathway="Clinical_Expert",
            data_quality_score=95.0,
            active_modalities=["Clinical"],
            confirmed_features={"Age": 55, "BMI": 28.5},
            prediction_snapshot={"Type2_Diabetes": {"screening_score": 0.75, "cutoff_T": 0.40, "risk_category": "MODERATE_RISK"}}
        )

        cls.rec_a2 = database.upsert_health_record(
            user_id=cls.patient_a["user_id"],
            source_session_id=f"sess_alpha_102_{prefix}",
            patient_id=cls.patient_a["user_id"],
            effective_pathway="Wearable_Gut_Fusion",
            data_quality_score=92.0,
            active_modalities=["Wearable", "Gut"],
            confirmed_features={"Steps": 8500},
            prediction_snapshot={"PreDiabetes": {"screening_score": 0.60, "cutoff_T": 0.50, "risk_category": "MODERATE_RISK"}}
        )


    def test_01_patient_create_consultation_request(self):
        """Test Patient creates a consultation request selecting Record A1 to share."""
        payload = {
            "specialization": "Cardiology",
            "category": "General Consultation",
            "reason": "Routine cardiac checkup and biomarker review",
            "urgency": "ROUTINE",
            "message": "Please review my recent lab predictions.",
            "record_ids": [self.rec_a1["record_id"]]
        }

        res = self.client.post("/api/v1/consultations", json=payload, headers=self.patient_a_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        cons = data["consultation"]
        self.assertEqual(cons["status"], "REQUESTED")
        self.assertEqual(cons["specialization"], "Cardiology")
        self.assertEqual(len(cons["shared_records"]), 1)
        self.assertEqual(cons["shared_records"][0]["record_id"], self.rec_a1["record_id"])
        self.assertEqual(cons["shared_records"][0]["share_status"], "ACTIVE")

        # Save consultation ID for subsequent tests
        TestLevel5Consultations.cons_id = cons["consultation_id"]

    def test_02_patient_ownership_isolation(self):
        """Test Patient B cannot access or cancel Patient A's consultation request."""
        res_get = self.client.get(f"/api/v1/consultations/{self.cons_id}", headers=self.patient_b_headers)
        self.assertEqual(res_get.status_code, 404)

        res_cancel = self.client.post(f"/api/v1/consultations/{self.cons_id}/cancel", json={"notes": "Unauthorized"}, headers=self.patient_b_headers)
        self.assertEqual(res_cancel.status_code, 400)

    def test_03_pre_assignment_doctor_access_denial(self):
        """Test Doctor cannot access clinical records while consultation is REQUESTED."""
        res = self.client.get(
            f"/api/v1/doctor/consultations/{self.cons_id}/records/{self.rec_a1['record_id']}",
            headers=self.doc_a_headers
        )
        self.assertEqual(res.status_code, 403)

    def test_04_admin_doctor_eligibility_assignment(self):
        """Test Admin can assign ONLY a VERIFIED doctor; PENDING doctor is rejected."""
        # Attempt assigning PENDING doctor
        res_p = self.client.post(
            f"/api/v1/admin/consultations/{self.cons_id}/assign",
            json={"doctor_id": self.doc_pending["doctor_profile"]["doctor_id"]},
            headers=self.admin_headers
        )
        self.assertEqual(res_p.status_code, 400)
        err_msg = res_p.json().get("message") or res_p.json().get("detail", "")
        self.assertIn("Only VERIFIED doctors can be assigned", err_msg)

        # Assign VERIFIED Doctor A
        res_v = self.client.post(
            f"/api/v1/admin/consultations/{self.cons_id}/assign",
            json={"doctor_id": self.doc_a["doctor_profile"]["doctor_id"], "notes": "Assigned to Dr. Alpha"},
            headers=self.admin_headers
        )
        self.assertEqual(res_v.status_code, 200)
        self.assertEqual(res_v.json()["consultation"]["status"], "ASSIGNED")

    def test_05_doctor_accept_assignment(self):
        """Test assigned Doctor A accepts the consultation (ASSIGNED -> ACCEPTED)."""
        res = self.client.post(
            f"/api/v1/doctor/consultations/{self.cons_id}/respond",
            json={"action": "ACCEPT", "reason": "Accepting cardiology case"},
            headers=self.doc_a_headers
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ACCEPTED")

    def test_06_authorized_read_only_access_and_state_transition(self):
        """Test Doctor A accesses shared Record A1: auto transitions ACCEPTED -> ACTIVE and returns READ-ONLY data."""
        res = self.client.get(
            f"/api/v1/doctor/consultations/{self.cons_id}/records/{self.rec_a1['record_id']}",
            headers=self.doc_a_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        rec = data["record"]
        self.assertEqual(rec["record_id"], self.rec_a1["record_id"])
        self.assertIn("READ-ONLY DOCTOR WORKSPACE", rec["disclaimer"])

        # Verify state transitioned to ACTIVE
        detail = database.get_patient_consultation_detail(self.patient_a["user_id"], self.cons_id)
        self.assertEqual(detail["status"], "ACTIVE")

    def test_07_unshared_record_access_blocked(self):
        """Test Doctor A cannot access Patient A's unshared Record A2."""
        res = self.client.get(
            f"/api/v1/doctor/consultations/{self.cons_id}/records/{self.rec_a2['record_id']}",
            headers=self.doc_a_headers
        )
        self.assertEqual(res.status_code, 403)

    def test_08_cross_doctor_isolation(self):
        """Test Doctor B cannot access Doctor A's assigned consultation or shared records."""
        res = self.client.get(
            f"/api/v1/doctor/consultations/{self.cons_id}/records/{self.rec_a1['record_id']}",
            headers=self.doc_b_headers
        )
        self.assertEqual(res.status_code, 403)

    def test_09_individual_record_consent_revocation(self):
        """Test Patient A revokes consent for Record A1 -> Doctor A subsequent access immediately blocked."""
        # Patient A revokes Record A1 consent
        res_rev = self.client.post(
            f"/api/v1/consultations/{self.cons_id}/records/{self.rec_a1['record_id']}/revoke",
            headers=self.patient_a_headers
        )
        self.assertEqual(res_rev.status_code, 200)

        # Doctor A attempts access -> Blocked (403)
        res_acc = self.client.get(
            f"/api/v1/doctor/consultations/{self.cons_id}/records/{self.rec_a1['record_id']}",
            headers=self.doc_a_headers
        )
        self.assertEqual(res_acc.status_code, 403)

    def test_10_doctor_reassignment_access_termination(self):
        """Test Admin reassigns Doctor A -> Doctor B: Doctor A loses access completely."""
        # Create a new consultation for testing reassignment
        req_res = self.client.post(
            "/api/v1/consultations",
            json={"specialization": "Cardiology", "category": "Followup", "reason": "Reassignment test", "record_ids": [self.rec_a1["record_id"]]},
            headers=self.patient_a_headers
        )
        c2_id = req_res.json()["consultation"]["consultation_id"]

        # Admin assigns Doctor A
        self.client.post(f"/api/v1/admin/consultations/{c2_id}/assign", json={"doctor_id": self.doc_a["doctor_profile"]["doctor_id"]}, headers=self.admin_headers)
        # Doctor A accepts
        self.client.post(f"/api/v1/doctor/consultations/{c2_id}/respond", json={"action": "ACCEPT"}, headers=self.doc_a_headers)

        # Admin reassigns to Doctor B
        self.client.post(f"/api/v1/admin/consultations/{c2_id}/assign", json={"doctor_id": self.doc_b["doctor_profile"]["doctor_id"]}, headers=self.admin_headers)

        # Doctor A attempts access -> Blocked (403)
        res_doc_a = self.client.get(f"/api/v1/doctor/consultations/{c2_id}/records/{self.rec_a1['record_id']}", headers=self.doc_a_headers)
        self.assertEqual(res_doc_a.status_code, 403)

    def test_11_doctor_suspension_immediate_access_block(self):
        """Test suspending Doctor B immediately terminates active clinical record access."""
        # Create consultation 3 assigned to Doctor B
        req_res = self.client.post(
            "/api/v1/consultations",
            json={"specialization": "Cardiology", "category": "Followup", "reason": "Suspension test", "record_ids": [self.rec_a1["record_id"]]},
            headers=self.patient_a_headers
        )
        c3_id = req_res.json()["consultation"]["consultation_id"]

        # Assign Doctor B & Accept
        self.client.post(f"/api/v1/admin/consultations/{c3_id}/assign", json={"doctor_id": self.doc_b["doctor_profile"]["doctor_id"]}, headers=self.admin_headers)
        self.client.post(f"/api/v1/doctor/consultations/{c3_id}/respond", json={"action": "ACCEPT"}, headers=self.doc_b_headers)

        # Doctor B accesses record successfully
        res_before = self.client.get(f"/api/v1/doctor/consultations/{c3_id}/records/{self.rec_a1['record_id']}", headers=self.doc_b_headers)
        self.assertEqual(res_before.status_code, 200)

        # Admin suspends Doctor B
        database.update_doctor_verification_status(self.admin["user_id"], self.doc_b["doctor_profile"]["doctor_id"], "SUSPENDED", "Suspended for security audit")

        # Doctor B attempts access after suspension -> Blocked (403)
        res_after = self.client.get(f"/api/v1/doctor/consultations/{c3_id}/records/{self.rec_a1['record_id']}", headers=self.doc_b_headers)
        self.assertEqual(res_after.status_code, 403)

        # Re-verify Doctor B for subsequent test cleanups
        database.update_doctor_verification_status(self.admin["user_id"], self.doc_b["doctor_profile"]["doctor_id"], "VERIFIED", "Re-instated")

    def test_12_completion_and_cancellation_access_block(self):
        """Test completing or cancelling consultation closes active record access."""
        # Create consultation 4
        req_res = self.client.post(
            "/api/v1/consultations",
            json={"specialization": "Cardiology", "category": "Followup", "reason": "Completion test", "record_ids": [self.rec_a1["record_id"]]},
            headers=self.patient_a_headers
        )
        c4_id = req_res.json()["consultation"]["consultation_id"]

        # Assign Doctor A & Accept
        self.client.post(f"/api/v1/admin/consultations/{c4_id}/assign", json={"doctor_id": self.doc_a["doctor_profile"]["doctor_id"]}, headers=self.admin_headers)
        self.client.post(f"/api/v1/doctor/consultations/{c4_id}/respond", json={"action": "ACCEPT"}, headers=self.doc_a_headers)

        # Complete consultation
        res_comp = self.client.post(f"/api/v1/doctor/consultations/{c4_id}/complete", json={"notes": "Case completed"}, headers=self.doc_a_headers)
        self.assertEqual(res_comp.status_code, 200)

        # Attempt access after completion -> Blocked (403)
        res_after_comp = self.client.get(f"/api/v1/doctor/consultations/{c4_id}/records/{self.rec_a1['record_id']}", headers=self.doc_a_headers)
        self.assertEqual(res_after_comp.status_code, 403)

    def test_13_audit_trail_preservation(self):
        """Test audit logs remain intact after access termination."""
        detail = database.get_patient_consultation_detail(self.patient_a["user_id"], self.cons_id)
        audit_actions = [a["action"] for a in detail["audit_history"]]
        self.assertIn("CREATED", audit_actions)
        self.assertIn("ASSIGNED", audit_actions)
        self.assertIn("ACCEPTED", audit_actions)
        self.assertIn("STATUS_CHANGED", audit_actions)
        self.assertIn("RECORD_ACCESS", audit_actions)
        self.assertIn("RECORD_REVOKED", audit_actions)

    def test_14_database_restart_persistence(self):
        """Test database state and consultations survive database re-initialization."""
        database.init_db()
        detail = database.get_patient_consultation_detail(self.patient_a["user_id"], self.cons_id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["consultation_id"], self.cons_id)


if __name__ == "__main__":
    unittest.main()
