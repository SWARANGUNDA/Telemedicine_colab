"""
ingestion.py — Section-Aware Document Parsing and Chunking Pipeline.

Parses raw guideline text files, extracts structured sections, enriches
each chunk with source manifest metadata, and prepares chunks for vector storage.
Strips raw metadata headers from chunk text so chunk text remains clean medical narrative.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from . import config
from .source_manifest import SourceManifestManager

logger = logging.getLogger("services.medical_rag.ingestion")


def clean_chunk_text(text: str) -> str:
    """Strip raw document header metadata lines from chunk text."""
    lines = []
    for line in text.split("\n"):
        line_s = line.strip()
        if not line_s:
            continue
        if any(line_s.startswith(prefix) for prefix in [
            "Organization:", "Publication Date:", "Document Version:", "Evidence Type:", "# "
        ]):
            continue
        lines.append(line_s)
    return " ".join(lines)


def parse_and_chunk_document(
    doc_path: Path,
    manifest_info: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Parse raw text document into section-aware chunks with metadata enrichment.

    Args:
        doc_path: Path to raw document file.
        manifest_info: Source manifest metadata for this document.

    Returns:
        List of chunk dictionaries with 'chunk_id', 'text', and 'metadata'.
    """
    if not doc_path.exists():
        logger.error("Document not found: %s", doc_path)
        return []

    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split document by markdown headings (e.g. ## Section X: Title)
    section_pattern = re.compile(r"^(##\s+.*?)$", re.MULTILINE)
    parts = section_pattern.split(content)

    chunks = []
    current_section = "General Overview"
    chunk_counter = 0

    for part in parts:
        part_str = part.strip()
        if not part_str:
            continue

        if part_str.startswith("## "):
            current_section = part_str.lstrip("#").strip()
        else:
            # Paragraph chunking inside section
            paragraphs = [p.strip() for p in part_str.split("\n\n") if len(p.strip()) > 30]
            for para in paragraphs:
                cleaned_para = clean_chunk_text(para)
                if not cleaned_para or len(cleaned_para) < 20:
                    continue

                chunk_counter += 1
                chunk_id = f"{manifest_info['doc_id']}_c{chunk_counter:03d}"

                chunk_metadata = {
                    "doc_id": manifest_info["doc_id"],
                    "organization": manifest_info["organization"],
                    "document_title": manifest_info["document_title"],
                    "publication_date": manifest_info["publication_date"],
                    "version": manifest_info["version"],
                    "current_status": manifest_info["current_status"],
                    "evidence_type": manifest_info["evidence_type"],
                    "disease_domains": manifest_info["disease_domains"],
                    "section_title": current_section,
                    "chunk_id": chunk_id,
                }

                chunks.append({
                    "chunk_id": chunk_id,
                    "text": cleaned_para,
                    "metadata": chunk_metadata,
                })

    logger.info("Parsed %s: Generated %d section-aware chunks", doc_path.name, len(chunks))
    return chunks


def process_all_documents() -> List[Dict[str, Any]]:
    """Process all documents in manifest and return combined chunks."""
    manifest_mgr = SourceManifestManager()
    all_chunks = []

    for src in manifest_mgr.list_sources():
        doc_filename = src.get("filename")
        if not doc_filename:
            continue
        doc_path = config.RAW_DOCS_DIR / doc_filename
        chunks = parse_and_chunk_document(doc_path, src)
        all_chunks.extend(chunks)

    logger.info("Total ingested chunks across knowledge base: %d", len(all_chunks))
    return all_chunks
