"""
session_manager.py — Server-Side Analysis Session & State Lifecycle Tracker.

Enforces strict valid session state transitions:
CREATED ➔ EXTRACTED ➔ CONFIRMED ➔ ANALYZED ➔ XAI_READY ➔ REPORT_READY

Prevents predicting, explaining, or generating RAG reports when prerequisites
are missing. Auto-purges expired session files.
"""

import datetime
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config
from .config import SessionState, VALID_TRANSITIONS

logger = logging.getLogger("web_platform.session_manager")


class PatientSession:
    """Represents a single patient analysis session."""

    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id: str = session_id
        self.user_id: Optional[str] = user_id
        self.state: str = SessionState.CREATED
        self.created_at: datetime.datetime = datetime.datetime.now()
        self.last_accessed: datetime.datetime = datetime.datetime.now()

        self.uploaded_files: List[Path] = []
        self.imdie_output: Optional[Dict[str, Any]] = None
        self.confirmed_features: Optional[Dict[str, Dict[str, Any]]] = None
        self.quality_scores: Optional[Dict[str, Any]] = None
        self.active_modalities: List[str] = []
        self.missing_modalities: List[str] = []

        self.prediction_output: Optional[Dict[str, Any]] = None
        self.xai_output: Optional[Dict[str, Any]] = None
        self.rag_context: Optional[Dict[str, Any]] = None
        self.rag_report: Optional[Dict[str, Any]] = None

    def transition_to(self, new_state: str) -> None:
        """Validate and execute state transition."""
        allowed_next = VALID_TRANSITIONS.get(self.state, set())
        if new_state not in allowed_next and new_state != self.state:
            raise ValueError(
                f"Invalid session state transition: Cannot transition from '{self.state}' to '{new_state}'. "
                f"Prerequisites for '{new_state}' have not been completed."
            )
        self.state = new_state
        self.last_accessed = datetime.datetime.now()
        logger.info("Session %s transitioned to state '%s'", self.session_id, new_state)

    def is_expired(self) -> bool:
        """Check if session exceeded expiry threshold."""
        delta = (datetime.datetime.now() - self.last_accessed).total_seconds()
        return delta > config.SESSION_EXPIRY_SECONDS


class SessionManager:
    """Manages active patient analysis sessions in memory."""

    def __init__(self):
        self.sessions: Dict[str, PatientSession] = {}

    def create_session(self, user_id: Optional[str] = None) -> PatientSession:
        """Initialize a new analysis session with UUID."""
        self.purge_expired_sessions()
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = PatientSession(session_id, user_id=user_id)
        self.sessions[session_id] = session
        logger.info("Created new patient analysis session %s for user %s", session_id, user_id)
        return session

    def get_session(self, session_id: str) -> PatientSession:
        """Retrieve active session by ID."""
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found or expired. Please upload reports to start a new session.")
        if session.is_expired():
            self.delete_session(session_id)
            raise KeyError(f"Session '{session_id}' has expired due to inactivity. Please start a new session.")
        session.last_accessed = datetime.datetime.now()
        return session

    def delete_session(self, session_id: str) -> None:
        """Purge session data and temporary uploaded files."""
        session = self.sessions.pop(session_id, None)
        if session:
            for file_path in session.uploaded_files:
                if file_path.exists():
                    try:
                        file_path.unlink()
                        logger.info("Cleaned up temp file: %s", file_path)
                    except Exception as e:
                        logger.warning("Error deleting file %s: %s", file_path, e)

    def purge_expired_sessions(self) -> None:
        """Purge all expired sessions."""
        expired_ids = [sid for sid, sess in self.sessions.items() if sess.is_expired()]
        for sid in expired_ids:
            self.delete_session(sid)
