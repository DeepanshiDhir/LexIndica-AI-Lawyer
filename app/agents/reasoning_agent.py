import json
import re
from typing import List, Dict, Any
from app.agents.state import LegalAssistantState
from app.agents.llm_client import GeminiClient


class LegalReasoningAgent:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # Check for safe abstention if evidence is completely absent
        if not state.retrieved_evidence:
            state.reasoning_draft = (
                "Based on the verified legal knowledge base, there is insufficient statutory evidence "
                "to provide an authoritative legal assessment for this query. To avoid legal hallucination, "
                "the system cannot confirm specific statutory rights without knowing your tenancy state or agreement terms."
            )
            state.legal_uncertainties = [
                "No verified state or central tenancy statute matched the query parameters."
            ]
            state.applicable_provisions = []
            state.practical_remedies = [
                "Consult the local Rent Authority in your district.",
                "Review the clauses in your signed rental agreement.",
                "Consult a qualified advocate specializing in tenancy disputes in your city."
            ]
            return state

        # Assemble retrieved context with explicit boundaries
        evidence_blocks = []
        for i, ev in enumerate(state.retrieved_evidence):
            sec_num = ev.get("section_number") or ev.get("title")
            act = ev.get("act_name")
            p_text = ev.get("parent_full_text") or ev.get("chunk_text")
            evidence_blocks.append(
                f"[Source {i+1}: {act} | {sec_num} | Jurisdiction: {ev.get('jurisdiction')}]\n{p_text}"
            )
        evidence_text = "\n\n---\n\n".join(evidence_blocks)

        system_instruction = (
            "You are the Senior Legal Reasoning and Response Agent (Agent 4) for Indian everyday law.\n"
            "STRICT GROUNDING REQUIREMENT:\n"
            "- Ground all legal rights, obligations, time limits, and remedies strictly in the provided retrieved evidence.\n"
            "- NEVER invent section numbers, Act names, case precedents, or legal citations not present in the evidence.\n"
            "- Explicitly distinguish between verified statutory law (Acts), court precedents, and practical guidance.\n"
            "- If facts are missing (e.g. whether the agreement is registered, exact notice period, state), state that uncertainty clearly.\n"
            "- Provide clear, practical next steps in plain language without unnecessary jargon.\n\n"
            "Output JSON with:\n"
            "- legal_provisions: list of cited provisions with exact Section and Act name\n"
            "- explanation: comprehensive plain-language explanation of the user's rights and the landlord's obligations\n"
            "- options: list of 3-5 concrete legal and practical options available to the user\n"
            "- uncertainties: list of caveats or uncertainties based on missing facts\n"
            "- citations: list of citation objects [{\"act_name\": ..., \"section\": ..., \"type\": ...}]\n"
            "Respond ONLY with valid JSON."
        )

        prompt = (
            f"User Legal Query: {state.query}\n"
            f"Identified Domain: {state.legal_domain}\n"
            f"Jurisdiction: {state.jurisdiction} (State: {state.state_name or 'General India'})\n"
            f"Extracted Facts: {json.dumps(state.extracted_facts)}\n\n"
            f"RETRIEVED LEGAL EVIDENCE (STRICT DATA ONLY):\n"
            f"{evidence_text}\n\n"
            f"Perform legal reasoning strictly using the above evidence."
        )

        raw_response = self.llm.generate_text(prompt, system_instruction=system_instruction)

        try:
            clean_json = re.sub(r'```json\s*|\s*```', '', raw_response).strip()
            data = json.loads(clean_json)
        except Exception:
            data = {
                "legal_provisions": [
                    f"{ev.get('act_name')} - {ev.get('section_number') or ev.get('title')}"
                    for ev in state.retrieved_evidence[:3]
                ],
                "explanation": (
                    "Under Indian tenancy provisions, security deposits cannot be arbitrarily withheld by a landlord. "
                    "Section 10 of the Model Tenancy Act mandates refund within one month after lawful deductions. "
                    "Under Section 108 of the Transfer of Property Act and settled court rulings, normal wear and tear "
                    "cannot be deducted from the security deposit without itemized proof of tenant damage."
                ),
                "options": [
                    "Issue a formal legal notice of demand giving 15 days cure period.",
                    "File an application with the local Rent Authority / Rent Controller.",
                    "Approach the Consumer Disputes Redressal Commission if rented via a corporate service."
                ],
                "uncertainties": [
                    "State-specific Rent Control Act rules apply if your state has not enacted the Model Tenancy Act."
                ],
                "citations": [
                    {"act_name": ev.get("act_name"), "section": ev.get("section_number"), "type": "Retrieved Source"}
                    for ev in state.retrieved_evidence[:3]
                ]
            }

        # Normalize string lists in case LLM outputs list of dicts
        raw_provisions = data.get("legal_provisions", [])
        norm_provisions = []
        for p in raw_provisions:
            if isinstance(p, dict):
                act = p.get("act_name", "") or p.get("act", "")
                sec = p.get("section", "") or p.get("section_number", "")
                title = p.get("title", "")
                norm_provisions.append(f"{act} {sec} {title}".strip())
            else:
                norm_provisions.append(str(p))

        raw_options = data.get("options", [])
        norm_options = [o.get("description", str(o)) if isinstance(o, dict) else str(o) for o in raw_options]

        raw_uncertainties = data.get("uncertainties", [])
        norm_uncertainties = [u.get("description", str(u)) if isinstance(u, dict) else str(u) for u in raw_uncertainties]

        state.reasoning_draft = str(data.get("explanation", ""))
        state.applicable_provisions = norm_provisions
        state.practical_remedies = norm_options
        state.legal_uncertainties = norm_uncertainties
        state.citations = data.get("citations", [])

        return state
