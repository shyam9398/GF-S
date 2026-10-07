from __future__ import annotations

import logging
import math
import re
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (math.sqrt(norm_a) * math.sqrt(norm_b))))


def _tokenize(text: str) -> list[str]:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return [w for w in cleaned.split() if len(w) >= 2]


def _bm25_similarity(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Lightweight, zero-memory BM25-style term-frequency scoring."""
    if not query_tokens or not doc_tokens:
        return 0.0
    doc_len = len(doc_tokens)
    tf_map: dict[str, int] = {}
    for token in doc_tokens:
        tf_map[token] = tf_map.get(token, 0) + 1

    k1 = 1.5
    b = 0.75
    avg_dl = 20.0
    score = 0.0
    query_set = set(query_tokens)

    for q in query_set:
        tf = tf_map.get(q, 0)
        if tf > 0:
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / avg_dl))
            score += numerator / denominator

    # Normalize to [0.0, 1.0]
    max_possible = len(query_set) * (k1 + 1.0)
    return round(min(1.0, score / max_possible), 4) if max_possible > 0 else 0.0


class BISSemanticService:
    """
    Lightweight, low-memory semantic matching service.
    Target memory: ~0 MB local neural weights (runs via Gemini API + BM25/lexical fallback).
    Replaces heavy local sentence-transformers models to strictly adhere to the 512MB RAM budget.
    """

    def __init__(self):
        self._gemini_client = None
        self._embedding_model = "models/gemini-embedding-001"
        self._embed_cache: dict[str, list[float]] = {}

    def _get_client(self):
        if self._gemini_client is None:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as exc:
                logger.warning(f"[SEMANTIC] Gemini client could not be initialized: {exc}")
                self._gemini_client = False
        return self._gemini_client if self._gemini_client is not False else None

    def _get_embedding(self, text: str) -> list[float] | None:
        trimmed = text[:1000].strip()
        if not trimmed:
            return None
        cache_key = trimmed.casefold()
        if cache_key in self._embed_cache:
            return self._embed_cache[cache_key]

        client = self._get_client()
        if client:
            try:
                resp = client.models.embed_content(
                    model=self._embedding_model,
                    contents=trimmed,
                )
                if resp and resp.embeddings and len(resp.embeddings) > 0:
                    vec = list(resp.embeddings[0].values)
                    if len(self._embed_cache) < 200:
                        self._embed_cache[cache_key] = vec
                    return vec
            except Exception as exc:
                logger.debug(f"[SEMANTIC] Embedding API call failed: {exc}")

        return None

    def compute_similarity(
        self,
        query_text: str,
        target_texts: list[str],
    ) -> list[float]:
        """
        Compute semantic similarity between query_text and target_texts.
        Returns a list of float scores between 0.0 and 1.0.
        Uses Gemini embeddings where available, falling back to BM25/lexical matching.
        Zero PyTorch or local transformer weights loaded into RAM.
        """
        if not query_text or not target_texts:
            return [0.0] * len(target_texts)

        # Attempt Gemini embedding cosine similarity
        query_vec = self._get_embedding(query_text)
        if query_vec:
            scores = []
            for target in target_texts:
                target_vec = self._get_embedding(target)
                if target_vec:
                    scores.append(round(_cosine_similarity(query_vec, target_vec), 4))
                else:
                    # Fallback for target
                    scores.append(self._fallback_score(query_text, target))
            return scores

        # Pure lightweight BM25 + Jaccard token fallback
        return [self._fallback_score(query_text, t) for t in target_texts]

    def _fallback_score(self, query: str, target: str) -> float:
        q_tokens = _tokenize(query)
        t_tokens = _tokenize(target)
        bm25 = _bm25_similarity(q_tokens, t_tokens)
        q_set = set(q_tokens)
        t_set = set(t_tokens)
        if not q_set or not t_set:
            return 0.0
        jaccard = len(q_set & t_set) / len(q_set | t_set)
        return round(0.7 * bm25 + 0.3 * jaccard, 4)
