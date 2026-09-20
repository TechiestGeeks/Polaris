import json
import os
from pathlib import Path

def generate_seed_data():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)
    audit_dir = data_dir / "audit"
    audit_dir.mkdir(exist_ok=True)
    
    policies = [
        # DATA-SHARING Scenario
        {
            "policy_id": "DATA-SHARING",
            "version": "3.0",
            "effective_date": "2024-01-01",
            "region": "GLOBAL",
            "department": "ALL",
            "vendor": "ALL",
            "supersedes": None,
            "priority": 50,
            "policy_type": "standard",
            "content": "External sharing of customer data is prohibited."
        },
        {
            "policy_id": "DATA-SHARING",
            "version": "5.0",
            "effective_date": "2026-04-01",
            "region": "GLOBAL",
            "department": "ALL",
            "vendor": "ALL",
            "supersedes": "3.0",
            "priority": 50,
            "policy_type": "standard",
            "content": "External sharing is permitted only with approved vendors."
        },
        {
            "policy_id": "VENDOR-EXCEPTION",
            "version": "1.0",
            "effective_date": "2026-06-01",
            "region": "GLOBAL",
            "department": "Analytics",
            "dataset": "Dataset Y",
            "vendor": "Vendor-X",
            "supersedes": None,
            "priority": 100,
            "policy_type": "exception",
            "content": "Vendor-X is not approved for Dataset Y."
        },
        # RETENTION Scenario
        {
            "policy_id": "RETENTION",
            "version": "4.0",
            "effective_date": "2026-01-01",
            "region": "GLOBAL",
            "department": "ALL",
            "supersedes": None,
            "priority": 50,
            "policy_type": "standard",
            "content": "Customer support records may be retained for 5 years."
        },
        {
            "policy_id": "EU-RETENTION",
            "version": "2.0",
            "effective_date": "2026-03-01",
            "region": "EU",
            "department": "Support",
            "supersedes": None,
            "priority": 90,
            "policy_type": "regional",
            "content": "Customer support records may be retained for 2 years."
        },
        # MISSING CONTEXT Scenario Support (EU-DATA)
        {
            "policy_id": "EU-DATA",
            "version": "2.0",
            "effective_date": "2026-05-01",
            "region": "EU",
            "department": "ALL",
            "vendor": "ALL",
            "supersedes": None,
            "priority": 85,
            "policy_type": "regional",
            "content": "Additional restrictions apply to certain customer datasets in the EU."
        },
        # CONFLICT Scenario (Contradictory policies with same priority)
        {
            "policy_id": "CONFLICT-A",
            "version": "1.0",
            "effective_date": "2026-01-01",
            "region": "GLOBAL",
            "department": "Marketing",
            "vendor": "Vendor-Z",
            "priority": 80,
            "policy_type": "standard",
            "content": "Marketing can share public data with Vendor-Z."
        },
        {
            "policy_id": "CONFLICT-B",
            "version": "1.0",
            "effective_date": "2026-01-01",
            "region": "GLOBAL",
            "department": "Marketing",
            "vendor": "Vendor-Z",
            "priority": 80,
            "policy_type": "standard",
            "content": "No data sharing is allowed with Vendor-Z due to audit."
        }
    ]

    with open(data_dir / "policies.json", "w", encoding="utf-8") as f:
        json.dump(policies, f, indent=2)

    print(f"Seed data created in {data_dir}")

if __name__ == "__main__":
    generate_seed_data()
