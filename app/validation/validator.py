from typing import List, Dict, Any
from datetime import datetime

class PolicyValidator:
    @staticmethod
    def validate_policy_data(policies_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates ingestion of policy data.
        Flags missing versions, invalid dates, etc.
        """
        validated = []
        for p in policies_data:
            issues = []
            
            if "policy_id" not in p:
                issues.append("Missing policy_id")
            
            if "version" not in p:
                p["version"] = "1.0"
                issues.append("Missing version, defaulted to 1.0")
                
            if "effective_date" not in p:
                issues.append("Missing effective_date")
            else:
                try:
                    datetime.strptime(p["effective_date"], "%Y-%m-%d")
                except ValueError:
                    issues.append("Invalid effective_date format, expected YYYY-MM-DD")
            
            if issues:
                print(f"Validation issues for policy {p.get('policy_id', 'UNKNOWN')}: {issues}")
                
            validated.append(p)
            
        return validated
