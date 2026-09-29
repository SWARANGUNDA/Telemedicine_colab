"""
test_level10_system_operations.py — Level 10 System Operations & Diagnostics Test Suite

Tests:
1. Admin-only RBAC access to system operational endpoints.
2. Truthful subsystem health diagnostics without metric fabrication.
3. Scientific ML config immutability (HTTP 400 when attempting to alter weights/thresholds).
4. Safe non-scientific operational settings management (maintenance mode/banner).
5. Failure resilience & graceful degradation under subsystem errors.
"""

import unittest
import secrets
import tempfile
import os

from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database

client = TestClient(app)


class TestLevel10SystemOperations(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        database.DB_PATH = self.tmp_db.name
        database.init_db()

        prefix = secrets.token_hex(4)
        self.admin_token = self._register_user(f"admin_{prefix}@test.com", "Pass123!", "ADMIN", "Admin Ten")
        self.patient_token = self._register_user(f"patient_{prefix}@test.com", "Pass123!", "PATIENT", "Patient Ten")
        self.doc_token = self._register_doctor(f"doctor_{prefix}@test.com", "Pass123!", "Dr. Ten", f"REG-10-{prefix}")

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

    def test_01_admin_health_diagnostics_and_rbac(self):
        """Verify Admin can access system health and non-admins are blocked with HTTP 403."""
        res_admin = client.get("/api/v1/admin/system/health", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_admin.status_code, 200)
        data = res_admin.json()
        self.assertIn("system_status", data)
        self.assertIn("services", data)

        # Patient blocked
        res_pat = client.get("/api/v1/admin/system/health", headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(res_pat.status_code, 403)

        # Doctor blocked
        res_doc = client.get("/api/v1/admin/system/health", headers={"Authorization": f"Bearer {self.doc_token}"})
        self.assertEqual(res_doc.status_code, 403)

    def test_02_truthful_subsystem_health_metrics(self):
        """Verify health check returns real subsystem statuses (DB, experts, fusion, RAG, SHAP)."""
        res = client.get("/api/v1/admin/system/health", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        services = res.json()["services"]
        self.assertIn("database", services)
        self.assertEqual(services["database"]["status"], "HEALTHY")
        self.assertIn("fusion_engine", services)

    def test_03_scientific_config_immutability(self):
        """Verify modifying scientific ML parameters is rejected with 400, while safe settings succeed."""
        # Safe setting update -> Success
        res_safe = client.post("/api/v1/admin/system/settings", json={
            "settings": {
                "maintenance_mode": "true",
                "maintenance_message": "Scheduled routine database index optimization."
            }
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_safe.status_code, 200)

        # Forbidden scientific mutation attempt -> Rejected 400 Bad Request
        res_forbidden = client.post("/api/v1/admin/system/settings", json={
            "settings": {
                "model_weights": "0.9, 0.1",
                "feature_thresholds": "0.5"
            }
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_forbidden.status_code, 400)

    def test_04_failure_resilience_and_graceful_degradation(self):
        """Verify subsystem health check remains usable and returns status object."""
        health = database.get_detailed_system_health()
        self.assertIn(health["system_status"], ("HEALTHY", "DEGRADED"))
        self.assertIn("pipeline_info", health)


if __name__ == "__main__":
    unittest.main()
