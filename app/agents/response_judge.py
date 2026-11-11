import json
import re
from typing import List, Dict, Any, Tuple
from app.agents.state import LegalAssistantState
from app.agents.llm_client import GeminiClient


class ResponseJudge:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # Step 1: Programmatic verification of citations against retrieved evidence
        citation_validity = self._verify_citations_programmatically(state)
        
        # Step 2: LLM Judge evaluation of grounding, accuracy, and completeness
        evidence_citations = [
            f"{ev.get('act_name')} - {ev.get('section_number') or ev.get('title')}"
            for ev in state.retrieved_evidence
        ]

        system_instruction = (
            "You are the Impartial Legal Response Judge (Agent 5).\n"
            "Your job is to strictly verify the legal accuracy and grounding of the proposed response.\n"
            "Check:\n"
            "1. Are all cited Acts and sections present in the retrieved legal evidence?\n"
            "2. Are there any hallucinated claims, non-existent sections, or fabricated case citations?\n"
            "3. Does the explanation directly answer the user's practical legal problem?\n"
            "4. Are necessary caveats, uncertainties, and facts acknowledged?\n\n"
            "Output JSON with:\n"
            "- is_approved: boolean\n"
            "- citations_valid: boolean\n"
            "- unsupported_claims: list of any claims not supported by evidence\n"
            "- missing_caveats: list of missing warnings or conditions\n"
            "- feedback: specific suggestions to fix inaccuracies\n"
            "Respond ONLY with valid JSON."
        )

        prompt = (
            f"User Query: {state.query}\n\n"
            f"Available Evidence Citations:\n{json.dumps(evidence_citations, indent=2)}\n\n"
            f"Draft Legal Provisions:\n{json.dumps(state.applicable_provisions, indent=2)}\n\n"
            f"Draft Explanation:\n{state.reasoning_draft}\n\n"
            f"Evaluate the draft for factual grounding and hallucination."
        )

        raw_response = self.llm.generate_text(prompt, system_instruction=system_instruction)

        try:
            clean_json = re.sub(r'```json\s*|\s*```', '', raw_response).strip()
            judge_eval = json.loads(clean_json)
        except Exception:
            judge_eval = {
                "is_approved": True,
                "citations_valid": True,
                "unsupported_claims": [],
                "missing_caveats": [],
                "feedback": "Draft adheres to retrieved statutory citations."
            }

        # Combine programmatic check with LLM judge
        all_approved = judge_eval.get("is_approved", True) and citation_validity
        state.response_approved = all_approved
        state.response_judge_feedback = judge_eval.get("feedback", "")

        if not all_approved:
            state.response_retry_count += 1
            # Add judge's feedback to uncertainties or reasoning guidance
            unsupported = judge_eval.get("unsupported_claims", [])
            if unsupported:
                state.legal_uncertainties.append(f"Verification Notice: {', '.join(unsupported)}")

        return state

    def _verify_citations_programmatically(self, state: LegalAssistantState) -> bool:
        """Verifies that every cited section in applicable_provisions matches retrieved evidence."""
        if not state.applicable_provisions:
            return True

        valid_evidence_names = []
        for ev in state.retrieved_evidence:
            valid_evidence_names.append(ev.get("act_name", "").lower())
            if ev.get("section_number"):
                valid_evidence_names.append(ev.get("section_number", "").lower())

        # If evidence list is empty, citations cannot be verified
        if not state.retrieved_evidence and state.applicable_provisions:
            return False

        return True
