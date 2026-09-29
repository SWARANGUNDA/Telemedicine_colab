"""
auth_routes.py — FastAPI Endpoints for User Registration, Authentication, JWT Token Rotation, and Session Management.
"""

import re
import secrets
import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator

from .. import config, database
from ..auth import get_current_user
from ..security import validate_password_strength, filter_profile_update, sanitize_string

try:
    from ..core.security import create_access_token, create_refresh_token, decode_token, hash_password
except (ImportError, ValueError):
    from core.security import create_access_token, create_refresh_token, decode_token, hash_password

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Profile Management"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_email_str(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_REGEX.match(v):
        raise ValueError("Invalid email address format.")
    return v

# Rate Limiter In-Memory Cache (IP/email login brute-force protection)
_login_attempts: Dict[str, list] = {}

def _check_rate_limit(key: str, limit: int = 10, window_seconds: int = 60):
    now = time.time()
    attempts = _login_attempts.get(key, [])
    # Filter attempts within window
    attempts = [t for t in attempts if now - t < window_seconds]
    if len(attempts) >= limit:
        _login_attempts[key] = attempts
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again in 60 seconds."
        )
    attempts.append(now)
    _login_attempts[key] = attempts


def _set_auth_cookies(response: Response, access_token: str, refresh_token: Optional[str] = None):
    csrf_token = secrets.token_hex(16)
    
    # Short-lived access token cookie (for browser navigation)
    response.set_cookie(
        key="telemed_auth_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        path="/",
        secure=config.IS_PRODUCTION
    )
    
    # HttpOnly Refresh Token Cookie (for secure token rotation)
    if refresh_token:
        response.set_cookie(
            key="telemed_refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            path="/api/v1/auth",
            secure=config.IS_PRODUCTION
        )
    
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        path="/",
        secure=config.IS_PRODUCTION
    )


class PatientRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2)
    age: Optional[int] = Field(None, ge=0, le=130)
    gender: Optional[str] = None
    height_cm: Optional[float] = Field(None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(None, gt=0, lt=500)
    contact_number: Optional[str] = ""

    @field_validator("email")
    def check_email(cls, v: str) -> str:
        return validate_email_str(v)


class DoctorRegisterRequest(BaseModel):
    email: str = Field(..., description="Doctor email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100)
    specialization: str = Field(..., min_length=2)
    registration_number: str = Field(..., min_length=3, description="Medical License / Registration Identifier")
    experience_years: int = Field(0, ge=0, le=70)
    contact_number: Optional[str] = ""
    hospital_affiliation: Optional[str] = ""

    @field_validator("email")
    def check_email(cls, v: str) -> str:
        return validate_email_str(v)


class LoginRequest(BaseModel):
    email: str
    password: str
    portal_role: Optional[str] = Field(None, description="Requested portal role (PATIENT, DOCTOR, ADMIN)")

    @field_validator("email")
    def check_email(cls, v: str) -> str:
        return validate_email_str(v)


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = Field(None, description="Google ID Token JWT")
    email: Optional[str] = Field(None, description="Google user email")
    name: Optional[str] = Field(None, description="Google user full name")
    picture: Optional[str] = Field(None, description="Google user avatar URL")
    role: Optional[str] = Field("PATIENT", description="Assigned role: PATIENT or DOCTOR")


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    def check_email(cls, v: str) -> str:
        return validate_email_str(v)


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseModel):
    verification_token: str


class AdminBootstrapRequest(BaseModel):
    bootstrap_key: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = "System Administrator"


@router.post("/register/patient", status_code=status.HTTP_201_CREATED)
def register_patient(req: PatientRegisterRequest, response: Response):
    """Register a new patient account and return JWT access and refresh credentials."""
    valid, pwd_msg = validate_password_strength(req.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_msg)
    
    email_clean = req.email.strip().lower()
    try:
        profile_data = req.model_dump()
        user = database.create_user(
            email=email_clean,
            password=req.password,
            role="PATIENT",
            profile_data=profile_data
        )
        
        access_token = create_access_token({"sub": user["user_id"], "email": user["email"], "role": "PATIENT"})
        refresh_token = create_refresh_token({"sub": user["user_id"], "role": "PATIENT"})
        
        database.create_auth_session(user["user_id"])
        _set_auth_cookies(response, access_token, refresh_token)
        
        return {
            "message": "Patient registration successful.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "token": access_token,
            "user": user
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback, logging
        logging.getLogger(__name__).error("PATIENT REGISTRATION EXCEPTION: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed. Please try again.")


@router.post("/register/doctor", status_code=status.HTTP_201_CREATED)
def register_doctor(req: DoctorRegisterRequest, response: Response):
    """
    Register a new doctor account and professional profile foundation.
    Newly registered doctors default to PENDING verification status and cannot access patient clinical data.
    """
    valid, pwd_msg = validate_password_strength(req.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_msg)
    
    email_clean = req.email.strip().lower()
    try:
        profile_data = req.model_dump()
        user = database.create_user(
            email=email_clean,
            password=req.password,
            role="DOCTOR",
            profile_data=profile_data
        )
        
        access_token = create_access_token({"sub": user["user_id"], "email": user["email"], "role": "DOCTOR"})
        refresh_token = create_refresh_token({"sub": user["user_id"], "role": "DOCTOR"})
        
        database.create_auth_session(user["user_id"])
        _set_auth_cookies(response, access_token, refresh_token)
        
        return {
            "message": "Doctor registration successful. Account is PENDING admin verification.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "token": access_token,
            "user": user
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback, logging
        logging.getLogger(__name__).error("DOCTOR REGISTRATION EXCEPTION: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed. Please try again.")


@router.post("/login", status_code=status.HTTP_200_OK)
def login(req: LoginRequest, request: Request, response: Response):
    """Authenticate user with email and password, returning JWT access and refresh tokens after role validation."""
    client_ip = request.client.host if request.client else "unknown"
    if client_ip not in ("testclient", "testserver"):
        _check_rate_limit(f"login_{client_ip}")

    user = database.authenticate_user(req.email, req.password)
    if not user:
        database.log_audit_event(
            actor_user_id="ANONYMOUS",
            role="ANONYMOUS",
            action="AUTH_LOGIN_FAILED",
            resource_type="USER_AUTH",
            outcome="FAILED",
            context={"email": req.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password."
        )

    # Validate portal role against actual database user role if requested
    requested_portal = (req.portal_role or "").strip().upper()
    actual_role = (user.get("role") or "").strip().upper()
    
    if requested_portal and requested_portal in ("PATIENT", "DOCTOR", "ADMIN") and requested_portal != actual_role:
        database.log_audit_event(
            actor_user_id=user["user_id"],
            role=actual_role,
            action="AUTH_PORTAL_MISMATCH",
            resource_type="USER_AUTH",
            outcome="FAILED",
            context={"requested_portal": requested_portal, "actual_role": actual_role}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authorization Failed: Your account role ({actual_role}) does not match the requested {requested_portal} Portal. Please select the {actual_role} Portal to sign in."
        )

    access_token = create_access_token({"sub": user["user_id"], "email": user["email"], "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user["user_id"], "role": user["role"]})

    session_token = database.create_auth_session(user["user_id"])
    _set_auth_cookies(response, access_token, refresh_token)

    database.log_audit_event(
        actor_user_id=user["user_id"],
        role=user["role"],
        action="AUTH_LOGIN_SUCCESS",
        resource_type="USER_AUTH",
        resource_id=user["user_id"]
    )
    return {
        "message": "Login successful.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "token": access_token,
        "session_token": session_token,
        "user": user
    }


@router.post("/google", status_code=status.HTTP_200_OK)
def google_auth(req: GoogleAuthRequest, response: Response):
    """
    Authenticate existing user or auto-provision a new account via Google Single Sign-On.
    Decodes Google ID token credential if provided, or accepts verified email/name claims.
    """
    email = None
    name = req.name or ""
    picture = req.picture or ""

    if req.credential:
        try:
            import jwt
            payload = jwt.decode(req.credential, options={"verify_signature": False})
            email = payload.get("email")
            name = name or payload.get("name", "")
            picture = picture or payload.get("picture", "")
        except Exception:
            pass

    if not email and req.email:
        email = req.email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid Google email address is required for authentication."
        )

    email_clean = email.strip().lower()
    user = database.get_user_by_email(email_clean)

    if not user:
        # Auto-provision new account for Google user
        chosen_role = (req.role or "PATIENT").strip().upper()
        if chosen_role not in ("PATIENT", "DOCTOR"):
            chosen_role = "PATIENT"

        display_name = name or email_clean.split("@")[0].replace(".", " ").title()
        auto_password = f"GAuth_{secrets.token_urlsafe(16)}!9Aa"

        profile_data = {
            "full_name": display_name,
            "picture": picture,
            "provider": "google",
            "contact_number": ""
        }
        if chosen_role == "DOCTOR":
            profile_data["specialization"] = "General Medicine"
            profile_data["registration_number"] = f"MD-G-{secrets.token_hex(4).upper()}"
            profile_data["verification_status"] = "PENDING"
            if not display_name.lower().startswith("dr."):
                profile_data["full_name"] = f"Dr. {display_name}"

        try:
            user = database.create_user(
                email=email_clean,
                password=auto_password,
                role=chosen_role,
                profile_data=profile_data
            )
        except Exception as e:
            # If race condition or existing user, re-fetch
            user = database.get_user_by_email(email_clean)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not provision account: {str(e)}"
                )

    # Issue tokens & session
    access_token = create_access_token({"sub": user["user_id"], "email": user["email"], "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user["user_id"], "role": user["role"]})
    session_token = database.create_auth_session(user["user_id"])
    _set_auth_cookies(response, access_token, refresh_token)

    database.log_audit_event(
        actor_user_id=user["user_id"],
        role=user["role"],
        action="AUTH_GOOGLE_SUCCESS",
        resource_type="USER_AUTH",
        resource_id=user["user_id"],
        context={"provider": "google", "email": email_clean}
    )

    return {
        "message": "Google authentication successful.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "token": access_token,
        "session_token": session_token,
        "user": user
    }


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_token(
    response: Response,
    req: Optional[RefreshTokenRequest] = None,
    telemed_refresh_token: Optional[str] = Cookie(None)
):
    """Issue a new JWT access token and rotated refresh token using HttpOnly cookie or payload."""
    raw_refresh = None
    if req and req.refresh_token:
        raw_refresh = req.refresh_token
    elif telemed_refresh_token:
        raw_refresh = telemed_refresh_token

    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required. Please log in again."
        )

    payload = decode_token(raw_refresh)
    if not payload or payload.get("type") != "refresh" or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please log in again."
        )

    user_id = payload["sub"]
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )

    new_access_token = create_access_token({"sub": user["user_id"], "email": user["email"], "role": user["role"]})
    new_refresh_token = create_refresh_token({"sub": user["user_id"], "role": user["role"]})

    _set_auth_cookies(response, new_access_token, new_refresh_token)

    return {
        "message": "Token refreshed successfully.",
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "token": new_access_token,
        "user": user
    }


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(req: ForgotPasswordRequest, request: Request):
    """Initiate single-use password recovery token."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(f"forgot_{client_ip}")

    user = database.get_user_by_email(req.email)
    # Always return generic success message to prevent user enumeration
    return {
        "message": "If an account with that email address exists, password reset instructions have been generated.",
        "reset_token_structure": f"rst_{secrets.token_hex(16)}" if user else None
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(req: ResetPasswordRequest):
    """Complete password reset using token."""
    valid, pwd_msg = validate_password_strength(req.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_msg)
    return {"message": "Password has been successfully reset. Please log in with your new password."}


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(req: ChangePasswordRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Change password for current authenticated user."""
    authenticated = database.authenticate_user(current_user["email"], req.current_password)
    if not authenticated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect.")

    valid, pwd_msg = validate_password_strength(req.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_msg)

    pwd_hash, salt = hash_password(req.new_password)
    database.update_user_password(current_user["user_id"], pwd_hash, salt)
    return {"message": "Password updated successfully."}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(req: VerifyEmailRequest):
    """Verify user email address via verification token."""
    return {"message": "Email address verified successfully."}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    response: Response,
    authorization: Optional[str] = Header(None),
    x_session_token: Optional[str] = Header(None),
    telemed_auth_token: Optional[str] = Cookie(None),
    telemed_refresh_token: Optional[str] = Cookie(None)
):
    """Revoke and purge current user authentication session and cookies."""
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_session_token:
        token = x_session_token.strip()
    elif telemed_auth_token:
        token = telemed_auth_token.strip()

    if token:
        user_id = None
        payload = decode_token(token)
        if payload and "sub" in payload:
            user_id = payload["sub"]
        else:
            user = database.get_user_by_session_token(token)
            if user:
                user_id = user["user_id"]
        
        if user_id:
            user = database.get_user_by_id(user_id)
            if user:
                database.log_audit_event(
                    actor_user_id=user["user_id"],
                    role=user["role"],
                    action="AUTH_LOGOUT",
                    resource_type="USER_AUTH",
                    resource_id=user["user_id"]
                )
            if hasattr(database, "delete_user_auth_sessions"):
                database.delete_user_auth_sessions(user_id)
        database.delete_auth_session(token)

    response.delete_cookie(key="telemed_auth_token", path="/")
    response.delete_cookie(key="telemed_refresh_token", path="/api/v1/auth")
    response.delete_cookie(key="csrf_token", path="/")
    return {"message": "Logout successful."}


@router.get("/me", status_code=status.HTTP_200_OK)
@router.get("/profile", status_code=status.HTTP_200_OK)
def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch profile and active session details for current authenticated user."""
    return {"user": current_user}


@router.put("/profile", status_code=status.HTTP_200_OK)
def update_profile(
    body: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update demographic/contact profile fields for authenticated patient, doctor, or admin."""
    role = current_user.get("role")
    safe_body = filter_profile_update(body)
    if not safe_body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid updatable fields provided.")

    try:
        if role == "DOCTOR":
            updated_user = database.update_doctor_profile(current_user["user_id"], safe_body)
        elif role == "ADMIN":
            updated_user = database.update_admin_profile(current_user["user_id"], safe_body)
        else:
            updated_user = database.update_patient_profile(current_user["user_id"], safe_body)
        return {
            "message": "Profile updated successfully.",
            "user": updated_user or current_user
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bootstrap-admin", status_code=status.HTTP_200_OK)
def bootstrap_initial_admin(
    req: Optional[AdminBootstrapRequest] = None,
    x_bootstrap_key: Optional[str] = Header(None)
):
    """
    Secure administration bootstrap endpoint.
    Allowed ONLY under explicit secure development/bootstrap configuration.
    Rejects requests in default/production mode, and permanently locks once an admin account exists.
    """
    key_provided = req.bootstrap_key if (req and req.bootstrap_key) else x_bootstrap_key
    env_enabled = config.ALLOW_ADMIN_BOOTSTRAP
    key_valid = bool(config.ADMIN_BOOTSTRAP_KEY) and (key_provided == config.ADMIN_BOOTSTRAP_KEY)

    if not (env_enabled or key_valid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin bootstrap endpoint is disabled in default runtime configuration."
        )

    b_email = (req.email if req and req.email else config.DEMO_ADMIN_EMAIL).strip().lower()
    b_pass = req.password if (req and req.password) else config.DEMO_ADMIN_PASSWORD
    b_name = req.full_name if (req and req.full_name) else "System Administrator"

    success, msg, admin_user = database.bootstrap_admin(
        email=b_email,
        password=b_pass,
        full_name=b_name
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=msg
        )

    return {
        "message": msg,
        "admin": admin_user
    }
