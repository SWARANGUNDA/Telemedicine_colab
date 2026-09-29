"""
test_level7d_admin_dashboard.py — Level 7D Admin Operations Dashboard & User Directory Test Suite

Tests:
1. Admin overview stats with real DB-backed metrics (total_patients, total_doctors, verified_doctors, pending_doctors, requested_consultations, active_consultations, completed_consultations).
2. Verification queue preview, consultation queue preview, and recent activity stream in admin stats.
3. User directory endpoint with role filtering and search.
4. Non-admin roles (PATIENT, DOCTOR) blocked with 403 Forbidden.
"""

import unittest
import secrets
import tempfile
import os

from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database

client = TestClient(app)


class TestLevel7DAdminDashboard(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        database.DB_PATH = self.tmp_db.name
        database.init_db()

        prefix = secrets.token_hex(4)
        self.admin_token = self._register_user(f"admin_{prefix}@test.com", "Pass123!", "ADMIN", "Admin User 7D")
        self.patient_token = self._register_user(f"patient_{prefix}@test.com", "Pass123!", "PATIENT", "Patient User 7D")
        self.doc_token = self._register_doctor(f"doctor_{prefix}@test.com", "Pass123!", "Dr. Doctor 7D", f"REG-7D-{prefix}")

    def tearDown(self):
        try:
            os.remove(self.tmp_db.name)
        except OSError:
            pass

    def _register_user(self, email, password, role, name):
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

    def test_01_admin_dashboard_stats_metrics_and_previews(self):
        """Verify GET /api/v1/admin/stats returns all required DB metrics and queue previews."""
        res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("stats", data)
        stats = data["stats"]

        # Metric keys check
        required_keys = [
            "total_users", "total_patients", "total_doctors",
            "verified_doctors", "pending_doctors",
            "requested_consultations", "active_consultations", "completed_consultations",
            "verification_preview", "consultation_preview", "recent_activity"
        ]
        for key in required_keys:
            self.assertIn(key, stats, f"Missing metric key: {key}")

        self.assertGreaterEqual(stats["total_users"], 3)
        self.assertGreaterEqual(stats["total_patients"], 1)
        self.assertGreaterEqual(stats["total_doctors"], 1)
        self.assertGreaterEqual(stats["pending_doctors"], 1)

    def test_02_admin_user_directory_role_filters_and_search(self):
        """Verify GET /api/v1/admin/users supports role filters and text search."""
        # List all users
        res_all = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_all.status_code, 200)
        users_all = res_all.json()["users"]
        self.assertGreaterEqual(len(users_all), 3)

        # Filter PATIENT
        res_pat = client.get("/api/v1/admin/users?role=PATIENT", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_pat.status_code, 200)
        p_users = res_pat.json()["users"]
        for u in p_users:
            self.assertEqual(u["role"], "PATIENT")

        # Filter DOCTOR
        res_doc = client.get("/api/v1/admin/users?role=DOCTOR", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_doc.status_code, 200)
        d_users = res_doc.json()["users"]
        for u in d_users:
            self.assertEqual(u["role"], "DOCTOR")

        # Search by query
        res_search = client.get("/api/v1/admin/users?search=Doctor", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_search.status_code, 200)
        s_users = res_search.json()["users"]
        self.assertTrue(any("Doctor" in (u.get("full_name") or u.get("email")) for u in s_users))

    def test_03_non_admin_users_blocked_from_admin_endpoints(self):
        """Verify non-admin roles (PATIENT/DOCTOR) receive 403 Forbidden on admin endpoints."""
        # Patient attempt
        p_res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(p_res.status_code, 403)

        # Doctor attempt
        d_res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {self.doc_token}"})
        self.assertEqual(d_res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
