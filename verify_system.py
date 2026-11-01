"""
verify_system.py - In-process verification test suite using Flask Test Client.
Tests all pages, CRUD operations, AI assistant, and CSV export.
"""

import json
from app import app
from database import query_one

def run_tests():
    client = app.test_client()
    passed = 0
    failed = 0

    def assert_eq(test_name, condition, details=""):
        nonlocal passed, failed
        if condition:
            print(f"  ✅ [PASS] {test_name}")
            passed += 1
        else:
            print(f"  ❌ [FAIL] {test_name} - {details}")
            failed += 1

    print("\n--- 1. Testing Page Routes ---")
    for path in ['/', '/dashboard', '/projects', '/tasks', '/team', '/ai-assistant', '/analytics']:
        res = client.get(path, follow_redirects=True)
        assert_eq(f"GET {path}", res.status_code == 200, f"Status: {res.status_code}")

    print("\n--- 2. Testing Dashboard API ---")
    res = client.get('/api/dashboard')
    data = json.loads(res.data)
    assert_eq("GET /api/dashboard status 200", res.status_code == 200)
    assert_eq("Dashboard metrics present", data.get('success') and 'metrics' in data)
    assert_eq("Dynamic project count > 0", data['metrics']['total_projects'] >= 6)
    assert_eq("Upcoming deadlines loaded", len(data.get('upcoming_deadlines', [])) > 0)
    assert_eq("Recent activities loaded", len(data.get('recent_activities', [])) > 0)

    print("\n--- 3. Testing Projects CRUD ---")
    # GET
    res = client.get('/api/projects')
    data = json.loads(res.data)
    assert_eq("GET /api/projects", res.status_code == 200 and len(data['projects']) >= 6)

    # POST (Create)
    new_proj = {
        "name": "Automated Smoke Test Project",
        "description": "Integration testing project",
        "status": "In Progress",
        "priority": "High",
        "start_date": "2026-11-01",
        "end_date": "2026-12-01",
        "budget": 15000,
        "lead_id": 1,
        "member_ids": [1, 2]
    }
    res = client.post('/api/projects', json=new_proj)
    data = json.loads(res.data)
    assert_eq("POST /api/projects", res.status_code == 201 and data.get('success'))
    new_proj_id = data.get('project_id')

    # GET Single
    res = client.get(f'/api/projects/{new_proj_id}')
    data = json.loads(res.data)
    assert_eq("GET /api/projects/<id>", res.status_code == 200 and data['project']['name'] == "Automated Smoke Test Project")

    # PUT (Update)
    new_proj['name'] = "Automated Smoke Test Project (Updated)"
    res = client.put(f'/api/projects/{new_proj_id}', json=new_proj)
    data = json.loads(res.data)
    assert_eq("PUT /api/projects/<id>", res.status_code == 200 and data.get('success'))

    print("\n--- 4. Testing Tasks CRUD ---")
    # POST
    new_task = {
        "title": "Verify OAuth2 Refresh Cycle",
        "description": "Unit test for token revocation",
        "project_id": new_proj_id,
        "assigned_to": 1,
        "status": "In Progress",
        "priority": "Urgent",
        "due_date": "2026-11-05",
        "estimated_hours": 8.0
    }
    res = client.post('/api/tasks', json=new_task)
    data = json.loads(res.data)
    assert_eq("POST /api/tasks", res.status_code == 201 and data.get('success'))
    task_id = data.get('task_id')

    # PUT (Move to Completed)
    new_task['status'] = 'Completed'
    res = client.put(f'/api/tasks/{task_id}', json=new_task)
    data = json.loads(res.data)
    assert_eq("PUT /api/tasks/<id> (Completed)", res.status_code == 200 and data.get('success'))

    # Verify project progress percentage recalculated dynamically
    res = client.get(f'/api/projects/{new_proj_id}')
    data = json.loads(res.data)
    assert_eq("Project progress % dynamically calculated", data['project']['progress_pct'] == 100.0)

    # DELETE Task
    res = client.delete(f'/api/tasks/{task_id}')
    assert_eq("DELETE /api/tasks/<id>", res.status_code == 200)

    # DELETE Project
    res = client.delete(f'/api/projects/{new_proj_id}')
    assert_eq("DELETE /api/projects/<id>", res.status_code == 200)

    print("\n--- 5. Testing Team Management API ---")
    res = client.get('/api/team')
    data = json.loads(res.data)
    assert_eq("GET /api/team", res.status_code == 200 and len(data['team']) >= 6)

    new_member = {
        "name": "Morgan Bailey",
        "email": "morgan.bailey@nexus.ai",
        "role": "Security Operations Lead",
        "department": "Engineering",
        "phone": "+1 (555) 999-1122",
        "status": "Active",
        "avatar": ""
    }
    res = client.post('/api/team', json=new_member)
    data = json.loads(res.data)
    assert_eq("POST /api/team", res.status_code == 201 and data.get('success'))
    mem_id = data.get('member_id')

    # Clean up test member
    res = client.delete(f'/api/team/{mem_id}')
    assert_eq("DELETE /api/team/<id>", res.status_code == 200)

    print("\n--- 6. Testing AI Engine & Chatbot ---")
    res = client.post('/api/ai/analyze')
    data = json.loads(res.data)
    assert_eq("POST /api/ai/analyze", res.status_code == 200 and data.get('success'))
    assert_eq("AI detected delayed projects", len(data['project_analysis']['delayed_projects']) > 0)
    assert_eq("AI produced task recommendations", len(data['task_recommendations']) > 0)
    assert_eq("AI predicted deadline slippage", len(data['deadline_predictions']) > 0)

    # Chatbot queries
    chat_queries = [
        "Which projects are currently delayed?",
        "Which tasks have the highest priority?",
        "What is our overall project completion rate?",
        "Which project needs immediate attention?",
        "Who on the team has the heaviest workload?"
    ]
    for q in chat_queries:
        res = client.post('/api/ai/chat', json={"message": q})
        data = json.loads(res.data)
        assert_eq(f'AI Chat: "{q}"', res.status_code == 200 and 'answer' in data.get('response', {}))

    print("\n--- 7. Testing CSV Exports ---")
    for exp_type in ['projects', 'tasks', 'team', 'delayed']:
        res = client.get(f'/api/export/{exp_type}')
        assert_eq(f"GET /api/export/{exp_type}", res.status_code == 200 and 'text/csv' in res.content_type)

    print("\n=======================================================")
    print(f"Test Summary: {passed} PASSED, {failed} FAILED")
    print("=======================================================\n")
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
