"""
repositories/repositories.py — Repository Pattern Layer for TeleMed AI Platform using SQLAlchemy 2.x.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.orm import Session
try:
    from ..models.models import (
        User, PatientProfile, DoctorProfile, DoctorCredential, DoctorAuditLog,
        AuthSession, HealthRecord, Assessment, Consultation, ConsultationSharedRecord,
        ConsultationAuditLog, ConsultationMessage, ConsultationNote, DoctorAvailabilitySlot,
        Appointment, Notification, SystemSetting, AuditEvent, AccountDeletionRequest
    )
except (ImportError, ValueError):
    from models.models import (
        User, PatientProfile, DoctorProfile, DoctorCredential, DoctorAuditLog,
        AuthSession, HealthRecord, Assessment, Consultation, ConsultationSharedRecord,
        ConsultationAuditLog, ConsultationMessage, ConsultationNote, DoctorAvailabilitySlot,
        Appointment, Notification, SystemSetting, AuditEvent, AccountDeletionRequest
    )


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, patient_id: str) -> Optional[PatientProfile]:
        return self.db.execute(select(PatientProfile).where(PatientProfile.patient_id == patient_id)).scalar_one_or_none()

    def get_by_user_id(self, user_id: str) -> Optional[PatientProfile]:
        return self.db.execute(select(PatientProfile).where(PatientProfile.user_id == user_id)).scalar_one_or_none()

    def create(self, profile: PatientProfile) -> PatientProfile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile


class DoctorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, doctor_id: str) -> Optional[DoctorProfile]:
        return self.db.execute(select(DoctorProfile).where(DoctorProfile.doctor_id == doctor_id)).scalar_one_or_none()

    def get_by_user_id(self, user_id: str) -> Optional[DoctorProfile]:
        return self.db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user_id)).scalar_one_or_none()

    def list_all(self, status: Optional[str] = None) -> List[DoctorProfile]:
        stmt = select(DoctorProfile)
        if status:
            stmt = stmt.where(DoctorProfile.verification_status == status)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, profile: DoctorProfile) -> DoctorProfile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile


class HealthRecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, record_id: str) -> Optional[HealthRecord]:
        return self.db.execute(select(HealthRecord).where(HealthRecord.record_id == record_id)).scalar_one_or_none()

    def get_by_session_id(self, session_id: str) -> Optional[HealthRecord]:
        return self.db.execute(select(HealthRecord).where(HealthRecord.source_session_id == session_id)).scalar_one_or_none()

    def list_by_user_id(self, user_id: str) -> List[HealthRecord]:
        return list(self.db.execute(select(HealthRecord).where(HealthRecord.user_id == user_id).order_by(HealthRecord.created_at.desc())).scalars().all())

    def create(self, record: HealthRecord) -> HealthRecord:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record


class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, assessment_id: str) -> Optional[Assessment]:
        return self.db.execute(select(Assessment).where(Assessment.assessment_id == assessment_id)).scalar_one_or_none()

    def list_by_patient_id(self, patient_id: str) -> List[Assessment]:
        return list(self.db.execute(select(Assessment).where(Assessment.patient_id == patient_id).order_by(Assessment.created_at.desc())).scalars().all())

    def create(self, assessment: Assessment) -> Assessment:
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment


class ConsultationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, consultation_id: str) -> Optional[Consultation]:
        return self.db.execute(select(Consultation).where(Consultation.consultation_id == consultation_id)).scalar_one_or_none()

    def list_by_user_id(self, user_id: str) -> List[Consultation]:
        return list(self.db.execute(select(Consultation).where(Consultation.user_id == user_id).order_by(Consultation.created_at.desc())).scalars().all())

    def list_by_doctor_id(self, doctor_id: str) -> List[Consultation]:
        return list(self.db.execute(select(Consultation).where(Consultation.assigned_doctor_id == doctor_id).order_by(Consultation.created_at.desc())).scalars().all())

    def create(self, consultation: Consultation) -> Consultation:
        self.db.add(consultation)
        self.db.commit()
        self.db.refresh(consultation)
        return consultation


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        return self.db.execute(select(Appointment).where(Appointment.appointment_id == appointment_id)).scalar_one_or_none()

    def list_by_patient_user_id(self, patient_user_id: str) -> List[Appointment]:
        return list(self.db.execute(select(Appointment).where(Appointment.patient_user_id == patient_user_id).order_by(Appointment.slot_start.desc())).scalars().all())

    def list_by_doctor_id(self, doctor_id: str) -> List[Appointment]:
        return list(self.db.execute(select(Appointment).where(Appointment.doctor_id == doctor_id).order_by(Appointment.slot_start.desc())).scalars().all())

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user_id(self, user_id: str) -> List[Notification]:
        return list(self.db.execute(select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())).scalars().all())

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_read(self, notification_id: str) -> bool:
        res = self.db.execute(update(Notification).where(Notification.notification_id == notification_id).values(is_read=1))
        self.db.commit()
        return res.rowcount > 0


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event: AuditEvent) -> AuditEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_events(self, limit: int = 100) -> List[AuditEvent]:
        return list(self.db.execute(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)).scalars().all())
