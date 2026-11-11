import sys
import os
from pathlib import Path

# Ensure project root is in sys.path regardless of execution working directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from typing import Dict, Any

from app.config.settings import settings
from app.api.server import get_graph
from app.generation.document_generator import LegalDocumentGenerator
from app.chunking.parser import StructureAwareLegalParser

st.set_page_config(
    page_title="LexIndica - Indian Legal Intelligence AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .disclaimer-card {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
        font-size: 0.88rem;
    }
    .citation-badge {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = "user_session_1"
    if "draft_doc" not in st.session_state:
        st.session_state.draft_doc = None
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")


init_session_state()

# Sidebar controls
with st.sidebar:
    st.image("https://img.icons8.com/color/96/scales--v1.png", width=64)
    st.title("LexIndica Legal AI")
    st.caption("Autonomous Legal Intelligence Platform for Indian Tenancy & Civil Law")
    
    st.divider()

    # Language selection
    language = st.selectbox(
        "🌐 Choose Language / भाषा चुनें",
        ["English", "Hindi (हिंदी)", "Hinglish (Hindi in Latin script)"],
        index=0
    )

    # Issue quick selection
    issue_category = st.selectbox(
        "📌 Select Legal Problem Domain",
        [
            "All Tenancy Domains",
            "Security Deposit Not Returned",
            "Illegal Deductions for Painting / Wear & Tear",
            "Unlawful Eviction Threat / Lockout",
            "Essential Services Cutoff (Water/Power)",
            "Rent Agreement & Notice Period Dispute",
            "Maintenance & Structural Repairs"
        ]
    )

    # State Selection
    state_selection = st.selectbox(
        "📍 State / Jurisdiction",
        ["All India (Central Law / MTA)", "Delhi (DRCA)", "Maharashtra (MRCA)", "Uttar Pradesh", "Karnataka", "Tamil Nadu", "Other"]
    )

    st.divider()

    # Gemini API Key configuration
    user_api_key = st.text_input(
        "🔑 Gemini API Key (Optional)",
        value=st.session_state.api_key,
        type="password",
        help="If left empty, system operates in grounded local verification mode."
    )
    if user_api_key != st.session_state.api_key:
        st.session_state.api_key = user_api_key
        os.environ["GEMINI_API_KEY"] = user_api_key
        st.success("API Key updated!")

    # PDF Upload
    st.divider()
    uploaded_pdf = st.file_uploader("📄 Upload Rent Agreement (PDF)", type=["pdf"])
    if uploaded_pdf:
        st.info(f"Loaded: {uploaded_pdf.name}")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.draft_doc = None
        st.rerun()


# Main View Tabs
tab_chat, tab_drafts, tab_sources = st.tabs(["💬 Legal Consultation Chat", "📝 Legal Document Generator", "📚 Legal Knowledge Base"])

with tab_chat:
    st.markdown('<div class="main-header">⚖️ LexIndica: Indian Legal Intelligence Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Get verified, grounded legal guidance on tenant-landlord rights, security deposits, and eviction protections in India.</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-card">
        <strong>⚠️ Legal Information Notice:</strong> This assistant provides legal information based on verified Indian statutory provisions (Model Tenancy Act 2021, Transfer of Property Act 1882, Rent Control Acts) and court precedents. It is <em>not</em> a law firm and does not provide formal legal representation. Always consult a licensed advocate for court appearances.
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "citations" in msg and msg["citations"]:
                with st.expander("🔍 Verified Statutory Citations & Evidence"):
                    for c in msg["citations"]:
                        st.markdown(f"- **{c.get('act_name')}** ({c.get('section', 'General')})")

    # Suggested Prompts
    if not st.session_state.messages:
        st.markdown("**Quick starter questions:**")
        cols = st.columns(3)
        if cols[0].button("💰 Landlord refusing to return deposit"):
            prompt_text = "My landlord is refusing to return my security deposit of Rs 50,000 saying they spent it on repainting. Can they legally deduct for paint?"
        elif cols[1].button("🚪 Landlord threatening to throw me out"):
            prompt_text = "My landlord is threatening to throw my luggage out and change the door lock because I refused a sudden 30% rent increase. What are my legal rights?"
        elif cols[2].button("📄 Draft 15-day refund notice"):
            prompt_text = "Please draft a formal 15-day legal demand notice for refund of my security deposit."
        else:
            prompt_text = None
    else:
        prompt_text = None

    # Chat Input
    user_input = st.chat_input("Describe your tenancy problem (in English, Hindi, or Hinglish)...")
    if prompt_text:
        user_input = prompt_text

    if user_input:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing Indian statutory provisions & precedents..."):
                try:
                    graph = get_graph()
                    # Include language preference in query
                    enriched_query = user_input
                    if "Hindi" in language:
                        enriched_query += " [Please respond in Hindi]"
                    elif "Hinglish" in language:
                        enriched_query += " [Please respond in Hinglish]"

                    result = graph.run(enriched_query, session_id=st.session_state.session_id)
                    response_text = result.final_response

                    st.markdown(response_text)

                    # Display retrieved sources
                    if result.retrieved_evidence:
                        with st.expander(f"📚 Retrieved Legal Evidence ({len(result.retrieved_evidence)} sources)"):
                            for ev in result.retrieved_evidence:
                                st.markdown(f"**{ev.get('act_name')} — {ev.get('title')}**")
                                st.caption(f"Jurisdiction: {ev.get('jurisdiction')} | Score: {ev.get('score', 0):.4f}")
                                st.text(ev.get("chunk_text", "")[:300] + "...")
                                st.divider()

                    # Save to session
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "citations": result.citations
                    })

                    # If document was generated
                    if result.generated_document:
                        st.session_state.draft_doc = result.generated_document
                        st.success("Draft legal document generated! Visit the 'Legal Document Generator' tab to view or edit.")

                except Exception as e:
                    err_msg = f"An error occurred while processing: {str(e)}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})


with tab_drafts:
    st.subheader("📝 Indian Legal Document Generator")
    st.caption("Generate formal, grounded legal drafts for dispute resolution.")

    doc_type = st.selectbox(
        "Choose Document to Draft",
        [
            "Security Deposit Refund Demand Notice (15-Day Cure Period)",
            "Complaint Petition to Rent Authority / Controller",
            "Urgent Maintenance & Structural Repairs Notice",
            "Advocate Consultation Fact Chronology Sheet"
        ]
    )

    with st.form("draft_form"):
        col1, col2 = st.columns(2)
        with col1:
            t_name = st.text_input("Tenant Full Name", value="Rajesh Sharma")
            l_name = st.text_input("Landlord Full Name", value="Vikram Malhotra")
            monthly_rent = st.text_input("Monthly Rent (Rs.)", value="Rs. 25,000/-")
            deposit_amt = st.text_input("Security Deposit Paid (Rs.)", value="Rs. 60,000/-")

        with col2:
            prop_addr = st.text_input("Rented Property Address", value="Flat 402, Green Woods Apartments, Indiranagar, Bengaluru")
            vacate_date = st.text_input("Date Vacated", value="31st October 2024")
            bank_info = st.text_input("Tenant Bank Account / UPI for Refund", value="HDFC Bank A/c: 50100123456789, IFSC: HDFC0000123")
            repairs_desc = st.text_input("Specific Repair / Deduction Dispute Details", value="Landlord deducted Rs. 35,000 for normal wall repainting without bills")

        submitted = st.form_submit_button("Generate Legal Draft")

    if submitted:
        facts = {
            "tenant_name": t_name,
            "landlord_name": l_name,
            "property_address": prop_addr,
            "monthly_rent": monthly_rent,
            "deposit_amount": deposit_amt,
            "vacation_date": vacate_date,
            "bank_details": bank_info,
            "defect_details": repairs_desc
        }
        if "Security Deposit Refund" in doc_type:
            st.session_state.draft_doc = LegalDocumentGenerator.generate_security_deposit_notice(facts)
        elif "Rent Authority" in doc_type:
            st.session_state.draft_doc = LegalDocumentGenerator.generate_rent_authority_complaint(facts)
        elif "Maintenance" in doc_type:
            st.session_state.draft_doc = LegalDocumentGenerator.generate_maintenance_notice(facts)
        else:
            st.session_state.draft_doc = LegalDocumentGenerator.generate_lawyer_fact_summary(facts)

    if st.session_state.draft_doc:
        st.subheader("Generated Draft (Editable)")
        edited_doc = st.text_area("Review and Edit Document:", value=st.session_state.draft_doc, height=450)
        st.download_button(
            label="📥 Download Legal Notice (.txt)",
            data=edited_doc,
            file_name="legal_notice_draft.txt",
            mime="text/plain"
        )


with tab_sources:
    st.subheader("📚 Verified Indian Legal Knowledge Base")
    st.write("Browse the verified statutory provisions, central model acts, state laws, and court precedents indexed in the system:")

    acts_info = [
        {
            "name": "Model Tenancy Act, 2021",
            "type": "Central Model Legislation",
            "authority": "Ministry of Housing and Urban Affairs (MoHUA)",
            "key_sections": "Section 4 (Written Agreement), Section 10 (Security Deposit 2-Month Cap & 1-Month Refund), Section 13 (24h Inspection Notice), Section 15 (Maintenance Schedule), Section 20 (Essential Services Severance Prohibition), Section 21 (Protection from Eviction)."
        },
        {
            "name": "Transfer of Property Act, 1882",
            "type": "Central Statutory Law",
            "authority": "Legislative Department, Ministry of Law and Justice",
            "key_sections": "Section 105 (Lease Definition), Section 106 (15-Day Notice for Monthly Leases), Section 107 (Lease Registration), Section 108(m) (Tenant Not Liable for Normal Wear & Tear), Section 108(f) (Right to Deduct Necessary Repairs from Rent), Section 111 (Determination of Lease)."
        },
        {
            "name": "Delhi Rent Control Act, 1958",
            "type": "State Tenancy Law (Delhi NCT)",
            "authority": "Delhi Rent Controller / Parliament of India",
            "key_sections": "Section 6A (Standard Rent 10% Revision Every 3 Years), Section 14 (Eviction Protection & Statutory Notice), Section 26 (Mandatory Rent Receipts), Section 27 (Deposit of Rent with Controller), Section 45 (Immediate Restoration of Essential Services)."
        },
        {
            "name": "Maharashtra Rent Control Act, 1999",
            "type": "State Tenancy Law (Maharashtra)",
            "authority": "Maharashtra State Legislature",
            "key_sections": "Section 15 (No Ejectment if Rent Paid), Section 24 (Recovery of Possession of License Premises), Section 29 (3-Month Jail / Fine for Cutting Electricity or Water), Section 55 (Mandatory Registration by Landlord)."
        },
        {
            "name": "Consumer Protection Act, 2019",
            "type": "Central Consumer Law",
            "authority": "Ministry of Consumer Affairs",
            "key_sections": "Section 2(7) (Housing Services / Co-living as Consumer Service), Section 34/35 (District Commission Complaints up to Rs 50 Lakhs), Section 39 (Order for Refund of Deposits and Compensation for Harassment)."
        },
        {
            "name": "Landmark Precedents on Tenancy & Wear & Tear",
            "type": "Judicial Precedents",
            "authority": "Supreme Court of India & High Courts",
            "key_sections": "Ramesh Chand Ardawatiya v. Anil Panjwani (No Forcible Eviction Without Court Order), Bishan Das v. State of Punjab (Rule of Law & Settled Possession), Suresh Kumar v. Bhupinder Singh (Illegal Deductions for Painting / Normal Wear & Tear), Nand Lal v. State of Haryana (Burden of Proof of Damage Lies on Landlord)."
        }
    ]

    for act in acts_info:
        with st.expander(f"📜 {act['name']} [{act['type']}]"):
            st.markdown(f"**Authority:** {act['authority']}")
            st.markdown(f"**Key Provisions Covered:**\n{act['key_sections']}")
