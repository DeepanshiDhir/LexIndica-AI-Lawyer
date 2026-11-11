from app.agents.state import LegalAssistantState
from app.safety.injection_scanner import PromptInjectionScanner
from app.safety.guardrails import LegalSafetyGuardrail


class SafetyAgent:
    def __init__(self):
        pass

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # 1. Scan for Prompt Injection
        injection_result = PromptInjectionScanner.scan(state.query)
        if not injection_result.is_safe:
            state.safety_passed = False
            state.safety_category = "Prompt Injection"
            state.safety_message = (
                "Security Alert: Your input triggered a security policy restriction "
                f"({injection_result.reason}). Please submit standard legal queries without system override syntax."
            )
            state.final_response = state.safety_message
            return state

        # 2. Check for Unlawful requests / Out of Scope
        safety_result = LegalSafetyGuardrail.check_safety(state.query)
        if not safety_result.is_allowed:
            state.safety_passed = False
            state.safety_category = safety_result.violation_category
            state.safety_message = (
                f"**Request Blocked [{safety_result.violation_category}]:**\n\n"
                f"{safety_result.explanation}\n\n"
                f"*Guidance:* {safety_result.remediation_advice}"
            )
            state.final_response = state.safety_message
            return state

        state.safety_passed = True
        return state
