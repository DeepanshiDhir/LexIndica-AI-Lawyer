import os
import hashlib
import numpy as np
from typing import List, Optional
from app.config.settings import settings


class LegalEmbedder:
    """Embedder supporting BAAI/bge-m3 via SentenceTransformers with fast offline fallback."""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE
        self._model = None
        self._dimension = 1024  # Standard BGE-M3 dimension

    def _load_model(self):
        if self._model is not None:
            return

        # Check if offline mode is explicitly requested or downloading HF models is disabled
        if not getattr(settings, "DOWNLOAD_HF_EMBEDDINGS", False) or os.environ.get("LEGAL_AI_OFFLINE", "0") == "1" or os.environ.get("HF_HUB_OFFLINE", "0") == "1":
            self._model = "FALLBACK"
            self._dimension = 1024
            return

        try:
            from sentence_transformers import SentenceTransformer
            # Try loading cached model first without network
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
                self._dimension = self._model.get_sentence_embedding_dimension()
                return
            except Exception:
                pass

            # Try loading online
            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._dimension = self._model.get_sentence_embedding_dimension()
        except Exception:
            # Fall back to offline deterministic semantic embedding
            self._model = "FALLBACK"
            self._dimension = 1024

    @property
    def dimension(self) -> int:
        if self._model is None:
            self._load_model()
        return self._dimension

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate normalized dense embeddings for a list of texts."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        self._load_model()
        if self._model != "FALLBACK":
            try:
                embeddings = self._model.encode(
                    texts,
                    batch_size=16,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                    convert_to_numpy=True
                )
                return embeddings.astype(np.float32)
            except Exception:
                pass

        return self._offline_embed_texts(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query text."""
        return self.embed_texts([query])[0]

    def _offline_embed_texts(self, texts: List[str]) -> np.ndarray:
        """Deterministic high-dimensional semantic hash embedding for offline/testing mode."""
        dim = self._dimension
        vectors = []
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            words = text.lower().replace("\n", " ").split()
            if not words:
                vectors.append(vec)
                continue

            for w in words:
                h1 = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % dim
                h2 = int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16) % dim
                sign1 = 1.0 if (h1 % 2 == 0) else -1.0
                sign2 = 1.0 if (h2 % 2 == 0) else -1.0
                vec[h1] += sign1
                vec[h2] += sign2

            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)

        return np.array(vectors, dtype=np.float32)
