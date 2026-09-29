"""
audit_logger.py — Audit Trail & Processing Log Module (Module 15).

Maintains a transparent, timestamped processing audit trail:
- Report Uploaded
- Document Classified
- Features Extracted
- Units Normalized
- Duplicates Resolved
- Features Validated
- Quality Scored
- Missing Features Checked
- Feature Routing Completed
- Expert Availability Checked
- Prediction Strategy Formulated
"""

import datetime
import logging
from typing import Any, Dict, List

logger = logging.getLogger("imdie.audit")


class AuditLogger:
    """Maintains a structured audit log of all IMDIE operations."""

    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def log_step(self, stage: str, status: str, details: Any = None):
        """Record a pipeline execution step."""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "stage": stage,
            "status": status,
            "details": details
        }
        self.logs.append(entry)
        logger.info("AUDIT [%s] %s — %s", status, stage, str(details)[:100] if details else "")

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_steps": len(self.logs),
            "audit_trail": self.logs
        }
