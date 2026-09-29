"""
models/models.py — SQLAlchemy 2.x Declarative ORM Models for TeleMed AI Platform.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
try:
    from ..database.db import Base
except (ImportError, ValueError):
    from database.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    salt: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # PATIENT, DOCTOR, ADMIN
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())

    patient_profile: Mapped[Optional["PatientProfile"]] = relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile: Mapped[Optional["DoctorProfile"]] = relationship("DoctorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    auth_sessions: Mapped[List["AuthSession"]] = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")
    health_records: Mapped[List["HealthRecord"]] = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    __table_args__ = {"extend_existing": True}

    patient_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contact_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())

    user: Mapped["User"] = relationship("User", back_populates="patient_profile")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="patient", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    __table_args__ = {"extend_existing": True}

    doctor_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    specialization: Mapped[str] = mapped_column(String, nullable=False)
    qualification: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    registration_number: Mapped[str] = mapped_column(String, nullable=False)
    registration_council: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    contact_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hospital_affiliation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, default="PENDING")
    credential_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())

    user: Mapped["User"] = relationship("User", back_populates="doctor_profile")
    credentials: Mapped[List["DoctorCredential"]] = relationship("DoctorCredential", back_populates="doctor", cascade="all, delete-orphan")
    availability_slots: Mapped[List["DoctorAvailabilitySlot"]] = relationship("DoctorAvailabilitySlot", back_populates="doctor", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")


class DoctorCredential(Base):
    __tablename__ = "doctor_credentials"
    __table_args__ = {"extend_existing": True}

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.doctor_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    stored_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[str] = mapped_column(String, nullable=False)

    doctor: Mapped["DoctorProfile"] = relationship("DoctorProfile", back_populates="credentials")


class DoctorAuditLog(Base):
    __tablename__ = "doctor_audit_logs"

    log_id: Mapped[str] = mapped_column(String, primary_key=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.doctor_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    old_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_user_id: Mapped[str] = mapped_column(String, nullable=False)
    actor_role: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="auth_sessions")


class HealthRecord(Base):
    __tablename__ = "health_records"

    record_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    source_session_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    patient_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, index=True)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String, default="v3.3")
    schema_version: Mapped[str] = mapped_column(String, default="v1.0")
    effective_pathway: Mapped[str] = mapped_column(String, nullable=False)
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_modalities: Mapped[str] = mapped_column(Text, nullable=False)
    confirmed_features: Mapped[str] = mapped_column(Text, nullable=False)
    prediction_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    xai_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="ANALYZED")

    user: Mapped["User"] = relationship("User", back_populates="health_records")


class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    assessment_date: Mapped[str] = mapped_column(String, nullable=False)
    overall_health_score: Mapped[float] = mapped_column(Float, nullable=False)
    highest_risk_disease: Mapped[str] = mapped_column(String, nullable=False)
    highest_risk_probability: Mapped[float] = mapped_column(Float, nullable=False)
    active_pathway: Mapped[str] = mapped_column(String, nullable=False)
    data_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())

    patient: Mapped["PatientProfile"] = relationship("PatientProfile", back_populates="assessments")


class Consultation(Base):
    __tablename__ = "consultations"

    consultation_id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_doctor_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("doctor_profiles.doctor_id", ondelete="SET NULL"), nullable=True, index=True)
    specialization: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, default="General Consultation")
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[str] = mapped_column(String, default="ROUTINE")
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="REQUESTED", index=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    completed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    messages: Mapped[List["ConsultationMessage"]] = relationship("ConsultationMessage", back_populates="consultation", cascade="all, delete-orphan")
    notes: Mapped[List["ConsultationNote"]] = relationship("ConsultationNote", back_populates="consultation", cascade="all, delete-orphan")
    audit_logs: Mapped[List["ConsultationAuditLog"]] = relationship("ConsultationAuditLog", back_populates="consultation", cascade="all, delete-orphan")
    appointment: Mapped[Optional["Appointment"]] = relationship("Appointment", back_populates="consultation", uselist=False, cascade="all, delete-orphan")


class ConsultationSharedRecord(Base):
    __tablename__ = "consultation_shared_records"

    share_id: Mapped[str] = mapped_column(String, primary_key=True)
    consultation_id: Mapped[str] = mapped_column(String, ForeignKey("consultations.consultation_id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, nullable=False)
    record_id: Mapped[str] = mapped_column(String, ForeignKey("health_records.record_id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    shared_at: Mapped[str] = mapped_column(String, nullable=False)
    revoked_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (UniqueConstraint("consultation_id", "record_id", name="uq_cons_record"),)


class ConsultationAuditLog(Base):
    __tablename__ = "consultation_audit_logs"

    log_id: Mapped[str] = mapped_column(String, primary_key=True)
    consultation_id: Mapped[str] = mapped_column(String, ForeignKey("consultations.consultation_id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, nullable=False)
    doctor_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_user_id: Mapped[str] = mapped_column(String, nullable=False)
    actor_role: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    old_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="audit_logs")


class ConsultationMessage(Base):
    __tablename__ = "consultation_messages"

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    consultation_id: Mapped[str] = mapped_column(String, ForeignKey("consultations.consultation_id", ondelete="CASCADE"), nullable=False, index=True)
    sender_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    sender_role: Mapped[str] = mapped_column(String, nullable=False)
    sender_name: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="messages")


class ConsultationNote(Base):
    __tablename__ = "consultation_notes"

    note_id: Mapped[str] = mapped_column(String, primary_key=True)
    consultation_id: Mapped[str] = mapped_column(String, ForeignKey("consultations.consultation_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.doctor_id", ondelete="CASCADE"), nullable=False)
    doctor_user_id: Mapped[str] = mapped_column(String, nullable=False)
    author_name: Mapped[str] = mapped_column(String, nullable=False)
    assessment: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    patient_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="notes")


class DoctorAvailabilitySlot(Base):
    __tablename__ = "doctor_availability_slots"

    slot_id: Mapped[str] = mapped_column(String, primary_key=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.doctor_id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    slot_start: Mapped[str] = mapped_column(String, nullable=False)
    slot_end: Mapped[str] = mapped_column(String, nullable=False)
    is_booked: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

    doctor: Mapped["DoctorProfile"] = relationship("DoctorProfile", back_populates="availability_slots")


class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id: Mapped[str] = mapped_column(String, primary_key=True)
    consultation_id: Mapped[str] = mapped_column(String, ForeignKey("consultations.consultation_id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.doctor_id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.patient_id", ondelete="CASCADE"), nullable=False)
    patient_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    slot_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_availability_slots.slot_id", ondelete="CASCADE"), nullable=False)
    slot_start: Mapped[str] = mapped_column(String, nullable=False)
    slot_end: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="REQUESTED")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="appointment")
    doctor: Mapped["DoctorProfile"] = relationship("DoctorProfile", back_populates="appointments")
    patient: Mapped["PatientProfile"] = relationship("PatientProfile", back_populates="appointments")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link_nav: Mapped[Optional[str]] = mapped_column(String, default="")
    is_read: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    setting_key: Mapped[str] = mapped_column(String, primary_key=True)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    actor_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String, default="")
    outcome: Mapped[str] = mapped_column(String, default="SUCCESS")
    context_json: Mapped[Optional[str]] = mapped_column(Text, default="{}")
    prev_hash: Mapped[str] = mapped_column(String, default="0")
    event_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_resource_composite", "resource_type", "resource_id"),
    )


class AccountDeletionRequest(Base):
    __tablename__ = "account_deletion_requests"

    request_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    created_at: Mapped[str] = mapped_column(String, nullable=False)
