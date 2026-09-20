from app.graph.state import AgentState
from app.llm.classifier import QueryClassifier
from app.llm.query_parser import QueryParser
from app.llm.explainer import Explainer
from app.retrieval.repository import PolicyRepository
from app.engine.rule_engine import RuleEngine
from app.models.schemas import FinalResponse
from datetime import datetime

# Instances
classifier = QueryClassifier()
parser = QueryParser()
explainer = Explainer()
repo = PolicyRepository()

async def classify_node(state: AgentState):
    existing_cat = state.get("classification")
    if existing_cat in ("ESCALATE_CONFIRMED", "ESCALATE_CANCELLED"):
        return {"classification": existing_cat}
    category = await classifier.classify(state["question"], history=state.get("history"))
    return {"classification": category}

async def handle_malicious_node(state: AgentState):
    response = FinalResponse(
        request_id="TBD_IN_ROUTER", decision="DENY", answer="Malicious",
        applicable_policies=[], exceptions=[], missing_context=[], conflicts=[], escalation_required=True
    )
    return {"final_response": response}

async def handle_general_node(state: AgentState):
    general_answer = await classifier.answer_general(state["question"], user_context=state["employee_context"], history=state.get("history"))
    response = FinalResponse(
        request_id="TBD_IN_ROUTER", decision="N/A", answer=general_answer,
        applicable_policies=[], exceptions=[], missing_context=[], conflicts=[], escalation_required=False
    )
    return {"final_response": response}

async def parse_node(state: AgentState):
    try:
        parsed_context = await parser.parse(state["question"], state["employee_context"], history=state.get("history"))
    except Exception as e:
        print(f"LLM Parse Error: {e}")
        from app.models.schemas import ParsedContext
        parsed_context = ParsedContext(intent="ERROR", action="error")
    
    emp = state["employee_context"]
    
    # 1. Requester (M)
    parsed_context.requester_employee = emp.get("name")
    
    # 2. Subject (X)
    from app.retrieval.employee_repository import EmployeeRepository
    emp_repo = EmployeeRepository()
    
    if not parsed_context.subject_employee or parsed_context.subject_employee.lower() in ["i", "me", "my", emp.get("name", "").lower()]:
        parsed_context.subject_employee = emp.get("name")
        parsed_context.role = emp.get("role")
        parsed_context.department = emp.get("department")
        parsed_context.access_level = emp.get("access_level")
        parsed_context.region = emp.get("region")
    else:
        subj_emp = emp_repo.get_employee_by_name(parsed_context.subject_employee)
        if subj_emp:
            parsed_context.role = subj_emp.get("role")
            parsed_context.department = subj_emp.get("department")
            parsed_context.access_level = subj_emp.get("access_level")
            parsed_context.region = subj_emp.get("region")

    if not parsed_context.source_region:
        parsed_context.source_region = parsed_context.region
            
    # 3. Recipient (Y)
    if parsed_context.recipient_employee:
        target_emp = emp_repo.get_employee_by_name(parsed_context.recipient_employee)
        if target_emp:
            parsed_context.target_employee_context = target_emp
            parsed_context.target_access_level = target_emp.get("access_level")
            parsed_context.target_role = target_emp.get("role")
            if not parsed_context.destination_region:
                parsed_context.destination_region = target_emp.get("region")
                
    # 3.5 Data Owner
    if parsed_context.data_owner:
        if not parsed_context.data_classification or parsed_context.data_classification == "ALL":
            parsed_context.data_classification = "HR_STANDARD"
            
    # 4. Resolve transfer context explicitly
    from app.engine.transfer_context_resolver import TransferContextResolver
    parsed_context = TransferContextResolver.resolve(parsed_context, state["question"])
            
    return {"parsed_context": parsed_context}


async def retrieve_node(state: AgentState):
    keyword_candidates = repo.get_candidate_policies(state["parsed_context"], state["question"])
    return {"candidate_policies": keyword_candidates}

def engine_node(state: AgentState):
    decision = RuleEngine.evaluate(state["candidate_policies"], state["parsed_context"])
    return {"decision": decision}

async def explain_node(state: AgentState):
    decision = state["decision"]
    parsed_context = state["parsed_context"]
    question = state["question"]
    
    try:
        explanation = await explainer.explain(question, parsed_context, decision)
    except Exception as e:
        explanation = f"Ollama is offline. Engine decided: {decision.decision}."
        
    response = FinalResponse(
        request_id="TBD_IN_ROUTER", 
        decision=decision.decision,
        answer=explanation,
        thinking_context=decision.model_dump_json(indent=2),
        applicable_policies=decision.applicable_policies,
        exceptions=[p for p in decision.applicable_policies if p.get("policy_type") == "exception"],
        missing_context=decision.missing_context,
        conflicts=decision.conflicts,
        escalation_required=decision.escalation_required
    )
    return {"final_response": response}

async def create_escalation_node(state: AgentState):
    response = FinalResponse(request_id="TBD", decision="ESCALATED", answer="Escalated.", applicable_policies=[], exceptions=[], missing_context=[], conflicts=[], escalation_required=False)
    return {"final_response": response}

async def cancel_escalation_node(state: AgentState):
    response = FinalResponse(request_id="TBD", decision="N/A", answer="Cancelled.", applicable_policies=[], exceptions=[], missing_context=[], conflicts=[], escalation_required=False)
    return {"final_response": response}
