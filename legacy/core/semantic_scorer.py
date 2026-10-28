"""
Semantic scorer — computes cosine similarity between skill sets / text
using sentence-transformers (local, no API key needed).

Loaded lazily on first use to avoid slowing down app startup.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import numpy as np
from loguru import logger

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    logger.info("Loading embedding model: {}", EMBEDDING_MODEL)
    return SentenceTransformer(EMBEDDING_MODEL)


def embed(texts: Sequence[str]) -> np.ndarray:
    """Return (N, D) embedding matrix for a list of strings."""
    model = _get_model()
    return model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)


def cosine_similarity_score(text_a: str, text_b: str) -> float:
    """Cosine similarity ∈ [0, 1] between two text strings."""
    if not text_a or not text_b:
        return 0.0
    vecs = embed([text_a, text_b])
    score = float(np.dot(vecs[0], vecs[1]))
    return max(0.0, min(1.0, score))


def skill_match_score(
    candidate_skills: list[str],
    required_skills: list[str],
) -> float:
    """
    Compute semantic skill overlap.

    Strategy:
      For each required skill, find max cosine similarity to any candidate skill.
      Final score = mean of per-required-skill max similarities.

    Returns float ∈ [0, 1].
    """
    if not required_skills:
        return 1.0     # no requirements → perfect match
    if not candidate_skills:
        return 0.0

    req_emb  = embed(required_skills)   # (R, D)
    cand_emb = embed(candidate_skills)  # (C, D)

    # Similarity matrix (R, C)
    sim_matrix = req_emb @ cand_emb.T
    best_per_req = sim_matrix.max(axis=1)   # (R,)

    return float(best_per_req.mean())


def text_relevance_score(candidate_text: str, job_text: str) -> float:
    """Generic text-to-text semantic relevance [0, 1]."""
    return cosine_similarity_score(candidate_text, job_text)
