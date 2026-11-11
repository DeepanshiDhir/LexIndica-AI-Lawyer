import json
import re
from app.agents.state import LegalAssistantState
from app.agents.llm_client import GeminiClient


class PolicyComplianceJudge:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # Programmatic Policy Rules:
        # 1. Output must never claim to be an attorney or provide formal representation.
        # 2. Output must never advise criminal or extra-judicial remedies (e.g. self-help locks, force).
        draft_lower = state.reasoning_draft.lower()

        forbidden_phrases = [
            "i am your lawyer",
            "as your attorney",
            "hire bouncers",
            "cut their electricity",
            "throw their bags out",
            "forge a document"
        ]

        violations = [p for p in forbidden_phrases if p in draft_lower]
        if violations:
            state.policy_compliant = False
            state.policy_notes = f"Policy violation detected: Draft contained prohibited text ({', '.join(violations)})."
            # Cleanse draft
            for p in violations:
                state.reasoning_draft = re.sub(re.escape(p), "[REDACTED - VIOLATES LEGAL POLICY]", state.reasoning_draft, flags=re.IGNORECASE)
            return state

        state.policy_compliant = True
        state.policy_notes = "Compliant with legal informational policy guidelines."
        return state
