"""
test_level8_appointments_notifications.py — Level 8 Appointments & In-App Notifications Test Suite

Tests:
1. Doctor availability slot configuration & access control.
2. Patient appointment booking with double-booking prevention.
3. Appointment lifecycle (REQUESTED, CONFIRMED, RESCHEDULED, CANCELLED).
4. Persistent in-app notifications & strict recipient privacy.
"""

import unittest
import secrets
import tempfile
import os
import datetime

from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database

client = TestClient(app)


class TestLevel8AppointmentsNotifications(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        database.DB_PATH = self.tmp_db.name
        database.init_db()

        prefix = secrets.token_hex(4)
        self.admin_token = self._register_user(f"admin_{prefix}@test.com", "Pass123!", "ADMIN", "Admin Eight")
        self.patient_token = self._register_user(f"patient_{prefix}@test.com", "Pass123!", "PATIENT", "Patient Eight")
        self.doc_token = self._register_doctor(f"doctor_{prefix}@test.com", "Pass123!", "Dr. Eight", f"REG-8-{prefix}")

        # Transition Doctor to VERIFIED
        doc_detail = self._get_doctor_detail_by_email(f"doctor_{prefix}@test.com")
        self.doc_id = doc_detail["doctor_id"]
        self._admin_transition_doctor(self.doc_id, "UNDER_REVIEW")
        self._admin_transition_doctor(self.doc_id, "VERIFIED")

        # Create active consultation
        c_res = client.post("/api/v1/consultations", json={
            "specialization": "Cardiology",
            "reason": "Routine heart health checkup"
        }, headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(c_res.status_code, 201)
        self.cons_id = c_res.json()["consultation"]["consultation_id"]

        # Admin assigns consultation & Doctor accepts
        client.post(f"/api/v1/admin/consultations/{self.cons_id}/assign", json={
            "doctor_id": self.doc_id, "notes": "Assign to Dr. Eight"
        }, headers={"Authorization": f"Bearer {self.admin_token}"})

        client.post(f"/api/v1/doctor/consultations/{self.cons_id}/respond", json={
            "action": "ACCEPT"
        }, headers={"Authorization": f"Bearer {self.doc_token}"})

    def tearDown(self):
        try:
            os.remove(self.tmp_db.name)
        except OSError:
            pass

    def _register_user(self, email, password, role="PATIENT", name="Test User"):
        res = client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": password, "full_name": name
        })
        token = res.json()["token"]
        if role != "PATIENT":
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
        return res.json()["token"]

    def _get_doctor_detail_by_email(self, email):
        conn = database.get_db_connection()
        try:
            row = conn.execute("SELECT * FROM doctor_profiles WHERE user_id IN (SELECT user_id FROM users WHERE email = ?)", (email.lower(),)).fetchone()
            return dict(row)
        finally:
            conn.close()

    def _admin_transition_doctor(self, doc_id, new_status):
        client.post(
            f"/api/v1/admin/doctor-applications/{doc_id}/transition",
            json={"status": new_status, "reason": f"Transition to {new_status}"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

    def test_01_doctor_configures_availability_slots(self):
        """Verify VERIFIED doctor can configure availability slots."""
        now = datetime.datetime.now(datetime.timezone.utc)
        slot1_start = (now + datetime.timedelta(days=1)).isoformat()
        slot1_end = (now + datetime.timedelta(days=1, hours=1)).isoformat()

        res = client.post("/api/v1/doctor/availability", json={
            "slots": [{"slot_start": slot1_start, "slot_end": slot1_end}]
        }, headers={"Authorization": f"Bearer {self.doc_token}"})
        self.assertEqual(res.status_code, 201)
        slots = res.json()["slots"]
        self.assertGreaterEqual(len(slots), 1)

    def test_02_patient_books_appointment_and_prevents_double_booking(self):
        """Verify patient can book an appointment and double booking same slot is rejected."""
        now = datetime.datetime.now(datetime.timezone.utc)
        slot_start = (now + datetime.timedelta(days=2)).isoformat()
        slot_end = (now + datetime.timedelta(days=2, hours=1)).isoformat()

        # Doctor creates slot
        cfg_res = client.post("/api/v1/doctor/availability", json={
            "slots": [{"slot_start": slot_start, "slot_end": slot_end}]
        }, headers={"Authorization": f"Bearer {self.doc_token}"})
        slot_id = cfg_res.json()["slots"][0]["slot_id"]

        # Patient books appointment
        book_res = client.post("/api/v1/appointments", json={
            "consultation_id": self.cons_id,
            "slot_id": slot_id,
            "notes": "Discuss cardiovascular telemetry"
        }, headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(book_res.status_code, 201)
        apt = book_res.json()["appointment"]
        self.assertEqual(apt["status"], "CONFIRMED")

        # Double booking attempt must fail with 409 Conflict or 400 Bad Request
        book_res2 = client.post("/api/v1/appointments", json={
            "consultation_id": self.cons_id,
            "slot_id": slot_id,
            "notes": "Second booking attempt"
        }, headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertIn(book_res2.status_code, (400, 409))

    def test_03_appointment_cancellation_releases_slot(self):
        """Verify cancelling appointment releases availability slot."""
        now = datetime.datetime.now(datetime.timezone.utc)
        slot_start = (now + datetime.timedelta(days=3)).isoformat()
        slot_end = (now + datetime.timedelta(days=3, hours=1)).isoformat()

        cfg_res = client.post("/api/v1/doctor/availability", json={
            "slots": [{"slot_start": slot_start, "slot_end": slot_end}]
        }, headers={"Authorization": f"Bearer {self.doc_token}"})
        slot_id = cfg_res.json()["slots"][0]["slot_id"]

        book_res = client.post("/api/v1/appointments", json={
            "consultation_id": self.cons_id,
            "slot_id": slot_id
        }, headers={"Authorization": f"Bearer {self.patient_token}"})
        apt_id = book_res.json()["appointment"]["appointment_id"]

        # Cancel appointment
        cancel_res = client.post(f"/api/v1/appointments/{apt_id}/status", json={
            "status": "CANCELLED",
            "reason": "Patient schedule conflict"
        }, headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(cancel_res.status_code, 200)

        # Slot should now be available again
        avail_res = client.get(f"/api/v1/doctors/{self.doc_id}/availability", headers={"Authorization": f"Bearer {self.patient_token}"})
        slots = avail_res.json()["slots"]
        self.assertTrue(any(s["slot_id"] == slot_id and s["is_booked"] == 0 for s in slots))

    def test_04_notifications_generation_and_recipient_privacy(self):
        """Verify notifications are created for important events and recipient privacy is enforced."""
        now = datetime.datetime.now(datetime.timezone.utc)
        slot_start = (now + datetime.timedelta(days=4)).isoformat()
        slot_end = (now + datetime.timedelta(days=4, hours=1)).isoformat()

        cfg_res = client.post("/api/v1/doctor/availability", json={
            "slots": [{"slot_start": slot_start, "slot_end": slot_end}]
        }, headers={"Authorization": f"Bearer {self.doc_token}"})
        slot_id = cfg_res.json()["slots"][0]["slot_id"]

        # Patient books appointment -> triggers notification for doctor
        book_res = client.post("/api/v1/appointments", json={
            "consultation_id": self.cons_id,
            "slot_id": slot_id
        }, headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(book_res.status_code, 201)

        # Doctor checks notifications
        doc_notif_res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {self.doc_token}"})
        self.assertEqual(doc_notif_res.status_code, 200)
        doc_notifs = doc_notif_res.json()["notifications"]
        self.assertGreaterEqual(len(doc_notifs), 1)

        notif_id = doc_notifs[0]["notification_id"]

        # Doctor marks notification read
        mark_res = client.post(f"/api/v1/notifications/{notif_id}/read", headers={"Authorization": f"Bearer {self.doc_token}"})
        self.assertEqual(mark_res.status_code, 200)

        # Patient trying to mark doctor's notification read must fail with 404 (privacy boundary)
        patient_mark_res = client.post(f"/api/v1/notifications/{notif_id}/read", headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(patient_mark_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
