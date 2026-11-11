import re
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from rank_bm25 import BM25Okapi

from app.chunking.schema import ChildChunk


def legal_tokenize(text: str) -> List[str]:
    """
    Tokenizes text for legal keyword matching:
    - Preserves section citations like 'section 10', 'sec 108', 's. 21'
    - Normalizes case while preserving specific statutory tokens
    - Captures acronyms like MTA, TPA, DRCA, MRCA, CPA
    """
    cleaned = text.lower()
    # Extract specific section patterns: 'section 10', 'section 108(f)'
    special_tokens = re.findall(r'(?:section|sec|s\.)\s*[0-9]+[a-z\(\)]*', cleaned)
    # Extract words
    words = re.findall(r'[a-z0-9_]+', cleaned)
    # Combine special tokens with regular words
    all_tokens = words + [t.replace(" ", "") for t in special_tokens]
    return all_tokens


class BM25LegalStore:
    def __init__(self):
        self.chunks: List[ChildChunk] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def add_chunks(self, chunks: List[ChildChunk]):
        if not chunks:
            return
        
        for ch in chunks:
            self.chunks.append(ch)
            tokens = legal_tokenize(ch.text)
            self.tokenized_corpus.append(tokens)

        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ChildChunk, float]]:
        if not self.bm25 or len(self.chunks) == 0:
            return []

        query_tokens = legal_tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        
        # Sort indices by descending score
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results: List[Tuple[ChildChunk, float]] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue

            chunk = self.chunks[idx]
            if filters and not self._matches_filter(chunk, filters):
                continue

            results.append((chunk, score))
            if len(results) >= top_k:
                break

        return results

    def _matches_filter(self, chunk: ChildChunk, filters: Dict[str, Any]) -> bool:
        meta = chunk.metadata
        for key, val in filters.items():
            if not val:
                continue
            if key == "jurisdiction":
                if meta.jurisdiction.lower() == "central" or "all" in (meta.state or "").lower():
                    continue
                if meta.jurisdiction.lower() != str(val).lower():
                    return False
            elif key == "state":
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
        with open(index_dir / "bm25.pkl", "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "tokenized_corpus": self.tokenized_corpus
            }, f)

    @classmethod
    def load(cls, index_dir: Path) -> "BM25LegalStore":
        index_dir = Path(index_dir)
        bm25_file = index_dir / "bm25.pkl"
        if not bm25_file.exists():
            raise FileNotFoundError(f"BM25 store file missing in {index_dir}")

        with open(bm25_file, "rb") as f:
            data = pickle.load(f)

        store = cls()
        store.chunks = data["chunks"]
        store.tokenized_corpus = data["tokenized_corpus"]
        if store.tokenized_corpus:
            store.bm25 = BM25Okapi(store.tokenized_corpus)
        return store
