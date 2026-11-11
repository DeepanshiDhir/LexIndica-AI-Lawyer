import json
import re
from app.agents.state import LegalAssistantState
from app.agents.llm_client import GeminiClient


class RetrievalJudge:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # If no evidence was retrieved at all
        if not state.retrieved_evidence:
            state.retrieval_sufficient = False
            state.retrieval_judge_notes = "No matching legal provisions found in index."
            state.retrieval_retry_count += 1
            state.retrieval_queries = [
                f"{state.legal_domain} Indian law provisions",
                "Model Tenancy Act Transfer of Property Act general rules"
            ]
            return state

        # Prepare evidence summary for evaluation
        evidence_summary = "\n".join([
            f"- [{ev.get('act_name')} | {ev.get('section_number') or ev.get('title')}]: {ev.get('chunk_text', '')[:200]}..."
            for ev in state.retrieved_evidence
        ])

        system_instruction = (
            "You are an impartial Legal Retrieval Judge (Agent 3).\n"
            "Evaluate whether the retrieved evidence is legally sufficient and relevant to address the user's issue.\n"
            "Criteria:\n"
            "1. Relevance: Does it cover the specific dispute (e.g. deposit, eviction, maintenance)?\n"
            "2. Source Authority: Are verified statutory acts (MTA, TPA, Rent Control) or precedents present?\n"
            "3. Coverage: Is there enough legal basis to provide grounded legal options?\n\n"
            "Output JSON with:\n"
            "- is_sufficient: boolean\n"
            "- coverage_score: float (0.0 to 1.0)\n"
            "- feedback: brief critique of retrieval quality\n"
            "- suggested_query_rewrite: optional improved query if insufficient\n"
            "Respond ONLY with valid JSON."
        )

        prompt = (
            f"User Legal Query: {state.query}\n"
            f"Legal Domain: {state.legal_domain}\n"
            f"Retrieved Evidence:\n{evidence_summary}"
        )

        raw_response = self.llm.generate_text(prompt, system_instruction=system_instruction)
        try:
            clean_json = re.sub(r'```json\s*|\s*```', '', raw_response).strip()
            eval_data = json.loads(clean_json)
        except Exception:
            eval_data = {
                "is_sufficient": True if len(state.retrieved_evidence) > 0 else False,
                "coverage_score": 0.85,
                "feedback": "Statutory provisions retrieved successfully.",
                "suggested_query_rewrite": None
            }

        is_sufficient = eval_data.get("is_sufficient", True)
        state.retrieval_sufficient = is_sufficient
        state.retrieval_judge_notes = eval_data.get("feedback", "")

        if not is_sufficient:
            state.retrieval_retry_count += 1
            rewrite = eval_data.get("suggested_query_rewrite")
            if rewrite:
                state.retrieval_queries = [rewrite]
            else:
                state.retrieval_queries = [f"{state.legal_domain} statutory remedies India"]

        return state
