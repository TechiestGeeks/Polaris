import json
import os
from typing import List, Dict, Any

class EmployeeRepository:
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "data")
        self.employees_file = os.path.join(self.data_dir, "employees.json")
        self._employees: List[Dict[str, Any]] = []
        self._load_employees()

    def _load_employees(self):
        if not os.path.exists(self.employees_file):
            print(f"Employee file not found: {self.employees_file}")
            return
            
        try:
            with open(self.employees_file, "r", encoding="utf-8") as f:
                self._employees = json.load(f)
        except Exception as e:
            print(f"Error loading employees: {e}")

    def _read(self) -> List[Dict[str, Any]]:
        """Always read fresh from disk so admin changes are immediately effective."""
        try:
            with open(self.employees_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_all_employees(self) -> List[Dict[str, Any]]:
        return self._read()

    def get_employee(self, employee_id: str) -> Dict[str, Any]:
        for emp in self._read():
            if emp.get("employee_id") == employee_id:
                return emp
        return None

    def get_employee_by_name(self, name: str) -> Dict[str, Any]:
        if not name: return None
        for emp in self._read():
            if emp.get("name", "").lower() == name.lower():
                return emp
        return None

    def update_employee_role(self, name: str, new_role: str, new_access_level: str) -> bool:
        employees = self._read()
        updated = False
        for emp in employees:
            if emp.get("name", "").lower() == name.lower():
                emp["role"] = new_role
                emp["access_level"] = new_access_level
                updated = True
                break
        
        if updated:
            with open(self.employees_file, "w", encoding="utf-8") as f:
                json.dump(employees, f, indent=2)
            self._load_employees()
        return updated
