from typing import Optional, Tuple
from app.models.schemas import ParsedContext

# ─────────────────────────────────────────────────────────────────────────────
# Authority Hierarchy
# Maps access level prefixes to a numeric tier.  Higher = more authority.
# ─────────────────────────────────────────────────────────────────────────────
_AUTHORITY_TIERS = {
    "L0": 0,   # Intern
    "L1": 1,   # Junior
    "L2": 2,   # Senior
    "L3": 3,   # Manager / Lead
    "L4": 4,   # Managerial / Director
    "L5": 5,   # Executive / C-Suite
}

# Threshold: recipients at this tier or above are considered to have native
# broad data access that supersedes lower-level sharing restrictions.
_NATIVE_ACCESS_THRESHOLD = 4  # L4+ (Director, Managerial, Executive)


def _tier(access_level: Optional[str]) -> int:
    """Return the numeric authority tier for an access_level string.

    Handles formats like ''L4-MANAGERIAL'', ''L5-EXECUTIVE'', ''Managerial'' etc.
    Returns -1 if the level is unrecognisable.
    """
    if not access_level:
        return -1
    al = access_level.upper()

    # Attempt canonical prefix match first (e.g. ''L4-...'')
    for prefix, tier in _AUTHORITY_TIERS.items():
        if al.startswith(prefix):
            return tier

    # Fallback: handle legacy / freeform labels
    if "EXECUTIVE" in al or "COO" in al or "CEO" in al or "CFO" in al or "CTO" in al or "CISO" in al:
        return 5
    if "DIRECTOR" in al or "MANAGERIAL" in al or "HEAD" in al:
        return 4
    if "MANAGER" in al or "LEAD" in al:
        return 3
    if "SENIOR" in al:
        return 2
    if "JUNIOR" in al:
        return 1
    if "INTERN" in al:
        return 0

    return -1


class RecipientAuthorityChecker:
    """
    Checks whether the *recipient* (target_employee Y) of a data share already
    holds a high enough authority level to make sharing restrictions from the
    *sharer*''s (X''s) side irrelevant for internal data movement.

    The reasoning principle:
        If Y is a Director or above (L4+), they have organisation-wide data
        access granted at their tier.  Restricting an Intern from sharing data
        WITH a Director conflates "the Intern cannot freely distribute PII" with
        "the Director cannot receive data they already have rights to".  These are
        different policy questions.

    Note: This check only applies to *internal* shares (external_party is False
    or None).  External sharing always falls back to the full policy pipeline.
    """

    @staticmethod
    def check(context: ParsedContext) -> Tuple[bool, str]:
        """
        Returns:
            (True, "RECIPIENT_HAS_NATIVE_ACCESS")  -- recipient outranks the
                restriction; the share should be ALLOW-ed.
            (False, "")                             -- normal policy evaluation
                should continue.
        """
        # Only relevant for DATA_SHARING or DATA_ACCESS intent
        if context.intent not in ("DATA_SHARING", "DATA_ACCESS"):
            return False, ""

        # Never bypass for external parties -- they are handled by dedicated policies
        if context.external_party is True:
            return False, ""

        # For DATA_SHARING, the recipient is the target employee.
        # For DATA_ACCESS, the recipient is the subject/requester employee.
        if context.intent == "DATA_SHARING":
            target_level = context.target_access_level
        else:
            target_level = context.access_level

        if not target_level:
            # Cannot determine recipient authority without their profile
            return False, ""

        recipient_tier = _tier(target_level)

        if recipient_tier >= _NATIVE_ACCESS_THRESHOLD:
            return True, "RECIPIENT_HAS_NATIVE_ACCESS"

        return False, ""
