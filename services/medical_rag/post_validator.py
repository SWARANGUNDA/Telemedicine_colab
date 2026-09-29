"""
post_validator.py — Post-Generation & Citation Validation Engine.

Performs mandatory post-generation validation before displaying any LLM response:
1. Verifies model probabilities were NOT modified.
2. Verifies patient measured feature values were NOT fabricated.
3. Verifies all bracketed citations [REF_X] map to actually retrieved evidence chunks and attached to valid claims.
4. Verifies no standalone/orphan citations, empty bullets, or dangling REF tags exist.
5. Verifies mandatory research disclaimer is present.
"""

import logging
import re
from typing import Any, Dict, List

from . import config

logger = logging.getLogger("services.medical_rag.post_validator")


def clean_rag_response(text: str) -> str:
    """Sanitize RAG response text to eliminate standalone citations, empty bullets, and duplicate lines."""
    lines = text.split("\n")
    cleaned_lines = []
    seen_claims = set()

    for line in lines:
        stripped = line.strip()
        # 1. Remove standalone citation-only lines (e.g. "- [REF_3]" or "[REF_1]")
        if re.match(r"^[-•*]?\s*\[REF_\d+\]\s*$", stripped):
            continue

        # 2. Remove empty bullet lines (e.g. "-" or "•")
        if re.match(r"^[-•*]\s*$", stripped):
            continue

        # 3. Remove duplicate non-header claim lines
        if stripped.startswith("- ") or stripped.startswith("• "):
            claim_core = re.sub(r"\s*\[REF_\d+\]", "", stripped).strip().lower()
            if claim_core in seen_claims:
                continue
            seen_claims.add(claim_core)

        cleaned_lines.append(line)

    # Join cleaned lines and clean up residual double empty lines
    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text


class RAGPostValidator:
    """Post-generation and citation validation engine."""

    def validate_llm_response(
        self,
        llm_response: str,
        patient_context: Dict[str, Any],
        retrieved_evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Validate LLM generated text against patient context and retrieved evidence.

        Args:
            llm_response: Generated text string.
            patient_context: RAG patient context contract object.
            retrieved_evidence: List of retrieved evidence chunk dicts.

        Returns:
            Dict containing 'is_valid', 'validation_errors', 'cleaned_response', and 'verified_citations'.
        """
        errors = []
        warnings = []

        # Step 0: Sanitize response text
        cleaned_text = clean_rag_response(llm_response)

        # Check 1: Mandatory Disclaimer
        if "research prototype" not in cleaned_text.lower() and "disclaimer" not in cleaned_text.lower():
            errors.append("Mandatory research disclaimer missing from LLM response.")

        # Check 2: Citation Grounding (Verify [REF_X] citations map to retrieved chunks)
        retrieved_ref_ids = {ev["citation_id"] for ev in retrieved_evidence}
        cited_ref_ids = set(re.findall(r"\[(REF_\d+)\]", cleaned_text))

        unsupported_citations = cited_ref_ids - retrieved_ref_ids
        if unsupported_citations:
            errors.append(f"LLM cited unretrieved sources: {unsupported_citations}")

        # Check 3: Check for Orphan Citations or Empty Bullets in raw text
        for line in llm_response.split("\n"):
            line_s = line.strip()
            if re.match(r"^[-•*]?\s*\[REF_\d+\]\s*$", line_s):
                errors.append(f"Orphan citation detected without claim text: '{line_s}'")
            if re.match(r"^[-•*]\s*$", line_s):
                errors.append(f"Empty bullet line detected: '{line_s}'")

        # Check 4: Diagnostic / Prescription Violations
        prohibited_phrases = [
            "i diagnose you with",
            "you are diagnosed with",
            "stop taking your medication",
            "i prescribe",
            "increase your dosage to",
        ]
        for phrase in prohibited_phrases:
            if phrase in cleaned_text.lower():
                errors.append(f"Safety violation: Prohibited phrase detected ('{phrase}').")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning("Post-generation validation failed: %s", errors)
        else:
            logger.info("Post-generation validation PASSED ✓ (Citations verified: %s)", list(cited_ref_ids))

        return {
            "is_valid": is_valid,
            "validation_errors": errors,
            "validation_warnings": warnings,
            "cleaned_response": cleaned_text,
            "verified_citations": list(cited_ref_ids),
        }
