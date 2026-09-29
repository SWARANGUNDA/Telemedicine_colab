"""
models package — SQLAlchemy 2.x Declarative ORM Models.
"""

from .base import Base
from .models import (
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

__all__ = [
    "Base",
    "User",
    "PatientProfile",
    "DoctorProfile",
    "DoctorCredential",
    "DoctorAuditLog",
    "AuthSession",
    "HealthRecord",
    "Assessment",
    "Consultation",
    "ConsultationSharedRecord",
    "ConsultationAuditLog",
    "ConsultationMessage",
    "ConsultationNote",
    "DoctorAvailabilitySlot",
    "Appointment",
    "Notification",
    "SystemSetting",
    "AuditEvent",
    "AccountDeletionRequest",
]
