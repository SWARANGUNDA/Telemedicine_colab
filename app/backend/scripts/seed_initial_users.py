"""
seed_initial_users.py — Seeds production initial accounts for Patient, Doctor, and Admin into PostgreSQL 17.
"""

import sys
import secrets
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
from models.models import User, PatientProfile, DoctorProfile, DoctorAuditLog

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("seed_users")


def seed_initial_users():
    logger.info("Starting initial users seeding in PostgreSQL 17...")

    if not check_db_connection():
        logger.error("PostgreSQL 17 is unreachable! Ensure Docker containers are running.")
        sys.exit(1)

    db = SessionLocal()

    seed_accounts = [
        {
            "email": "patient@telemed.ai",
            "password": "Password123!",
            "role": "PATIENT",
            "full_name": "Demo Patient Account",
            "age": 34,
            "gender": "Female",
            "height_cm": 165.0,
            "weight_kg": 62.0,
            "contact_number": "+1-555-0192"
        },
        {
            "email": "doctor@telemed.ai",
            "password": "Password123!",
            "role": "DOCTOR",
            "full_name": "Dr. Sarah Jenkins, MD",
            "specialization": "Cardiology & Internal Medicine",
            "qualification": "MBBS, MD Cardiology",
            "registration_number": "MED-REG-882194",
            "registration_council": "American Board of Internal Medicine",
            "experience_years": 12,
            "contact_number": "+1-555-0188",
            "hospital_affiliation": "TeleMed Central Hospital",
            "verification_status": "VERIFIED"
        },
        {
            "email": "admin@telemed.ai",
            "password": "Password123!",
            "role": "ADMIN",
            "full_name": "TeleMed System Administrator"
        },
        {
            "email": "ramu@telemed.ai",
            "password": "Password123!",
            "role": "PATIENT",
            "full_name": "Ramu Patient Account",
            "age": 45,
            "gender": "Male",
            "height_cm": 172.0,
            "weight_kg": 78.0,
            "contact_number": "+1-555-0199"
        }
    ]

    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for acc in seed_accounts:
            email_clean = acc["email"].strip().lower()
            existing_user = db.query(User).filter_by(email=email_clean).first()

            pwd_hash, salt = hash_password(acc["password"])

            if existing_user:
                # Update password hash for predictable login
                existing_user.password_hash = pwd_hash
                existing_user.salt = salt
                existing_user.updated_at = now
                logger.info(f"Updated password hash for existing user: {email_clean} ({existing_user.role})")
            else:
                user_id = f"usr_seed_{secrets.token_hex(4)}"
                new_user = User(
                    user_id=user_id,
                    email=email_clean,
                    password_hash=pwd_hash,
                    salt=salt,
                    role=acc["role"],
                    created_at=now,
                    updated_at=now
                )
                db.add(new_user)
                db.flush()

                if acc["role"] == "PATIENT":
                    patient_id = f"pat_seed_{secrets.token_hex(4)}"
                    p_profile = PatientProfile(
                        patient_id=patient_id,
                        user_id=user_id,
                        full_name=acc["full_name"],
                        age=acc["age"],
                        gender=acc["gender"],
                        height_cm=acc["height_cm"],
                        weight_kg=acc["weight_kg"],
                        contact_number=acc["contact_number"],
                        created_at=now
                    )
                    db.add(p_profile)

                elif acc["role"] == "DOCTOR":
                    doctor_id = f"doc_seed_{secrets.token_hex(4)}"
                    d_profile = DoctorProfile(
                        doctor_id=doctor_id,
                        user_id=user_id,
                        full_name=acc["full_name"],
                        specialization=acc["specialization"],
                        qualification=acc["qualification"],
                        registration_number=acc["registration_number"],
                        registration_council=acc["registration_council"],
                        experience_years=acc["experience_years"],
                        contact_number=acc["contact_number"],
                        hospital_affiliation=acc["hospital_affiliation"],
                        verification_status=acc["verification_status"],
                        credential_notes="Seeded verified demo doctor account.",
                        created_at=now
                    )
                    db.add(d_profile)
                    db.flush()

                    audit_log = DoctorAuditLog(
                        log_id=f"aud_{secrets.token_hex(6)}",
                        doctor_id=doctor_id,
                        user_id=user_id,
                        action="VERIFIED_BY_ADMIN",
                        old_status="PENDING",
                        new_status="VERIFIED",
                        actor_user_id=user_id,
                        actor_role="ADMIN",
                        reason="Initial platform demo doctor seeding.",
                        timestamp=now
                    )
                    db.add(audit_log)

                logger.info(f"Seeded new user: {email_clean} ({acc['role']})")

        db.commit()
        logger.info("Successfully completed initial user seeding in PostgreSQL 17!")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed initial users: {str(e)}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    seed_initial_users()
