"""
websocket_manager.py — Real-Time WebSocket Connection Manager for TeleMed AI Platform.

Handles active client connections, user room subscriptions, and real-time event broadcasting
for push notifications, live chat messages, typing indicators, and online status.
"""

import json
import logging
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket

logger = logging.getLogger("web_platform.websocket_manager")


class ConnectionManager:
    """Manages active WebSocket connections for push notifications, live consultation chat, and audio call signaling."""

    def __init__(self):
        # Map user_id -> list of active WebSockets
        self.active_user_connections: Dict[str, List[WebSocket]] = {}
        # Map consultation_id -> set of active WebSockets
        self.consultation_rooms: Dict[str, Set[WebSocket]] = {}
        # Map consultation_id -> {user_id: WebSocket} for audio call signaling
        self.call_rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect_user(self, user_id: str, websocket: WebSocket):
        """Accept WebSocket connection and attach to user_id notification channel."""
        await websocket.accept()
        if user_id not in self.active_user_connections:
            self.active_user_connections[user_id] = []
        self.active_user_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user_id {user_id}. Total connections: {len(self.active_user_connections[user_id])}")

    def disconnect_user(self, user_id: str, websocket: WebSocket):
        """Disconnect WebSocket connection from user channel."""
        if user_id in self.active_user_connections:
            if websocket in self.active_user_connections[user_id]:
                self.active_user_connections[user_id].remove(websocket)
            if not self.active_user_connections[user_id]:
                del self.active_user_connections[user_id]
        logger.info(f"WebSocket disconnected for user_id {user_id}.")

    async def connect_chat(self, consultation_id: str, websocket: WebSocket):
        """Accept WebSocket connection and join consultation chat room."""
        await websocket.accept()
        if consultation_id not in self.consultation_rooms:
            self.consultation_rooms[consultation_id] = set()
        self.consultation_rooms[consultation_id].add(websocket)
        logger.info(f"WebSocket joined chat room {consultation_id}. Active participants: {len(self.consultation_rooms[consultation_id])}")

    def disconnect_chat(self, consultation_id: str, websocket: WebSocket):
        """Leave consultation chat room."""
        if consultation_id in self.consultation_rooms:
            self.consultation_rooms[consultation_id].discard(websocket)
            if not self.consultation_rooms[consultation_id]:
                del self.consultation_rooms[consultation_id]
        logger.info(f"WebSocket left chat room {consultation_id}.")

    async def send_user_notification(self, user_id: str, payload: Dict[str, Any]):
        """Send push notification message to all active WebSocket connections of a user."""
        if user_id in self.active_user_connections:
            msg_str = json.dumps(payload)
            for ws in list(self.active_user_connections[user_id]):
                try:
                    await ws.send_text(msg_str)
                except Exception as e:
                    logger.warning(f"Error sending WebSocket message to user {user_id}: {e}")

    async def broadcast_chat_message(self, consultation_id: str, payload: Dict[str, Any], sender_ws: Optional[WebSocket] = None):
        """Broadcast live message to all participants in a consultation chat room."""
        if consultation_id in self.consultation_rooms:
            msg_str = json.dumps(payload)
            for ws in list(self.consultation_rooms[consultation_id]):
                if ws != sender_ws:
                    try:
                        await ws.send_text(msg_str)
                    except Exception as e:
                        logger.warning(f"Error broadcasting chat message in room {consultation_id}: {e}")

    async def broadcast_event_to_users(self, user_ids: List[str], payload: Dict[str, Any]):
        """Broadcast real-time push event to multiple target user IDs simultaneously."""
        for u_id in set(user_ids):
            if u_id:
                await self.send_user_notification(u_id, payload)

    def get_online_users(self) -> List[str]:
        """Returns list of currently online user IDs with active WebSocket connections."""
        return list(self.active_user_connections.keys())

    # ── Audio Call Signaling Room Management ─────────────────────────────

    async def connect_call(self, consultation_id: str, user_id: str, websocket: WebSocket):
        """Register a user's WebSocket for audio call signaling in a consultation room."""
        if consultation_id not in self.call_rooms:
            self.call_rooms[consultation_id] = {}
        self.call_rooms[consultation_id][user_id] = websocket
        logger.info(f"Call signaling: user {user_id} joined call room {consultation_id}. Participants: {list(self.call_rooms[consultation_id].keys())}")

    def disconnect_call(self, consultation_id: str, user_id: str):
        """Remove a user from audio call signaling room."""
        if consultation_id in self.call_rooms:
            self.call_rooms[consultation_id].pop(user_id, None)
            if not self.call_rooms[consultation_id]:
                del self.call_rooms[consultation_id]
        logger.info(f"Call signaling: user {user_id} left call room {consultation_id}.")

    def get_call_peer_ws(self, consultation_id: str, sender_id: str) -> Optional[WebSocket]:
        """Get the WebSocket of the OTHER participant in a call room (not the sender)."""
        room = self.call_rooms.get(consultation_id, {})
        for uid, ws in room.items():
            if uid != sender_id:
                return ws
        return None

    def is_call_active(self, consultation_id: str) -> bool:
        """Check if a call room has 2 participants (call in progress)."""
        return len(self.call_rooms.get(consultation_id, {})) >= 2

    def get_call_participants(self, consultation_id: str) -> List[str]:
        """Get list of user_ids currently in a call room."""
        return list(self.call_rooms.get(consultation_id, {}).keys())


# Singleton instance
ws_manager = ConnectionManager()

