import re
from typing import List, Tuple
from pydantic import BaseModel


class SafetyCheckResult(BaseModel):
    is_allowed: bool
    violation_category: str = "None"
    explanation: str = "Request is lawful and within scope."
    remediation_advice: str = ""


class LegalSafetyGuardrail:
    UNLAWFUL_PATTERNS = [
        (
            r"(?i)(forge|fake|counterfeit|fabricate)\s+(a\s+|the\s+)?.*(rent\s+agreement|receipt|court\s+order|signature|stamp\s+paper|document)",
            "Document Forgery",
            "I cannot assist with forging, fabricating, or tampering with legal documents, rent agreements, or receipts. Falsification of documents is a punishable criminal offense under Indian law (Section 336 Bharatiya Nyaya Sanhita, 2023 / Section 465 IPC)."
        ),
        (
            r"(?i)(destroy|delete|hide|tamper\s+with)\s+.*(evidence|records|messages|proof)",
            "Evidence Tampering",
            "I cannot assist with destroying or concealing evidence or records. Causing disappearance of evidence is an offense under Section 238 BNS / Section 201 IPC."
        ),
        (
            r"(?i)(hire|send)\s+.*(goons|bouncers|muscle|thugs)\s+.*(beat|threaten|kick\s+out|evict)",
            "Physical Force or Violence",
            "I cannot provide assistance or advice involving the use of physical force, hiring bouncers/thugs, or intimidation. The Supreme Court of India in Ramesh Chand Ardawatiya v. Anil Panjwani has firmly held that extra-judicial eviction by force is unlawful and invites criminal prosecution."
        ),
        (
            r"(?i)(how\s+(can|do)\s+i|help\s+me|want\s+to|planning\s+to|how\s+to)\s+.*(cut(\s+off)?|disconnect|turn\s+off)\s+.*(water|electricity|power|gas|utilities)",
            "Unlawful Essential Services Severance",
            "I cannot assist in disconnecting essential utilities like water or electricity to coerce a tenant. Doing so is explicitly illegal under Section 20 of the Model Tenancy Act, Section 45 of Delhi Rent Control Act, and Section 29 of Maharashtra Rent Control Act, punishable with fines and restoration orders."
        ),
        (
            r"(?i)(threaten|harass|blackmail|extort)\s+(my\s+)?(tenant|landlord)",
            "Harassment or Extortion",
            "I cannot assist with threats, harassment, extortion, or criminal intimidation."
        )
    ]

    SUPPORTED_DOMAINS = [
        "tenant", "landlord", "rent", "deposit", "eviction", "lease", "agreement",
        "maintenance", "repairs", "notice", "kiraya", "makan", "kirayedar",
        "consumer", "property", "broker", "brokerage", "stamp", "registration"
    ]

    @classmethod
    def check_safety(cls, text: str) -> SafetyCheckResult:
        # Check unlawful patterns
        for pattern, category, explanation in cls.UNLAWFUL_PATTERNS:
            if re.search(pattern, text):
                return SafetyCheckResult(
                    is_allowed=False,
                    violation_category=category,
                    explanation=explanation,
                    remediation_advice="If you are facing a dispute, please seek advice through lawful legal channels, the Rent Authority, or a qualified advocate."
                )

        # Check scope
        text_lower = text.lower()
        has_legal_keyword = any(k in text_lower for k in cls.SUPPORTED_DOMAINS)
        
        unrelated_signals = [
            "bitcoin", "cryptocurrency", "stock prediction", "write python script for",
            "quantum mechanics", "movie review", "essay on shakespeare", "recipe for cake"
        ]
        if any(u in text_lower for u in unrelated_signals) and not has_legal_keyword:
            return SafetyCheckResult(
                is_allowed=False,
                violation_category="Out of Scope",
                explanation="This assistant specializes in Indian everyday legal problems, primarily tenant-landlord disputes, rent agreements, security deposits, and housing consumer rights.",
                remediation_advice="Please ask questions related to Indian tenancy law, rental agreements, eviction protections, or security deposits."
            )

        return SafetyCheckResult(
            is_allowed=True,
            violation_category="None",
            explanation="Request is lawful and within scope."
        )
