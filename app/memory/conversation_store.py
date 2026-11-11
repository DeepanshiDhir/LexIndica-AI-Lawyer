from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ConversationSession(BaseModel):
    session_id: str
    user_id: str = "anonymous"
    messages: List[Dict[str, str]] = Field(default_factory=list)
    confirmed_facts: Dict[str, Any] = Field(default_factory=dict)
    jurisdiction: str = "Central"
    state_name: Optional[str] = None
    language: str = "English"


class MemoryStore:
    def __init__(self):
        self._sessions: Dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession(session_id=session_id)
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get_or_create(session_id)
        session.messages.append({"role": role, "content": content})

    def update_facts(self, session_id: str, new_facts: Dict[str, Any]):
        session = self.get_or_create(session_id)
        session.confirmed_facts.update(new_facts)

    def get_facts(self, session_id: str) -> Dict[str, Any]:
        return self.get_or_create(session_id).confirmed_facts

    def clear(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]


# Global in-memory singleton
conversation_memory = MemoryStore()
