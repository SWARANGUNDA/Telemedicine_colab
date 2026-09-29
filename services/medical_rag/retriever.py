"""
retriever.py — Multi-Stage Medical Evidence Retriever.

Performs candidate search, optional reranking, and final evidence selection
while preserving exact source citations and version metadata.
"""

import logging
from typing import Any, Dict, List, Optional

from . import config
from .vector_store import SemanticVectorStore

logger = logging.getLogger("services.medical_rag.retriever")


class EvidenceRetriever:
    """Configurable Multi-Stage Evidence Retriever with metadata filtering."""

    def __init__(self, vector_store: Optional[SemanticVectorStore] = None):
        if vector_store is not None:
            self.vector_store = vector_store
        else:
            self.vector_store = SemanticVectorStore()
            if not self.vector_store.load_store():
                logger.info("Initializing vector store from raw documents...")
                from .ingestion import process_all_documents
                chunks = process_all_documents()
                self.vector_store.build_index(chunks)

    def retrieve_evidence(
        self,
        query: str,
        top_k: int = config.DEFAULT_TOP_K,
        disease_filter: Optional[List[str]] = None,
        evidence_type_filter: Optional[str] = None,
        candidate_k: int = config.RERANK_CANDIDATE_K,
    ) -> List[Dict[str, Any]]:
        """Multi-stage retrieval pipeline:
        Stage 1: Candidate Search (candidate_k)
        Stage 2: Reranking & Diversity Selection
        Stage 3: Citation Metadata Formatting

        Args:
            query: Search query string.
            top_k: Final number of evidence chunks to select.
            disease_filter: Optional list of target disease domains.
            evidence_type_filter: Optional evidence level filter.
            candidate_k: Number of candidates for initial retrieval.

        Returns:
            List of selected evidence chunk dicts with formatted citations.
        """
        search_query = query
        q_lower = query.lower()
        is_blood_test_query = any(term in q_lower for term in ["blood test", "blood tests", "lab test", "lab tests", "lab evaluation", "lab panel", "blood work", "diagnostic test", "marker", "panel"])

        if is_blood_test_query:
            search_query = f"{query} laboratory blood tests diagnostic confirmation HbA1c Fasting Blood Glucose Lipid Panel Triglycerides ALT AST liver function cholesterol"
        elif any(term in q_lower for term in ["liver", "nafld", "fatty liver", "alt", "ast"]):
            search_query = f"{query} liver fat NAFLD ALT AST hepatic enzymes diagnostic evaluation"
        elif any(term in q_lower for term in ["blood pressure", "hypertension", "bp", "dash", "sodium"]):
            search_query = f"{query} blood pressure hypertension DASH sodium restriction ACC AHA guidelines"

        # Stage 1: Candidate Retrieval
        candidates = self.vector_store.search(
            query_text=search_query,
            top_k=max(candidate_k, top_k),
            disease_filter=disease_filter,
            evidence_type_filter=evidence_type_filter,
        )

        if not candidates:
            logger.warning("No candidate evidence chunks retrieved for query: '%s'", query)
            return []

        # Stage 2: Reranking & Intent Relevance Scoring
        if is_blood_test_query:
            lab_keywords = {"blood", "hba1c", "glucose", "lipid", "alt", "ast", "cholesterol", "triglycerides", "panel", "laboratory", "diagnostic", "marker", "screening", "vitals"}
            for cand in candidates:
                txt_lower = cand["text"].lower()
                matches = sum(1 for kw in lab_keywords if kw in txt_lower)
                # Boost similarity score if matching target lab keywords
                cand["similarity_score"] += matches * 0.05

            candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

        selected = []
        seen_sections = set()

        for cand in candidates:
            sec_key = (cand["metadata"]["doc_id"], cand["metadata"]["section_title"])
            if sec_key not in seen_sections or len(selected) < top_k:
                seen_sections.add(sec_key)
                selected.append(cand)

            if len(selected) >= top_k:
                break

        # Stage 3: Citation Metadata Formatting
        formatted_evidence = []
        for idx, chunk in enumerate(selected, 1):
            meta = chunk["metadata"]
            citation_str = (
                f"[{meta['organization']}, {meta['document_title']} (v{meta['version']}, {meta['publication_date']}), "
                f"{meta['section_title']}]"
            )

            formatted_evidence.append({
                "citation_id": f"REF_{idx}",
                "citation_string": citation_str,
                "text": chunk["text"],
                "similarity_score": chunk["similarity_score"],
                "metadata": meta,
            })

        logger.info(
            "Retrieved %d evidence chunks for query: '%s' (top score: %.4f)",
            len(formatted_evidence), query, formatted_evidence[0]["similarity_score"] if formatted_evidence else 0.0,
        )
        return formatted_evidence
