import json
from typing import Dict, Any, Optional
from app.llm.ollama_client import OllamaClient
from app.models.schemas import ParsedContext

class QueryParser:
    def __init__(self):
        self.client = OllamaClient()
        self.system_prompt = """You are a policy question analysis engine for POLARIS. 
Your job is to convert the employee question and any extra context into structured JSON using a precise 3-actor model.

CRITICAL RULES:
1. "requester_employee" is the person asking the question (e.g., "Can I...").
2. "subject_employee" is the person taking the action. Usually the same as requester_employee unless asking on behalf of someone else (e.g., "Can Alice...").
3. "recipient_employee" is the person receiving data/actions.
4. "data_owner" is the person whose data is being accessed or shared (e.g., "Can I share Hasini's data" -> data_owner="Hasini").
5. "action" must be EXACTLY ONE of: "ACCESS", "INTERNAL_SHARE", "EXTERNAL_SHARE", "APPROVE_EXTERNAL_SHARE", "HR_ACTION".
6. Extract regions if mentioned: source_region, destination_region.
7. Extract destination department if mentioned: destination_department.
8. "sharing_type": "INTERNAL" or "EXTERNAL".
9. "data_classification": Map the data to a standard term if possible (e.g., CUSTOMER_RAW, CUSTOMER_PII, FINANCIAL, HR).
10. FOLLOW-UPS: If the user says "Why?", "What about...", or uses pronouns ("he", "she", "his", "it"), infer the subject, recipient, data_owner, and action from the Chat History. DO NOT clear them out! Maintain the same intent and action unless explicitly changed.
11. "explicit_external_signal": Set to true ONLY if the text explicitly mentions sharing outside the organization (e.g., 'external', 'third-party', 'vendor', 'outside', 'customer'). DO NOT set to true for internal departments or general company matters like 'company growth'.

Output ONLY a JSON object that strictly matches this schema:
{
  "intent": "DATA_SHARING" | "RETENTION" | "DATA_ACCESS" | "DEVICE" | "HR_ACTION" | "OTHER",
  "action": "ACCESS" | "INTERNAL_SHARE" | "EXTERNAL_SHARE" | "APPROVE_EXTERNAL_SHARE" | "HR_ACTION",
  "requester_employee": "string or null",
  "subject_employee": "string or null",
  "recipient_employee": "string or null",
  "destination_department": "string or null",
  "data_owner": "string or null",
  "source_region": "string or null",
  "destination_region": "string or null",
  "data_classification": "string or null",
  "sharing_type": "INTERNAL" | "EXTERNAL" | null,
  "vendor": "string or null",
  "requested_date": "YYYY-MM-DD or null",
  "external_party": boolean or null,
  "explicit_external_signal": boolean or null
}
"""

    async def parse(self, question: str, context: Optional[Dict[str, Any]] = None, history: Optional[list] = None) -> ParsedContext:
        prompt = f"Current Question: {question}\nRequester Profile: {json.dumps(context or {})}"
        if history:
            last_turns = history[-5:]
            history_lines = []
            for h in last_turns:
                history_lines.append(f"  - User asked: \"{h.get('question', '')}\"")
                history_lines.append(f"    Agent Answer: \"{h.get('answer', '')}\"")
                history_lines.append(f"    Decision was: {h.get('decision', '')}")
            prompt = "Recent Chat History (most recent last):\n" + "\n".join(history_lines) + "\n\n" + prompt
            
        prompt += "\n\nJSON Output:"
        response_text = await self.client.generate(prompt, system=self.system_prompt, format="json")
        
        try:
            parsed = json.loads(response_text)
            pc = ParsedContext(**parsed)
            pc.employee_name = pc.requester_employee
            pc.target_employee = pc.recipient_employee
            return pc
        except Exception as e:
            print(f"Failed to parse query: {e}. Raw response: {response_text}")
            return ParsedContext(intent="ERROR", action="error")
