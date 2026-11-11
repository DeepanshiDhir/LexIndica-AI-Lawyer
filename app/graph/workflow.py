from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from app.agents.state import LegalAssistantState
from app.agents.llm_client import GeminiClient
from app.agents.query_agent import QueryUnderstandingAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.retrieval_judge import RetrievalJudge
from app.agents.reasoning_agent import LegalReasoningAgent
from app.agents.response_judge import ResponseJudge
from app.agents.policy_agent import PolicyComplianceJudge
from app.agents.safety_agent import SafetyAgent
from app.agents.formatter import FinalResponseFormatter
from app.retrieval.hybrid_retriever import HybridLegalRetriever
from app.generation.document_generator import LegalDocumentGenerator
from app.config.settings import settings


class LegalAssistantGraph:
    def __init__(self, retriever: HybridLegalRetriever, llm_client: GeminiClient):
        self.retriever = retriever
        self.llm_client = llm_client

        # Instantiate agents
        self.safety_agent = SafetyAgent()
        self.query_agent = QueryUnderstandingAgent(llm_client)
        self.retrieval_agent = RetrievalAgent(retriever)
        self.retrieval_judge = RetrievalJudge(llm_client)
        self.reasoning_agent = LegalReasoningAgent(llm_client)
        self.response_judge = ResponseJudge(llm_client)
        self.policy_agent = PolicyComplianceJudge(llm_client)
        self.formatter = FinalResponseFormatter(llm_client)

        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(LegalAssistantState)

        # Add Nodes
        workflow.add_node("safety_check", self._node_safety)
        workflow.add_node("query_understanding", self._node_query)
        workflow.add_node("retrieval", self._node_retrieval)
        workflow.add_node("retrieval_judge", self._node_retrieval_judge)
        workflow.add_node("legal_reasoning", self._node_reasoning)
        workflow.add_node("response_judge", self._node_response_judge)
        workflow.add_node("policy_compliance", self._node_policy)
        workflow.add_node("final_formatter", self._node_formatter)

        # Set Entry Point
        workflow.set_entry_point("safety_check")

        # Edge from safety check: if unsafe, exit directly to format, else continue
        workflow.add_conditional_edges(
            "safety_check",
            self._route_after_safety,
            {
                "query_understanding": "query_understanding",
                "final_formatter": "final_formatter"
            }
        )

        workflow.add_edge("query_understanding", "retrieval")
        workflow.add_edge("retrieval", "retrieval_judge")

        # Edge from retrieval judge: retry retrieval or proceed to reasoning
        workflow.add_conditional_edges(
            "retrieval_judge",
            self._route_after_retrieval_judge,
            {
                "retrieval": "retrieval",
                "legal_reasoning": "legal_reasoning"
            }
        )

        workflow.add_edge("legal_reasoning", "response_judge")

        # Edge from response judge: retry reasoning or proceed to policy compliance
        workflow.add_conditional_edges(
            "response_judge",
            self._route_after_response_judge,
            {
                "legal_reasoning": "legal_reasoning",
                "policy_compliance": "policy_compliance"
            }
        )

        workflow.add_edge("policy_compliance", "final_formatter")
        workflow.add_edge("final_formatter", END)

        return workflow.compile()

    # Node wrappers
    def _node_safety(self, state: LegalAssistantState) -> LegalAssistantState:
        return self.safety_agent.process(state)

    def _node_query(self, state: LegalAssistantState) -> LegalAssistantState:
        return self.query_agent.process(state)

    def _node_retrieval(self, state: LegalAssistantState) -> LegalAssistantState:
        return self.retrieval_agent.process(state)

    def _node_retrieval_judge(self, state: LegalAssistantState) -> LegalAssistantState:
        return self.retrieval_judge.process(state)

    def _node_reasoning(self, state: LegalAssistantState) -> LegalAssistantState:
        return self.reasoning_agent.process(state)

    def _node_response_judge(self, state: LegalAssistantState) -> LegalAssistantState:
        return self.response_judge.process(state)

    def _node_policy(self, state: LegalAssistantState) -> LegalAssistantState:
        return self.policy_agent.process(state)

    def _node_formatter(self, state: LegalAssistantState) -> LegalAssistantState:
        state = self.formatter.process(state)
        # If a draft document was requested
        if state.document_requested:
            facts = dict(state.extracted_facts)
            if state.document_requested == "notice":
                state.generated_document = LegalDocumentGenerator.generate_security_deposit_notice(facts)
            elif state.document_requested == "complaint":
                state.generated_document = LegalDocumentGenerator.generate_rent_authority_complaint(facts)
            elif state.document_requested == "maintenance":
                state.generated_document = LegalDocumentGenerator.generate_maintenance_notice(facts)
            elif state.document_requested == "summary":
                state.generated_document = LegalDocumentGenerator.generate_lawyer_fact_summary(facts)
        return state

    # Conditional Routing functions
    def _route_after_safety(self, state: LegalAssistantState) -> Literal["query_understanding", "final_formatter"]:
        if not state.safety_passed:
            return "final_formatter"
        return "query_understanding"

    def _route_after_retrieval_judge(self, state: LegalAssistantState) -> Literal["retrieval", "legal_reasoning"]:
        if not state.retrieval_sufficient and state.retrieval_retry_count <= settings.MAX_AGENT_CORRECTIONS:
            return "retrieval"
        return "legal_reasoning"

    def _route_after_response_judge(self, state: LegalAssistantState) -> Literal["legal_reasoning", "policy_compliance"]:
        if not state.response_approved and state.response_retry_count <= settings.MAX_AGENT_CORRECTIONS:
            return "legal_reasoning"
        return "policy_compliance"

    def run(self, query: str, session_id: str = "default") -> LegalAssistantState:
        initial_state = LegalAssistantState(query=query, session_id=session_id)
        final_dict = self.graph.invoke(initial_state)
        if isinstance(final_dict, dict):
            return LegalAssistantState(**final_dict)
        return final_dict
