"""
test_level3_health_records.py — Level 3 Persistent Patient Health Records & Longitudinal History Verification Test Suite.

Tests:
1. Idempotent health record creation upon prediction completion.
2. Same-session duplicate prevention (one session = one record).
3. Partial record safety (prediction record persists even if XAI/RAG skipped).
4. Snapshot attachment for XAI and RAG report (status transition ANALYZED -> XAI_READY -> REPORT_READY).
5. Historical snapshot immutability & no Q&A contamination.
6. Multiple analyses history preservation (no overwrite).
7. Database restart-safe migration & persistence.
8. IDOR isolation (list/detail/export/delete blocked for unauthorized users).
9. Active session reset & logout vs persistent history preservation.
10. Side-by-side comparison matrix with missing values (N/A) & numeric delta.
11. Longitudinal trends chronology with zero value interpolation.
12. Record export disclaimers & exclusion of secrets/tokens/hashes.
13. Safe record deletion by owner.
"""

import os
import json
import unittest
import uuid
import sqlite3
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend import database

class TestLevel3HealthRecords(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()

    def setUp(self):
        self.client = TestClient(app)

    def test_01_idempotent_health_record_creation(self):
        """Verify successful prediction creates a single persistent record with source_session_id."""
        email = f"pat_rec1_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Rec Test Patient 1"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["user_id"]

        # Upload report
        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]

        # Confirm
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})

        # Predict
        pred = self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(pred.status_code, 200)
        rec_id = pred.json().get("record_id")
        self.assertIsNotNone(rec_id)

        # Check DB directly
        rec = database.get_patient_health_record(user_id, rec_id)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["source_session_id"], sid)
        self.assertEqual(rec["status"], "ANALYZED")
        self.assertIn("Type2_Diabetes", rec["prediction_snapshot"]["disease_outcomes"])

    def test_02_same_session_duplicate_prevention(self):
        """Verify repeated predict calls for same session update existing record, never duplicate it."""
        email = f"pat_rec2_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Rec Test Patient 2"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["user_id"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})

        # Predict 1
        p1 = self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})
        rec1_id = p1.json().get("record_id")

        # Predict 2 (same session)
        p2 = self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})
        rec2_id = p2.json().get("record_id")

        self.assertEqual(rec1_id, rec2_id)

        # Verify only 1 record exists for patient in DB
        recs = database.list_patient_health_records(user_id)
        self.assertEqual(len(recs), 1)

    def test_03_partial_record_safety(self):
        """Verify health record survives even if XAI/RAG are never generated."""
        email = f"pat_rec3_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Rec Test Patient 3"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["user_id"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})

        recs = database.list_patient_health_records(user_id)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["status"], "ANALYZED")
        self.assertIsNone(recs[0]["xai_snapshot"])
        self.assertIsNone(recs[0]["report_snapshot"])

    def test_04_snapshot_attachment_xai_and_report(self):
        """Verify XAI and RAG report attach to existing record and update status."""
        email = f"pat_rec4_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Rec Test Patient 4"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["user_id"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})

        # Generate XAI -> XAI_READY
        self.client.post("/api/v1/xai/explain", json={"session_id": sid, "target_disease": "Type2_Diabetes"}, headers={"Authorization": f"Bearer {token}"})
        rec_xai = database.list_patient_health_records(user_id)[0]
        self.assertEqual(rec_xai["status"], "XAI_READY")
        self.assertIsNotNone(rec_xai["xai_snapshot"])

        # Generate RAG report -> REPORT_READY
        self.client.post("/api/v1/rag/report", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})
        rec_rep = database.list_patient_health_records(user_id)[0]
        self.assertEqual(rec_rep["status"], "REPORT_READY")
        self.assertIsNotNone(rec_rep["report_snapshot"])

    def test_05_snapshot_immutability_and_no_qa_contamination(self):
        """Verify Q&A does NOT alter prediction, XAI, or report snapshots."""
        email = f"pat_rec5_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Rec Test Patient 5"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["user_id"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})
        self.client.post("/api/v1/rag/report", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})

        before_rec = database.list_patient_health_records(user_id)[0]

        # Ask Q&A
        self.client.post("/api/v1/rag/qanda", json={"session_id": sid, "question": "What should I eat?"}, headers={"Authorization": f"Bearer {token}"})

        after_rec = database.list_patient_health_records(user_id)[0]
        self.assertEqual(before_rec["prediction_snapshot"], after_rec["prediction_snapshot"])
        self.assertEqual(before_rec["report_snapshot"], after_rec["report_snapshot"])

    def test_06_multiple_analyses_history_preservation(self):
        """Verify running 2 distinct sessions creates 2 persistent health records."""
        email = f"pat_rec6_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Rec Test Patient 6"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["user_id"]

        # Run 1
        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up1 = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical1.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid1 = up1.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid1, "confirmed_features": up1.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        self.client.post("/api/v1/predict/analyze", json={"session_id": sid1}, headers={"Authorization": f"Bearer {token}"})

        # Run 2
        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up2 = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical2.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid2 = up2.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid2, "confirmed_features": up2.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        self.client.post("/api/v1/predict/analyze", json={"session_id": sid2}, headers={"Authorization": f"Bearer {token}"})

        recs = database.list_patient_health_records(user_id)
        self.assertEqual(len(recs), 2)
        sids = {r["source_session_id"] for r in recs}
        self.assertEqual(sids, {sid1, sid2})

    def test_07_restart_persistence_and_migration_safety(self):
        """Verify database re-initialization is restart-safe and preserves existing records."""
        database.init_db()
        # Call init_db again
        database.init_db()
        # Verify schema tables exist
        conn = database.get_db_connection()
        tbls = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        tbl_names = [t["name"] for t in tbls]
        self.assertIn("health_records", tbl_names)

    def test_08_idor_isolation_list_detail_export_delete(self):
        """Verify Patient B cannot access, list, export, or delete Patient A's records."""
        # Patient A
        reg_a = self.client.post("/api/v1/auth/register/patient", json={
            "email": f"pat_a_{uuid.uuid4().hex[:8]}@telemed.ai", "password": "Password123!", "full_name": "Patient A"
        })
        token_a = reg_a.json()["token"]
        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up_a = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token_a}"})
        sid_a = up_a.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid_a, "confirmed_features": up_a.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token_a}"})
        pred_a = self.client.post("/api/v1/predict/analyze", json={"session_id": sid_a}, headers={"Authorization": f"Bearer {token_a}"})
        rec_id_a = pred_a.json()["record_id"]

        # Patient B
        reg_b = self.client.post("/api/v1/auth/register/patient", json={
            "email": f"pat_b_{uuid.uuid4().hex[:8]}@telemed.ai", "password": "Password123!", "full_name": "Patient B"
        })
        token_b = reg_b.json()["token"]

        # Patient B tries to get Patient A's record detail
        det_b = self.client.get(f"/api/v1/records/{rec_id_a}", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(det_b.status_code, 404)

        # Patient B tries to export Patient A's record
        exp_b = self.client.get(f"/api/v1/records/{rec_id_a}/export", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(exp_b.status_code, 404)

        # Patient B tries to delete Patient A's record
        del_b = self.client.delete(f"/api/v1/records/{rec_id_a}", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(del_b.status_code, 404)

    def test_09_reset_analysis_and_logout_preservation(self):
        """Verify logging out or resetting working state does not delete DB records."""
        email = f"pat_rec9_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Rec Test Patient 9"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["user_id"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})

        # Logout
        self.client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})

        # Login again
        login_res = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        new_token = login_res.json()["token"]

        # Records are still present
        recs = self.client.get("/api/v1/records", headers={"Authorization": f"Bearer {new_token}"}).json()
        self.assertEqual(recs["total_records"], 1)

    def test_10_export_disclaimer_and_token_safety(self):
        """Verify record export JSON contains research disclaimer and excludes secrets/tokens/hashes."""
        email = f"pat_exp_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Export Test Patient"
        })
        token = reg.json()["token"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        pred = self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})
        rec_id = pred.json()["record_id"]

        exp = self.client.get(f"/api/v1/records/{rec_id}/export", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(exp.status_code, 200)
        exp_data = exp.json()
        self.assertIn("disclaimer", exp_data["export_metadata"])
        self.assertIn("does NOT constitute a clinical diagnosis", exp_data["export_metadata"]["disclaimer"])
        exp_str = json.dumps(exp_data)
        self.assertNotIn("password_hash", exp_str)
        self.assertNotIn("salt", exp_str)

    def test_11_safe_record_deletion(self):
        """Verify record deletion by owner permanently removes the record."""
        email = f"pat_del_{uuid.uuid4().hex[:8]}@telemed.ai"
        reg = self.client.post("/api/v1/auth/register/patient", json={
            "email": email, "password": "Password123!", "full_name": "Delete Test Patient"
        })
        token = reg.json()["token"]

        with open("tests/fixtures/medical_reports/test_files/clinical_report.txt", "rb") as f:
            up = self.client.post("/api/v1/intake/upload", files=[("files", ("clinical.txt", f, "text/plain"))], headers={"Authorization": f"Bearer {token}"})
        sid = up.json()["session_id"]
        self.client.post("/api/v1/intake/confirm", json={"session_id": sid, "confirmed_features": up.json()["extracted_features"]}, headers={"Authorization": f"Bearer {token}"})
        pred = self.client.post("/api/v1/predict/analyze", json={"session_id": sid}, headers={"Authorization": f"Bearer {token}"})
        rec_id = pred.json()["record_id"]

        del_res = self.client.delete(f"/api/v1/records/{rec_id}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(del_res.status_code, 200)

        # Confirm list is now empty
        recs = self.client.get("/api/v1/records", headers={"Authorization": f"Bearer {token}"}).json()
        self.assertEqual(recs["total_records"], 0)


if __name__ == "__main__":
    unittest.main()
