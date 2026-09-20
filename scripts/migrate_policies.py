import json
import os
import sys

def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pol_path = os.path.join(base_dir, "data", "policies.json")
    
    if not os.path.exists(pol_path):
        print("Policies not found")
        sys.exit(1)
        
    with open(pol_path, "r", encoding="utf-8") as f:
        policies = json.load(f)
        
    for p in policies:
        c = p.get("content", "").lower()
        
        # 1. Determine effect
        if "prohibited" in c or "not approved" in c or "denied" in c or "not permitted" in c or "must not" in c or "unauthorized" in c or "no data sharing" in c:
            effect = "DENY"
        elif "requires" in c and "approval" in c:
            effect = "ALLOW_WITH_CONDITION"
        elif "requires" in c and ("consent" in c or "training" in c or "sign-off" in c):
            effect = "ALLOW_WITH_CONDITION"
        else:
            effect = "ALLOW"
            
        p["effect"] = effect
        
        # 2. Determine Action
        if "external" in c and "shar" in c:
            p["action"] = "EXTERNAL_SHARE"
        elif "cross-border" in c or "cross-department" in c or "shar" in c:
            p["action"] = "INTERNAL_SHARE"
        elif p["policy_id"].startswith("DATA-SHARING"):
            p["action"] = "EXTERNAL_SHARE" if "external" in c else "INTERNAL_SHARE"
        else:
            p["action"] = "ACCESS"
            
        # 3. Hierarchy / Min access level
        r = p.get("role", "ALL").lower()
        if r == "intern": p["min_access_level"] = "L0-INTERN"
        elif r == "junior": p["min_access_level"] = "L1-JUNIOR"
        elif r == "senior": p["min_access_level"] = "L2-SENIOR"
        elif r == "lead": p["min_access_level"] = "L3-LEAD"
        elif r == "manager": p["min_access_level"] = "L4-MANAGERIAL"
        elif r == "executive": p["min_access_level"] = "L5-EXECUTIVE"
        else: p["min_access_level"] = None
        
        p["max_access_level"] = None
        
        # 4. Regions
        reg = p.get("region", "GLOBAL")
        if reg == "GLOBAL":
            p["allowed_source_regions"] = ["ALL"]
            p["allowed_destination_regions"] = ["ALL"]
        else:
            p["allowed_source_regions"] = [reg]
            if "cross-border" in c:
                p["allowed_destination_regions"] = ["ALL"]
            else:
                p["allowed_destination_regions"] = [reg]
                
        # 5. Conditions
        if effect == "ALLOW_WITH_CONDITION":
            p["requires_approval"] = True
            if "manager approval" in c: p["approval_role"] = "Manager"
            elif "cfo approval" in c: p["approval_role"] = "CFO"
            elif "coo approval" in c: p["approval_role"] = "COO"
            elif "department head approval" in c: p["approval_role"] = "Director"
            else: p["approval_role"] = "Admin"
        else:
            p["requires_approval"] = False
            p["approval_role"] = None
            
        p["resource"] = p.get("data_type", "ALL").upper()
        
    with open(pol_path, "w", encoding="utf-8") as f:
        json.dump(policies, f, indent=2)
        
    print(f"Migrated {len(policies)} policies successfully.")

if __name__ == "__main__":
    run()
