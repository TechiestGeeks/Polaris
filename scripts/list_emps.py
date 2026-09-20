import json
data = json.load(open('data/employees.json', 'r', encoding='utf-8'))
for e in data:
    print(f"{e['employee_id']} | {e['name']} | {e['role']} | {e['access_level']} | {e['region']}")
