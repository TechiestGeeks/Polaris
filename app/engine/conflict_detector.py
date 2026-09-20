from typing import List, Tuple
from app.models.schemas import Policy

class ConflictDetector:
    @staticmethod
    def detect_conflicts(policies: List[Policy]) -> Tuple[bool, List[str]]:
        if not policies or len(policies) == 1:
            return False, []
            
        effects = set(p.effect for p in policies)
        
        # If we have mixed effects remaining at the exact same priority level, it's a conflict
        if len(effects) > 1 and "DENY" in effects and ("ALLOW" in effects or "ALLOW_WITH_CONDITION" in effects):
            descs = [f"[{p.policy_id}]: {p.effect}" for p in policies]
            return True, descs
            
        return False, []
