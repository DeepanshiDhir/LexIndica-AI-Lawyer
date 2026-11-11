import json
from typing import List
from app.agents.state import LegalAssistantState
from app.agents.llm_client import GeminiClient


class FinalResponseFormatter:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def process(self, state: LegalAssistantState) -> LegalAssistantState:
        # If safety agent flagged an issue or already generated an error response
        if not state.safety_passed:
            return state

        lang = state.preferred_language.lower()
        is_hindi = "hindi" in lang and "hinglish" not in lang
        is_hinglish = "hinglish" in lang

        # Format citations
        cited_texts = []
        for prov in state.applicable_provisions:
            cited_texts.append(f"• **{prov}**")
        citations_str = "\n".join(cited_texts) if cited_texts else "• General Principles of Indian Law"

        # Format practical remedies
        remedies_texts = []
        for i, opt in enumerate(state.practical_remedies, 1):
            remedies_texts.append(f"{i}. {opt}")
        remedies_str = "\n".join(remedies_texts) if remedies_texts else "Consult a legal professional."

        # Format uncertainties
        uncertainties_str = ""
        if state.legal_uncertainties:
            unc_list = "\n".join([f"• {u}" for u in state.legal_uncertainties])
            uncertainties_str = f"\n\n### ⚠️ Important Uncertainties & Missing Facts\n{unc_list}"

        # Standard Disclaimer
        disclaimer = (
            "\n\n---\n"
            "⚖️ **Disclaimer:** *This analysis is provided for legal informational purposes under Indian law "
            "and does not constitute formal legal advice or an attorney-client relationship. "
            "Court procedures and state-specific tenancy amendments may vary. If you are facing imminent eviction "
            "or severe financial disputes, please consult a qualified advocate or the local Legal Services Authority (DLSA).*"
        )

        if is_hindi:
            hindi_header = "### 📋 आपकी कानूनी स्थिति का विश्लेषण (Legal Summary)"
            provisions_header = "### 📜 लागू होने वाले भारतीय कानून एवं धाराएं (Applicable Laws & Sections)"
            steps_header = "### 🛠️ व्यावहारिक कदम एवं आपके कानूनी विकल्प (Practical Options)"
            advocate_header = "### 👨‍⚖️ वकील से कब संपर्क करें (When to Consult a Lawyer)"
            advocate_text = "यदि मकान मालिक 15 दिनों के नोटिस के बाद भी डिपॉजिट वापस नहीं करता है या जबरन बेदखल करने की धमकी देता है, तो तुरंत अपने जिले के रेंट अथॉरिटी या किसी अनुभवी वकील से संपर्क करें।"

            state.final_response = (
                f"{hindi_header}\n{state.reasoning_draft}\n\n"
                f"{provisions_header}\n{citations_str}\n\n"
                f"{steps_header}\n{remedies_str}"
                f"{uncertainties_str}\n\n"
                f"{advocate_header}\n{advocate_text}"
                f"{disclaimer}"
            )
        elif is_hinglish:
            hinglish_header = "### 📋 Aapki Legal Situation Ka Summary"
            provisions_header = "### 📜 Relevant Indian Laws aur Sections"
            steps_header = "### 🛠️ Practical Steps aur Next Options"
            advocate_header = "### 👨‍⚖️ Lawyer Se Kab Consult Karein"
            advocate_text = "Agar landlord formal notice ke baad bhi deposit refund nahi karta ya eviction ki dhamki deta hai, toh Rent Authority ya advocate se consult karein."

            state.final_response = (
                f"{hinglish_header}\n{state.reasoning_draft}\n\n"
                f"{provisions_header}\n{citations_str}\n\n"
                f"{steps_header}\n{remedies_str}"
                f"{uncertainties_str}\n\n"
                f"{advocate_header}\n{advocate_text}"
                f"{disclaimer}"
            )
        else:
            state.final_response = (
                f"### 📋 Legal Assessment & Summary\n{state.reasoning_draft}\n\n"
                f"### 📜 Applicable Indian Statutory Provisions & Precedents\n{citations_str}\n\n"
                f"### 🛠️ Practical Options & Next Steps\n{remedies_str}"
                f"{uncertainties_str}\n\n"
                f"### 👨‍⚖️ When to Consult a Qualified Advocate\n"
                f"You should consult a local advocate if:\n"
                f"1. The landlord fails to comply with a 15-day formal demand notice.\n"
                f"2. You are facing threats of illegal lockout, physical harassment, or disconnected utilities.\n"
                f"3. You need to initiate formal proceedings before the Rent Tribunal or Civil Court."
                f"{disclaimer}"
            )

        # Suggested follow-up questions
        state.suggested_followups = [
            "Would you like me to draft a formal 15-Day Legal Demand Notice for refund of your security deposit?",
            "Do you have a written and registered rent agreement for your tenancy?",
            "What state or city is your rented accommodation located in?"
        ]

        return state
