from datetime import datetime
from typing import List, Dict, Any
from app.models.schemas import Policy

class VersionResolver:
    @staticmethod
    def filter_by_date(policies: List[Policy], requested_date_str: str) -> List[Policy]:
        """
        Filter policies that were effective at requested_date_str.
        Superseded policies are handled by checking if the newer policy was active on the date.
        Actually, a more robust way is to sort by effective date, and for any given policy_id, 
        pick the one whose effective date is <= requested_date and (expiration_date > requested_date or is None).
        Also, if a policy supersedes another, the older policy is implicitly expired on the effective date of the new one.
        """
        if not policies:
            return []
            
        try:
            req_date = datetime.strptime(requested_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            # If no valid date provided, assume today
            req_date = datetime.today().date()

        # Group by policy_id
        grouped = {}
        for p in policies:
            grouped.setdefault(p.policy_id, []).append(p)

        active_policies = []
        for pid, versions in grouped.items():
            # Sort versions by effective date ascending
            versions.sort(key=lambda x: x.effective_date)
            
            # Find the most recent version that is effective on or before req_date
            applicable_version = None
            for i, v in enumerate(versions):
                try:
                    eff_date = datetime.strptime(v.effective_date, "%Y-%m-%d").date()
                except ValueError:
                    continue # Skip invalid dates (should be caught by validator)
                    
                if eff_date <= req_date:
                    applicable_version = v
                else:
                    # Since it's sorted, any subsequent version is in the future relative to req_date
                    break
            
            if applicable_version:
                # Need to also check explicit expiration date if present
                if applicable_version.expiration_date:
                    try:
                        exp_date = datetime.strptime(applicable_version.expiration_date, "%Y-%m-%d").date()
                        if exp_date <= req_date:
                            continue # Expired
                    except ValueError:
                        pass
                active_policies.append(applicable_version)

        return active_policies
