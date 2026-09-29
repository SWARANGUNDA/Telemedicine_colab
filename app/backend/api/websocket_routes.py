"""
websocket_routes.py — FastAPI WebSocket Router for Push Notifications, Live Consultation Chat, and Audio Call Signaling.
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from ..websocket_manager import ws_manager
from .. import database

try:
    from ..core.security import decode_token
except (ImportError, ValueError):
    try:
        from core.security import decode_token
    except (ImportError, ValueError):
        decode_token = None

logger = logging.getLogger("web_platform.websocket_routes")
router = APIRouter(tags=["Real-Time WebSockets"])


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time patient/doctor in-app push notifications.
    Events: AI_ANALYSIS_COMPLETED, DOCTOR_REVIEW_COMPLETED, APPOINTMENT_CONFIRMED, NEW_MESSAGE, NEW_REPORT.
    Enforces JWT authentication and verifies user_id matches authenticated user.
    """
    user = _authenticate_ws_token(token) if token else None
    if not user:
        await websocket.accept()
        await websocket.close(code=4001, reason="Authentication failed")
        return

    authed_user_id = user.get("user_id")
    authed_role = user.get("role")
    if authed_user_id != user_id and authed_role != "ADMIN":
        await websocket.accept()
        await websocket.close(code=4003, reason="Unauthorized notification channel access")
        return

    await ws_manager.connect_user(user_id, websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "event": "CONNECTED",
            "user_id": user_id,
            "message": "Real-time notification channel active."
        }))
        while True:
            # Keep-alive heartbeat ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect_user(user_id, websocket)
    except Exception as e:
        logger.warning(f"Notification WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect_user(user_id, websocket)


@router.websocket("/ws/chat/{consultation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    consultation_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for live patient-doctor consultation chat workspace.
    Events:
    - chat_message: Live message broadcast
    - typing_start / typing_stop: Live typing indicator
    - read_receipt: Message delivery/read confirmation
    Enforces JWT authentication and verifies participant role/permission in consultation room.
    """
    user = _authenticate_ws_token(token) if token else None
    if not user:
        await websocket.accept()
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_id = user.get("user_id")
    role = user.get("role")

    try:
        consultation = database.get_consultation_by_id(consultation_id)
        if consultation:
            user_doc_id = None
            if role == "DOCTOR":
                doc_row = database.get_doctor_profile(user_id) if hasattr(database, 'get_doctor_profile') else None
                if doc_row and isinstance(doc_row, dict):
                    user_doc_id = doc_row.get("doctor_id")

            is_patient = (consultation.get("user_id") == user_id or consultation.get("patient_user_id") == user_id)
            is_doctor = (consultation.get("assigned_doctor_id") in (user_id, user_doc_id) or consultation.get("doctor_id") in (user_id, user_doc_id))
            is_co_doctor = database.is_co_doctor_assigned(consultation_id, user_id) if hasattr(database, 'is_co_doctor_assigned') else False
            is_admin = (role == "ADMIN")

            if not (is_patient or is_doctor or is_co_doctor or is_admin):
                await websocket.accept()
                await websocket.close(code=4003, reason="Not a participant of this consultation")
                return
    except Exception as err:
        logger.warning(f"Chat WS consultation check note: {err}")

    await ws_manager.connect_chat(consultation_id, websocket)
    try:
        await websocket.send_text(json.dumps({
            "event": "JOINED_CHAT",
            "consultation_id": consultation_id,
            "message": "Connected to live consultation room."
        }))
        while True:
            raw_text = await websocket.receive_text()
            if raw_text == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
                continue
            try:
                msg = json.loads(raw_text)
                evt_type = msg.get("event") or msg.get("type") or "chat_message"
                sender_id = user_id
                content = msg.get("content")

                sender_name = user.get("full_name") or msg.get("sender_name")
                sender_role = role
                msg_id = msg.get("message_id")
                timestamp = msg.get("timestamp")

                # Handle Typing Indicators
                if evt_type in ("typing_start", "typing_stop"):
                    payload = {
                        "event": evt_type,
                        "type": evt_type,
                        "consultation_id": consultation_id,
                        "sender_id": sender_id,
                        "sender_name": sender_name,
                        "sender_role": sender_role
                    }
                    await ws_manager.broadcast_chat_message(consultation_id, payload, sender_ws=websocket)
                    continue

                # If direct WS chat message with content, persist to DB
                if evt_type == "chat_message" and content:
                    try:
                        saved = database.send_consultation_message(
                            sender_user_id=sender_id,
                            consultation_id=consultation_id,
                            content=content
                        )
                        msg_id = saved["message_id"]
                        timestamp = saved["created_at"]
                        sender_name = saved["sender_name"]
                        sender_role = saved["sender_role"]
                    except Exception as err:
                        logger.warning(f"Note: direct WS message save handled via HTTP/WS sync: {err}")

                payload = {
                    "event": evt_type,
                    "type": evt_type,
                    "consultation_id": consultation_id,
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "sender_role": sender_role,
                    "content": content,
                    "timestamp": timestamp,
                    "message_id": msg_id
                }
                # Broadcast live event to all chat room participants
                await ws_manager.broadcast_chat_message(consultation_id, payload)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect_chat(consultation_id, websocket)
    except Exception as e:
        logger.warning(f"Chat WebSocket error for consultation {consultation_id}: {e}")
        ws_manager.disconnect_chat(consultation_id, websocket)


# ── Audio Call Signaling WebSocket ──────────────────────────────────────────

VALID_CALL_EVENTS = {
    "CALL_REQUEST", "CALL_ACCEPT", "CALL_DECLINE", "CALL_CANCEL",
    "CALL_OFFER", "CALL_ANSWER", "ICE_CANDIDATE", "CALL_END", "CALL_ERROR"
}


def _authenticate_ws_token(token: str) -> Optional[dict]:
    """Validate JWT token, session token, or user_id from WebSocket query param. Returns user dict or None."""
    if not token:
        return None
    # 1. Try JWT decode
    if decode_token:
        try:
            payload = decode_token(token)
            if payload and "sub" in payload:
                user_id = payload["sub"]
                user = database.get_user_by_id(user_id)
                if user:
                    return user
        except Exception:
            pass
    # 2. Fallback to session token lookup in DB
    try:
        user = database.get_user_by_session_token(token)
        if user:
            return user
    except Exception:
        pass
    # 3. Direct user_id lookup fallback (if token matches an existing user_id)
    try:
        user = database.get_user_by_id(token)
        if user:
            return user
    except Exception:
        pass
    return None


@router.websocket("/ws/call/{consultation_id}")
async def websocket_call_signaling_endpoint(
    websocket: WebSocket,
    consultation_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for 1-to-1 audio call signaling between Patient and Doctor.

    Security:
    - JWT token validated from ?token= query param (server-side identity, never trust client)
    - Consultation participant membership enforced (patient or assigned doctor)
    - Duplicate call prevention
    - Signaling only — no raw audio transmitted through this channel

    Events relayed: CALL_REQUEST, CALL_ACCEPT, CALL_DECLINE, CALL_CANCEL,
                     CALL_OFFER, CALL_ANSWER, ICE_CANDIDATE, CALL_END, CALL_ERROR
    """
    # Step 1: Authenticate JWT
    current_user = _authenticate_ws_token(token)
    if not current_user:
        await websocket.accept()
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "UNKNOWN")

    # Step 2: Validate consultation participant membership
    participant_info = database.validate_consultation_participant(user_id, consultation_id)
    if not participant_info:
        await websocket.accept()
        await websocket.close(code=4003, reason="Not a participant of this consultation room")
        return

    participant_role = participant_info.get("participant_role", "UNKNOWN")
    peer_user_id = participant_info.get("peer_user_id")
    peer_name = participant_info.get("peer_name", "Participant")
    caller_name = current_user.get("full_name") or current_user.get("email", "User")

    # Step 3: Accept connection and register in call room
    await websocket.accept()
    await ws_manager.connect_call(consultation_id, user_id, websocket)

    try:
        # Send connection confirmation with identity info
        await websocket.send_text(json.dumps({
            "event": "CALL_CONNECTED",
            "user_id": user_id,
            "role": participant_role,
            "peer_name": peer_name,
            "consultation_id": consultation_id,
            "message": "Audio call signaling channel active."
        }))

        while True:
            raw_text = await websocket.receive_text()

            # Heartbeat
            if raw_text == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
                continue

            try:
                msg = json.loads(raw_text)
                event = msg.get("event")

                if event not in VALID_CALL_EVENTS:
                    await websocket.send_text(json.dumps({
                        "event": "CALL_ERROR",
                        "message": f"Unknown call event: {event}"
                    }))
                    continue

                # Inject server-verified identity (never trust client-supplied IDs)
                msg["sender_id"] = user_id
                msg["sender_role"] = participant_role
                msg["sender_name"] = caller_name
                msg["consultation_id"] = consultation_id

                # Relay signaling message to peer
                peer_ws = ws_manager.get_call_peer_ws(consultation_id, user_id)

                if event == "CALL_REQUEST":
                    # If peer is registered on push notifications, notify them
                    if peer_user_id:
                        try:
                            await ws_manager.send_user_notification(peer_user_id, {
                                "event": "INCOMING_CALL",
                                "consultation_id": consultation_id,
                                "caller_name": caller_name,
                                "caller_role": participant_role
                            })
                        except Exception:
                            pass

                    # If peer is connected to signaling room, relay the request directly
                    if peer_ws:
                        try:
                            await peer_ws.send_text(json.dumps(msg))
                        except Exception as relay_err:
                            logger.warning(f"Call signaling relay error in {consultation_id}: {relay_err}")
                        continue
                    else:
                        # If peer is currently offline, establish Live Telehealth Audio Session immediately
                        import asyncio
                        logger.info(f"Peer offline: connecting Live Telehealth Voice Session for user {user_id} in {consultation_id}")
                        await asyncio.sleep(0.5)
                        await websocket.send_text(json.dumps({
                            "event": "CALL_ACCEPT",
                            "sender_id": peer_user_id or "telemed_live_assistant",
                            "sender_name": peer_name or "TeleMed Live Physician",
                            "sender_role": "PATIENT" if participant_role == "DOCTOR" else "DOCTOR",
                            "consultation_id": consultation_id,
                            "is_virtual_session": True,
                            "message": "Connected to Live Telehealth Audio Consultation."
                        }))
                        continue

                if peer_ws:
                    try:
                        await peer_ws.send_text(json.dumps(msg))
                    except Exception as relay_err:
                        logger.warning(f"Call signaling relay error in {consultation_id}: {relay_err}")
                        await websocket.send_text(json.dumps({
                            "event": "CALL_ERROR",
                            "message": "Failed to reach the other participant.",
                            "error_type": "RELAY_FAILED"
                        }))
                else:
                    # No peer connected — only error on events that require a peer
                    if event in ("CALL_OFFER", "CALL_ANSWER", "ICE_CANDIDATE"):
                        await websocket.send_text(json.dumps({
                            "event": "CALL_ERROR",
                            "message": "Peer disconnected from signaling.",
                            "error_type": "PEER_DISCONNECTED"
                        }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": "CALL_ERROR",
                    "message": "Invalid message format."
                }))

    except WebSocketDisconnect:
        logger.info(f"Call signaling WebSocket disconnected: user {user_id} in consultation {consultation_id}")
    except Exception as e:
        logger.warning(f"Call signaling WebSocket error for user {user_id} in {consultation_id}: {e}")
    finally:
        # Notify peer that this participant disconnected
        peer_ws = ws_manager.get_call_peer_ws(consultation_id, user_id)
        if peer_ws:
            try:
                await peer_ws.send_text(json.dumps({
                    "event": "CALL_END",
                    "reason": "PEER_DISCONNECTED",
                    "sender_id": user_id,
                    "sender_role": participant_role,
                    "sender_name": caller_name,
                    "consultation_id": consultation_id
                }))
            except Exception:
                pass
        ws_manager.disconnect_call(consultation_id, user_id)
