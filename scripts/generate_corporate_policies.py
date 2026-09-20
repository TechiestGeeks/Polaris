import json
import random
import uuid
import os
from datetime import datetime, timedelta

DEPARTMENTS = ["ALL", "IT", "HR", "Finance", "Legal", "Operations", "Sales", "Marketing", "Analytics"]
REGIONS = ["GLOBAL", "US", "EU", "APAC", "India", "UK"]
ROLES = ["ALL", "Intern", "Junior", "Senior", "Manager", "Executive", "Contractor"]
DATA_TYPES = ["ALL", "customer", "financial", "HR", "source_code", "marketing_assets", "health_records"]
VENDORS = ["ALL", "Vendor-X", "Vendor-Y", "Vendor-Z", "CloudCorp", "SecuriTech"]

TEMPLATES = [
    ("IT-SEC", "All {role} employees in {region} must use MFA to access {data_type} data."),
    ("IT-SEC", "Access to {data_type} from unmanaged devices is strictly prohibited for the {department} department."),
    ("HR-CONDUCT", "{role} personnel in {department} must complete annual compliance training regarding {data_type} handling."),
    ("FIN-EXPENSE", "Travel expenses for {role} staff in {region} must be approved by a Manager prior to booking."),
    ("FACILITY", "Physical access to server rooms containing {data_type} is restricted to {department} staff with {role} clearance."),
    ("REMOTE", "Remote work for {role} employees in {region} requires a dedicated, private workspace to prevent exposure of {data_type}."),
    ("VENDOR", "Sharing {data_type} with {vendor} requires explicit authorization from the {department} department head."),
    ("DATA-PRIV", "Processing of {data_type} in {region} must comply with local data protection regulations at all times."),
    ("LEGAL", "Any legal requests for {data_type} from {region} authorities must be routed through the Legal department."),
    ("COMM", "Public communication regarding {data_type} by {role} employees must be vetted by Marketing and PR.")
]

def generate_policies(count=300):
    policies = []
    
    for i in range(count):
        cat_prefix, template = random.choice(TEMPLATES)
        role = random.choice(ROLES)
        region = random.choice(REGIONS)
        dept = random.choice(DEPARTMENTS)
        data_type = random.choice(DATA_TYPES)
        vendor = random.choice(VENDORS)
        
        content = template.format(role=role, region=region, department=dept, data_type=data_type, vendor=vendor)
        
        policy_id = f"{cat_prefix}-{uuid.uuid4().hex[:6].upper()}"
        
        # Priority mapping
        priority = 50
        if role == "Executive": priority = 100
        elif role == "Manager": priority = 80
        elif region != "GLOBAL": priority = 70
        elif vendor != "ALL": priority = 85
        
        policy = {
            "policy_id": policy_id,
            "version": "1.0",
            "effective_date": (datetime.now() - timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d"),
            "expiration_date": None if random.random() > 0.2 else (datetime.now() + timedelta(days=random.randint(100, 1000))).strftime("%Y-%m-%d"),
            "region": region,
            "department": dept,
            "role": role,
            "vendor": vendor,
            "data_type": data_type,
            "dataset": "ALL",
            "supersedes": None,
            "priority": priority,
            "policy_type": "standard",
            "content": content
        }
        
        policies.append(policy)
        
    return policies

def main():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    policies_path = os.path.join(data_dir, "policies.json")
    
    existing_policies = []
    if os.path.exists(policies_path):
        with open(policies_path, "r", encoding="utf-8") as f:
            try:
                existing_policies = json.load(f)
            except Exception:
                pass
                
    new_policies = generate_policies(300)
    
    # Append the new policies
    all_policies = existing_policies + new_policies
    
    with open(policies_path, "w", encoding="utf-8") as f:
        json.dump(all_policies, f, indent=2)
        
    print(f"Generated and appended {len(new_policies)} new Big Shot Corporate policies.")
    print(f"Total policies is now {len(all_policies)}.")

if __name__ == "__main__":
    main()
