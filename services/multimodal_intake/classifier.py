"""
classifier.py — Document Classification Module (Module 1).

Automatically identifies document type:
- Clinical Report
- Wearable Report
- Gut Microbiome Report

Supports text, dictionary content, file content inspection, and batch files.
"""

from enum import Enum
from typing import Dict, List, Union
from . import config


class DocumentType(str, Enum):
    CLINICAL = "Clinical Report"
    WEARABLE = "Wearable Report"
    GUT_MICROBIOME = "Gut Microbiome Report"
    MULTIMODAL = "Multimodal Report"
    UNKNOWN = "Unknown Document Type"


def classify_text_or_dict(content: Union[str, Dict, List]) -> DocumentType:
    """Classify input text, dictionary keys, or list content into DocumentType.

    Modality is determined strictly from canonical primary features, completely ignoring
    generic patient demographics (Age, Gender, Patient_ID, Height, Weight).
    """
    if isinstance(content, dict):
        # Extract features dictionary if available
        clin_feats = content.get("clinical_features", content.get("CLINICAL", {}))
        wear_feats = content.get("wearable_features", content.get("WEARABLE", {}))
        gut_feats = content.get("gut_features", content.get("GUT_MICROBIOME", {}))

        # Check primary non-demographic biomarkers / telemetry / taxa
        has_primary_clin = any(k not in ("Patient_ID", "Age", "Gender", "Height", "Weight", "BMI") for k in clin_feats.keys())
        has_primary_wear = len(wear_feats) > 0
        has_primary_gut = len(gut_feats) > 0

        active_count = sum([has_primary_clin, has_primary_wear, has_primary_gut])
        if active_count > 1:
            return DocumentType.MULTIMODAL
        elif has_primary_gut:
            return DocumentType.GUT_MICROBIOME
        elif has_primary_wear:
            return DocumentType.WEARABLE
        elif has_primary_clin:
            return DocumentType.CLINICAL

        text_corpus = " ".join(f"{k} {v}" for k, v in content.items()).lower()
    elif isinstance(content, list):
        text_corpus = " ".join(str(item) for item in content).lower()
    else:
        text_corpus = str(content).lower()

    # Count keyword occurrences for each modality excluding generic demographics
    clinical_score = sum(1 for kw in config.CLINICAL_KEYWORDS if kw in text_corpus)
    wearable_score = sum(1 for kw in config.WEARABLE_KEYWORDS if kw in text_corpus)
    gut_score = sum(1 for kw in config.GUT_KEYWORDS if kw in text_corpus)

    active_modalities = []
    if clinical_score >= 1:
        active_modalities.append(DocumentType.CLINICAL)
    if wearable_score >= 1:
        active_modalities.append(DocumentType.WEARABLE)
    if gut_score >= 1:
        active_modalities.append(DocumentType.GUT_MICROBIOME)

    if len(active_modalities) > 1:
        return DocumentType.MULTIMODAL
    elif len(active_modalities) == 1:
        return active_modalities[0]

    return DocumentType.UNKNOWN


def classify_multiple_documents(docs: List[Union[str, Dict]]) -> List[Dict[str, Union[int, DocumentType]]]:
    """Classify multiple uploaded documents simultaneously.

    Args:
        docs: List of document strings or dictionaries.

    Returns:
        List of dicts with document index, classification result, and confidence.
    """
    results = []
    for idx, doc in enumerate(docs):
        doc_type = classify_text_or_dict(doc)
        results.append({
            "doc_index": idx,
            "document_type": doc_type.value,
            "enum": doc_type
        })
    return results
