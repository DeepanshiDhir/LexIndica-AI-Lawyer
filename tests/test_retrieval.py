import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["LEGAL_AI_OFFLINE"] = "1"

from pathlib import Path
from app.config.settings import settings
from app.retrieval.vector_store import FAISSVectorStore
from app.retrieval.bm25_store import BM25LegalStore
from app.retrieval.parent_store import ParentSectionStore
from app.embeddings.embedder import LegalEmbedder
from app.retrieval.hybrid_retriever import HybridLegalRetriever


def test_hybrid_retrieval():
    idx_dir = settings.INDEX_DIR
    assert (idx_dir / "faiss.index").exists(), "FAISS index must exist"
    assert (idx_dir / "bm25.pkl").exists(), "BM25 index must exist"
    assert (idx_dir / "parent_sections.json").exists(), "Parent store must exist"

    vs = FAISSVectorStore.load(idx_dir)
    bm = BM25LegalStore.load(idx_dir)
    ps = ParentSectionStore.load(idx_dir)
    embedder = LegalEmbedder()

    retriever = HybridLegalRetriever(vs, bm, ps, embedder)

    # Test query
    results = retriever.retrieve("Security deposit refund within one month on vacating", top_k=3)
    assert len(results) > 0

    top_result = results[0]
    assert top_result.parent_section is not None
    assert top_result.citation_id is not None
    assert top_result.act_name is not None
    assert top_result.combined_score > 0

    # Ensure parent section contains full text
    assert len(top_result.parent_section.full_text) > len(top_result.chunk.text) or (
        top_result.parent_section.section_id == top_result.chunk.parent_section_id
    )


def test_metadata_filtering():
    idx_dir = settings.INDEX_DIR
    vs = FAISSVectorStore.load(idx_dir)
    bm = BM25LegalStore.load(idx_dir)
    ps = ParentSectionStore.load(idx_dir)
    embedder = LegalEmbedder()
    retriever = HybridLegalRetriever(vs, bm, ps, embedder)

    # Retrieve only Delhi jurisdiction
    delhi_results = retriever.retrieve("Revision of rent and eviction", jurisdiction="Delhi", top_k=3)
    assert len(delhi_results) > 0
    for r in delhi_results:
        assert r.chunk.metadata.jurisdiction.lower() in ["central", "delhi"]
