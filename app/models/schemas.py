from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class Policy(BaseModel):
    policy_id: str
    version: str = "1.0"
    effective_date: str
    expiration_date: Optional[str] = None
    region: str = "GLOBAL"
    department: str = "ALL"
    role: str = "ALL"
    access_level: str = "ALL"
    
    # NEW fields for structured logic
    min_access_level: Optional[str] = None
    max_access_level: Optional[str] = None
    allowed_source_regions: List[str] = ["ALL"]
    allowed_destination_regions: List[str] = ["ALL"]
    effect: str = "ALLOW" # "ALLOW", "DENY", "ALLOW_WITH_CONDITION", "EXCEPTION"
    action: str = "ACCESS" # "ACCESS", "INTERNAL_SHARE", "EXTERNAL_SHARE", "APPROVE_EXTERNAL_SHARE"
    resource: str = "ALL"  # e.g., CUSTOMER_DATA
    requires_approval: bool = False
    approval_role: Optional[str] = None

    data_type: str = "ALL"
    dataset: str = "ALL"
    vendor: str = "ALL"
    priority: int = 50
    supersedes: Optional[str] = None
    policy_type: str = "standard"
    content: str

class ParsedContext(BaseModel):
    intent: Optional[str] = None
    action: Optional[str] = None
    
    # 3-actor model
    requester_employee: Optional[str] = None
    subject_employee: Optional[str] = None
    recipient_employee: Optional[str] = None
    
    role: Optional[str] = None
    employee_name: Optional[str] = None
    target_employee: Optional[str] = None
    target_role: Optional[str] = None
    target_employee_context: Optional[Dict[str, Any]] = None
    target_access_level: Optional[str] = None   # resolved access level of the recipient (Y)
    access_level: Optional[str] = None
    department: Optional[str] = None
    
    # Regional tracking
    region: Optional[str] = None
    source_region: Optional[str] = None
    destination_region: Optional[str] = None
    
    # Classification
    data_classification: Optional[str] = None
    data_owner: Optional[str] = None
    sharing_type: Optional[str] = None # "INTERNAL" | "EXTERNAL"
    
    data_type: Optional[str] = None
    dataset: Optional[str] = None
    vendor: Optional[str] = None
    requested_date: Optional[str] = None
    external_party: Optional[bool] = None
    explicit_external_signal: Optional[bool] = False
    destination_department: Optional[str] = None
    missing_context: List[str] = []
    confidence: float = 1.0

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    region: str
    access_level: str

class QueryRequest(BaseModel):
    question: str
    employee_id: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None

class EscalationStatus(BaseModel):
    critical: bool = False
    escalation_required: bool = False
    reason: Optional[str] = None

class RuleDecision(BaseModel):
    decision: str
    reason_code: str
    applicable_policies: List[Dict[str, Any]] = []
    winning_policy: Optional[Dict[str, Any]] = None
    overridden_policies: List[str] = []
    conditions: List[str] = []
    missing_context: List[str] = []
    conflicts: List[str] = []
    escalation_required: bool = False
    escalation_reason: Optional[str] = None

class AuditRecord(BaseModel):
    request_id: str
    timestamp: str
    question: str
    parsed_context: Dict[str, Any]
    candidate_policies: List[str]
    applicable_policies: List[str]
    excluded_policies: List[str]
    policy_versions_considered: List[str]
    decision: str
    reason_code: str
    winning_policy: Optional[Dict[str, Any]]
    conflicts: List[str]
    missing_context: List[str]
    escalation: Dict[str, Any]
    final_answer: str

class FinalResponse(BaseModel):
    request_id: str
    decision: str
    answer: str
    thinking_context: str = ""
    applicable_policies: List[Dict[str, Any]]
    exceptions: List[Dict[str, Any]]
    missing_context: List[str]
    conflicts: List[str]
    escalation_required: bool

class EscalationTicket(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    question: str
    context: str
    status: str = "Pending"
    admin_response: Optional[str] = None
    timestamp: str
