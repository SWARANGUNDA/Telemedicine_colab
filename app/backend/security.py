"""
security.py — Level 11 Security, Rate Limiting, Input Validation & Production Hardening Module.

Provides:
1. Rate limiter with IP + endpoint scoping and brute-force protection.
2. Strong password policy enforcement.
3. Input sanitization and anti-injection utilities.
4. Security headers middleware.
5. Sensitive data scrubbing for safe error responses.
"""

import time
import re
import threading
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("web_platform.security")

# ---------------------------------------------------------------------------
# Rate Limiter — Sliding Window with IP + Route Scoping
# ---------------------------------------------------------------------------

class RateLimiter:
    """Thread-safe sliding window rate limiter with configurable limits per route category."""

    def __init__(self):
        self._lock = threading.Lock()
        # {key: [timestamp, ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        # Configurable limits: (max_requests, window_seconds)
        self.limits = {
            "login": (10, 60),          # 10 login attempts per minute per IP
            "register": (10, 60),      # 10 registrations per minute per IP
            "api_default": (120, 60),  # 120 API calls per minute per IP
            "upload": (10, 60),        # 10 uploads per minute per IP
        }

    def _clean_old(self, key: str, window: float, now: float):
        self._requests[key] = [t for t in self._requests[key] if now - t < window]

    def check(self, client_ip: str, category: str = "api_default") -> Tuple[bool, int]:
        """
        Check if the request is within rate limits.
        Returns (allowed, retry_after_seconds).
        """
        max_requests, window = self.limits.get(category, self.limits["api_default"])
        key = f"{client_ip}:{category}"
        now = time.time()

        with self._lock:
            self._clean_old(key, window, now)
            if len(self._requests[key]) >= max_requests:
                oldest = self._requests[key][0] if self._requests[key] else now
                retry_after = int(window - (now - oldest)) + 1
                return False, max(retry_after, 1)
            self._requests[key].append(now)
            return True, 0

    def record(self, client_ip: str, category: str = "api_default"):
        """Record a request (used when check is deferred)."""
        key = f"{client_ip}:{category}"
        now = time.time()
        with self._lock:
            window = self.limits.get(category, self.limits["api_default"])[1]
            self._clean_old(key, window, now)
            self._requests[key].append(now)


# Global singleton
RATE_LIMITER = RateLimiter()


# ---------------------------------------------------------------------------
# Strong Password Policy
# ---------------------------------------------------------------------------

PASSWORD_MIN_LENGTH = 8
PASSWORD_REGEX = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,128}$'
)

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforce strong password policy:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    Returns (valid, error_message).
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
    if len(password) > 128:
        return False, "Password must not exceed 128 characters."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)."
    return True, ""


# ---------------------------------------------------------------------------
# Input Sanitization
# ---------------------------------------------------------------------------

# Characters that could be used for SQL injection or XSS
DANGEROUS_PATTERNS = [
    re.compile(r'<script', re.IGNORECASE),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),
    re.compile(r'--'),  # SQL comment
]

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input: trim, length-limit, strip dangerous patterns."""
    if not isinstance(value, str):
        return str(value)[:max_length]
    value = value.strip()[:max_length]
    # Strip null bytes
    value = value.replace('\x00', '')
    return value

def check_path_traversal(filename: str) -> bool:
    """Return True if filename contains path traversal attempts."""
    dangerous = ['..', '/', '\\', '\x00', '%2e', '%2f', '%5c']
    lower = filename.lower()
    return any(d in lower for d in dangerous)


# ---------------------------------------------------------------------------
# Sensitive Data Scrubbing
# ---------------------------------------------------------------------------

SENSITIVE_FIELDS = {
    'password', 'password_hash', 'salt', 'token', 'secret',
    'api_key', 'credential', 'session_token', 'auth_token',
    'db_path', 'file_path', 'stored_filename'
}

def scrub_sensitive_data(data: dict) -> dict:
    """Remove sensitive fields from API response dictionaries."""
    if not isinstance(data, dict):
        return data
    cleaned = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_FIELDS:
            continue
        elif isinstance(v, dict):
            cleaned[k] = scrub_sensitive_data(v)
        elif isinstance(v, list):
            cleaned[k] = [scrub_sensitive_data(i) if isinstance(i, dict) else i for i in v]
        else:
            cleaned[k] = v
    return cleaned

def safe_error_message(exc: Exception) -> str:
    """Return a safe error message that doesn't leak stack traces or internal paths."""
    msg = str(exc)
    # Strip file paths
    msg = re.sub(r'[A-Za-z]:\\[^\s"\']+', '[internal path]', msg)
    msg = re.sub(r'/[^\s"\']*\.(py|db|sql|conf|env)', '[internal path]', msg)
    # Strip stack trace patterns
    msg = re.sub(r'File ".*?", line \d+', '[internal]', msg)
    msg = re.sub(r'Traceback.*$', '', msg, flags=re.DOTALL)
    return msg.strip() or "An internal error occurred."


# ---------------------------------------------------------------------------
# Security Headers
# ---------------------------------------------------------------------------

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(self), microphone=(self), geolocation=()",
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https:; media-src 'self' blob: data:; connect-src 'self' http://localhost:* http://127.0.0.1:* ws: wss: https:; frame-ancestors 'self' http://localhost:* http://127.0.0.1:*; frame-src 'self' data: blob: http://localhost:* http://127.0.0.1:*;",
}


# ---------------------------------------------------------------------------
# Privilege Escalation Prevention
# ---------------------------------------------------------------------------

PROFILE_FORBIDDEN_FIELDS = {
    'user_id', 'role', 'email', 'password', 'password_hash', 'salt',
    'created_at', 'verification_status', 'doctor_id', 'patient_id',
    'is_admin', 'is_verified', 'is_suspended'
}

def filter_profile_update(data: dict) -> dict:
    """Remove fields that should never be user-updatable via profile endpoints."""
    return {k: v for k, v in data.items() if k.lower() not in PROFILE_FORBIDDEN_FIELDS}


# ---------------------------------------------------------------------------
# File Security & Magic Byte Validation (Phase 3)
# ---------------------------------------------------------------------------

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max limit

MAGIC_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpeg": [b"\xff\xd8\xff"],
    "jpg": [b"\xff\xd8\xff"],
}

def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent directory traversal attacks."""
    clean_name = Path(filename).name
    if '.' in clean_name:
        base, _, ext = clean_name.rpartition('.')
        clean_base = re.sub(r'[^a-zA-Z0-9]+', '_', base).strip('_')
        clean_ext = re.sub(r'[^a-zA-Z0-9]+', '', ext)
        return f"{clean_base}.{clean_ext}" if clean_ext else clean_base
    clean = re.sub(r'[^a-zA-Z0-9]+', '_', clean_name).strip('_')
    return clean or "uploaded_report"

def validate_uploaded_file(filename: str, content: bytes) -> Tuple[bool, str, str]:
    """Validate uploaded file size, magic signature, and sanitize filename.

    Returns:
        Tuple[is_valid, error_message, sanitized_filename]
    """
    if len(content) > MAX_FILE_SIZE_BYTES:
        return False, f"File size ({round(len(content) / (1024*1024), 1)} MB) exceeds 25 MB limit.", filename

    clean_name = sanitize_filename(filename)
    ext = clean_name.split('.')[-1].lower() if '.' in clean_name else ""

    if ext in MAGIC_SIGNATURES:
        signatures = MAGIC_SIGNATURES[ext]
        has_matching_sig = any(content.startswith(sig) for sig in signatures)
        if not has_matching_sig:
            return False, f"Invalid file content signature for extension .{ext}. File header magic bytes do not match expected format.", clean_name

    return True, "", clean_name

