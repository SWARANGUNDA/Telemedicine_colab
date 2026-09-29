"""
seed_sprint17_data.py — Sprint 17 Comprehensive Database Seeder for PostgreSQL 17.

Seeds realistic development data:
- 50+ Patients
- 10+ Doctors (Verified, Pending, Rejected)
- 3 Admins
- 100+ Health Records & Assessments
- 30+ Appointments
- 50+ Notifications
- 50+ Consultations & Messages
- 100+ Audit Events with SHA-256 hash chaining
"""

import sys
import secrets
import json
import random
import logging
import datetime
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from database.db import SessionLocal, check_db_connection
from core.security import hash_password
from models.models import (
    User,
    PatientProfile,
    DoctorProfile,
    DoctorAvailabilitySlot,
    DoctorAuditLog,
    HealthRecord,
    Assessment,
    Appointment,
    Consultation,
    ConsultationMessage,
    ConsultationNote,
    Notification,
    AuditEvent,
    SystemSetting,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("seed_sprint17")

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
    "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
    "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Donald", "Sandra",
    "Mark", "Ashley", "Paul", "Kimberly", "Steven", "Emily", "Andrew", "Donna", "Kenneth", "Michelle",
    "Joshua", "Carol", "George", "Amanda", "Kevin", "Dorothy", "Brian", "Melissa", "Edward", "Deborah",
    "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon", "Jeffrey", "Laura", "Ryan", "Cynthia"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
]

SPECIALIZATIONS = [
    "Cardiology & Internal Medicine",
    "Endocrinology & Diabetes",
    "Gastroenterology",
    "Pulmonology & Respiratory Medicine",
    "Neurology",
    "General Practice & Family Medicine",
    "Nephrology",
    "Geriatric Medicine",
    "Oncology",
    "Preventive Care & Wellness"
]

DISEASES = [
    "Coronary Artery Disease", "Hypertension", "Type 2 Diabetes", "Nonalcoholic Fatty Liver Disease",
    "Chronic Kidney Disease", "Heart Failure", "Asthma", "Metabolic Syndrome", "Arrhythmia", "Low Risk / Healthy"
]

PATHWAYS = ["Full Multimodal (C+W+G)", "Clinical + Wearable (C+W)", "Clinical + Gut (C+G)", "Clinical Only (C)"]


def seed_sprint17():
    logger.info("Starting Sprint 17 Comprehensive Seeding in PostgreSQL 17...")

    if not check_db_connection():
        logger.error("PostgreSQL 17 is unreachable!")
        sys.exit(1)

    db = SessionLocal()
    try:
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now_dt.isoformat()

        # -------------------------------------------------------------------------
        # 1. SEED ADMIN ACCOUNTS (3 Admins)
        # -------------------------------------------------------------------------
        admins_data = [
            ("admin@telemed.ai", "TeleMed System Administrator"),
            ("lead_admin@telemed.ai", "Lead Operations Admin"),
            ("compliance_admin@telemed.ai", "HIPAA Compliance Officer"),
        ]
        admin_users = []
        for email, full_name in admins_data:
            existing = db.query(User).filter_by(email=email).first()
            if not existing:
                u_id = f"usr_admin_{secrets.token_hex(4)}"
                pwd_h, salt = hash_password("Password123!")
                u = User(
                    user_id=u_id, email=email, password_hash=pwd_h, salt=salt,
                    role="ADMIN", created_at=now_iso, updated_at=now_iso
                )
                db.add(u)
                admin_users.append(u)
                logger.info(f"Seeded Admin: {email}")
            else:
                admin_users.append(existing)

        db.flush()

        # -------------------------------------------------------------------------
        # 2. SEED DOCTOR ACCOUNTS (12 Doctors)
        # -------------------------------------------------------------------------
        doctors_data = [
            ("doctor@telemed.ai", "Dr. Sarah Jenkins, MD", "Cardiology & Internal Medicine", "VERIFIED"),
            ("dr.chen@telemed.ai", "Dr. Robert Chen, MD", "Endocrinology & Diabetes", "VERIFIED"),
            ("dr.patel@telemed.ai", "Dr. Ananya Patel, MD", "Gastroenterology", "VERIFIED"),
            ("dr.williams@telemed.ai", "Dr. Marcus Williams, MD", "Pulmonology & Respiratory Medicine", "VERIFIED"),
            ("dr.garcia@telemed.ai", "Dr. Elena Garcia, MD", "Neurology", "VERIFIED"),
            ("dr.kim@telemed.ai", "Dr. Min-Jun Kim, MD", "General Practice & Family Medicine", "VERIFIED"),
            ("dr.taylor@telemed.ai", "Dr. David Taylor, MD", "Nephrology", "VERIFIED"),
            ("dr.adams@telemed.ai", "Dr. Rachel Adams, MD", "Geriatric Medicine", "VERIFIED"),
            ("dr.new_applicant1@telemed.ai", "Dr. Michael Ross, MD", "Oncology", "PENDING"),
            ("dr.new_applicant2@telemed.ai", "Dr. Jessica Pearson, MD", "Preventive Care & Wellness", "PENDING"),
            ("dr.rejected1@telemed.ai", "Dr. Arthur Pendelton, MD", "Cardiology", "REJECTED"),
            ("dr.rejected2@telemed.ai", "Dr. Victoria Sterling, MD", "Endocrinology", "REJECTED"),
        ]

        doctor_profiles = []
        for idx, (email, name, spec, status) in enumerate(doctors_data):
            existing_user = db.query(User).filter_by(email=email).first()
            if not existing_user:
                u_id = f"usr_doc_{secrets.token_hex(4)}"
                pwd_h, salt = hash_password("Password123!")
                u = User(
                    user_id=u_id, email=email, password_hash=pwd_h, salt=salt,
                    role="DOCTOR", created_at=now_iso, updated_at=now_iso
                )
                db.add(u)
                db.flush()

                d_id = f"doc_{secrets.token_hex(4)}"
                reg_num = f"MED-REG-{882000 + idx}"
                dp = DoctorProfile(
                    doctor_id=d_id,
                    user_id=u_id,
                    full_name=name,
                    specialization=spec,
                    qualification="MBBS, MD",
                    registration_number=reg_num,
                    registration_council="American Board of Medical Specialties",
                    experience_years=5 + (idx * 2) % 20,
                    contact_number=f"+1-555-01{10+idx:02d}",
                    hospital_affiliation="TeleMed Central Academic Hospital",
                    verification_status=status,
                    credential_notes=f"Sprint 17 Seed Doctor ({status})",
                    created_at=now_iso
                )
                db.add(dp)
                db.flush()
                doctor_profiles.append(dp)

                # Add Doctor Audit Log
                db.add(DoctorAuditLog(
                    log_id=f"aud_{secrets.token_hex(6)}",
                    doctor_id=d_id,
                    user_id=u_id,
                    action="VERIFIED_BY_ADMIN" if status == "VERIFIED" else "SUBMITTED",
                    old_status="PENDING",
                    new_status=status,
                    actor_user_id=admin_users[0].user_id,
                    actor_role="ADMIN",
                    reason=f"Doctor account initialization: status {status}",
                    timestamp=now_iso
                ))

                # Add Availability Slots for Verified Doctors
                if status == "VERIFIED":
                    for s_idx in range(5):
                        slot_start = (now_dt + datetime.timedelta(days=s_idx + 1, hours=9)).isoformat()
                        slot_end = (now_dt + datetime.timedelta(days=s_idx + 1, hours=9, minutes=45)).isoformat()
                        db.add(DoctorAvailabilitySlot(
                            slot_id=f"slt_{secrets.token_hex(4)}",
                            doctor_id=d_id,
                            doctor_user_id=u_id,
                            slot_start=slot_start,
                            slot_end=slot_end,
                            is_booked=0,
                            created_at=now_iso
                        ))
            else:
                dp = db.query(DoctorProfile).filter_by(user_id=existing_user.user_id).first()
                if dp:
                    doctor_profiles.append(dp)

        db.flush()

        # -------------------------------------------------------------------------
        # 3. SEED PATIENT ACCOUNTS (55 Patients)
        # -------------------------------------------------------------------------
        patient_profiles = []
        demo_pat_user = db.query(User).filter_by(email="patient@telemed.ai").first()
        if not demo_pat_user:
            u_id = f"usr_pat_demo"
            pwd_h, salt = hash_password("Password123!")
            demo_pat_user = User(user_id=u_id, email="patient@telemed.ai", password_hash=pwd_h, salt=salt, role="PATIENT", created_at=now_iso, updated_at=now_iso)
            db.add(demo_pat_user)
            db.flush()

        pp = db.query(PatientProfile).filter_by(user_id=demo_pat_user.user_id).first()
        if not pp:
            p_id = f"pat_demo_{secrets.token_hex(4)}"
            pp = PatientProfile(
                patient_id=p_id, user_id=demo_pat_user.user_id, full_name="Demo Patient Account",
                age=34, gender="Female", height_cm=165.0, weight_kg=62.0, contact_number="+1-555-0192", created_at=now_iso
            )
            db.add(pp)
            db.flush()
        patient_profiles.append(pp)

        for i in range(1, 55):
            fn = FIRST_NAMES[i % len(FIRST_NAMES)]
            ln = LAST_NAMES[i % len(LAST_NAMES)]
            email = f"patient_{i}@telemed.ai"
            existing = db.query(User).filter_by(email=email).first()
            if not existing:
                u_id = f"usr_pat_{i:03d}"
                pwd_h, salt = hash_password("Password123!")
                u = User(
                    user_id=u_id, email=email, password_hash=pwd_h, salt=salt,
                    role="PATIENT", created_at=now_iso, updated_at=now_iso
                )
                db.add(u)
                db.flush()
                p_id = f"pat_{i:03d}"
                pp = PatientProfile(
                    patient_id=p_id, user_id=u_id, full_name=f"{fn} {ln}",
                    age=20 + (i * 3) % 60,
                    gender="Male" if i % 2 == 0 else "Female",
                    height_cm=155.0 + (i * 1.5) % 35,
                    weight_kg=52.0 + (i * 2.1) % 45,
                    contact_number=f"+1-555-02{i:02d}",
                    created_at=now_iso
                )
                db.add(pp)
                patient_profiles.append(pp)
            else:
                pp = db.query(PatientProfile).filter_by(user_id=existing.user_id).first()
                if pp:
                    patient_profiles.append(pp)

        db.flush()
        logger.info(f"Seeded/Verified {len(patient_profiles)} Patients and {len(doctor_profiles)} Doctors.")

        # -------------------------------------------------------------------------
        # 4. SEED HEALTH RECORDS & ASSESSMENTS (110+ Records)
        # -------------------------------------------------------------------------
        health_records = []
        assessments = []
        for idx, pat in enumerate(patient_profiles):
            num_recs = 2 + (idx % 3)
            for r_idx in range(num_recs):
                rec_dt = now_dt - datetime.timedelta(days=(r_idx * 14) + (idx % 5))
                rec_iso = rec_dt.isoformat()
                sess_id = f"sess_{pat.patient_id}_{r_idx}"
                rec_id = f"rec_{pat.patient_id}_{r_idx}"
                ass_id = f"ass_{pat.patient_id}_{r_idx}"

                disease = DISEASES[(idx + r_idx) % len(DISEASES)]
                prob = round(0.12 + ((idx * 7 + r_idx * 13) % 78) / 100.0, 2)
                score = round(max(15.0, 100.0 - (prob * 100.0) + random.uniform(-5, 5)), 1)
                pathway = PATHWAYS[(idx + r_idx) % len(PATHWAYS)]
                dq_score = round(0.85 + random.uniform(0.0, 0.14), 2)

                # Generate TreeSHAP breakdown snapshot
                xai_data = {
                    "shap_values": {
                        "systolic_bp": round(random.uniform(0.05, 0.25), 3),
                        "bmi": round(random.uniform(0.02, 0.18), 3),
                        "heart_rate_variability": round(random.uniform(-0.15, 0.10), 3),
                        "fasting_glucose": round(random.uniform(0.01, 0.22), 3),
                        "gut_microbiome_diversity": round(random.uniform(-0.12, 0.08), 3)
                    },
                    "top_risk_factors": ["High Systolic Blood Pressure", "Elevated BMI", "Low HRV Index"],
                    "protective_factors": ["High Gut Microbiome Diversity", "Regular Exercise Profile"]
                }

                pred_snapshot = {
                    "overall_health_score": score,
                    "highest_risk_disease": disease,
                    "highest_risk_probability": prob,
                    "active_pathway": pathway,
                    "data_quality_score": dq_score,
                    "risk_breakdown": {
                        "cardiovascular": round(prob * 0.9, 2),
                        "metabolic": round(prob * 0.8, 2),
                        "respiratory": round(prob * 0.4, 2)
                    }
                }

                # HealthRecord
                hr = db.query(HealthRecord).filter_by(record_id=rec_id).first()
                if not hr:
                    hr = HealthRecord(
                        record_id=rec_id,
                        user_id=pat.user_id,
                        source_session_id=sess_id,
                        patient_id=pat.patient_id,
                        created_at=rec_iso,
                        updated_at=rec_iso,
                        pipeline_version="v3.3",
                        schema_version="v1.0",
                        effective_pathway=pathway,
                        data_quality_score=dq_score,
                        active_modalities="Clinical, Wearable, Gut",
                        confirmed_features=json.dumps({"age": pat.age, "gender": pat.gender, "height": pat.height_cm, "weight": pat.weight_kg}),
                        prediction_snapshot=json.dumps(pred_snapshot),
                        xai_snapshot=json.dumps(xai_data),
                        report_snapshot=json.dumps({"summary": f"Comprehensive AI Assessment for {pat.full_name}", "recommendation": "Maintain daily cardiovascular monitoring and balanced diet."}),
                        status="ANALYZED"
                    )
                    db.add(hr)
                    health_records.append(hr)

                # Assessment
                ass = db.query(Assessment).filter_by(assessment_id=ass_id).first()
                if not ass:
                    ass = Assessment(
                        assessment_id=ass_id,
                        patient_id=pat.patient_id,
                        session_id=sess_id,
                        assessment_date=rec_iso,
                        overall_health_score=score,
                        highest_risk_disease=disease,
                        highest_risk_probability=prob,
                        active_pathway=pathway,
                        data_quality_score=dq_score,
                        created_at=rec_iso
                    )
                    db.add(ass)
                    assessments.append(ass)

        db.flush()

        # -------------------------------------------------------------------------
        # 5. SEED CONSULTATIONS, MESSAGES & APPOINTMENTS (35+ Appointments/Consultations)
        # -------------------------------------------------------------------------
        verified_doctors = [d for d in doctor_profiles if d.verification_status == "VERIFIED"]
        for idx in range(min(35, len(patient_profiles))):
            pat = patient_profiles[idx]
            doc = verified_doctors[idx % len(verified_doctors)]
            c_id = f"cons_{pat.patient_id}_{doc.doctor_id}"
            app_id = f"app_{pat.patient_id}_{doc.doctor_id}"
            c_dt = now_dt - datetime.timedelta(days=idx % 10, hours=idx % 8)
            c_iso = c_dt.isoformat()

            cons = db.query(Consultation).filter_by(consultation_id=c_id).first()
            if not cons:
                cons = Consultation(
                    consultation_id=c_id,
                    patient_id=pat.patient_id,
                    user_id=pat.user_id,
                    assigned_doctor_id=doc.doctor_id,
                    specialization=doc.specialization,
                    category="Specialist Follow-up",
                    reason=f"Clinical consultation regarding elevated risk factors.",
                    urgency="HIGH" if idx % 4 == 0 else "ROUTINE",
                    message="Patient requested detailed AI prediction review.",
                    status="ACTIVE" if idx % 2 == 0 else "COMPLETED",
                    created_at=c_iso,
                    updated_at=c_iso
                )
                db.add(cons)
                db.flush()

                # Add messages
                db.add(ConsultationMessage(
                    message_id=f"msg_{c_id}_1",
                    consultation_id=c_id,
                    sender_user_id=pat.user_id,
                    sender_role="PATIENT",
                    sender_name=pat.full_name,
                    content="Hello Doctor, I recently completed my AI health assessment and wanted your feedback on my risk score.",
                    created_at=c_iso
                ))
                db.add(ConsultationMessage(
                    message_id=f"msg_{c_id}_2",
                    consultation_id=c_id,
                    sender_user_id=doc.user_id,
                    sender_role="DOCTOR",
                    sender_name=doc.full_name,
                    content=f"Hello {pat.full_name}. I have reviewed your assessment and TreeSHAP risk factors. Everything looks manageable with proper guidance.",
                    created_at=(c_dt + datetime.timedelta(minutes=15)).isoformat()
                ))

                # Add Doctor Note if completed
                if cons.status == "COMPLETED":
                    db.add(ConsultationNote(
                        note_id=f"note_{c_id}",
                        consultation_id=c_id,
                        doctor_id=doc.doctor_id,
                        doctor_user_id=doc.user_id,
                        author_name=doc.full_name,
                        assessment="Patient demonstrates mild metabolic risk elevation with good overall compliance.",
                        follow_up_guidance="Repeat wearable intake assessment in 30 days.",
                        patient_summary="Discussed risk factors and lifestyle optimizations.",
                        created_at=(c_dt + datetime.timedelta(hours=1)).isoformat(),
                        updated_at=(c_dt + datetime.timedelta(hours=1)).isoformat()
                    ))

            # Appointment
            app = db.query(Appointment).filter_by(appointment_id=app_id).first()
            if not app:
                slot = db.query(DoctorAvailabilitySlot).filter_by(doctor_id=doc.doctor_id).first()
                if not slot:
                    slot_id = f"slt_{doc.doctor_id}_{idx}"
                    slot = DoctorAvailabilitySlot(
                        slot_id=slot_id,
                        doctor_id=doc.doctor_id,
                        doctor_user_id=doc.user_id,
                        slot_start=(c_dt + datetime.timedelta(days=2)).isoformat(),
                        slot_end=(c_dt + datetime.timedelta(days=2, minutes=45)).isoformat(),
                        is_booked=1,
                        created_at=c_iso
                    )
                    db.add(slot)
                    db.flush()

                app = Appointment(
                    appointment_id=app_id,
                    consultation_id=c_id,
                    doctor_id=doc.doctor_id,
                    patient_id=pat.patient_id,
                    patient_user_id=pat.user_id,
                    slot_id=slot.slot_id,
                    slot_start=(c_dt + datetime.timedelta(days=2)).isoformat(),
                    slot_end=(c_dt + datetime.timedelta(days=2, minutes=45)).isoformat(),
                    status="SCHEDULED" if idx % 2 == 0 else "COMPLETED",
                    notes="TeleMed Virtual Consultation Slot",
                    created_at=c_iso,
                    updated_at=c_iso
                )
                db.add(app)

        db.flush()

        # -------------------------------------------------------------------------
        # 6. SEED NOTIFICATIONS (60+ Notifications)
        # -------------------------------------------------------------------------
        for idx, pat in enumerate(patient_profiles[:30]):
            n_id1 = f"notif_{pat.patient_id}_1"
            if not db.query(Notification).filter_by(notification_id=n_id1).first():
                db.add(Notification(
                    notification_id=n_id1,
                    user_id=pat.user_id,
                    type="ASSESSMENT_READY",
                    title="AI Health Report Ready",
                    message="Your latest AI health assessment results have been compiled successfully.",
                    link_nav="/records",
                    is_read=1 if idx % 2 == 0 else 0,
                    created_at=(now_dt - datetime.timedelta(hours=idx * 2)).isoformat()
                ))
            n_id2 = f"notif_{pat.patient_id}_2"
            if not db.query(Notification).filter_by(notification_id=n_id2).first():
                db.add(Notification(
                    notification_id=n_id2,
                    user_id=pat.user_id,
                    type="APPOINTMENT_CONFIRMED",
                    title="Consultation Appointment Scheduled",
                    message="Your appointment with your specialist has been confirmed.",
                    link_nav="/appointments",
                    is_read=0,
                    created_at=(now_dt - datetime.timedelta(hours=idx * 3 + 1)).isoformat()
                ))

        for idx, doc in enumerate(doctor_profiles[:6]):
            n_id = f"notif_doc_{doc.doctor_id}"
            if not db.query(Notification).filter_by(notification_id=n_id).first():
                db.add(Notification(
                    notification_id=n_id,
                    user_id=doc.user_id,
                    type="PATIENT_ASSIGNED",
                    title="New Patient Consultation Request",
                    message="A patient has requested a specialist consultation in your queue.",
                    link_nav="/doctor/queue",
                    is_read=0,
                    created_at=(now_dt - datetime.timedelta(hours=idx * 4)).isoformat()
                ))

        db.flush()

        # -------------------------------------------------------------------------
        # 7. SEED AUDIT EVENTS WITH HASH CHAINING (100+ Audit Log Entries)
        # -------------------------------------------------------------------------
        actions = [
            ("USER_LOGIN", "AUTH", "SUCCESS"),
            ("VIEW_RECORD", "HEALTH_RECORD", "SUCCESS"),
            ("CREATE_ASSESSMENT", "ASSESSMENT", "SUCCESS"),
            ("SCHEDULE_APPOINTMENT", "APPOINTMENT", "SUCCESS"),
            ("POST_MESSAGE", "CONSULTATION", "SUCCESS"),
            ("VERIFY_DOCTOR", "ADMIN", "SUCCESS"),
        ]

        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        last_evt = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        if last_evt and last_evt.event_hash:
            prev_hash = last_evt.event_hash

        for i in range(105):
            evt_id = f"evt_sprint17_{i:04d}"
            if not db.query(AuditEvent).filter_by(event_id=evt_id).first():
                act, res_type, outcome = actions[i % len(actions)]
                actor = patient_profiles[i % len(patient_profiles)].user_id if i % 3 != 0 else admin_users[0].user_id
                role = "PATIENT" if i % 3 != 0 else "ADMIN"
                evt_dt = now_dt - datetime.timedelta(minutes=(105 - i) * 15)
                evt_iso = evt_dt.isoformat()

                # compute SHA-256 event hash
                payload = f"{evt_id}|{actor}|{act}|{res_type}||{outcome}|{evt_iso}|{prev_hash}"
                import hashlib
                event_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

                db.add(AuditEvent(
                    event_id=evt_id,
                    actor_user_id=actor,
                    role=role,
                    action=act,
                    resource_type=res_type,
                    resource_id=f"res_{i}",
                    outcome=outcome,
                    context_json=json.dumps({"ip": f"192.168.1.{10+i%200}", "user_agent": "TeleMed MultiModal Platform Client"}),
                    prev_hash=prev_hash,
                    event_hash=event_hash,
                    created_at=evt_iso
                ))
                prev_hash = event_hash

        db.commit()
        logger.info("Successfully completed Sprint 17 Comprehensive Database Seeding!")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed Sprint 17 data: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_sprint17()
