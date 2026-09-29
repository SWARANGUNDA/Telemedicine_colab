"""
etl_migrate_sqlite_to_postgres.py — One-Time ETL Data Migration from legacy SQLite to PostgreSQL 17.
"""

import sys
import sqlite3
import logging
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from database.db import SessionLocal, check_db_connection
from models.models import (
    User,
    PatientProfile,
    DoctorProfile,
    DoctorCredential,
    DoctorAuditLog,
    AuthSession,
    HealthRecord,
    Assessment,
    Consultation,
    ConsultationSharedRecord,
    ConsultationAuditLog,
    ConsultationMessage,
    ConsultationNote,
    DoctorAvailabilitySlot,
    Appointment,
    Notification,
    SystemSetting,
    AuditEvent,
    AccountDeletionRequest,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("etl_migration")

SQLITE_DB_PATH = backend_dir / "telemed.db"


def run_etl_migration():
    logger.info("Starting One-Time ETL Data Migration from SQLite to PostgreSQL 17...")

    if not check_db_connection():
        logger.error("PostgreSQL 17 container is unreachable! Please start docker containers.")
        sys.exit(1)

    if not SQLITE_DB_PATH.exists():
        logger.info(f"SQLite database file not found at {SQLITE_DB_PATH}. Skipping ETL.")
        return

    sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    pg_session = SessionLocal()

    migration_counts = {}

    try:
        # 1. Migrate Users
        sqlite_cursor.execute("SELECT * FROM users")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(User).filter_by(user_id=r["user_id"]).first()
            if not existing:
                u = User(
                    user_id=r["user_id"],
                    email=r["email"],
                    password_hash=r["password_hash"],
                    salt=r["salt"],
                    role=r["role"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                pg_session.add(u)
                count += 1
        pg_session.commit()
        migration_counts["users"] = count

        # 2. Migrate Patient Profiles
        sqlite_cursor.execute("SELECT * FROM patient_profiles")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(PatientProfile).filter_by(patient_id=r["patient_id"]).first()
            if not existing:
                p = PatientProfile(
                    patient_id=r["patient_id"],
                    user_id=r["user_id"],
                    full_name=r["full_name"],
                    age=r["age"],
                    gender=r["gender"],
                    height_cm=r["height_cm"],
                    weight_kg=r["weight_kg"],
                    contact_number=r["contact_number"],
                    created_at=r["created_at"],
                )
                pg_session.add(p)
                count += 1
        pg_session.commit()
        migration_counts["patient_profiles"] = count

        # 3. Migrate Doctor Profiles
        sqlite_cursor.execute("SELECT * FROM doctor_profiles")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(DoctorProfile).filter_by(doctor_id=r["doctor_id"]).first()
            if not existing:
                d = DoctorProfile(
                    doctor_id=r["doctor_id"],
                    user_id=r["user_id"],
                    full_name=r["full_name"],
                    specialization=r["specialization"],
                    qualification=r.dict().get("qualification") if hasattr(r, 'dict') else (r["qualification"] if "qualification" in r.keys() else None),
                    registration_number=r["registration_number"],
                    registration_council=r["registration_council"] if "registration_council" in r.keys() else None,
                    experience_years=r["experience_years"] if "experience_years" in r.keys() else 0,
                    contact_number=r["contact_number"] if "contact_number" in r.keys() else None,
                    hospital_affiliation=r["hospital_affiliation"] if "hospital_affiliation" in r.keys() else None,
                    verification_status=r["verification_status"] if "verification_status" in r.keys() else "PENDING",
                    credential_notes=r["credential_notes"] if "credential_notes" in r.keys() else None,
                    created_at=r["created_at"],
                )
                pg_session.add(d)
                count += 1
        pg_session.commit()
        migration_counts["doctor_profiles"] = count

        # 4. Migrate Doctor Credentials
        sqlite_cursor.execute("SELECT * FROM doctor_credentials")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(DoctorCredential).filter_by(document_id=r["document_id"]).first()
            if not existing:
                dc = DoctorCredential(
                    document_id=r["document_id"],
                    doctor_id=r["doctor_id"],
                    user_id=r["user_id"],
                    document_type=r["document_type"],
                    original_filename=r["original_filename"],
                    stored_filename=r["stored_filename"],
                    file_path=r["file_path"],
                    file_size_bytes=r["file_size_bytes"],
                    mime_type=r["mime_type"],
                    uploaded_at=r["uploaded_at"],
                )
                pg_session.add(dc)
                count += 1
        pg_session.commit()
        migration_counts["doctor_credentials"] = count

        # 5. Migrate Auth Sessions
        sqlite_cursor.execute("SELECT * FROM auth_sessions")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(AuthSession).filter_by(token=r["token"]).first()
            if not existing:
                s = AuthSession(
                    token=r["token"],
                    user_id=r["user_id"],
                    expires_at=r["expires_at"],
                    created_at=r["created_at"],
                )
                pg_session.add(s)
                count += 1
        pg_session.commit()
        migration_counts["auth_sessions"] = count

        # 6. Migrate Health Records
        sqlite_cursor.execute("SELECT * FROM health_records")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(HealthRecord).filter_by(record_id=r["record_id"]).first()
            if not existing:
                hr = HealthRecord(
                    record_id=r["record_id"],
                    user_id=r["user_id"],
                    source_session_id=r["source_session_id"],
                    patient_id=r["patient_id"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    pipeline_version=r["pipeline_version"],
                    schema_version=r["schema_version"],
                    effective_pathway=r["effective_pathway"],
                    data_quality_score=r["data_quality_score"],
                    active_modalities=r["active_modalities"],
                    confirmed_features=r["confirmed_features"],
                    prediction_snapshot=r["prediction_snapshot"],
                    xai_snapshot=r["xai_snapshot"],
                    report_snapshot=r["report_snapshot"],
                    status=r["status"],
                )
                pg_session.add(hr)
                count += 1
        pg_session.commit()
        migration_counts["health_records"] = count

        # 7. Migrate Consultations
        sqlite_cursor.execute("SELECT * FROM consultations")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(Consultation).filter_by(consultation_id=r["consultation_id"]).first()
            if not existing:
                c = Consultation(
                    consultation_id=r["consultation_id"],
                    patient_id=r["patient_id"],
                    user_id=r["user_id"],
                    assigned_doctor_id=r["assigned_doctor_id"],
                    specialization=r["specialization"],
                    category=r["category"],
                    reason=r["reason"],
                    urgency=r["urgency"],
                    message=r["message"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    completed_at=r["completed_at"],
                )
                pg_session.add(c)
                count += 1
        pg_session.commit()
        migration_counts["consultations"] = count

        # 8. Migrate Consultation Shared Records
        sqlite_cursor.execute("SELECT * FROM consultation_shared_records")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(ConsultationSharedRecord).filter_by(share_id=r["share_id"]).first()
            if not existing:
                csr = ConsultationSharedRecord(
                    share_id=r["share_id"],
                    consultation_id=r["consultation_id"],
                    patient_id=r["patient_id"],
                    record_id=r["record_id"],
                    status=r["status"],
                    shared_at=r["shared_at"],
                    revoked_at=r["revoked_at"],
                )
                pg_session.add(csr)
                count += 1
        pg_session.commit()
        migration_counts["consultation_shared_records"] = count

        # 9. Migrate Consultation Messages
        sqlite_cursor.execute("SELECT * FROM consultation_messages")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(ConsultationMessage).filter_by(message_id=r["message_id"]).first()
            if not existing:
                cm = ConsultationMessage(
                    message_id=r["message_id"],
                    consultation_id=r["consultation_id"],
                    sender_user_id=r["sender_user_id"],
                    sender_role=r["sender_role"],
                    sender_name=r["sender_name"],
                    content=r["content"],
                    created_at=r["created_at"],
                )
                pg_session.add(cm)
                count += 1
        pg_session.commit()
        migration_counts["consultation_messages"] = count

        # 10. Migrate Consultation Notes
        sqlite_cursor.execute("SELECT * FROM consultation_notes")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(ConsultationNote).filter_by(note_id=r["note_id"]).first()
            if not existing:
                cn = ConsultationNote(
                    note_id=r["note_id"],
                    consultation_id=r["consultation_id"],
                    doctor_id=r["doctor_id"],
                    doctor_user_id=r["doctor_user_id"],
                    author_name=r["author_name"],
                    assessment=r["assessment"],
                    follow_up_guidance=r["follow_up_guidance"],
                    patient_summary=r["patient_summary"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                pg_session.add(cn)
                count += 1
        pg_session.commit()
        migration_counts["consultation_notes"] = count

        # 11. Migrate Doctor Availability Slots
        sqlite_cursor.execute("SELECT * FROM doctor_availability_slots")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(DoctorAvailabilitySlot).filter_by(slot_id=r["slot_id"]).first()
            if not existing:
                das = DoctorAvailabilitySlot(
                    slot_id=r["slot_id"],
                    doctor_id=r["doctor_id"],
                    doctor_user_id=r["doctor_user_id"],
                    slot_start=r["slot_start"],
                    slot_end=r["slot_end"],
                    is_booked=r["is_booked"],
                    created_at=r["created_at"],
                )
                pg_session.add(das)
                count += 1
        pg_session.commit()
        migration_counts["doctor_availability_slots"] = count

        # 12. Migrate Appointments
        sqlite_cursor.execute("SELECT * FROM appointments")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(Appointment).filter_by(appointment_id=r["appointment_id"]).first()
            if not existing:
                apt = Appointment(
                    appointment_id=r["appointment_id"],
                    consultation_id=r["consultation_id"],
                    doctor_id=r["doctor_id"],
                    patient_id=r["patient_id"],
                    patient_user_id=r["patient_user_id"],
                    slot_id=r["slot_id"],
                    slot_start=r["slot_start"],
                    slot_end=r["slot_end"],
                    status=r["status"],
                    notes=r["notes"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                pg_session.add(apt)
                count += 1
        pg_session.commit()
        migration_counts["appointments"] = count

        # 13. Migrate Notifications
        sqlite_cursor.execute("SELECT * FROM notifications")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(Notification).filter_by(notification_id=r["notification_id"]).first()
            if not existing:
                n = Notification(
                    notification_id=r["notification_id"],
                    user_id=r["user_id"],
                    type=r["type"],
                    title=r["title"],
                    message=r["message"],
                    link_nav=r["link_nav"],
                    is_read=r["is_read"],
                    created_at=r["created_at"],
                )
                pg_session.add(n)
                count += 1
        pg_session.commit()
        migration_counts["notifications"] = count

        # 14. Migrate System Settings
        sqlite_cursor.execute("SELECT * FROM system_settings")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(SystemSetting).filter_by(setting_key=r["setting_key"]).first()
            if not existing:
                ss = SystemSetting(
                    setting_key=r["setting_key"],
                    setting_value=r["setting_value"],
                    updated_at=r["updated_at"],
                    updated_by=r["updated_by"],
                )
                pg_session.add(ss)
                count += 1
        pg_session.commit()
        migration_counts["system_settings"] = count

        # 15. Migrate Audit Events
        sqlite_cursor.execute("SELECT * FROM audit_events")
        rows = sqlite_cursor.fetchall()
        count = 0
        for r in rows:
            existing = pg_session.query(AuditEvent).filter_by(event_id=r["event_id"]).first()
            if not existing:
                ae = AuditEvent(
                    event_id=r["event_id"],
                    actor_user_id=r["actor_user_id"],
                    role=r["role"],
                    action=r["action"],
                    resource_type=r["resource_type"],
                    resource_id=r["resource_id"],
                    outcome=r["outcome"],
                    context_json=r["context_json"],
                    prev_hash=r["prev_hash"],
                    event_hash=r["event_hash"],
                    created_at=r["created_at"],
                )
                pg_session.add(ae)
                count += 1
        pg_session.commit()
        migration_counts["audit_events"] = count

        logger.info("\n=======================================================")
        logger.info("ETL MIGRATION SUMMARY (SQLite -> PostgreSQL 17)")
        logger.info("=======================================================")
        for table, cnt in migration_counts.items():
            logger.info(f"  - Table '{table}': {cnt} rows inserted")

    except Exception as e:
        pg_session.rollback()
        logger.error(f"ETL Migration failed: {str(e)}", exc_info=True)
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    run_etl_migration()
