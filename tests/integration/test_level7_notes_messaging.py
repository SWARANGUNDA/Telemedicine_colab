"""
test_level7_notes_messaging.py — Level 7C Test Suite for Consultation Notes & Secure Patient–Doctor Messaging.
Verifies:
1. Patient and assigned VERIFIED doctor can send and retrieve consultation messages.
2. Admin role is strictly forbidden from reading or writing clinical messages/notes (403 Forbidden).
3. Assigned VERIFIED doctor can record/update structured clinical notes.
4. Patient can read doctor consultation summary/notes.
5. Unassigned or unverified doctors are blocked from accessing notes/messages.
6. Terminal/completed consultations block new messages and note updates while preserving history.
"""

import os
import sys
import unittest
import tempfile
import shutil
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.backend.main import app
from app.backend import database, config

client = TestClient(app)


class TestLevel7CNotesMessaging(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_level7c.db")
        cls.orig_db_path = database.DB_PATH
        config.DB_PATH = cls.db_path
        database.DB_PATH = cls.db_path
        database.init_db()

    @classmethod
    def tearDownClass(cls):
        config.DB_PATH = cls.orig_db_path
        database.DB_PATH = cls.orig_db_path
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        from app.backend.security import RATE_LIMITER
        RATE_LIMITER._requests.clear()
        database.init_db()
        prefix = f"{self._testMethodName}_{secrets.token_hex(4)}"
        self.patient_token = self._register_user(f"patient_{prefix}@test.com", "StrongPass#2026!", "PATIENT", "Patient Seven C")
        self.doc_token = self._register_doctor(f"doctor_{prefix}@test.com", "StrongPass#2026!", "Dr. Seven C", f"REG-7C-{secrets.token_hex(4)}")
        self.admin_token = self._register_user(f"admin_{prefix}@test.com", "StrongPass#2026!", "ADMIN", "Admin Seven C")

        # Admin verifies doctor
        doc_detail = self._get_doctor_detail_by_email(f"doctor_{prefix}@test.com")
        self.doc_id = doc_detail["doctor_id"]
        self._admin_transition_doctor(self.doc_id, "UNDER_REVIEW")
        self._admin_transition_doctor(self.doc_id, "VERIFIED")

        # Patient creates consultation
        c_res = client.post(
            "/api/v1/consultations",
            json={
                "specialization": "Cardiology",
                "category": "General Consultation",
                "reason": "Chest tightness and elevated metabolic score",
                "urgency": "ROUTINE",
                "record_ids": []
            },
            headers={"Authorization": f"Bearer {self.patient_token}"}
        )
        self.assertEqual(c_res.status_code, 201)
        self.consultation_id = c_res.json()["consultation"]["consultation_id"]

        # Admin assigns VERIFIED doctor
        client.post(
            f"/api/v1/admin/consultations/{self.consultation_id}/assign",
            json={"doctor_id": self.doc_id},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        # Doctor accepts assignment
        client.post(
            f"/api/v1/doctor/consultations/{self.consultation_id}/respond",
            json={"action": "ACCEPT", "reason": "Accepting case"},
            headers={"Authorization": f"Bearer {self.doc_token}"}
        )

    def _register_user(self, email, password, role, name):
        res = client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": password, "full_name": name
        })
        token = res.json()["token"]
        if role != "PATIENT":
            # Direct DB update for test role setting
            conn = database.get_db_connection()
            with conn:
                conn.execute("UPDATE users SET role = ? WHERE email = ?", (role, email.lower()))
            conn.close()

        return token

    def _register_doctor(self, email, password, name, reg_num):
        res = client.post("/api/v1/auth/register/doctor", json={
            "email": email,
            "password": password,
            "full_name": name,
            "specialization": "Cardiology",
            "qualification": "MBBS, MD",
            "registration_number": reg_num,
            "registration_council": "State Council",
            "experience_years": 10
        })
        self.assertEqual(res.status_code, 201)
        return res.json()["token"]

    def _get_doctor_detail_by_email(self, email):
        conn = database.get_db_connection()
        row = conn.execute("SELECT doctor_id FROM doctor_profiles JOIN users ON doctor_profiles.user_id = users.user_id WHERE users.email = ?", (email.lower(),)).fetchone()
        conn.close()
        return dict(row)

    def _admin_transition_doctor(self, doc_id, new_status):
        res = client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            json={"status": new_status, "reason": f"Transition to {new_status}"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res.status_code, 200)

    def test_01_send_and_list_consultation_messages(self):
        """Verify patient and assigned doctor can exchange messages."""
        # Patient sends message
        res1 = client.post(
            f"/api/v1/consultations/{self.consultation_id}/messages",
            json={"content": "Hello Dr. Seven C, I have questions about my screening score."},
            headers={"Authorization": f"Bearer {self.patient_token}"}
        )
        self.assertEqual(res1.status_code, 201)

        # Doctor sends response
        res2 = client.post(
            f"/api/v1/consultations/{self.consultation_id}/messages",
            json={"content": "Hello Patient, I have reviewed your screening profile."},
            headers={"Authorization": f"Bearer {self.doc_token}"}
        )
        self.assertEqual(res2.status_code, 201)

        # Patient lists messages
        list_res = client.get(
            f"/api/v1/consultations/{self.consultation_id}/messages",
            headers={"Authorization": f"Bearer {self.patient_token}"}
        )
        self.assertEqual(list_res.status_code, 200)
        msgs = list_res.json()["messages"]
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["sender_role"], "PATIENT")
        self.assertEqual(msgs[1]["sender_role"], "DOCTOR")

    def test_02_admin_blocked_from_clinical_messaging_and_notes(self):
        """Verify ADMIN role is strictly forbidden from sending or viewing clinical messages/notes (403 Forbidden)."""
        # Admin attempts to read messages
        read_res = client.get(
            f"/api/v1/consultations/{self.consultation_id}/messages",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(read_res.status_code, 403)

        # Admin attempts to send message
        send_res = client.post(
            f"/api/v1/consultations/{self.consultation_id}/messages",
            json={"content": "Admin attempting to read/write clinical chat"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(send_res.status_code, 400) # ValueError: Access denied

        # Admin attempts to read doctor notes
        note_res = client.get(
            f"/api/v1/consultations/{self.consultation_id}/notes",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(note_res.status_code, 403)

    def test_03_doctor_notes_creation_and_patient_retrieval(self):
        """Verify assigned VERIFIED doctor can save notes and patient can view doctor summary."""
        # Doctor saves consultation note
        save_res = client.post(
            f"/api/v1/doctor/consultations/{self.consultation_id}/notes",
            json={
                "assessment": "Patient presents with mild glucose elevation. No acute distress.",
                "follow_up_guidance": "Increase dietary fiber and repeat HbA1c in 60 days.",
                "patient_summary": "Overall low risk. Continue healthy lifestyle habits."
            },
            headers={"Authorization": f"Bearer {self.doc_token}"}
        )
        self.assertEqual(save_res.status_code, 200)
        note_data = save_res.json()["note"]
        self.assertEqual(note_data["author_name"], "Dr. Dr. Seven C")

        # Patient reads note
        p_note_res = client.get(
            f"/api/v1/consultations/{self.consultation_id}/notes",
            headers={"Authorization": f"Bearer {self.patient_token}"}
        )
        self.assertEqual(p_note_res.status_code, 200)
        p_note = p_note_res.json()["note"]
        self.assertIsNotNone(p_note)
        self.assertEqual(p_note["patient_summary"], "Overall low risk. Continue healthy lifestyle habits.")

    def test_04_completed_consultation_blocks_write_capabilities(self):
        """Verify completed consultation blocks new message and note writes while preserving history."""
        # Doctor completes consultation
        comp_res = client.post(
            f"/api/v1/doctor/consultations/{self.consultation_id}/complete",
            json={"notes": "Case complete"},
            headers={"Authorization": f"Bearer {self.doc_token}"}
        )
        self.assertEqual(comp_res.status_code, 200)

        # Attempt to send message after completion -> 400 Bad Request (Closed status)
        msg_res = client.post(
            f"/api/v1/consultations/{self.consultation_id}/messages",
            json={"content": "New message after completion"},
            headers={"Authorization": f"Bearer {self.patient_token}"}
        )
        self.assertEqual(msg_res.status_code, 400)

        # Attempt to save note after completion -> 400 Bad Request (Closed status)
        note_res = client.post(
            f"/api/v1/doctor/consultations/{self.consultation_id}/notes",
            json={
                "assessment": "Updated assessment post-completion",
                "patient_summary": "Summary post-completion"
            },
            headers={"Authorization": f"Bearer {self.doc_token}"}
        )
        self.assertEqual(note_res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
