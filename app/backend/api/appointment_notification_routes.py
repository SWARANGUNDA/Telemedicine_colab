"""
appointment_notification_routes.py — FastAPI Endpoints for Level 8 Appointment Scheduling & In-App Notifications.
Strictly enforces RBAC and recipient privacy boundaries.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import database
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/v1", tags=["Level 8: Appointments & Notifications"])


class AvailabilitySlotItem(BaseModel):
    slot_start: str = Field(..., description="UTC Start ISO string")
    slot_end: str = Field(..., description="UTC End ISO string")


class ConfigureAvailabilityRequest(BaseModel):
    slots: List[AvailabilitySlotItem]


class BookAppointmentRequest(BaseModel):
    consultation_id: Optional[str] = Field(None, description="Active consultation ID (Optional)")
    slot_id: Optional[str] = Field(None, description="Available doctor slot ID (Optional)")
    notes: Optional[str] = Field(None, description="Optional booking notes")
    doctor_id: Optional[str] = Field(None, description="Doctor ID if booking on-demand/fallback slot")
    slot_start: Optional[str] = Field(None, description="Start time ISO string if fallback slot")
    slot_end: Optional[str] = Field(None, description="End time ISO string if fallback slot")


class UpdateAppointmentStatusRequest(BaseModel):
    status: str = Field(..., description="REQUESTED, CONFIRMED, UPCOMING, IN_CONSULTATION, COMPLETED, CANCELLED, NO_SHOW, RESCHEDULED")
    reason: Optional[str] = Field(None, description="Reason for cancellation or reschedule")
    new_slot_id: Optional[str] = Field(None, description="New slot ID if rescheduling")


# ------------------------------------------------------------------
# Notifications Endpoints
# ------------------------------------------------------------------

@router.get("/notifications", status_code=status.HTTP_200_OK)
def get_notifications(
    unread_only: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Fetch persistent in-app notifications for the authenticated user."""
    notifs = database.get_user_notifications(current_user["user_id"], unread_only=unread_only)
    unread_count = sum(1 for n in notifs if n["is_read"] == 0)
    return {
        "status": "SUCCESS",
        "unread_count": unread_count,
        "notifications": notifs
    }


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_read(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark a notification as read."""
    success = database.mark_notification_read(current_user["user_id"], notification_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return {"status": "SUCCESS", "message": "Notification marked as read."}


@router.post("/notifications/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark all notifications as read for current user."""
    count = database.mark_all_notifications_read(current_user["user_id"])
    return {"status": "SUCCESS", "marked_read_count": count}


# ------------------------------------------------------------------
# Doctor Availability Endpoints
# ------------------------------------------------------------------

@router.post("/doctor/availability", status_code=status.HTTP_201_CREATED)
def configure_doctor_availability(
    req: ConfigureAvailabilityRequest,
    current_user: Dict[str, Any] = Depends(require_role(["DOCTOR"]))
):
    """Configure availability slots for a VERIFIED doctor."""
    try:
        slots_list = [s.model_dump() for s in req.slots]
        all_slots = database.set_doctor_availability_slots(current_user["user_id"], slots_list)
        return {
            "status": "SUCCESS",
            "message": f"Successfully configured availability slots.",
            "slots": all_slots
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/doctor/availability/slot", status_code=status.HTTP_201_CREATED)
def add_single_doctor_availability_slot(
    req: AvailabilitySlotItem,
    current_user: Dict[str, Any] = Depends(require_role(["DOCTOR"]))
):
    """Add a single consultation availability slot for the logged-in VERIFIED doctor."""
    try:
        slot = database.add_doctor_availability_slot(current_user["user_id"], req.slot_start, req.slot_end)
        return {
            "status": "SUCCESS",
            "message": "Availability slot added successfully.",
            "slot": slot
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/doctor/availability/{slot_id}", status_code=status.HTTP_200_OK)
def delete_doctor_availability_slot(
    slot_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["DOCTOR"]))
):
    """Delete an unbooked availability slot for the logged-in doctor."""
    success = database.delete_doctor_availability_slot(current_user["user_id"], slot_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete slot. Slot may be booked, invalid, or owned by another doctor.")
    return {"status": "SUCCESS", "message": "Slot deleted successfully."}


@router.get("/doctor/my-availability", status_code=status.HTTP_200_OK)
def get_my_availability_slots(
    available_only: bool = False,
    current_user: Dict[str, Any] = Depends(require_role(["DOCTOR"]))
):
    """Get all availability slots for the authenticated doctor."""
    user_id = current_user["user_id"]
    doc_profile = database.get_doctor_profile(user_id) if hasattr(database, "get_doctor_profile") else None
    doc_id = doc_profile.get("doctor_id") if (doc_profile and isinstance(doc_profile, dict) and "doctor_id" in doc_profile) else user_id
    slots = database.list_doctor_availability_slots(doc_id, available_only=available_only)
    return {
        "status": "SUCCESS",
        "doctor_id": doc_id,
        "slots": slots
    }


@router.get("/doctor/profile", status_code=status.HTTP_200_OK)
def get_doctor_profile_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve profile details for current authenticated doctor."""
    if current_user.get("role") not in ("DOCTOR", "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access restricted to verified doctors.")
    
    user_id = current_user["user_id"]
    user_obj = database.get_user_by_id(user_id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor account not found.")

    doc_prof = user_obj.get("doctor_profile")
    return {
        "status": "SUCCESS",
        "doctor_id": doc_prof.get("doctor_id") if doc_prof else None,
        "profile": doc_prof or user_obj,
        "user": user_obj
    }


@router.put("/doctor/profile", status_code=status.HTTP_200_OK)
def update_doctor_profile_endpoint(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update doctor profile details in persistent database."""
    user_id = current_user["user_id"]
    updated = database.update_doctor_profile(user_id, payload)
    return {
        "status": "SUCCESS",
        "message": "Doctor profile updated successfully.",
        "profile": updated or payload
    }


@router.get("/doctors", status_code=status.HTTP_200_OK)
def list_verified_doctors(
    specialization: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List verified doctors for patient appointment booking and specialist consultation."""
    doctors = database.list_doctors(status="VERIFIED")
    if specialization and specialization.upper() != "ALL":
        doctors = [d for d in doctors if d.get("doctor_profile", {}).get("specialization") == specialization]
    return {
        "status": "SUCCESS",
        "doctors": doctors
    }


@router.get("/doctors/{doctor_id}/availability", status_code=status.HTTP_200_OK)
def list_doctor_availability(
    doctor_id: str,
    available_only: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List available consultation slots for a specific doctor."""
    slots = database.list_doctor_availability_slots(doctor_id, available_only=available_only)
    return {
        "status": "SUCCESS",
        "doctor_id": doctor_id,
        "slots": slots
    }


# ------------------------------------------------------------------
# Appointment Endpoints
# ------------------------------------------------------------------

@router.post("/appointments", status_code=status.HTTP_201_CREATED)
def book_consultation_appointment(
    req: BookAppointmentRequest,
    current_user: Dict[str, Any] = Depends(require_role(["PATIENT", "DOCTOR", "ADMIN"]))
):
    """Patient or Doctor books a consultation appointment slot."""
    try:
        booking_user_id = current_user["user_id"]
        if current_user.get("role") in ("DOCTOR", "ADMIN") and req.consultation_id:
            c = database.get_consultation_by_id(req.consultation_id)
            if c and c.get("user_id"):
                booking_user_id = c["user_id"]

        apt = database.book_appointment(
            user_id=booking_user_id,
            consultation_id=req.consultation_id,
            slot_id=req.slot_id,
            notes=req.notes or "",
            doctor_id=req.doctor_id,
            slot_start=req.slot_start,
            slot_end=req.slot_end
        )
        import asyncio
        from ..websocket_manager import ws_manager
        doc_u = database.get_doctor_user_id(apt.get("doctor_id"))
        user_ids = [current_user["user_id"]]
        if doc_u:
            user_ids.append(doc_u)
        payload = {
            "event": "APPOINTMENT_CREATED",
            "type": "APPOINTMENT_CREATED",
            "appointment": apt,
            "message": "New patient appointment booked."
        }
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast_event_to_users(user_ids, payload))
        except RuntimeError:
            pass

        return {
            "status": "SUCCESS",
            "message": "Appointment successfully booked.",
            "appointment": apt
        }
    except ValueError as e:
        msg = str(e)
        status_code = status.HTTP_409_CONFLICT if ("already" in msg.lower() or "conflict" in msg.lower() or "unavailable" in msg.lower()) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=msg)


@router.get("/appointments", status_code=status.HTTP_200_OK)
def list_user_appointments(
    status_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List appointments for Patient, Doctor, or Admin."""
    apts = database.list_user_appointments(
        user_id=current_user["user_id"],
        role=current_user["role"],
        status_filter=status_filter
    )
    return {
        "status": "SUCCESS",
        "count": len(apts),
        "appointments": apts
    }


@router.post("/appointments/{appointment_id}/status", status_code=status.HTTP_200_OK)
def update_appointment_status(
    appointment_id: str,
    req: UpdateAppointmentStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancel, complete, or reschedule an appointment."""
    try:
        apt = database.update_appointment_status(
            user_id=current_user["user_id"],
            role=current_user["role"],
            appointment_id=appointment_id,
            new_status=req.status,
            reason=req.reason,
            new_slot_id=req.new_slot_id
        )
        import asyncio
        from ..websocket_manager import ws_manager
        patient_u = apt.get("patient_user_id")
        doc_u = database.get_doctor_user_id(apt.get("doctor_id"))
        user_ids = [u for u in (patient_u, doc_u) if u]
        payload = {
            "event": f"APPOINTMENT_{req.status.upper()}",
            "type": "APPOINTMENT_UPDATED",
            "status": req.status.upper(),
            "appointment": apt,
            "message": f"Appointment status updated to '{req.status}'."
        }
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast_event_to_users(user_ids, payload))
        except RuntimeError:
            pass

        return {
            "status": "SUCCESS",
            "message": f"Appointment status updated to '{req.status}'.",
            "appointment": apt
        }
    except ValueError as e:
        msg = str(e)
        status_code = status.HTTP_409_CONFLICT if ("already" in msg.lower() or "conflict" in msg.lower() or "terminal" in msg.lower()) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=msg)


@router.post("/appointments/{appointment_id}/join", status_code=status.HTTP_200_OK)
def join_consultation_appointment(
    appointment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Transition appointment & consultation to IN_CONSULTATION status when joining session."""
    try:
        apt = database.update_appointment_status(
            user_id=current_user["user_id"],
            role=current_user["role"],
            appointment_id=appointment_id,
            new_status="IN_CONSULTATION"
        )
        import asyncio
        from ..websocket_manager import ws_manager
        patient_u = apt.get("patient_user_id")
        doc_u = database.get_doctor_user_id(apt.get("doctor_id"))
        user_ids = [u for u in (patient_u, doc_u) if u]
        payload = {
            "event": "CONSULTATION_STARTED",
            "type": "CONSULTATION_STARTED",
            "appointment": apt,
            "message": "Teleconsultation session active."
        }
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast_event_to_users(user_ids, payload))
        except RuntimeError:
            pass

        return {
            "status": "SUCCESS",
            "message": "Successfully joined active teleconsultation session.",
            "appointment": apt
        }
    except ValueError as e:
        msg = str(e)
        status_code = status.HTTP_409_CONFLICT if ("terminal" in msg.lower() or "conflict" in msg.lower()) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=msg)
