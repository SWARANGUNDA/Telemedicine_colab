"""Database package for TeleMed AI.

Provides database connectivity, SQLAlchemy models/session bridges,
and re-exports all repository methods from database_legacy for backwards compatibility.
"""

from .db import engine, SessionLocal, Base, get_db, check_db_connection

def init_db():
    """PostgreSQL Initialization bridge (tables created via Alembic / ORM)."""
    check_db_connection()

try:
    from app.backend.database_legacy import *
except (ImportError, ValueError):
    try:
        from ..database_legacy import *
    except (ImportError, ValueError):
        try:
            from database_legacy import *
        except Exception:
            pass

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "check_db_connection",
    "init_db",
    "get_db_connection",
    "create_user",
    "get_user_by_id",
    "get_user_by_email",
    "authenticate_user",
    "hash_password",
    "verify_password",
    "update_user_password",
    "create_auth_session",
    "get_user_by_session_token",
    "has_active_session",
    "delete_auth_session",
    "delete_user_auth_sessions",
    "ensure_demo_users_seeded",
    "bootstrap_admin",
    "update_patient_profile",
    "update_doctor_profile",
    "update_admin_profile",
    "get_doctor_profile",
    "list_doctors",
    "submit_doctor_application",
    "list_doctor_applications",
    "get_doctor_application_detail",
    "update_doctor_status",
    "update_doctor_verification_status",
    "create_doctor_credential",
    "list_doctor_credentials",
    "get_doctor_credential_by_id",
    "delete_doctor_credential",
    "get_doctor_user_id",
    "upsert_health_record",
    "get_patient_health_record",
    "list_patient_health_records",
    "delete_patient_health_record",
    "attach_report_snapshot_to_record",
    "attach_xai_snapshot_to_record",
    "create_consultation_request",
    "get_patient_consultation_detail",
    "get_admin_consultation_detail",
    "get_doctor_consultation_detail",
    "get_consultation_by_id",
    "list_patient_consultations",
    "list_doctor_consultations",
    "list_admin_consultations",
    "assign_doctor_to_consultation",
    "claim_open_consultation",
    "respond_to_doctor_assignment",
    "cancel_patient_consultation",
    "complete_consultation",
    "invite_co_doctor",
    "is_co_doctor_assigned",
    "list_co_doctors",
    "validate_consultation_participant",
    "send_consultation_message",
    "list_consultation_messages",
    "mark_messages_read",
    "upsert_doctor_consultation_note",
    "get_consultation_note",
    "revoke_shared_record_consent",
    "is_doctor_assigned_to_patient",
    "get_doctor_authorized_patient_record",
    "add_doctor_availability_slot",
    "set_doctor_availability_slots",
    "list_doctor_availability_slots",
    "delete_doctor_availability_slot",
    "book_appointment",
    "list_user_appointments",
    "get_appointment_detail",
    "update_appointment_status",
    "create_notification",
    "get_user_notifications",
    "mark_notification_read",
    "mark_all_notifications_read",
    "list_user_conversations",
    "get_admin_stats",
    "list_users",
    "export_user_account_data",
    "request_account_deletion",
    "get_system_settings",
    "update_system_settings",
    "get_detailed_system_health",
    "log_audit_event",
    "log_consultation_audit",
    "log_doctor_audit",
    "query_admin_audit_logs",
    "verify_audit_log_integrity",
    "get_patient_access_history",
    "get_doctor_audit_history",
    "compute_event_hash",
]
