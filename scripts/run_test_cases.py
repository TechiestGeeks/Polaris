"""
Run all 100 test cases against the PolarisV2 Policy Reasoning Agent API.
Saves full results to test_results.txt in the project root.
"""

import httpx
import asyncio
import time
import sys
import os

API_URL = "http://localhost:8000/api/ask"

# Each test case: (test_number, employee_id, prompt)
# employee_id is the "logged-in" user asking the question.
# For general/observational queries we use ADM001 (Admin).
# For employee-specific queries we use the relevant employee.

TEST_CASES = [
    # Employee-focused (TC 01-25)
    (1, "EMP009", "What is Arjun Mehta's employee ID, department, role, access level, and region?"),
    (2, "EMP009", "Can you identify the employee with ID EMP003?"),
    (3, "EMP009", "What access level does Rahul Verma have?"),
    (4, "EMP009", "Rahul Verma is a Senior Engineer. Does his record classify him as a senior-level user?"),
    (5, "EMP009", "Who is the Tech Lead in Engineering in India?"),
    (6, "EMP009", "Who is the Engineering Manager in India?"),
    (7, "EMP009", "Who is the Analytics Manager in India?"),
    (8, "EMP009", "Who is the Data Scientist in Analytics located in the EU?"),
    (9, "EMP009", "Who is the Senior Data Scientist in Singapore?"),
    (10, "EMP009", "Which employees belong to the Support department in the EU?"),
    (11, "EMP009", "Which employees in Engineering have L4-MANAGERIAL access?"),
    (12, "EMP009", "Which employees have L2-SENIOR access?"),
    (13, "EMP009", "Which employees are interns?"),
    (14, "EMP009", "Who is the Chief Operating Officer and what is their access level?"),
    (15, "EMP009", "Does EMP015 belong to a regional office or have global scope?"),
    (16, "EMP009", "Find all Legal employees and their access levels."),
    (17, "EMP009", "Who is the Legal Director in the EU?"),
    (18, "EMP009", "Who is the Legal Manager in the US?"),
    (19, "EMP009", "What is unusual about Hasini's employee record?"),
    (20, "EMP009", "What is unusual about ADM001 compared with the other access-level values?"),
    (21, "EMP009", "What is unusual about Kushal's region value?"),
    (22, "EMP009", "Is there an employee whose role suggests seniority but whose access level is junior?"),
    (23, "EMP009", "Are there any employees whose role and access level appear inconsistent?"),
    (24, "EMP009", "Find all employees in India with junior access."),
    (25, "EMP009", "Find all employees in the EU with managerial or director-level access."),
    
    # Vendor-focused (TC 26-43)
    (26, "EMP009", "What services does VND001 provide, and what is its current recorded status?"),
    (27, "EMP009", "Is Datalink Systems' contract still valid today?"),
    (28, "EMP009", "Is VND002 still an active vendor today?"),
    (29, "EMP009", "What is the compliance certification of SecureNet Analytics?"),
    (30, "EMP009", "Which vendor is responsible for payroll processing?"),
    (31, "EMP009", "Is PayFlow's contract still valid today?"),
    (32, "EMP009", "Which vendor is currently marked Under Review?"),
    (33, "EMP009", "Can CloudVault Storage be treated as an active vendor today based only on the supplied records?"),
    (34, "EMP009", "Which vendor provides legal services in the EU?"),
    (35, "EMP009", "Is LegalEdge Partners' contract still valid today?"),
    (36, "EMP009", "Which vendor provides penetration-testing services?"),
    (37, "EMP009", "Is NetSentry Cyber currently usable based on vendor status and contract date?"),
    (38, "EMP009", "Which vendors have GDPR compliance listed?"),
    (39, "EMP009", "Which vendors operate in India?"),
    (40, "EMP009", "Which vendors have a Global region?"),
    (41, "EMP009", "Which vendor provides HR Management software?"),
    (42, "EMP009", "Which vendor provides Marketing Analytics?"),
    (43, "EMP009", "Are there any vendors whose status is Active but whose contract end date has already passed?"),
    
    # Combined employee + vendor reasoning (TC 44-50)
    (44, "EMP011", "Can HR employee Siddharth Rao use HRBridge Software?"),
    (45, "EMP012", "Can Lakshmi Pillai, the HR Manager, use HRBridge Software?"),
    (46, "EMP022", "Can the EU Legal Director Jayasri use LegalEdge Partners?"),
    (47, "EMP018", "Can the EU Engineering Manager Anna Kowalski use SecureNet Analytics?"),
    (48, "EMP008", "Can Analytics employee Divya Krishnan use MarketPulse Analytics?"),
    (49, "EMP009", "Can EU Data Scientist Rohan Gupta use MarketPulse Analytics?"),
    (50, "EMP001", "Can Arjun Mehta use Datalink Systems for company work today?"),
    
    # Data-sharing scenarios (TC 51-100)
    (51, "EMP002", "Can Priya Sharma share anonymized analytics data with an external vendor from India?"),
    (52, "EMP001", "Can Arjun Mehta share anonymized analytics data with an external vendor from India?"),
    (53, "EMP004", "Can Sneha Iyer share standard customer data with an approved vendor in India?"),
    (54, "EMP005", "Can Vikram Nair share customer PII with an approved vendor in India?"),
    (55, "EMP006", "Can Ananya Reddy share customer data with an external vendor in India?"),
    (56, "EMP007", "Can Karthik Menon share anonymized analytics data with a vendor in India?"),
    (57, "EMP008", "Can Divya Krishnan share anonymized analytics data with a vendor in India?"),
    (58, "EMP008", "Can Divya Krishnan share raw customer analytics data with a vendor in India?"),
    (59, "EMP010", "Can Meera Joshi share raw customer analytics data with an approved vendor in India?"),
    (60, "EMP009", "Can Rohan Gupta share anonymized analytics data from the EU?"),
    (61, "EMP009", "Can Rohan Gupta share raw customer data with an external vendor from the EU?"),
    (62, "EMP016", "Can Elena Mueller share standard engineering data with an external vendor in the EU?"),
    (63, "EMP018", "Can Anna Kowalski share source code with an external vendor in the EU?"),
    (64, "EMP017", "Can Thomas Schmidt share customer support records externally in the EU?"),
    (65, "EMP019", "Can Lukas Weber share customer support records with an external vendor in the EU?"),
    (66, "EMP022", "Can Jayasri share privileged legal documents with an external legal vendor in the EU?"),
    (67, "EMP023", "Can Ganesh share privileged legal documents with an external legal vendor in the EU?"),
    (68, "EMP021", "Can Joshna share ordinary legal documents with an external vendor in the US?"),
    (69, "EMP021", "Can Joshna share privileged legal documents with an external vendor in the US?"),
    (70, "EMP013", "Can Nikhil Desai share financial records with an external vendor in India?"),
    (71, "EMP014", "Can Shalini Kapoor share financial records with an approved vendor in India?"),
    (72, "EMP011", "Can Siddharth Rao share employee data with HRBridge?"),
    (73, "EMP012", "Can Lakshmi Pillai share employee PII with an approved HR vendor?"),
    (74, "EMP020", "Can Sophia Chen share standard customer data with an approved vendor in Singapore?"),
    (75, "EMP020", "Can Sophia Chen share sensitive customer PII with an approved vendor in Singapore?"),
    (76, "EMP015", "Can Rajesh Subramanian authorize global sharing of sensitive customer data?"),
    (77, "EMP001", "Can Arjun Mehta authorize global sharing of sensitive customer data?"),
    (78, "EMP003", "Can Rahul Verma share customer data because he is a Senior Engineer?"),
    (79, "EMP003", "Should Rahul Verma's role or his recorded access level determine his sharing authority?"),
    (80, "EMP024", "Can Hasini share sensitive customer data because her role is Executive?"),
    (81, "EMP024", "Can Hasini approve sharing solely because her role says Executive?"),
    (82, "EMP007", "Can Karthik Menon share raw customer data because he works in Analytics?"),
    (83, "EMP008", "Can Divya Krishnan share raw customer data because she is a Senior Analyst?"),
    (84, "EMP010", "Can Meera Joshi share raw customer data because she is an Analytics Manager?"),
    (85, "EMP006", "Can Ananya Reddy share anonymized analytics data because it is anonymized?"),
    (86, "EMP017", "Can Thomas Schmidt share anonymized customer-support statistics with an external vendor?"),
    (87, "EMP019", "Can Lukas Weber share anonymized customer-support statistics externally?"),
    (88, "EMP016", "Can Elena Mueller share source code externally because she is a Senior Engineer?"),
    (89, "EMP004", "Can Sneha Iyer share source code with an external technology vendor?"),
    (90, "EMP005", "Can Vikram Nair share source code with an external technology vendor?"),
    (91, "EMP022", "Can a Legal Director in the EU share privileged legal data with an external legal vendor?"),
    (92, "EMP023", "Can a Legal Intern in the EU share standard legal documents externally?"),
    (93, "EMP014", "Can a Finance Manager in India share financial records with an approved vendor?"),
    (94, "EMP013", "Can a Financial Analyst in India share financial records with an approved vendor?"),
    (95, "EMP016", "Can an EU Senior Engineer share anonymized engineering telemetry with an external vendor?"),
    (96, "EMP009", "Can an EU Data Scientist share anonymized customer data while an India Senior Analyst cannot share raw customer data?"),
    (97, "EMP005", "Does L4 authority automatically allow an employee to share every type of data?"),
    (98, "EMP001", "Does the same L2 hierarchy have the same data-sharing authority in every region?"),
    (99, "EMP001", "Does job title alone determine data-sharing authority?"),
    (100, "EMP003", "Can the agent approve this data-sharing request when the employee's role, hierarchy, and region conflict? Rahul Verma — Senior Engineer — L1-JUNIOR — India — Customer Data."),
]


async def run_test(client: httpx.AsyncClient, test_num: int, employee_id: str, prompt: str) -> dict:
    """Run a single test case and return the result."""
    payload = {
        "question": prompt,
        "employee_id": employee_id,
        "history": []
    }
    
    try:
        response = await client.post(API_URL, json=payload, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        return {
            "test_num": test_num,
            "employee_id": employee_id,
            "prompt": prompt,
            "decision": data.get("decision", "N/A"),
            "answer": data.get("answer", "No answer returned"),
            "thinking_context": data.get("thinking_context", ""),
            "applicable_policies": data.get("applicable_policies", []),
            "missing_context": data.get("missing_context", []),
            "conflicts": data.get("conflicts", []),
            "escalation_required": data.get("escalation_required", False),
            "error": None,
        }
    except Exception as e:
        return {
            "test_num": test_num,
            "employee_id": employee_id,
            "prompt": prompt,
            "decision": "ERROR",
            "answer": f"Error: {str(e)}",
            "thinking_context": "",
            "applicable_policies": [],
            "missing_context": [],
            "conflicts": [],
            "escalation_required": False,
            "error": str(e),
        }


async def main():
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_results.txt")
    total = len(TEST_CASES)
    results = []
    
    print(f"Starting {total} test cases against PolarisV2 Agent...")
    print(f"Results will be saved to: {output_path}")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        for i, (test_num, employee_id, prompt) in enumerate(TEST_CASES):
            print(f"[{i+1}/{total}] Running Test Case {test_num:03d} (Employee: {employee_id})...")
            start_time = time.time()
            
            result = await run_test(client, test_num, employee_id, prompt)
            elapsed = time.time() - start_time
            result["elapsed_seconds"] = round(elapsed, 2)
            results.append(result)
            
            status = "OK" if result["error"] is None else "ERROR"
            print(f"         -> {status} | Decision: {result['decision']} | {elapsed:.1f}s")
    
    # Write results to file
    print("\n" + "=" * 70)
    print(f"Writing results to {output_path}...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("POLARISV2 POLICY REASONING AGENT — TEST RESULTS\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Test Cases: {total}\n")
        
        errors = sum(1 for r in results if r["error"] is not None)
        f.write(f"Successful: {total - errors}\n")
        f.write(f"Errors: {errors}\n")
        f.write("=" * 80 + "\n\n")
        
        for r in results:
            f.write("-" * 80 + "\n")
            f.write(f"TEST CASE {r['test_num']:03d}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Employee ID: {r['employee_id']}\n")
            f.write(f"Prompt: {r['prompt']}\n")
            f.write(f"Time: {r['elapsed_seconds']}s\n\n")
            f.write(f"Decision: {r['decision']}\n\n")
            f.write(f"Agent Response:\n{r['answer']}\n\n")
            
            if r['applicable_policies']:
                f.write(f"Applicable Policies:\n")
                for p in r['applicable_policies']:
                    f.write(f"  - {p}\n")
                f.write("\n")
            
            if r['missing_context']:
                f.write(f"Missing Context: {r['missing_context']}\n\n")
            
            if r['conflicts']:
                f.write(f"Conflicts: {r['conflicts']}\n\n")
            
            if r['escalation_required']:
                f.write(f"Escalation Required: Yes\n\n")
            
            if r['error']:
                f.write(f"ERROR: {r['error']}\n\n")
            
            f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("END OF TEST RESULTS\n")
        f.write("=" * 80 + "\n")
    
    print(f"Done! Results saved to: {output_path}")
    print(f"Summary: {total - errors}/{total} successful, {errors} errors")


if __name__ == "__main__":
    asyncio.run(main())
