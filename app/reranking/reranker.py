import os
from typing import List, Tuple, Optional
from app.config.settings import settings
from app.chunking.schema import ChildChunk


class CrossEncoderReranker:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.RERANKER_MODEL
        self._model = None
        self._initialized = False

    def _init_model(self):
        if self._initialized:
            return

        if not getattr(settings, "USE_CROSS_ENCODER", False) or not getattr(settings, "DOWNLOAD_HF_EMBEDDINGS", False) or os.environ.get("LEGAL_AI_OFFLINE", "0") == "1" or os.environ.get("HF_HUB_OFFLINE", "0") == "1":
            self._model = None
            self._initialized = True
            return

        try:
            from sentence_transformers import CrossEncoder
            try:
                self._model = CrossEncoder(self.model_name, max_length=512, local_files_only=True)
            except Exception:
                self._model = CrossEncoder(self.model_name, max_length=512)
        except Exception:
            self._model = None
            
        self._initialized = True

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[ChildChunk, float]],
        top_k: int = 5
    ) -> List[Tuple[ChildChunk, float]]:
        if not candidates:
            return []

        self._init_model()
        if self._model is None:
            # Sort by existing fusion score
            candidates_sorted = sorted(candidates, key=lambda x: x[1], reverse=True)
            return candidates_sorted[:top_k]

        try:
            pairs = [[query, chunk.text] for chunk, _ in candidates]
            scores = self._model.predict(pairs)
            
            rescored = []
            for (chunk, _), score in zip(candidates, scores):
                rescored.append((chunk, float(score)))

            rescored.sort(key=lambda x: x[1], reverse=True)
            return rescored[:top_k]
        except Exception:
            return candidates[:top_k]
