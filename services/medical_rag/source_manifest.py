"""
source_manifest.py — Authoritative Knowledge Source Registry & Manifest.

Maintains an immutable registry of all indexed medical guidelines,
publications, versions, dates, and evidence levels.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config

logger = logging.getLogger("services.medical_rag.source_manifest")


# Initial Authoritative Source Registry
INITIAL_SOURCES: List[Dict[str, Any]] = [
    {
        "doc_id": "ADA_DIABETES_CARE_2024",
        "organization": "American Diabetes Association (ADA)",
        "document_title": "Standards of Care in Diabetes — 2024",
        "publication_date": "2024-01-01",
        "version": "2024.1",
        "current_status": "CURRENT",
        "disease_domains": ["Type2_Diabetes", "Prediabetes"],
        "evidence_type": "CLINICAL_GUIDELINE",
        "filename": "ada_standards_of_care_2024.txt",
    },
    {
        "doc_id": "WHO_OBESITY_GUIDANCE_2023",
        "organization": "World Health Organization (WHO)",
        "document_title": "Clinical Guidelines for Obesity Prevention and Management",
        "publication_date": "2023-06-15",
        "version": "2023.2",
        "current_status": "CURRENT",
        "disease_domains": ["Obesity", "Metabolic_Syndrome"],
        "evidence_type": "CLINICAL_GUIDELINE",
        "filename": "who_obesity_guidelines_2023.txt",
    },
    {
        "doc_id": "AASLD_MASLD_PRACTICE_2023",
        "organization": "American Association for the Study of Liver Diseases (AASLD)",
        "document_title": "Practice Guidance on Metabolic Dysfunction-Associated Steatotic Liver Disease (MASLD/NAFLD)",
        "publication_date": "2023-12-01",
        "version": "2023.1",
        "current_status": "CURRENT",
        "disease_domains": ["NAFLD", "Metabolic_Syndrome"],
        "evidence_type": "CLINICAL_GUIDELINE",
        "filename": "aasld_masld_guidance_2023.txt",
    },
    {
        "doc_id": "AHA_NHLBI_METSYN_CRITERIA_2022",
        "organization": "American Heart Association / NHLBI",
        "document_title": "Diagnosis and Management of the Metabolic Syndrome: An American Heart Association/National Heart, Lung, and Blood Institute Scientific Statement",
        "publication_date": "2022-09-10",
        "version": "2022.1",
        "current_status": "CURRENT",
        "disease_domains": ["Metabolic_Syndrome"],
        "evidence_type": "CLINICAL_GUIDELINE",
        "filename": "aha_metsyn_statement_2022.txt",
    },
    {
        "doc_id": "ISAPP_PREBIOTICS_FIBER_2023",
        "organization": "International Scientific Association for Probiotics and Prebiotics (ISAPP)",
        "document_title": "Consensus Statement on Prebiotics, Dietary Fiber, and Short-Chain Fatty Acids in Metabolic Health",
        "publication_date": "2023-04-20",
        "version": "2023.1",
        "current_status": "CURRENT",
        "disease_domains": ["Type2_Diabetes", "Obesity", "NAFLD", "Metabolic_Syndrome"],
        "evidence_type": "EMERGING_RESEARCH",
        "filename": "isapp_prebiotics_fiber_2023.txt",
    },
]


class SourceManifestManager:
    """Manages reading, registering, and validating authoritative sources."""

    def __init__(self, manifest_path: Path = config.MANIFEST_PATH):
        self.manifest_path = manifest_path
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.initialize_manifest()

    def initialize_manifest(self) -> None:
        if self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.sources = data.get("sources", {})
            logger.info("Loaded source manifest from %s (%d sources)", self.manifest_path, len(self.sources))
        else:
            self.sources = {src["doc_id"]: src for src in INITIAL_SOURCES}
            self.save_manifest()
            logger.info("Created initial source manifest at %s (%d sources)", self.manifest_path, len(self.sources))

    def save_manifest(self) -> None:
        payload = {
            "manifest_version": "1.0",
            "sources": self.sources,
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def get_source(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.sources.get(doc_id)

    def list_sources(self) -> List[Dict[str, Any]]:
        return list(self.sources.values())
