from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class DocumentType(str, Enum):
    CENTRAL_ACT = "Central Acts"
    STATE_LAW = "State Laws"
    RULES_REGULATIONS = "Rules and regulations"
    COURT_JUDGMENT = "Court judgments"
    GOVT_NOTIFICATION = "Government notifications"
    OFFICIAL_GUIDANCE = "Official legal guidance"


class LegalMetadata(BaseModel):
    document_id: str
    document_title: str
    document_type: str = DocumentType.CENTRAL_ACT.value
    act_name: str
    chapter: Optional[str] = None
    section_number: Optional[str] = None
    subsection_number: Optional[str] = None
    jurisdiction: str = "Central"
    state: Optional[str] = "All"
    language: str = "English"
    effective_date: Optional[str] = None
    amendment_date: Optional[str] = None
    source_url: Optional[str] = None
    parent_document_id: Optional[str] = None
    authority_info: Optional[str] = None
    is_verified: bool = True
    extra: Dict[str, Any] = Field(default_factory=dict)


class ParentSection(BaseModel):
    section_id: str
    act_name: str
    chapter: Optional[str] = None
    section_number: Optional[str] = None
    title: str
    full_text: str
    metadata: LegalMetadata
    child_chunk_ids: List[str] = Field(default_factory=list)


class ChildChunk(BaseModel):
    chunk_id: str
    parent_section_id: str
    act_name: str
    section_number: Optional[str] = None
    chunk_index: int
    text: str
    token_count: int
    metadata: LegalMetadata
