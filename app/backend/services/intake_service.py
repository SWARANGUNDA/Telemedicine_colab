"""
intake_service.py — Service Wrapper around MultimodalIntakeEngine (IMDIE).

Wraps the frozen Phase 1 IMDIE engine, executing stages 1–15:
classification, extraction, mapping, normalization, validation, quality scoring,
missing feature assistance, multi-report fusion, and expert routing.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Union

from services.multimodal_intake.engine import MultimodalIntakeEngine

logger = logging.getLogger("web_platform.services.intake")


class IntakeService:
    """Service layer wrapping MultimodalIntakeEngine."""

    def __init__(self):
        self.imdie = MultimodalIntakeEngine()

    def process_uploaded_reports(
        self,
        file_inputs: List[Union[str, Path, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Pass uploaded report filepaths or dicts to IMDIE."""
        logger.info("Executing IMDIE processing for %d files...", len(file_inputs))
        str_inputs = [str(f) if isinstance(f, Path) else f for f in file_inputs]
        result = self.imdie.process_reports(str_inputs)
        return result
