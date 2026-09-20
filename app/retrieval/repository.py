import json
import os
from typing import List, Dict, Any
from app.models.schemas import Policy

class PolicyRepository:
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "data")
        self.policies_file = os.path.join(self.data_dir, "policies.json")
        self._policies: List[Policy] = []
        self._load_policies()

    def _load_policies(self):
        if not os.path.exists(self.policies_file):
            print(f"Policy file not found: {self.policies_file}")
            return
            
        try:
            with open(self.policies_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._policies = [Policy(**p) for p in data]
        except Exception as e:
            print(f"Error loading policies: {e}")

    def _read(self) -> List[Policy]:
        """Always read fresh from disk so admin changes are immediately effective."""
        try:
            with open(self.policies_file, "r", encoding="utf-8") as f:
                return [Policy(**p) for p in json.load(f)]
        except Exception:
            return []

    def get_all_policies(self) -> List[Policy]:
        return self._read()

    def get_candidate_policies(self, context: Any, question: str = "") -> List[Policy]:
        policies = self._read()
        if not question:
            return policies

        stopwords = {
            "can", "i", "the", "a", "an", "what", "how", "who", "is", "am", "are",
            "do", "does", "did", "to", "for", "with", "my", "this", "in", "on", "at",
            "today", "yesterday", "tomorrow", "access", "use", "view", "read", "get",
            "need", "have", "want", "like", "it", "be", "from", "of", "and", "or",
            "will", "would", "could", "should", "our", "their", "its", "about", "much",
            "data", "share", "sharing", "internal", "external", "policy", "rule", "guideline"
        }
        q_words = set(
            w.lower().rstrip("?.,!") for w in question.split()
            if w.lower().rstrip("?.,!") not in stopwords and len(w) > 2
        )

        # Include parsed context to make retrieval more robust
        if getattr(context, "intent", None) and context.intent != "OTHER":
            q_words.update(w.lower() for w in context.intent.split("_"))
        if getattr(context, "action", None):
            q_words.update(w.lower() for w in context.action.split("_"))
        if getattr(context, "data_classification", None):
            q_words.update(w.lower() for w in context.data_classification.split("_"))
        if getattr(context, "sharing_type", None):
            q_words.update(w.lower() for w in context.sharing_type.split("_"))

        candidates = []
        for p in policies:
            # Semantic Gate: if this is a sharing intent, strictly enforce transfer type
            if context.intent == "DATA_SHARING":
                if context.action == "INTERNAL_SHARE" and p.action == "EXTERNAL_SHARE":
                    continue
                if context.action == "EXTERNAL_SHARE" and p.action == "INTERNAL_SHARE":
                    continue
                    
            content_words = set(p.content.lower().split())
            pid_words = set(p.policy_id.lower().split("-"))
            
            # Strong match: matches a word in the policy ID (e.g. "leave", "remote")
            if q_words.intersection(pid_words):
                candidates.append(p)
                continue
                
            # Content match: requires at least 2 matching words if the query has multiple keywords
            overlap = q_words.intersection(content_words)
            if len(overlap) >= 2 or (len(overlap) == 1 and len(q_words) == 1):
                candidates.append(p)

        return candidates
