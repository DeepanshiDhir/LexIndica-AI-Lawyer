from typing import List, Dict, Any
from app.agents.state import LegalAssistantState
from app.retrieval.hybrid_retriever import HybridLegalRetriever, RetrievedEvidence


class RetrievalAgent:
    def __init__(self, retriever: HybridLegalRetriever):
        self.retriever = retriever

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # Use generated retrieval queries or fallback to user query
        queries = state.retrieval_queries if state.retrieval_queries else [state.query]
        
        all_evidence: Dict[str, RetrievedEvidence] = {}
        for q in queries[:3]:
            evidence_items = self.retriever.retrieve(
                query=q,
                jurisdiction=state.jurisdiction,
                state=state.state_name,
                top_k=4
            )
            for ev in evidence_items:
                cid = ev.chunk.chunk_id
                if cid not in all_evidence or ev.combined_score > all_evidence[cid].combined_score:
                    all_evidence[cid] = ev

        # Sort evidence by combined score
        sorted_evidence = sorted(all_evidence.values(), key=lambda e: e.combined_score, reverse=True)
        top_evidence = sorted_evidence[:5]

        # Convert to serializable dicts for state
        state.retrieved_evidence = [
            {
                "citation_id": ev.citation_id,
                "act_name": ev.act_name,
                "section_number": ev.section_number,
                "title": ev.title,
                "chunk_text": ev.chunk.text,
                "parent_full_text": ev.parent_section.full_text if ev.parent_section else ev.chunk.text,
                "score": ev.combined_score,
                "is_authoritative": ev.is_authoritative,
                "source_url": ev.chunk.metadata.source_url,
                "jurisdiction": ev.chunk.metadata.jurisdiction,
                "document_type": ev.chunk.metadata.document_type
            }
            for ev in top_evidence
        ]

        return state
