from typing import TypedDict, List, Dict, Any, Optional
from app.models.schemas import ParsedContext, RuleDecision, FinalResponse

class AgentState(TypedDict):
    question: str
    employee_context: Dict[str, Any]
    history: Optional[List[Dict[str, str]]]
    classification: Optional[str]      # MALICIOUS, GENERAL, POLICY
    parsed_context: Optional[ParsedContext]
    candidate_policies: List[Dict[str, Any]]
    decision: Optional[RuleDecision]
    final_response: Optional[FinalResponse]
    escalation_confirmed: Optional[bool]
