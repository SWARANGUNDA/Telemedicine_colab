"""
logging_config.py — Structured Production Logging for TeleMed AI Platform.

Configures file and stream loggers:
- logs/api.log: REST HTTP request logs
- logs/prediction.log: ML inference and fusion logs
- logs/security.log: Auth, JWT, and RBAC logs
- logs/audit.log: Immutable governance logs
- logs/error.log: System warnings and errors
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s")


def setup_logger(name: str, log_filename: str, level=logging.INFO) -> logging.Logger:
    """Configures a dedicated logger with rotating file handler and console output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger

    # File Handler (Max 10MB per file, max 5 backup files)
    file_path = LOG_DIR / log_filename
    file_handler = RotatingFileHandler(file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(console_handler)

    return logger


# Instantiate dedicated production loggers
api_logger = setup_logger("telemed.api", "api.log")
prediction_logger = setup_logger("telemed.prediction", "prediction.log")
security_logger = setup_logger("telemed.security", "security.log")
audit_logger = setup_logger("telemed.audit", "audit.log")
error_logger = setup_logger("telemed.error", "error.log", level=logging.WARNING)
