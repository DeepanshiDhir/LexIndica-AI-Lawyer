from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel

from app.chunking.schema import ChildChunk, ParentSection
from app.retrieval.vector_store import FAISSVectorStore
from app.retrieval.bm25_store import BM25LegalStore
from app.retrieval.parent_store import ParentSectionStore
from app.embeddings.embedder import LegalEmbedder
from app.reranking.reranker import CrossEncoderReranker
from app.config.settings import settings


class RetrievedEvidence(BaseModel):
    chunk: ChildChunk
    parent_section: Optional[ParentSection] = None
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    rrf_score: float
    rerank_score: Optional[float] = None
    combined_score: float
    citation_id: str
    act_name: str
    section_number: Optional[str] = None
    title: str
    is_authoritative: bool = True


class HybridLegalRetriever:
    def __init__(
        self,
        vector_store: FAISSVectorStore,
        bm25_store: BM25LegalStore,
        parent_store: ParentSectionStore,
        embedder: LegalEmbedder,
        reranker: Optional[CrossEncoderReranker] = None,
        rrf_k: int = 60
    ):
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.parent_store = parent_store
        self.embedder = embedder
        self.reranker = reranker or CrossEncoderReranker()
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        state: Optional[str] = None,
        document_type: Optional[str] = None,
        top_k: int = 5,
        dense_k: int = 15,
        sparse_k: int = 15,
    ) -> List[RetrievedEvidence]:
        filters: Dict[str, Any] = {}
        if jurisdiction and jurisdiction.lower() not in ["all", "any", "india"]:
            filters["jurisdiction"] = jurisdiction
        if state and state.lower() not in ["all", "any", "none"]:
            filters["state"] = state
        if document_type:
            filters["document_type"] = document_type

        # 1. Dense retrieval
        query_vec = self.embedder.embed_query(query)
        dense_results = self.vector_store.search(query_vec, top_k=dense_k, filters=filters)

        # 2. Sparse retrieval
        sparse_results = self.bm25_store.search(query, top_k=sparse_k, filters=filters)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}
        chunk_map: Dict[str, ChildChunk] = {}

        for rank, (chunk, score) in enumerate(dense_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            dense_ranks[cid] = rank + 1
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        for rank, (chunk, score) in enumerate(sparse_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            sparse_ranks[cid] = rank + 1
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        if not rrf_scores:
            return []

        # Sort by RRF score
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        fusion_candidates = [(chunk_map[cid], rrf_scores[cid]) for cid in sorted_cids]

        # 4. Cross-encoder Reranking
        # Take top candidates for reranking
        candidate_pool = fusion_candidates[: max(top_k * 2, 10)]
        reranked = self.reranker.rerank(query, candidate_pool, top_k=top_k)

        # 5. Enrich with Parent Sections
        evidence_list: List[RetrievedEvidence] = []
        for chunk, score in reranked:
            parent = self.parent_store.get(chunk.parent_section_id)
            cid = chunk.chunk_id
            
            # Format clean citation id: e.g. "MTA-2021-Sec-10" or "DRCA-1958-Sec-14"
            clean_sec = (chunk.section_number or "General").replace(" ", "-")
            short_act = "".join([w[0] for w in chunk.act_name.split() if w[0].isupper()]) or "LAW"
            citation_id = f"{short_act}-{clean_sec}"

            evidence = RetrievedEvidence(
                chunk=chunk,
                parent_section=parent,
                dense_rank=dense_ranks.get(cid),
                sparse_rank=sparse_ranks.get(cid),
                rrf_score=rrf_scores.get(cid, 0.0),
                rerank_score=score,
                combined_score=score if score is not None else rrf_scores.get(cid, 0.0),
                citation_id=citation_id,
                act_name=chunk.act_name,
                section_number=chunk.section_number,
                title=parent.title if parent else chunk.metadata.document_title,
                is_authoritative=chunk.metadata.is_verified,
            )
            evidence_list.append(evidence)

        return evidence_list
