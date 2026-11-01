"""
app.py - Main Flask Application for AI-Powered Software Management System.
Connects SQLite directly via parameterized queries, serves REST API endpoints,
and delivers modern HTML/CSS/JS frontend views.
"""

import os
import io
import csv
from datetime import datetime, date
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    session, Response, send_file, send_from_directory
)
from werkzeug.security import check_password_hash, generate_password_hash
from database import (
    get_db, query_all, query_one, execute_commit, record_activity, DB_PATH
)
from init_db import init_database, seed_demo_data
import ai_engine

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'nexus-software-management-super-secret-key-2026')

# Auto-initialize database on application startup
with app.app_context():
    init_database()
    seed_demo_data()


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def get_current_user():
    """Returns currently authenticated user from session or default demo admin."""
    user_id = session.get('user_id')
    if user_id:
        user = query_one("SELECT id, username, email, full_name, role, avatar FROM users WHERE id = ?", (user_id,))
        if user:
            return user
    # Fallback to default demo administrator
    admin = query_one("SELECT id, username, email, full_name, role, avatar FROM users WHERE username = 'admin'")
    return admin or {"id": 1, "username": "admin", "full_name": "Alex Vance", "role": "admin"}


# ---------------------------------------------------------
# Web Page Routes
# ---------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('dashboard_view'))


@app.route('/dashboard')
def dashboard_view():
    user = get_current_user()
    return render_template('dashboard.html', active_page='dashboard', user=user)


@app.route('/projects')
def projects_view():
    user = get_current_user()
    return render_template('projects.html', active_page='projects', user=user)


@app.route('/tasks')
def tasks_view():
    user = get_current_user()
    return render_template('tasks.html', active_page='tasks', user=user)


@app.route('/team')
def team_view():
    user = get_current_user()
    return render_template('team.html', active_page='team', user=user)


@app.route('/ai-assistant')
def ai_assistant_view():
    user = get_current_user()
    return render_template('ai_assistant.html', active_page='ai-assistant', user=user)


@app.route('/analytics')
@app.route('/reports')
def analytics_view():
    user = get_current_user()
    return render_template('analytics.html', active_page='analytics', user=user)


# ---------------------------------------------------------
# Authentication API
# ---------------------------------------------------------

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    user = query_one("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        record_activity('user_login', f"User {user['username']} logged in successfully", user['full_name'], 'auth', user['id'])
        return jsonify({
            "success": True,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "full_name": user['full_name'],
                "role": user['role'],
                "avatar": user['avatar']
            }
        })

    return jsonify({"success": False, "error": "Invalid username or password"}), 401


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    username = session.get('username', 'User')
    session.clear()
    record_activity('user_logout', f"{username} logged out", username, 'auth')
    return jsonify({"success": True})


@app.route('/api/auth/me', methods=['GET'])
def api_me():
    user = get_current_user()
    return jsonify({"success": True, "user": user})


# ---------------------------------------------------------
# Dashboard API
# ---------------------------------------------------------

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    # 1. Project stats
    total_projects = query_one("SELECT COUNT(*) as c FROM projects")['c']
    active_projects = query_one("SELECT COUNT(*) as c FROM projects WHERE status = 'In Progress'")['c']
    completed_projects = query_one("SELECT COUNT(*) as c FROM projects WHERE status = 'Completed'")['c']
    on_hold_projects = query_one("SELECT COUNT(*) as c FROM projects WHERE status = 'On Hold'")['c']
    not_started_projects = query_one("SELECT COUNT(*) as c FROM projects WHERE status = 'Not Started'")['c']

    # 2. Task stats
    total_tasks = query_one("SELECT COUNT(*) as c FROM tasks")['c']
    completed_tasks = query_one("SELECT COUNT(*) as c FROM tasks WHERE status = 'Completed'")['c']
    pending_tasks = total_tasks - completed_tasks
    in_progress_tasks = query_one("SELECT COUNT(*) as c FROM tasks WHERE status = 'In Progress'")['c']
    todo_tasks = query_one("SELECT COUNT(*) as c FROM tasks WHERE status = 'To Do'")['c']
    review_tasks = query_one("SELECT COUNT(*) as c FROM tasks WHERE status = 'Review'")['c']

    # 3. Team stats
    total_team = query_one("SELECT COUNT(*) as c FROM team_members")['c']

    # 4. Overall project progress calculation
    overall_progress_pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # 5. Project status distribution
    project_status_counts = {
        "In Progress": active_projects,
        "Completed": completed_projects,
        "Not Started": not_started_projects,
        "On Hold": on_hold_projects
    }

    # 6. Task priority distribution
    task_priorities = query_all("""
        SELECT priority, COUNT(*) as count 
        FROM tasks 
        GROUP BY priority
    """)
    priority_map = {"Urgent": 0, "High": 0, "Medium": 0, "Low": 0}
    for tp in task_priorities:
        priority_map[tp['priority']] = tp['count']

    # 7. Recent activities
    activities = query_all("SELECT * FROM activities ORDER BY created_at DESC LIMIT 8")

    # 8. Upcoming deadlines
    upcoming_deadlines = query_all("""
        SELECT t.id, t.title, t.due_date, t.priority, t.status, p.name as project_name, m.name as assignee_name
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        LEFT JOIN team_members m ON t.assigned_to = m.id
        WHERE t.status != 'Completed'
        ORDER BY t.due_date ASC
        LIMIT 6
    """)

    # 9. Quick AI alert summary
    ai_analysis = ai_engine.analyze_all_projects()

    return jsonify({
        "success": True,
        "metrics": {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "on_hold_projects": on_hold_projects,
            "not_started_projects": not_started_projects,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "todo_tasks": todo_tasks,
            "review_tasks": review_tasks,
            "total_team_members": total_team,
            "overall_progress_pct": overall_progress_pct
        },
        "charts": {
            "project_status": project_status_counts,
            "task_priority": priority_map,
            "task_status": {
                "To Do": todo_tasks,
                "In Progress": in_progress_tasks,
                "Review": review_tasks,
                "Completed": completed_tasks
            }
        },
        "recent_activities": activities,
        "upcoming_deadlines": upcoming_deadlines,
        "ai_alert": {
            "delayed_count": ai_analysis['delayed_count'],
            "critical_count": ai_analysis['critical_count'],
            "status": ai_analysis['system_status']
        }
    })


# ---------------------------------------------------------
# Projects API (CRUD)
# ---------------------------------------------------------

@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    search = request.args.get('search', '').strip()

    sql = """
        SELECT p.*, 
               m.name as lead_name, m.avatar as lead_avatar,
               (SELECT COUNT(*) FROM tasks WHERE project_id = p.id) as total_tasks,
               (SELECT COUNT(*) FROM tasks WHERE project_id = p.id AND status = 'Completed') as completed_tasks
        FROM projects p
        LEFT JOIN team_members m ON p.lead_id = m.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != 'All':
        sql += " AND p.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != 'All':
        sql += " AND p.priority = ?"
        params.append(priority_filter)

    if search:
        sql += " AND (p.name LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += " ORDER BY p.id DESC"
    projects = query_all(sql, params)

    # Calculate progress % and fetch assigned members for each project
    for p in projects:
        total = p['total_tasks']
        done = p['completed_tasks']
        p['progress_pct'] = round((done / total * 100), 1) if total > 0 else (100.0 if p['status'] == 'Completed' else 0.0)

        # Assigned members
        members = query_all("""
            SELECT m.id, m.name, m.role, m.avatar 
            FROM project_members pm
            JOIN team_members m ON pm.member_id = m.id
            WHERE pm.project_id = ?
        """, (p['id'],))
        p['members'] = members

    return jsonify({"success": True, "projects": projects})


@app.route('/api/projects', methods=['POST'])
def api_create_project():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    status = data.get('status', 'In Progress')
    priority = data.get('priority', 'Medium')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    budget = float(data.get('budget', 0) or 0)
    lead_id = data.get('lead_id') or None
    member_ids = data.get('member_ids', [])

    if not name or not start_date or not end_date:
        return jsonify({"success": False, "error": "Project name, start date, and end date are required"}), 400

    user = get_current_user()

    res = execute_commit(
        """
        INSERT INTO projects (name, description, status, priority, start_date, end_date, budget, lead_id, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, description, status, priority, start_date, end_date, budget, lead_id, user.get('id', 1))
    )
    project_id = res['lastrowid']

    # Insert project members
    if member_ids:
        for mid in member_ids:
            execute_commit("INSERT OR IGNORE INTO project_members (project_id, member_id) VALUES (?, ?)", (project_id, mid))

    record_activity('project_created', f'Created project "{name}"', user.get('full_name', 'Admin'), 'project', project_id)

    return jsonify({"success": True, "project_id": project_id, "message": "Project created successfully"}), 201


@app.route('/api/projects/<int:project_id>', methods=['GET'])
def api_get_project(project_id):
    project = query_one("""
        SELECT p.*, m.name as lead_name, m.avatar as lead_avatar, m.role as lead_role
        FROM projects p
        LEFT JOIN team_members m ON p.lead_id = m.id
        WHERE p.id = ?
    """, (project_id,))

    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404

    # Fetch tasks
    tasks = query_all("""
        SELECT t.*, m.name as assignee_name, m.avatar as assignee_avatar, m.role as assignee_role
        FROM tasks t
        LEFT JOIN team_members m ON t.assigned_to = m.id
        WHERE t.project_id = ?
        ORDER BY t.due_date ASC
    """, (project_id,))

    # Fetch members
    members = query_all("""
        SELECT m.id, m.name, m.role, m.avatar, m.email
        FROM project_members pm
        JOIN team_members m ON pm.member_id = m.id
        WHERE pm.project_id = ?
    """, (project_id,))

    total = len(tasks)
    done = len([t for t in tasks if t['status'] == 'Completed'])
    project['total_tasks'] = total
    project['completed_tasks'] = done
    project['progress_pct'] = round((done / total * 100), 1) if total > 0 else (100.0 if project['status'] == 'Completed' else 0.0)
    project['tasks'] = tasks
    project['members'] = members

    return jsonify({"success": True, "project": project})


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def api_update_project(project_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    status = data.get('status', 'In Progress')
    priority = data.get('priority', 'Medium')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    budget = float(data.get('budget', 0) or 0)
    lead_id = data.get('lead_id') or None
    member_ids = data.get('member_ids')

    if not name or not start_date or not end_date:
        return jsonify({"success": False, "error": "Name, start date, and end date are required"}), 400

    execute_commit(
        """
        UPDATE projects
        SET name = ?, description = ?, status = ?, priority = ?, start_date = ?, end_date = ?, budget = ?, lead_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (name, description, status, priority, start_date, end_date, budget, lead_id, project_id)
    )

    if member_ids is not None:
        execute_commit("DELETE FROM project_members WHERE project_id = ?", (project_id,))
        for mid in member_ids:
            execute_commit("INSERT OR IGNORE INTO project_members (project_id, member_id) VALUES (?, ?)", (project_id, mid))

    user = get_current_user()
    record_activity('project_updated', f'Updated project "{name}" (Status: {status})', user.get('full_name', 'Admin'), 'project', project_id)

    return jsonify({"success": True, "message": "Project updated successfully"})


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    project = query_one("SELECT name FROM projects WHERE id = ?", (project_id,))
    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404

    execute_commit("DELETE FROM projects WHERE id = ?", (project_id,))
    user = get_current_user()
    record_activity('project_deleted', f'Deleted project "{project["name"]}"', user.get('full_name', 'Admin'), 'project', project_id)

    return jsonify({"success": True, "message": "Project deleted successfully"})


# ---------------------------------------------------------
# Tasks API (CRUD)
# ---------------------------------------------------------

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    project_id = request.args.get('project_id')
    status = request.args.get('status')
    priority = request.args.get('priority')
    assigned_to = request.args.get('assigned_to')
    search = request.args.get('search', '').strip()

    sql = """
        SELECT t.*, p.name as project_name, 
               m.name as assignee_name, m.avatar as assignee_avatar, m.role as assignee_role
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        LEFT JOIN team_members m ON t.assigned_to = m.id
        WHERE 1=1
    """
    params = []

    if project_id and project_id != 'All':
        sql += " AND t.project_id = ?"
        params.append(project_id)

    if status and status != 'All':
        sql += " AND t.status = ?"
        params.append(status)

    if priority and priority != 'All':
        sql += " AND t.priority = ?"
        params.append(priority)

    if assigned_to and assigned_to != 'All':
        sql += " AND t.assigned_to = ?"
        params.append(assigned_to)

    if search:
        sql += " AND (t.title LIKE ? OR t.description LIKE ? OR p.name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    sql += " ORDER BY t.due_date ASC, t.id DESC"
    tasks = query_all(sql, params)

    return jsonify({"success": True, "tasks": tasks})


@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    project_id = data.get('project_id')
    assigned_to = data.get('assigned_to') or None
    status = data.get('status', 'To Do')
    priority = data.get('priority', 'Medium')
    due_date = data.get('due_date')
    estimated_hours = float(data.get('estimated_hours', 0) or 0)

    if not title or not project_id or not due_date:
        return jsonify({"success": False, "error": "Task title, project, and due date are required"}), 400

    completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'Completed' else None

    res = execute_commit(
        """
        INSERT INTO tasks (title, description, project_id, assigned_to, status, priority, due_date, estimated_hours, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, project_id, assigned_to, status, priority, due_date, estimated_hours, completed_at)
    )
    task_id = res['lastrowid']

    user = get_current_user()
    record_activity('task_created', f'Created task "{title}"', user.get('full_name', 'Admin'), 'task', task_id)

    return jsonify({"success": True, "task_id": task_id, "message": "Task created successfully"}), 201


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def api_get_task(task_id):
    task = query_one("""
        SELECT t.*, p.name as project_name, m.name as assignee_name, m.avatar as assignee_avatar
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        LEFT JOIN team_members m ON t.assigned_to = m.id
        WHERE t.id = ?
    """, (task_id,))

    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404

    return jsonify({"success": True, "task": task})


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_update_task(task_id):
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    project_id = data.get('project_id')
    assigned_to = data.get('assigned_to') or None
    status = data.get('status', 'To Do')
    priority = data.get('priority', 'Medium')
    due_date = data.get('due_date')
    estimated_hours = float(data.get('estimated_hours', 0) or 0)

    if not title or not project_id or not due_date:
        return jsonify({"success": False, "error": "Title, project, and due date are required"}), 400

    # Fetch existing task to check status changes
    old_task = query_one("SELECT status, title FROM tasks WHERE id = ?", (task_id,))
    completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'Completed' else None

    execute_commit(
        """
        UPDATE tasks
        SET title = ?, description = ?, project_id = ?, assigned_to = ?, status = ?, priority = ?, due_date = ?, estimated_hours = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (title, description, project_id, assigned_to, status, priority, due_date, estimated_hours, completed_at, task_id)
    )

    user = get_current_user()
    if old_task and old_task['status'] != status:
        if status == 'Completed':
            record_activity('task_completed', f'Completed task "{title}"', user.get('full_name', 'Admin'), 'task', task_id)
        else:
            record_activity('status_changed', f'Changed task "{title}" status to {status}', user.get('full_name', 'Admin'), 'task', task_id)
    else:
        record_activity('task_updated', f'Updated task "{title}"', user.get('full_name', 'Admin'), 'task', task_id)

    return jsonify({"success": True, "message": "Task updated successfully"})


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    task = query_one("SELECT title FROM tasks WHERE id = ?", (task_id,))
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404

    execute_commit("DELETE FROM tasks WHERE id = ?", (task_id,))
    user = get_current_user()
    record_activity('task_deleted', f'Deleted task "{task["title"]}"', user.get('full_name', 'Admin'), 'task', task_id)

    return jsonify({"success": True, "message": "Task deleted successfully"})


# ---------------------------------------------------------
# Team Management API (CRUD)
# ---------------------------------------------------------

@app.route('/api/team', methods=['GET'])
def api_get_team():
    team = query_all("SELECT * FROM team_members ORDER BY id ASC")
    
    # Calculate task stats for each member
    for m in team:
        m_tasks = query_all("SELECT status FROM tasks WHERE assigned_to = ?", (m['id'],))
        total = len(m_tasks)
        done = len([t for t in m_tasks if t['status'] == 'Completed'])
        m['total_tasks'] = total
        m['completed_tasks'] = done
        m['active_tasks'] = total - done
        m['completion_rate'] = round((done / total * 100), 1) if total > 0 else 0.0

        # Assigned projects
        projs = query_all("""
            SELECT p.id, p.name 
            FROM project_members pm
            JOIN projects p ON pm.project_id = p.id
            WHERE pm.member_id = ?
        """, (m['id'],))
        m['projects'] = projs

    return jsonify({"success": True, "team": team})


@app.route('/api/team', methods=['POST'])
def api_create_member():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', '').strip()
    department = data.get('department', 'Engineering').strip()
    phone = data.get('phone', '').strip()
    status = data.get('status', 'Active')
    avatar = data.get('avatar', '').strip()

    if not name or not email or not role:
        return jsonify({"success": False, "error": "Name, email, and role are required"}), 400

    if not avatar:
        avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}"

    try:
        res = execute_commit(
            """
            INSERT INTO team_members (name, email, role, department, phone, status, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, email, role, department, phone, status, avatar)
        )
        member_id = res['lastrowid']
        user = get_current_user()
        record_activity('team_added', f'Added new team member {name} ({role})', user.get('full_name', 'Admin'), 'team', member_id)
        return jsonify({"success": True, "member_id": member_id, "message": "Team member added successfully"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/team/<int:member_id>', methods=['GET'])
def api_get_member(member_id):
    member = query_one("SELECT * FROM team_members WHERE id = ?", (member_id,))
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    tasks = query_all("""
        SELECT t.*, p.name as project_name
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE t.assigned_to = ?
        ORDER BY t.due_date ASC
    """, (member_id,))

    member['tasks'] = tasks
    return jsonify({"success": True, "member": member})


@app.route('/api/team/<int:member_id>', methods=['PUT'])
def api_update_member(member_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', '').strip()
    department = data.get('department', 'Engineering').strip()
    phone = data.get('phone', '').strip()
    status = data.get('status', 'Active')
    avatar = data.get('avatar', '').strip()

    if not name or not email or not role:
        return jsonify({"success": False, "error": "Name, email, and role are required"}), 400

    execute_commit(
        """
        UPDATE team_members
        SET name = ?, email = ?, role = ?, department = ?, phone = ?, status = ?, avatar = ?
        WHERE id = ?
        """,
        (name, email, role, department, phone, status, avatar, member_id)
    )

    user = get_current_user()
    record_activity('team_updated', f'Updated profile for {name}', user.get('full_name', 'Admin'), 'team', member_id)

    return jsonify({"success": True, "message": "Team member updated successfully"})


@app.route('/api/team/<int:member_id>', methods=['DELETE'])
def api_delete_member(member_id):
    member = query_one("SELECT name FROM team_members WHERE id = ?", (member_id,))
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    execute_commit("DELETE FROM team_members WHERE id = ?", (member_id,))
    user = get_current_user()
    record_activity('team_deleted', f'Removed team member {member["name"]}', user.get('full_name', 'Admin'), 'team', member_id)

    return jsonify({"success": True, "message": "Team member deleted successfully"})


# ---------------------------------------------------------
# AI Features API
# ---------------------------------------------------------

@app.route('/api/ai/analyze', methods=['POST', 'GET'])
def api_ai_analyze():
    project_analysis = ai_engine.analyze_all_projects()
    task_recommendations = ai_engine.get_task_recommendations()
    deadline_predictions = ai_engine.predict_deadlines()
    productivity_insights = ai_engine.get_productivity_insights()

    return jsonify({
        "success": True,
        "project_analysis": project_analysis,
        "task_recommendations": task_recommendations,
        "deadline_predictions": deadline_predictions,
        "productivity_insights": productivity_insights
    })


@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    reply = ai_engine.answer_ai_query(message)
    return jsonify({
        "success": True,
        "response": reply
    })


# ---------------------------------------------------------
# Reports & Analytics API
# ---------------------------------------------------------

@app.route('/api/reports', methods=['GET'])
def api_get_reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Base projects
    p_sql = "SELECT * FROM projects WHERE 1=1"
    p_params = []
    if start_date:
        p_sql += " AND start_date >= ?"
        p_params.append(start_date)
    if end_date:
        p_sql += " AND end_date <= ?"
        p_params.append(end_date)
    
    projects = query_all(p_sql, p_params)
    tasks = query_all("SELECT * FROM tasks")

    # Metrics
    project_reports = []
    delayed_projects = []
    today = ai_engine.get_current_date()

    for p in projects:
        m = ai_engine.calculate_project_metrics(p, tasks)
        project_reports.append(m)
        if m['is_overdue'] or m['risk_level'] == 'Critical':
            delayed_projects.append(m)

    # Monthly performance
    monthly_tasks = query_all("""
        SELECT strftime('%Y-%m', completed_at) as month, COUNT(*) as count
        FROM tasks
        WHERE status = 'Completed' AND completed_at IS NOT NULL
        GROUP BY month
        ORDER BY month ASC
    """)

    # Team productivity
    prod = ai_engine.get_productivity_insights()

    return jsonify({
        "success": True,
        "project_reports": project_reports,
        "delayed_projects": delayed_projects,
        "team_productivity": prod['member_stats'],
        "monthly_velocity": monthly_tasks,
        "overall_completion_rate": prod['overall_completion_rate']
    })


# ---------------------------------------------------------
# CSV Data Export API
# ---------------------------------------------------------

@app.route('/api/export/<string:export_type>', methods=['GET'])
def api_export_csv(export_type):
    output = io.StringIO()
    writer = csv.writer(output)

    if export_type == 'projects':
        writer.writerow(['Project ID', 'Name', 'Status', 'Priority', 'Start Date', 'End Date', 'Budget ($)', 'Total Tasks', 'Completed Tasks'])
        projects = query_all("""
            SELECT p.id, p.name, p.status, p.priority, p.start_date, p.end_date, p.budget,
                   (SELECT COUNT(*) FROM tasks WHERE project_id = p.id) as total_tasks,
                   (SELECT COUNT(*) FROM tasks WHERE project_id = p.id AND status = 'Completed') as completed_tasks
            FROM projects p
        """)
        for p in projects:
            writer.writerow([p['id'], p['name'], p['status'], p['priority'], p['start_date'], p['end_date'], p['budget'], p['total_tasks'], p['completed_tasks']])
        filename = f"projects_export_{date.today()}.csv"

    elif export_type == 'tasks':
        writer.writerow(['Task ID', 'Title', 'Project', 'Assignee', 'Status', 'Priority', 'Due Date', 'Estimated Hours'])
        tasks = query_all("""
            SELECT t.id, t.title, p.name as project_name, m.name as assignee_name, t.status, t.priority, t.due_date, t.estimated_hours
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN team_members m ON t.assigned_to = m.id
        """)
        for t in tasks:
            writer.writerow([t['id'], t['title'], t['project_name'], t['assignee_name'] or 'Unassigned', t['status'], t['priority'], t['due_date'], t['estimated_hours']])
        filename = f"tasks_export_{date.today()}.csv"

    elif export_type == 'team':
        writer.writerow(['Member ID', 'Name', 'Email', 'Role', 'Department', 'Phone', 'Status', 'Assigned Tasks', 'Completed Tasks'])
        team = query_all("SELECT * FROM team_members")
        for m in team:
            tasks = query_all("SELECT status FROM tasks WHERE assigned_to = ?", (m['id'],))
            total = len(tasks)
            done = len([t for t in tasks if t['status'] == 'Completed'])
            writer.writerow([m['id'], m['name'], m['email'], m['role'], m['department'], m['phone'] or '', m['status'], total, done])
        filename = f"team_productivity_export_{date.today()}.csv"

    elif export_type == 'delayed':
        writer.writerow(['Project ID', 'Project Name', 'Priority', 'Status', 'Target Deadline', 'Days Overdue', 'Health Score', 'Completed Tasks', 'Total Tasks'])
        analysis = ai_engine.analyze_all_projects()
        for dp in analysis['delayed_projects']:
            writer.writerow([dp['project_id'], dp['name'], dp['priority'], dp['status'], dp['end_date'], abs(dp['days_remaining']), dp['health_score'], dp['completed_tasks'], dp['total_tasks']])
        filename = f"delayed_projects_audit_{date.today()}.csv"

    else:
        return jsonify({"success": False, "error": "Invalid export type"}), 400

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ---------------------------------------------------------
# Static File Fallback
# ---------------------------------------------------------

@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"\n=======================================================")
    print(f"🚀 NexusAI Software Management System running on:")
    print(f"   👉 http://127.0.0.1:{port}")
    print(f"   👉 http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)
