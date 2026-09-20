from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List, Dict, Any

from app.models.schemas import QueryRequest, FinalResponse, AuditRecord, LoginRequest, LoginResponse, ParsedContext
from app.llm.query_parser import QueryParser
from app.engine.rule_engine import RuleEngine
from app.llm.explainer import Explainer
from app.llm.classifier import QueryClassifier
from app.retrieval.repository import PolicyRepository
from app.retrieval.employee_repository import EmployeeRepository
from app.audit.logger import AuditLogger

router = APIRouter()

# Instantiate components
repo = PolicyRepository()
employee_repo = EmployeeRepository()
logger = AuditLogger()

from app.graph.builder import polaris_graph
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    if request.password != "PolarisTest123":
        raise HTTPException(status_code=401, detail="Invalid password")
        
    # Find employee by name (username)
    for emp in employee_repo.get_all_employees():
        if emp.get("name") == request.username:
            return LoginResponse(
                employee_id=emp["employee_id"],
                name=emp["name"],
                role=emp["role"],
                department=emp["department"],
                region=emp["region"],
                access_level=emp["access_level"]
            )
            
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/ask", response_model=FinalResponse)
async def ask_question(request: QueryRequest):
    req_id = logger.generate_request_id()
    timestamp = datetime.now().isoformat()
    
    # 0. Fetch logged-in employee context
    employee = employee_repo.get_employee(request.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    # Check history for pending escalation confirmation
    is_escalate_confirm = False
    is_escalate_cancel = False
    
    if request.history:
        last_msg = request.history[-1]
        # Our frontend history stores {question, answer, decision}
        if last_msg.get("decision") == "ESCALATED":
            lower_q = request.question.lower().strip()
            if lower_q in ("yes", "y", "yeah", "yep", "please", "do it"):
                is_escalate_confirm = True
            elif lower_q in ("no", "n", "nope", "cancel", "nevermind"):
                is_escalate_cancel = True
                
    cat = None
    if is_escalate_confirm: cat = "ESCALATE_CONFIRMED"
    elif is_escalate_cancel: cat = "ESCALATE_CANCELLED"

    # ── CONTEXT ENRICHMENT ─────────────────────────────────────────────
    # For EVERY non-first message, enrich the question with previous context
    # so the entire pipeline (classifier, parser, retriever, explainer) 
    # always understands the conversation flow.
    enriched_question = request.question
    if request.history:
        from app.llm.ollama_client import OllamaClient
        client = OllamaClient()
        system_prompt = """You are an expert at resolving conversational context. 
Your task is to rewrite the 'MOST RECENT QUESTION' so it is fully standalone.
Use the 'PAST CONVERSATION' ONLY to resolve missing pronouns (he, she, it), missing subjects, or missing actions in the MOST RECENT QUESTION.
DO NOT answer the question. DO NOT summarize the past conversation. Only output the rewritten MOST RECENT QUESTION."""
        
        hist_lines = []
        for i, h in enumerate(request.history[-3:]):
            hist_lines.append(f"[Past Turn {i+1}] User: {h.get('question', '')}")
            hist_lines.append(f"[Past Turn {i+1}] Agent: {h.get('answer', '')}")
        hist_text = "\n".join(hist_lines)
        
        prompt = f"PAST CONVERSATION:\n{hist_text}\n\nMOST RECENT QUESTION: {request.question}\n\nRewrite the MOST RECENT QUESTION to be standalone:"
        
        try:
            enriched = await client.generate(prompt, system=system_prompt)
            if enriched and enriched.strip():
                enriched_question = enriched.strip()
        except Exception as e:
            print(f"Context enrichment error: {e}")

    initial_state = {
        "question": enriched_question,
        "employee_context": employee,
        "history": request.history,
        "classification": cat,
        "parsed_context": None,
        "candidate_policies": [],
        "decision": None,
        "final_response": None
    }
    
    # Run LangGraph
    final_state = await polaris_graph.ainvoke(initial_state)
    
    final_response = final_state["final_response"]
    final_response.request_id = req_id
    
    # Audit log if policy evaluation happened
    decision = final_state.get("decision")
    if decision:
        parsed_context = final_state["parsed_context"]
        candidate_policies = final_state["candidate_policies"]
        audit_record = AuditRecord(
            request_id=req_id,
            timestamp=timestamp,
            question=request.question,
            parsed_context=parsed_context.model_dump(),
            candidate_policies=[f"{p.policy_id} v{p.version}" for p in candidate_policies],
            applicable_policies=[f"{p['policy_id']} v{p['version']}" for p in decision.applicable_policies],
            excluded_policies=[], 
            policy_versions_considered=[],
            decision=decision.decision,
            reason_code=decision.reason_code,
            winning_policy=decision.winning_policy,
            conflicts=decision.conflicts,
            missing_context=decision.missing_context,
            escalation={
                "escalation_required": decision.escalation_required,
                "reason": decision.escalation_reason
            },
            final_answer=final_response.answer
        )
        logger.log(audit_record)
        
    return final_response

@router.get("/policies")
def get_policies():
    return repo.get_all_policies()

@router.get("/employees")
def get_employees():
    return employee_repo.get_all_employees()

@router.get("/messages/{employee_id}")
def get_messages(employee_id: str):
    import os, json
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    path = os.path.join(DATA_DIR, "escalations.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        escalations = json.load(f)
    return [e for e in escalations if e["employee_id"] == employee_id]
