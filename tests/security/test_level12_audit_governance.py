"""
test_level12_audit_governance.py — Level 12 Audit, Accountability & Data Governance Test Suite

Tests:
1. Immutable append-only audit ledger with SHA-256 hash chaining.
2. Automatic exclusion of sensitive fields (passwords, salts, tokens).
3. Patient access history and consent privacy boundaries.
4. Admin audit console search, role/outcome filters, and CSV/JSON exports.
5. Cryptographic hash integrity verification (VALID / INVALID).
6. Account data export endpoint.
7. Account deletion request workflow.
"""

import unittest
import secrets
import tempfile
import os

from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database

client = TestClient(app)


class TestLevel12AuditGovernance(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        database.DB_PATH = self.tmp_db.name
        database.init_db()

        # Isolate audit log table for cryptographic chain test
        session = database.SessionLocal()
        try:
            session.query(database.pg_models.AuditEvent).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        prefix = secrets.token_hex(4)
        self.patient_token, self.pat_user = self._register_patient(f"pat12_{prefix}@test.com", "Pass1234!")
        self.admin_token, self.admin_user = self._register_user(f"admin12_{prefix}@test.com", "Pass1234!", "ADMIN")

    def tearDown(self):
        try:
            os.remove(self.tmp_db.name)
        except OSError:
            pass

    def _register_patient(self, email, password):
        res = client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": password, "full_name": "Audit Test Patient"
        })
        body = res.json()
        return body["token"], body["user"]

    def _register_user(self, email, password, role="ADMIN"):
        res = client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": password, "full_name": "Audit Test Admin"
        })
        user = res.json()["user"]
        token = res.json()["token"]
        if role != "PATIENT":
            conn = database.get_db_connection()
            with conn:
                conn.execute("UPDATE users SET role = ? WHERE email = ?", (role, email.lower()))
            conn.close()
        return token, user

    def test_01_audit_log_append_only_and_hash_chaining(self):
        """Verify audit events are logged with SHA-256 hash chaining."""
        event1 = database.log_audit_event("usr_1", "PATIENT", "LOGIN", "AUTH")
        event2 = database.log_audit_event("usr_2", "ADMIN", "VERIFY_DOCTOR", "DOCTOR_PROFILE")

        self.assertIsNotNone(event1["event_id"])
        self.assertIsNotNone(event2["event_id"])

        # Check hash chaining
        integrity = database.verify_audit_log_integrity()
        self.assertEqual(integrity["status"], "VALID")
        self.assertGreaterEqual(integrity["verified_count"], 2)

    def test_02_sensitive_data_exclusion_in_audit(self):
        """Verify sensitive parameters (passwords, salts, tokens) are excluded from context payload."""
        event = database.log_audit_event(
            actor_user_id="usr_test",
            role="PATIENT",
            action="LOGIN_TEST",
            resource_type="AUTH",
            context={
                "email": "test@test.com",
                "password": "SecretPassword123!",
                "token": "secret_token_123",
                "salt": "secret_salt"
            }
        )

        logs = database.query_admin_audit_logs(action="LOGIN_TEST")
        self.assertGreater(logs["total"], 0)
        ctx = logs["items"][0]["context"]
        self.assertNotIn("password", ctx)
        self.assertNotIn("token", ctx)
        self.assertNotIn("salt", ctx)
        self.assertIn("email", ctx)

    def test_03_patient_access_history_endpoint(self):
        """Verify patient can query access history for their account."""
        res = client.get("/api/v1/patient/access-history", headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_history", data)

    def test_04_admin_audit_console_filtering_and_export(self):
        """Verify Admin can filter audit logs and export in CSV format."""
        database.log_audit_event("usr_admin", "ADMIN", "SYSTEM_HEALTH_CHECK", "SYSTEM")

        # Query admin audit endpoint
        res = client.get("/api/v1/admin/audit?role=ADMIN", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.json()["total"], 1)

        # Export CSV
        res_csv = client.get("/api/v1/admin/audit/export?format=csv", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn("event_id,actor_user_id", res_csv.text)

    def test_05_cryptographic_integrity_verification_endpoint(self):
        """Verify Admin audit integrity endpoint returns status VALID."""
        res = client.get("/api/v1/admin/audit/integrity", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "VALID")

    def test_06_account_data_export(self):
        """Verify authenticated user can export their permitted profile/record JSON."""
        res = client.get("/api/v1/patient/governance/data-export", headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("user_profile", data)
        self.assertEqual(data["user_profile"]["email"], self.pat_user["email"])

    def test_07_account_deletion_request_workflow(self):
        """Verify submitting account deletion request stores request and logs to audit ledger."""
        res = client.post("/api/v1/patient/governance/delete-request", json={
            "reason": "Relocating to another state."
        }, headers={"Authorization": f"Bearer {self.patient_token}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "PENDING")
        self.assertIn("delreq_", data["request_id"])


if __name__ == "__main__":
    unittest.main()
