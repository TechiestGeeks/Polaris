from typing import List
from app.models.schemas import Policy, ParsedContext
from app.engine.normalizer import Normalizer
from app.engine.recipient_authority_checker import _tier

class ScopeMatcher:
    @staticmethod
    def match_scope(policies: List[Policy], context: ParsedContext) -> List[Policy]:
        """
        Filter policies that match the provided context strictly using the structured schema.
        """
        matched = []
        
        ctx_role = Normalizer.normalize_role(context.role) if context.role else None
        ctx_resource = Normalizer.normalize_data_classification(context.data_classification or context.data_type)
        ctx_tier = _tier(context.access_level)
        
        for p in policies:
            # Action match
            if context.action and p.action != context.action:
                continue
                    
            # Resource (Data Classification) Match
            if p.resource != "ALL" and ctx_resource != "ALL" and p.resource != ctx_resource:
                continue
                
            # Legacy field matches
            if not ScopeMatcher._match_field(p.department, context.department, "ALL"):
                continue
            if not ScopeMatcher._match_field(p.vendor, context.vendor, "ALL"):
                continue
                
            # Role matching: Check canonical role OR min/max access level
            role_matches = ScopeMatcher._match_field(p.role, ctx_role, "ALL")
            if not role_matches:
                # If role text doesn't match, check if access level fits in min/max bounds
                p_min = _tier(p.min_access_level) if p.min_access_level else -1
                p_max = _tier(p.max_access_level) if p.max_access_level else 999
                
                if p_min > -1 and ctx_tier > -1:
                    if not (p_min <= ctx_tier <= p_max):
                        continue
                else:
                    # Neither role nor hierarchy matched
                    continue
                    
            # Region constraints
            if "ALL" not in p.allowed_source_regions:
                if context.source_region and context.source_region.upper() not in p.allowed_source_regions:
                    continue
                    
            if "ALL" not in p.allowed_destination_regions:
                if context.destination_region and context.destination_region.upper() not in p.allowed_destination_regions:
                    continue
            
            matched.append(p)
            
        return matched

    @staticmethod
    def _match_field(policy_val: str, ctx_val: str, wildcard: str) -> bool:
        if not policy_val or policy_val.upper() == wildcard or policy_val.upper() == "ALL":
            return True
        if not ctx_val:
            return False
        return policy_val.lower() == ctx_val.lower()

    @staticmethod
    def check_missing_context(policies: List[Policy], context: ParsedContext) -> List[str]:
        missing = set()
        fields = ["department", "role", "vendor", "source_region", "destination_region", "data_type"]
        
        for p in policies:
            if p.department != "ALL" and not context.department: missing.add("department")
            if p.vendor != "ALL" and not context.vendor: missing.add("vendor")
            if p.role != "ALL" and not p.min_access_level and not context.role: missing.add("role")
            if "ALL" not in p.allowed_source_regions and not context.source_region: missing.add("source_region")
            if "ALL" not in p.allowed_destination_regions and not context.destination_region: missing.add("destination_region")
            
        return list(missing)
