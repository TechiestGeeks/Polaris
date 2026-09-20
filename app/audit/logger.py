import json
import os
import uuid
from datetime import datetime
from app.models.schemas import AuditRecord

class AuditLogger:
    def __init__(self):
        self.audit_dir = os.getenv("AUDIT_DIR", "data/audit")
        os.makedirs(self.audit_dir, exist_ok=True)

    def generate_request_id(self) -> str:
        return str(uuid.uuid4())

    def log(self, record: AuditRecord):
        filename = f"audit_{record.request_id}.json"
        filepath = os.path.join(self.audit_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(record.model_dump_json(indent=2))
        except Exception as e:
            print(f"Failed to write audit log: {e}")
