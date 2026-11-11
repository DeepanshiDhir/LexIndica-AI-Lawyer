import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config.settings import settings
from app.retrieval.vector_store import FAISSVectorStore
from app.retrieval.bm25_store import BM25LegalStore
from app.retrieval.parent_store import ParentSectionStore
from app.embeddings.embedder import LegalEmbedder
from app.reranking.reranker import CrossEncoderReranker
from app.retrieval.hybrid_retriever import HybridLegalRetriever
from app.agents.llm_client import GeminiClient
from app.graph.workflow import LegalAssistantGraph
from app.memory.conversation_store import conversation_memory
from app.generation.document_generator import LegalDocumentGenerator

app = FastAPI(
    title="Indian Legal AI Assistant API",
    description="Conversational legal assistant grounded in Indian tenancy law and statutory provisions.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global graph singleton
graph_instance: Optional[LegalAssistantGraph] = None


def get_graph() -> LegalAssistantGraph:
    global graph_instance
    if graph_instance is None:
        idx_dir = settings.INDEX_DIR
        if not (idx_dir / "faiss.index").exists():
            from app.ingestion.indexer import build_all_indexes
            build_all_indexes()

        vs = FAISSVectorStore.load(idx_dir)
        bm = BM25LegalStore.load(idx_dir)
        ps = ParentSectionStore.load(idx_dir)
        embedder = LegalEmbedder()
        reranker = CrossEncoderReranker()
        retriever = HybridLegalRetriever(vs, bm, ps, embedder, reranker)
        llm = GeminiClient()
        graph_instance = LegalAssistantGraph(retriever, llm)
    return graph_instance


# Pydantic Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_user"
    preferred_language: Optional[str] = "English"
    state_override: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    legal_domain: str
    jurisdiction: str
    applicable_provisions: List[str]
    citations: List[Dict[str, str]]
    suggested_followups: List[str]
    retrieved_sources_count: int
    generated_document: Optional[str] = None
    safety_passed: bool


class DocumentRequest(BaseModel):
    doc_type: str  # notice, complaint, maintenance, summary
    facts: Dict[str, Any]


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "Indian Legal AI Assistant",
        "environment": settings.APP_ENV,
        "indexes_present": (settings.INDEX_DIR / "faiss.index").exists(),
        "embedding_model": settings.EMBEDDING_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY"))
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        graph = get_graph()
        session = conversation_memory.get_or_create(req.session_id)
        
        # Run graph workflow
        result = graph.run(query=req.message, session_id=req.session_id)
        
        # Save to conversation memory
        conversation_memory.add_message(req.session_id, "user", req.message)
        conversation_memory.add_message(req.session_id, "assistant", result.final_response)
        if result.extracted_facts:
            conversation_memory.update_facts(req.session_id, result.extracted_facts)

        return ChatResponse(
            response=result.final_response,
            legal_domain=result.legal_domain,
            jurisdiction=result.jurisdiction,
            applicable_provisions=result.applicable_provisions,
            citations=result.citations,
            suggested_followups=result.suggested_followups,
            retrieved_sources_count=len(result.retrieved_evidence),
            generated_document=result.generated_document,
            safety_passed=result.safety_passed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-document")
def generate_document(req: DocumentRequest):
    dtype = req.doc_type.lower()
    if "notice" in dtype:
        doc = LegalDocumentGenerator.generate_security_deposit_notice(req.facts)
    elif "complaint" in dtype:
        doc = LegalDocumentGenerator.generate_rent_authority_complaint(req.facts)
    elif "maintenance" in dtype:
        doc = LegalDocumentGenerator.generate_maintenance_notice(req.facts)
    elif "summary" in dtype:
        doc = LegalDocumentGenerator.generate_lawyer_fact_summary(req.facts)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported document type: {req.doc_type}")

    return {"document_text": doc, "doc_type": dtype}


@app.get("/api/sources")
def list_sources():
    ps = ParentSectionStore.load(settings.INDEX_DIR)
    acts: Dict[str, Dict[str, Any]] = {}
    for sec in ps.sections.values():
        act = sec.act_name
        if act not in acts:
            acts[act] = {
                "act_name": act,
                "document_type": sec.metadata.document_type,
                "jurisdiction": sec.metadata.jurisdiction,
                "authority": sec.metadata.authority_info,
                "source_url": sec.metadata.source_url,
                "sections": []
            }
        acts[act]["sections"].append(sec.title)

    return {"sources": list(acts.values())}
