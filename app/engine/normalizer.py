from typing import Dict

# Define canonical mappings

ROLE_MAPPING = {
    "engineering manager": "Manager",
    "senior engineer": "Senior",
    "junior analyst": "Junior",
    "tech lead": "Lead",
    "hr manager": "Manager",
    "finance manager": "Manager",
    "analytics manager": "Manager",
    "senior data scientist": "Senior",
    "financial analyst": "Senior",  # guessing from level L2
    "senior analyst": "Senior",
    "junior engineer": "Junior",
    "hr executive": "Junior",
    "support specialist": "Junior",
    "support manager": "Manager",
    "chief operating officer": "Executive",
    "director": "Director",
    "intern": "Intern"
}

# Normalizes freeform text to standard classifications
DATA_CLASSIFICATION_MAPPING = {
    "raw customer": "CUSTOMER_RAW",
    "anonymized customer": "CUSTOMER_ANONYMIZED",
    "customer": "CUSTOMER_STANDARD",
    "customer pii": "CUSTOMER_PII",
    "sensitive": "CUSTOMER_SENSITIVE_PII",
    "financial": "FINANCIAL_STANDARD",
    "hr": "HR_STANDARD",
    "source code": "SOURCE_CODE",
    "marketing": "MARKETING_ASSETS",
    "health records": "HEALTH_RECORDS",
    "all": "ALL"
}

class Normalizer:
    @staticmethod
    def normalize_role(raw_role: str) -> str:
        if not raw_role:
            return "ALL"
        rl = raw_role.lower()
        if rl in ROLE_MAPPING:
            return ROLE_MAPPING[rl]
        for key, val in ROLE_MAPPING.items():
            if key in rl:
                return val
        return raw_role.capitalize()
    
    @staticmethod
    def normalize_data_classification(raw_class: str) -> str:
        if not raw_class:
            return "ALL"
        rl = raw_class.lower()
        if rl in DATA_CLASSIFICATION_MAPPING:
            return DATA_CLASSIFICATION_MAPPING[rl]
        for key, val in DATA_CLASSIFICATION_MAPPING.items():
            if key in rl:
                return val
        return raw_class.upper()
