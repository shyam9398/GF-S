from __future__ import annotations

import logging
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_INSTANCE = None


def get_embedding_model():
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("[SEMANTIC] Loading all-MiniLM-L6-v2 sentence transformer model...")
            _MODEL_INSTANCE = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("[SEMANTIC] Sentence transformer model loaded successfully.")
        except Exception as exc:
            logger.warning(f"[SEMANTIC] Could not load sentence-transformers model: {exc}")
            _MODEL_INSTANCE = False
    return _MODEL_INSTANCE if _MODEL_INSTANCE is not False else None


class BISSemanticService:
    """
    Semantic similarity computation between procurement specifications
    and candidate BIS standards using local embeddings.
    """

    def __init__(self):
        self.model = get_embedding_model()

    def compute_similarity(
        self,
        query_text: str,
        target_texts: list[str],
    ) -> list[float]:
        """
        Compute cosine similarities between query_text and target_texts.
        Returns a list of float scores between 0.0 and 1.0.
        """
        if not query_text or not target_texts:
            return [0.0] * len(target_texts)

        if self.model is not None:
            try:
                from sklearn.metrics.pairwise import cosine_similarity

                query_emb = self.model.encode([query_text], show_progress_bar=False)
                target_embs = self.model.encode(target_texts, show_progress_bar=False)

                sims = cosine_similarity(query_emb, target_embs)[0]
                return [round(float(max(0.0, min(1.0, s))), 4) for s in sims]
            except Exception as exc:
                logger.warning(f"[SEMANTIC] Error during embedding computation: {exc}")

        # Fallback: token overlap Jaccard/Dice if model is unavailable
        q_tokens = set(query_text.lower().split())
        results = []
        for t in target_texts:
            t_tokens = set(t.lower().split())
            if not q_tokens or not t_tokens:
                results.append(0.0)
            else:
                inter = len(q_tokens.intersection(t_tokens))
                dice = (2.0 * inter) / (len(q_tokens) + len(t_tokens))
                results.append(round(dice, 4))
        return results
