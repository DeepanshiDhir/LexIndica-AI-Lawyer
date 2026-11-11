import json
import re
from typing import Dict, Any
from app.agents.state import LegalAssistantState
from app.agents.llm_client import GeminiClient
from app.safety.injection_scanner import PromptInjectionScanner


class QueryUnderstandingAgent:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # Wrap untrusted user text safely
        safe_query = PromptInjectionScanner.wrap_untrusted_data(state.query, tag="user_query")

        system_instruction = (
            "You are an expert Indian Legal AI Assistant (Agent 1: Query Understanding Agent).\n"
            "Analyze the user's everyday legal problem and output a structured JSON with:\n"
            "- legal_domain: Specific category (e.g. 'Security Deposit Refund Dispute', 'Unlawful Eviction Threat', 'Rent Agreement & Notice Period')\n"
            "- jurisdiction: 'Central', 'Delhi', 'Maharashtra', or specific state\n"
            "- state_name: Name of Indian state or union territory if mentioned\n"
            "- preferred_language: 'English', 'Hindi', or 'Hinglish'\n"
            "- extracted_facts: Key extracted parameters (rent_amount, deposit_amount, notice_served, tenancy_duration, location)\n"
            "- missing_facts: Essential missing legal facts needed to give definitive advice\n"
            "- retrieval_queries: 2 to 4 optimized search queries targeting Indian statutory provisions and judgments\n"
            "Respond ONLY with valid JSON."
        )

        prompt = f"Analyze this user query:\n{safe_query}"
        raw_response = self.llm.generate_text(prompt, system_instruction=system_instruction)

        try:
            # Clean JSON markdown fences if present
            clean_json = re.sub(r'```json\s*|\s*```', '', raw_response).strip()
            data = json.loads(clean_json)
        except Exception:
            data = {
                "legal_domain": "Tenant-Landlord Dispute",
                "jurisdiction": "Central",
                "state_name": None,
                "preferred_language": "English",
                "extracted_facts": {},
                "missing_facts": ["Details of written agreement and tenancy location"],
                "retrieval_queries": [state.query, "Indian tenancy security deposit law", "Model Tenancy Act"]
            }

        state.legal_domain = data.get("legal_domain", state.legal_domain)
        state.jurisdiction = data.get("jurisdiction", state.jurisdiction)
        state.state_name = data.get("state_name", state.state_name)
        state.preferred_language = data.get("preferred_language", state.preferred_language)
        state.extracted_facts = data.get("extracted_facts", {})
        state.missing_facts = data.get("missing_facts", [])
        state.retrieval_queries = data.get("retrieval_queries", [state.query])

        # If user explicitly requested document generation
        q_lower = state.query.lower()
        if any(w in q_lower for w in ["draft notice", "legal notice", "generate letter", "demand notice", "notice draft"]):
            state.document_requested = "notice"
        elif any(w in q_lower for w in ["draft complaint", "file complaint", "consumer complaint"]):
            state.document_requested = "complaint"

        return state
