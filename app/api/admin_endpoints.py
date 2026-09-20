from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
import json
import os
import uuid
from datetime import datetime

admin_router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

ADMIN_CREDENTIALS = {"username": "Admin", "password": "Admin123"}

# ── Helpers ────────────────────────────────────────────────────────────────

def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ── Models ─────────────────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class EmployeeCreate(BaseModel):
    name: str
    department: str
    role: str
    access_level: str
    region: str

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    access_level: Optional[str] = None
    region: Optional[str] = None

class PolicyCreate(BaseModel):
    policy_id: str
    content: str
    policy_type: str = "standard"
    priority: int = 50
    region: str = "GLOBAL"
    department: str = "ALL"
    role: str = "ALL"
    access_level: str = "ALL"
    data_type: str = "ALL"
    dataset: str = "ALL"
    vendor: str = "ALL"
    effective_date: str = ""
    expiration_date: Optional[str] = None
    version: str = "1.0"
    supersedes: Optional[str] = None

class VendorCreate(BaseModel):
    name: str
    category: str
    contact: str
    region: str
    status: str = "Active"
    contract_end: str = ""
    compliance: str = ""

# ── Auth ───────────────────────────────────────────────────────────────────

@admin_router.post("/login")
def admin_login(req: AdminLoginRequest):
    if req.username == ADMIN_CREDENTIALS["username"] and req.password == ADMIN_CREDENTIALS["password"]:
        return {"role": "admin", "name": "Admin", "username": "Admin"}
    raise HTTPException(status_code=401, detail="Invalid admin credentials")

# ── Stats ──────────────────────────────────────────────────────────────────

@admin_router.get("/stats")
def get_stats():
    employees = load_json("employees.json")
    policies = load_json("policies.json")
    vendors = load_json("vendors.json")
    active_vendors = [v for v in vendors if v.get("status") == "Active"]
    return {
        "employees": len(employees),
        "vendors": len(vendors),
        "active_vendors": len(active_vendors),
        "policies": len(policies),
        "compliance_rate": 100
    }

# ── Employees ──────────────────────────────────────────────────────────────

@admin_router.get("/employees")
def list_employees():
    return load_json("employees.json")

@admin_router.post("/employees", status_code=201)
def create_employee(emp: EmployeeCreate):
    employees = load_json("employees.json")
    # Generate next employee ID
    existing_ids = [int(e["employee_id"].replace("EMP", "")) for e in employees if e["employee_id"].startswith("EMP")]
    next_num = max(existing_ids, default=0) + 1
    new_emp = {
        "employee_id": f"EMP{str(next_num).zfill(3)}",
        "name": emp.name,
        "department": emp.department,
        "role": emp.role,
        "access_level": emp.access_level,
        "region": emp.region
    }
    employees.append(new_emp)
    save_json("employees.json", employees)
    return new_emp

@admin_router.patch("/employees/{employee_id}")
def update_employee(employee_id: str, update: EmployeeUpdate):
    employees = load_json("employees.json")
    for i, emp in enumerate(employees):
        if emp["employee_id"] == employee_id:
            data = update.model_dump(exclude_none=True)
            employees[i].update(data)
            save_json("employees.json", employees)
            return employees[i]
    raise HTTPException(status_code=404, detail="Employee not found")

@admin_router.delete("/employees/{employee_id}")
def delete_employee(employee_id: str):
    employees = load_json("employees.json")
    new_list = [e for e in employees if e["employee_id"] != employee_id]
    if len(new_list) == len(employees):
        raise HTTPException(status_code=404, detail="Employee not found")
    save_json("employees.json", new_list)
    return {"message": "Employee removed"}

# ── Policies ───────────────────────────────────────────────────────────────

@admin_router.get("/policies")
def list_policies():
    return load_json("policies.json")

@admin_router.post("/policies", status_code=201)
def create_policy(pol: PolicyCreate):
    policies = load_json("policies.json")
    # Check duplicate
    if any(p["policy_id"] == pol.policy_id for p in policies):
        raise HTTPException(status_code=409, detail=f"Policy ID '{pol.policy_id}' already exists")
    new_pol = {
        **pol.model_dump(),
        "effective_date": pol.effective_date or datetime.now().strftime("%Y-%m-%d")
    }
    policies.append(new_pol)
    save_json("policies.json", policies)
    return new_pol

@admin_router.delete("/policies/{policy_id}")
def delete_policy(policy_id: str):
    policies = load_json("policies.json")
    new_list = [p for p in policies if p["policy_id"] != policy_id]
    if len(new_list) == len(policies):
        raise HTTPException(status_code=404, detail="Policy not found")
    save_json("policies.json", new_list)
    return {"message": "Policy deleted"}

# ── Vendors ────────────────────────────────────────────────────────────────

@admin_router.get("/vendors")
def list_vendors():
    return load_json("vendors.json")

@admin_router.post("/vendors", status_code=201)
def create_vendor(v: VendorCreate):
    vendors = load_json("vendors.json")
    existing_ids = [int(x["vendor_id"].replace("VND", "")) for x in vendors if x["vendor_id"].startswith("VND")]
    next_num = max(existing_ids, default=0) + 1
    new_v = {"vendor_id": f"VND{str(next_num).zfill(3)}", **v.model_dump()}
    vendors.append(new_v)
    save_json("vendors.json", vendors)
    return new_v

@admin_router.patch("/vendors/{vendor_id}")
def update_vendor(vendor_id: str, status: str):
    vendors = load_json("vendors.json")
    for i, v in enumerate(vendors):
        if v["vendor_id"] == vendor_id:
            vendors[i]["status"] = status
            save_json("vendors.json", vendors)
            return vendors[i]
    raise HTTPException(status_code=404, detail="Vendor not found")

@admin_router.delete("/vendors/{vendor_id}")
def delete_vendor(vendor_id: str):
    vendors = load_json("vendors.json")
    new_list = [v for v in vendors if v["vendor_id"] != vendor_id]
    if len(new_list) == len(vendors):
        raise HTTPException(status_code=404, detail="Vendor not found")
    save_json("vendors.json", new_list)
    return {"message": "Vendor removed"}

# ── Escalations ────────────────────────────────────────────────────────────

class ResolveEscalationRequest(BaseModel):
    admin_response: str

@admin_router.get("/escalations")
def list_escalations():
    return load_json("escalations.json")

@admin_router.post("/escalations/{escalation_id}/resolve")
def resolve_escalation(escalation_id: str, req: ResolveEscalationRequest):
    escalations = load_json("escalations.json")
    for i, esc in enumerate(escalations):
        if esc["id"] == escalation_id:
            escalations[i]["status"] = "Resolved"
            escalations[i]["admin_response"] = req.admin_response
            save_json("escalations.json", escalations)
            return escalations[i]
    raise HTTPException(status_code=404, detail="Escalation not found")
