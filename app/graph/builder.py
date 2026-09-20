from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import (
    classify_node,
    handle_malicious_node,
    handle_general_node,
    parse_node,
    retrieve_node,
    engine_node,
    explain_node,
    create_escalation_node,
    cancel_escalation_node
)

def route_classification(state: AgentState):
    cat = state.get("classification")
    if cat == "MALICIOUS":
        return "malicious"
    elif cat == "GENERAL":
        return "general"
    elif cat == "ESCALATE_CONFIRMED":
        return "escalate_confirmed"
    elif cat == "ESCALATE_CANCELLED":
        return "escalate_cancelled"
    else:
        return "policy"

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("malicious", handle_malicious_node)
    workflow.add_node("general", handle_general_node)
    workflow.add_node("parse", parse_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("engine", engine_node)
    workflow.add_node("explain", explain_node)
    workflow.add_node("create_escalation", create_escalation_node)
    workflow.add_node("cancel_escalation", cancel_escalation_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Conditional edge
    workflow.add_conditional_edges(
        "classify",
        route_classification,
        {
            "malicious": "malicious",
            "general": "general",
            "escalate_confirmed": "create_escalation",
            "escalate_cancelled": "cancel_escalation",
            "policy": "parse"
        }
    )
    
    # Normal edges
    workflow.add_edge("malicious", END)
    workflow.add_edge("general", END)
    workflow.add_edge("create_escalation", END)
    workflow.add_edge("cancel_escalation", END)
    
    workflow.add_edge("parse", "retrieve")
    workflow.add_edge("retrieve", "engine")
    workflow.add_edge("engine", "explain")
    workflow.add_edge("explain", END)
    
    return workflow.compile()

# Singleton graph instance
polaris_graph = build_graph()
