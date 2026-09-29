"""
template_detector.py — Layout & Template Detection Engine (Phase 1).

Identifies report layouts (Apollo, Max, Thyrocare, Ayumetrix, Wearables, Gut Microbiome, etc.)
from text headers, organization signatures, table headers, and feature compositions.
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, Tuple

logger = logging.getLogger("imdie.template_detector")


class ReportTemplate(str, Enum):
    APOLLO = "APOLLO_HEALTHCARE"
    MAX_HEALTHCARE = "MAX_HEALTHCARE"
    THYROCARE = "THYROCARE"
    AYUMETRIX = "AYUMETRIX"
    SUNRISE_DIAGNOSTICS = "SUNRISE_DIAGNOSTICS"
    WEARABLE_CSV = "WEARABLE_TELEMETRY"
    GUT_MICROBIOME = "GUT_MICROBIOME"
    GENERIC_CLINICAL = "GENERIC_CLINICAL"
    UNKNOWN = "UNKNOWN_LAYOUT"


def detect_report_template(
    text_content: str,
    raw_extracted: Dict[str, Any] = None
) -> Tuple[ReportTemplate, float, Dict[str, Any]]:
    """Detect document layout template and confidence score.

    Args:
        text_content: Plaintext extracted from document.
        raw_extracted: Optional dictionary of raw extracted keys.

    Returns:
        Tuple of (ReportTemplate, confidence_score, metadata_details).
    """
    text_upper = (text_content or "").upper()
    keys_str = " ".join(raw_extracted.keys()).upper() if raw_extracted else ""
    full_text_search = text_upper + " " + keys_str

    meta = {
        "detected_keywords": [],
        "layout_format": "SINGLE_COLUMN"
    }

    # 1. Organization Signature Checks
    if "APOLLO" in full_text_search or "SUNRISE DIAGNOSTIC" in full_text_search:
        meta["detected_keywords"].append("APOLLO_SUNRISE")
        return ReportTemplate.APOLLO, 0.95, meta

    if "MAX HEALTHCARE" in full_text_search or "MAX LAB" in full_text_search:
        meta["detected_keywords"].append("MAX_LAB")
        return ReportTemplate.MAX_HEALTHCARE, 0.95, meta

    if "THYROCARE" in full_text_search:
        meta["detected_keywords"].append("THYROCARE")
        return ReportTemplate.THYROCARE, 0.95, meta

    if "AYUMETRIX" in full_text_search:
        meta["detected_keywords"].append("AYUMETRIX")
        return ReportTemplate.AYUMETRIX, 0.95, meta

    # 2. Domain & Layout Pattern Checks
    if any(kw in full_text_search for kw in ["AKKERMANSIA", "FAECALIBACTERIUM", "SHANNON_DIVERSITY", "MICROBIOME", "16S RRNA"]):
        meta["detected_keywords"].append("GUT_MICROBIOME_TAXA")
        meta["layout_format"] = "TAXONOMY_MATRIX"
        return ReportTemplate.GUT_MICROBIOME, 0.90, meta

    if any(kw in full_text_search for kw in ["STEPS", "ACTIVE_MINUTES", "RESTING_HEART_RATE", "CGM_AVERAGE", "TIME_IN_RANGE"]):
        meta["detected_keywords"].append("WEARABLE_TELEMETRY")
        meta["layout_format"] = "CSV_TIME_SERIES"
        return ReportTemplate.WEARABLE_CSV, 0.90, meta

    if any(kw in full_text_search for kw in ["HBA1C", "GLUCOSE", "CHOLESTEROL", "TRIGLYCERIDES", "ALT", "AST"]):
        meta["detected_keywords"].append("CLINICAL_LAB_VALUES")
        return ReportTemplate.GENERIC_CLINICAL, 0.80, meta

    return ReportTemplate.UNKNOWN, 0.50, meta
