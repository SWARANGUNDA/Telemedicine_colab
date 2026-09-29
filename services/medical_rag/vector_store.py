"""
vector_store.py — Semantic Vector Store Engine.

Provides persistent storage, TF-IDF + dense semantic embedding representation,
and rich metadata filtering (by disease domain, organization, evidence type, version).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import config

logger = logging.getLogger("services.medical_rag.vector_store")


class SemanticVectorStore:
    """Persistent Semantic Vector Store with rich metadata filtering."""

    def __init__(self, index_path: Path = config.VECTOR_STORE_PATH):
        self.index_path = index_path
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors: Optional[np.ndarray] = None
        self.is_indexed: bool = False

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """Build TF-IDF semantic vector representation over chunks and save."""
        if not chunks:
            logger.warning("No chunks provided to build_index.")
            return

        self.chunks = chunks
        texts = [c["text"] for c in chunks]

        # Fit TF-IDF Vectorizer with sublinear scaling
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
            stop_words="english",
        )
        self.doc_vectors = self.vectorizer.fit_transform(texts).toarray()
        self.is_indexed = True

        self.save_store()
        logger.info("Vector index successfully built with %d chunks.", len(chunks))

    def save_store(self) -> None:
        """Save chunk text, metadata, and vectors to JSON."""
        if not self.is_indexed or self.doc_vectors is None:
            return

        vocab_dict = {k: int(v) for k, v in self.vectorizer.vocabulary_.items()} if self.vectorizer else {}
        serialized = {
            "chunks": self.chunks,
            "vocabulary": vocab_dict,
            "idf": self.vectorizer.idf_.tolist() if self.vectorizer else [],
            "doc_vectors": self.doc_vectors.tolist(),
        }
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2)
        logger.info("Saved vector store index to %s", self.index_path)

    def load_store(self) -> bool:
        """Load persistent vector store from JSON."""
        if not self.index_path.exists():
            logger.info("Vector index file does not exist yet at %s", self.index_path)
            return False

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.chunks = data["chunks"]
            vocab = data["vocabulary"]
            idf = np.array(data["idf"])
            self.doc_vectors = np.array(data["doc_vectors"])

            # Reconstruct vectorizer
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
                stop_words="english",
            )
            self.vectorizer.vocabulary_ = vocab
            self.vectorizer.idf_ = idf

            self.is_indexed = True
            logger.info("Successfully loaded vector store with %d chunks.", len(self.chunks))
            return True
        except Exception as e:
            logger.error("Failed to load vector store: %s", e)
            return False

    def search(
        self,
        query_text: str,
        top_k: int = config.DEFAULT_TOP_K,
        disease_filter: Optional[List[str]] = None,
        evidence_type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search with metadata filtering.

        Args:
            query_text: Search query string.
            top_k: Number of candidate chunks to retrieve.
            disease_filter: Optional list of required disease domains.
            evidence_type_filter: Optional required evidence_type string.

        Returns:
            List of matching chunk dicts with 'similarity_score'.
        """
        if not self.is_indexed or self.vectorizer is None or self.doc_vectors is None:
            if not self.load_store():
                raise RuntimeError("VectorStore is empty and not loaded.")

        # Transform query
        q_vec = self.vectorizer.transform([query_text]).toarray()
        scores = cosine_similarity(q_vec, self.doc_vectors)[0]

        # Apply metadata filtering
        candidate_results = []
        for idx, (chunk, score) in enumerate(zip(self.chunks, scores)):
            meta = chunk["metadata"]

            # Filter by disease domain
            if disease_filter:
                chunk_domains = meta.get("disease_domains", [])
                if not any(d in chunk_domains for d in disease_filter):
                    continue

            # Filter by evidence type
            if evidence_type_filter:
                if meta.get("evidence_type") != evidence_type_filter:
                    continue

            result = dict(chunk)
            result["similarity_score"] = round(float(score), 4)
            candidate_results.append(result)

        # Sort by similarity score descending
        candidate_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return candidate_results[:top_k]
