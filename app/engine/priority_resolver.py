from typing import List, Tuple
from app.models.schemas import Policy

class PriorityResolver:
    @staticmethod
    def resolve_priority(policies: List[Policy]) -> Tuple[List[Policy], List[Policy]]:
        """
        Precedence Model:
        1. Explicit Exception DENY (100)
        2. Explicit Exception ALLOW (90)
        3. Regional DENY (80)
        4. Regional ALLOW (70)
        5. Explicit DENY (60)
        6. Conditional ALLOW (ALLOW_WITH_CONDITION) (50)
        7. Explicit ALLOW (40)
        8. Default (0)
        """
        if not policies:
            return [], []
            
        def calculate_score(p: Policy) -> int:
            score = 0
            
            # Base effect scores
            if p.effect == "DENY":
                score = 60
            elif p.effect == "ALLOW_WITH_CONDITION":
                score = 50
            elif p.effect == "ALLOW":
                score = 40
                
            # Overrides
            if p.policy_type == "regional":
                score += 20
            elif p.policy_type == "exception":
                score += 40
                
            # Specificity bonuses (minor bumps to resolve ties)
            if p.role and p.role.upper() not in ("ALL", "GLOBAL"):
                score += 5
            if p.vendor and p.vendor.upper() not in ("ALL", "GLOBAL"):
                score += 3
            if p.resource and p.resource.upper() not in ("ALL", "GLOBAL"):
                score += 2
                
            return score
            
        scored_policies = [(calculate_score(p), p) for p in policies]
        highest_score = max(score for score, p in scored_policies)
        
        highest_policies = [p for score, p in scored_policies if score == highest_score]
        overridden = [p for score, p in scored_policies if score < highest_score]
        
        return highest_policies, overridden
