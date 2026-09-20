import json
from app.llm.ollama_client import OllamaClient
from app.models.schemas import RuleDecision, ParsedContext

class Explainer:
    def __init__(self):
        self.client = OllamaClient()
        self.system_prompt = """You are a policy explanation agent for POLARIS.
Your job is to read the deterministic Rule Engine Output and provide a direct, natural language answer.
You must NOT evaluate the policy yourself. The Rule Engine has already made the decision.

Decision Meanings:
- ALLOW: The action is permitted.
- DENY: The action is prohibited.
- PENDING_APPROVAL: The action is conditionally allowed, but requires approval from a specific role.
- CONFLICT: Policies contradict each other.
- INSUFFICIENT_CONTEXT: We need more info (e.g. region, vendor). Ask the user for the missing fields.

Provide a conversational Direct Answer. Do not output verbose JSON.
If the request is DENIED or has NO_APPLICABLE_POLICY, politely address the employee by name, state their current role/level, and mention that while their current role restricts this action, employees at a higher level might be permitted to do so.
"""

    async def explain(self, question: str, parsed_context: ParsedContext, decision: RuleDecision) -> str:
        prompt = f"""Question: {question}

Requester & Target Employee Context:
{parsed_context.model_dump_json(indent=2, exclude_none=True)}

Rule Engine Output:
{decision.model_dump_json(indent=2)}

Please provide the final explanation to the employee following this structure:
**Direct Answer:** [Your conversational explanation based on the Rule Engine Output]
**Policies Referenced:** [Bulleted list of applied policy IDs, or "None"]
"""
        response_text = await self.client.generate(prompt, system=self.system_prompt)
        return response_text.strip()
