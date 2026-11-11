from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class FactItem(BaseModel):
    category: str
    detail: str
    is_confirmed: bool = True


class LegalAssistantState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # User input & session
    query: str
    session_id: str = "default_session"
    preferred_language: str = "English"

    # Query Understanding
    legal_domain: str = "General Tenancy Dispute"
    extracted_facts: Dict[str, Any] = Field(default_factory=dict)
    missing_facts: List[str] = Field(default_factory=list)
    jurisdiction: str = "Central"
    state_name: Optional[str] = None
    retrieval_queries: List[str] = Field(default_factory=list)

    # Retrieval
    retrieved_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_sufficient: bool = False
    retrieval_judge_notes: str = ""
    retrieval_retry_count: int = 0

    # Reasoning & Generation
    reasoning_draft: str = ""
    applicable_provisions: List[str] = Field(default_factory=list)
    practical_remedies: List[str] = Field(default_factory=list)
    legal_uncertainties: List[str] = Field(default_factory=list)

    # Judges
    response_approved: bool = False
    response_judge_feedback: str = ""
    response_retry_count: int = 0

    policy_compliant: bool = True
    policy_notes: str = ""

    safety_passed: bool = True
    safety_category: str = "None"
    safety_message: str = ""

    # Final Output
    final_response: str = ""
    citations: List[Dict[str, str]] = Field(default_factory=list)
    uncertainty_statement: str = ""
    suggested_followups: List[str] = Field(default_factory=list)
    
    # Document Generation
    document_requested: Optional[str] = None
    generated_document: Optional[str] = None
