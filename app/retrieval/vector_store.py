import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import faiss

from app.chunking.schema import ChildChunk


class FAISSVectorStore:
    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks: List[ChildChunk] = []
        self.chunk_id_map: Dict[str, int] = {}

    def add_chunks(self, chunks: List[ChildChunk], embeddings: np.ndarray):
        if len(chunks) == 0:
            return
        
        # Ensure float32 and normalized
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        
        faiss.normalize_L2(embeddings)

        start_idx = len(self.chunks)
        self.index.add(embeddings)
        
        for i, chunk in enumerate(chunks):
            self.chunks.append(chunk)
            self.chunk_id_map[chunk.chunk_id] = start_idx + i

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ChildChunk, float]]:
        if self.index.ntotal == 0:
            return []

        q_vec = query_vector.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(q_vec)

        # Retrieve a broader pool if filtering is applied
        fetch_k = min(self.index.ntotal, top_k * 4 if filters else top_k)
        scores, indices = self.index.search(q_vec, fetch_k)

        results: List[Tuple[ChildChunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            
            # Apply metadata filter
            if filters and not self._matches_filter(chunk, filters):
                continue

            results.append((chunk, float(score)))
            if len(results) >= top_k:
                break

        return results

    def _matches_filter(self, chunk: ChildChunk, filters: Dict[str, Any]) -> bool:
        meta = chunk.metadata
        for key, val in filters.items():
            if not val:
                continue
            if key == "jurisdiction":
                # Central laws and nationwide precedents apply across India
                if meta.jurisdiction.lower() == "central" or "all" in (meta.state or "").lower():
                    continue
                if meta.jurisdiction.lower() != str(val).lower():
                    return False
            elif key == "state":
                # Central laws or 'all states' apply to any state query
                if meta.jurisdiction.lower() == "central" or "all" in (meta.state or "").lower():
                    continue
                val_str = str(val).lower()
                state_str = (meta.state or "").lower()
                if val_str not in state_str and state_str not in val_str:
                    return False
            elif key == "document_type":
                if meta.document_type.lower() != str(val).lower():
                    return False
            elif hasattr(meta, key):
                if str(getattr(meta, key)).lower() != str(val).lower():
                    return False
        return True

    def save(self, index_dir: Path):
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_dir / "faiss.index"))
        with open(index_dir / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)

    @classmethod
    def load(cls, index_dir: Path) -> "FAISSVectorStore":
        index_dir = Path(index_dir)
        index_path = index_dir / "faiss.index"
        chunks_path = index_dir / "chunks.pkl"

        if not index_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(f"FAISS index files missing in {index_dir}")

        index = faiss.read_index(str(index_path))
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)

        store = cls(dimension=index.d)
        store.index = index
        store.chunks = chunks
        store.chunk_id_map = {c.chunk_id: i for i, c in enumerate(chunks)}
        return store
