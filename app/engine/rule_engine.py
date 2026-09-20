from typing import List, Dict, Any, Tuple
from app.models.schemas import Policy, ParsedContext, RuleDecision
from app.engine.version_resolver import VersionResolver
from app.engine.scope_matcher import ScopeMatcher
from app.engine.priority_resolver import PriorityResolver
from app.engine.conflict_detector import ConflictDetector
from app.engine.recipient_authority_checker import RecipientAuthorityChecker

class RuleEngine:
    @staticmethod
    def evaluate(candidate_policies: List[Policy], context: ParsedContext) -> RuleDecision:
        req_date = context.requested_date
        date_filtered = VersionResolver.filter_by_date(candidate_policies, req_date)
        
        scope_matched = ScopeMatcher.match_scope(date_filtered, context)
        
        missing_fields = ScopeMatcher.check_missing_context(date_filtered, context)
        if not scope_matched and missing_fields:
            return RuleDecision(
                decision="INSUFFICIENT_CONTEXT",
                reason_code="MISSING_REQUIRED_FIELDS",
                applicable_policies=[],
                missing_context=missing_fields
            )
            
        if not scope_matched:
            return RuleDecision(
                decision="NO_APPLICABLE_POLICY",
                reason_code="NO_MATCH",
                applicable_policies=[]
            )

        highest_policies, overridden = PriorityResolver.resolve_priority(scope_matched)
        overridden_desc = [f"{p.policy_id} v{p.version}" for p in overridden]

        has_conflict, conflict_desc = ConflictDetector.detect_conflicts(highest_policies)
        if has_conflict:
            return RuleDecision(
                decision="CONFLICT",
                reason_code="UNRESOLVABLE_CONFLICT",
                applicable_policies=[p.model_dump() for p in highest_policies],
                overridden_policies=overridden_desc,
                conflicts=conflict_desc,
                escalation_required=True,
                escalation_reason="Conflicting policies have equal authority."
            )

        authority_bypass, authority_reason = RecipientAuthorityChecker.check(context)
        if authority_bypass:
            return RuleDecision(
                decision="ALLOW",
                reason_code="RECIPIENT_ACCESS_SUPERSEDES",
                applicable_policies=[p.model_dump() for p in highest_policies],
                winning_policy=highest_policies[0].model_dump(),
                overridden_policies=overridden_desc,
                conditions=[
                    f"Recipient '{context.target_employee}' holds access level '{context.target_access_level}' which grants native access."
                ]
            )

        # 5. Evaluate based on structured effect
        winning_policy = highest_policies[0]
        decision = winning_policy.effect
        
        conditions = []
        if decision == "ALLOW_WITH_CONDITION":
            decision = "PENDING_APPROVAL"
            conditions.append(f"Requires approval from: {winning_policy.approval_role}")
            
        reason_code = "STANDARD_MATCH"
        if winning_policy.policy_type == "exception":
            reason_code = "EXCEPTION_OVERRIDE"
        elif winning_policy.policy_type == "regional":
            reason_code = "REGIONAL_OVERRIDE"

        return RuleDecision(
            decision=decision,
            reason_code=reason_code,
            applicable_policies=[p.model_dump() for p in highest_policies],
            winning_policy=winning_policy.model_dump(),
            overridden_policies=overridden_desc,
            conditions=conditions
        )
