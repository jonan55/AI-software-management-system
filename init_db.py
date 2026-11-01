"""
init_db.py - Initializes SQLite database schema and seeds initial demonstration data.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from database import DB_PATH, get_db_connection

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'admin',
    avatar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    avatar TEXT,
    phone TEXT,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'In Progress' CHECK(status IN ('Not Started', 'In Progress', 'Completed', 'On Hold')),
    priority TEXT NOT NULL DEFAULT 'Medium' CHECK(priority IN ('Low', 'Medium', 'High', 'Urgent')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget REAL DEFAULT 0.0,
    lead_id INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_members (
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, member_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES team_members(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'To Do' CHECK(status IN ('To Do', 'In Progress', 'Review', 'Completed')),
    priority TEXT NOT NULL DEFAULT 'Medium' CHECK(priority IN ('Low', 'Medium', 'High', 'Urgent')),
    due_date DATE NOT NULL,
    estimated_hours REAL DEFAULT 0.0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    user_name TEXT DEFAULT 'System',
    entity_type TEXT,
    entity_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_database():
    """Creates tables if they do not exist."""
    conn = get_db_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print("Database schema successfully verified and created.")
    finally:
        conn.close()


def seed_demo_data():
    """Seeds rich demo data if database is empty."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("Database already contains records. Skipping seed.")
            return

        print("Seeding initial demonstration data...")

        # 1. Users
        users = [
            ('admin', 'admin@nexus.ai', generate_password_hash('admin123'), 'Alex Vance', 'admin', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'),
            ('pm_sarah', 'sarah@nexus.ai', generate_password_hash('demo123'), 'Sarah Connor', 'project_manager', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80')
        ]
        cursor.executemany(
            "INSERT INTO users (username, email, password_hash, full_name, role, avatar) VALUES (?, ?, ?, ?, ?, ?)",
            users
        )

        # 2. Team Members
        team = [
            ('Alex Rivera', 'alex.rivera@nexus.ai', 'Senior Full-Stack Engineer', 'Engineering', 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&auto=format&fit=crop&q=80', '+1 (555) 234-5678', 'Active'),
            ('Sophia Chen', 'sophia.chen@nexus.ai', 'Lead AI & Machine Learning Scientist', 'Engineering', 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80', '+1 (555) 345-6789', 'Active'),
            ('Marcus Vance', 'marcus.vance@nexus.ai', 'Principal DevOps & Cloud Architect', 'DevOps', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80', '+1 (555) 456-7890', 'Active'),
            ('Elena Rostova', 'elena.rostova@nexus.ai', 'Senior UI/UX Product Designer', 'Design', 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150&auto=format&fit=crop&q=80', '+1 (555) 567-8901', 'Active'),
            ('Jordan Taylor', 'jordan.taylor@nexus.ai', 'Lead QA Automation Engineer', 'QA', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80', '+1 (555) 678-9012', 'Active'),
            ('Priya Patel', 'priya.patel@nexus.ai', 'Technical Product Manager', 'Product', 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80', '+1 (555) 789-0123', 'Active')
        ]
        cursor.executemany(
            "INSERT INTO team_members (name, email, role, department, avatar, phone, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            team
        )

        # 3. Projects
        # Current reference date: 2026-11-01
        projects = [
            (
                'Nexus AI Engine Core v2.0',
                'Next-generation cognitive inference pipeline, real-time context retrieval, and low-latency embeddings.',
                'In Progress',
                'Urgent',
                '2026-09-15',
                '2026-11-15',
                85000.0,
                2,  # Sophia Chen
                1
            ),
            (
                'Cloud Infrastructure Modernization',
                'Migrate monolithic services to auto-scaling Kubernetes clusters with zero-downtime blue/green deployment.',
                'In Progress',
                'High',
                '2026-10-01',
                '2026-11-25',
                52000.0,
                3,  # Marcus Vance
                1
            ),
            (
                'Mobile App Redesign (iOS & Android)',
                'Complete overhaul of mobile interfaces with modern micro-interactions, dark mode, and offline caching.',
                'In Progress',
                'Medium',
                '2026-10-15',
                '2026-12-10',
                38000.0,
                4,  # Elena Rostova
                1
            ),
            (
                'Enterprise SSO & RBAC Security Suite',
                'Implement SAML 2.0, OpenID Connect, multi-tenant RBAC policies, and real-time security audit trails.',
                'Completed',
                'High',
                '2026-08-01',
                '2026-10-28',
                30000.0,
                1,  # Alex Rivera
                1
            ),
            (
                'Legacy Billing & Subscription Migration',
                'Unify disparate Stripe and PayPal recurring billing engines into centralized idempotent billing ledger.',
                'Not Started',
                'High',
                '2026-11-10',
                '2026-12-28',
                45000.0,
                6,  # Priya Patel
                1
            ),
            (
                'Automated End-to-End Test Suite',
                'Build comprehensive Playwright and Cypress regression pipeline across all core microservices.',
                'In Progress',
                'Medium',
                '2026-09-20',
                '2026-10-30', # Past due date! Demonstrates delayed project identification
                22000.0,
                5,  # Jordan Taylor
                1
            )
        ]

        cursor.executemany(
            """
            INSERT INTO projects (name, description, status, priority, start_date, end_date, budget, lead_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            projects
        )

        # 4. Project Members assignments
        project_members = [
            (1, 2), (1, 1), (1, 5),  # AI Core: Sophia, Alex, Jordan
            (2, 3), (2, 1),          # Cloud: Marcus, Alex
            (3, 4), (3, 1), (3, 5),  # Mobile: Elena, Alex, Jordan
            (4, 1), (4, 3),          # SSO: Alex, Marcus
            (5, 6), (5, 1),          # Billing: Priya, Alex
            (6, 5), (6, 1)           # QA Suite: Jordan, Alex
        ]
        cursor.executemany(
            "INSERT INTO project_members (project_id, member_id) VALUES (?, ?)",
            project_members
        )

        # 5. Tasks
        # Current date: 2026-11-01
        tasks = [
            # Project 1: Nexus AI Engine Core v2.0 (Due 2026-11-15)
            ('Benchmark Vector Index Latency', 'Profile cosine similarity retrieval over 1M documents in SQLite vector extension.', 1, 2, 'Completed', 'High', '2026-10-20', 16.0, '2026-10-20 14:30:00'),
            ('Implement Streaming Chat Response API', 'Build Server-Sent Events (SSE) streaming endpoint for AI chat assistant.', 1, 1, 'Completed', 'Urgent', '2026-10-26', 14.0, '2026-10-25 17:00:00'),
            ('Calibrate Heuristic Task Urgency Weights', 'Fine-tune dynamic priority weights for deadline risk prediction model.', 1, 2, 'In Progress', 'Urgent', '2026-11-03', 12.0, None),
            ('Stress Test Concurrent Chat Threads', 'Simulate 500 simultaneous user sessions against rule-based engine.', 1, 5, 'To Do', 'High', '2026-11-08', 18.0, None),
            ('Document AI Prompt Fallback Protocols', 'Create comprehensive developer guide for rule-based vs LLM modes.', 1, 6, 'To Do', 'Medium', '2026-11-12', 8.0, None),

            # Project 2: Cloud Infrastructure Modernization (Due 2026-11-25)
            ('Provision Production EKS Cluster', 'Deploy multi-AZ Kubernetes cluster with Terraform and configure Cilium CNI.', 2, 3, 'Completed', 'High', '2026-10-18', 24.0, '2026-10-17 11:00:00'),
            ('Setup Prometheus & Grafana Dashboards', 'Configure cluster monitoring metrics, alertmanager routing and disk alerts.', 2, 3, 'In Progress', 'High', '2026-11-04', 16.0, None),
            ('Configure Blue-Green Ingress Routing', 'Set up ALB controller with traffic shifting for canary deployments.', 2, 1, 'Review', 'Urgent', '2026-11-06', 12.0, None),
            ('Implement Vault Secrets Injection', 'Replace environment variable secrets with dynamic HashiCorp Vault tokens.', 2, 3, 'To Do', 'Medium', '2026-11-18', 14.0, None),

            # Project 3: Mobile App Redesign (Due 2026-12-10)
            ('Design High-Fidelity Design System in Figma', 'Create typography scales, dark mode palettes, and icon sets.', 3, 4, 'Completed', 'High', '2026-10-25', 30.0, '2026-10-24 16:00:00'),
            ('Prototype Bottom Sheet Navigation', 'Build fluid gesture-based sheet modal for quick task editing.', 3, 4, 'In Progress', 'Medium', '2026-11-07', 15.0, None),
            ('Implement SQLite Offline Cache Layer', 'Enable local SQLite database persistence for mobile disconnected state.', 3, 1, 'To Do', 'High', '2026-11-20', 20.0, None),
            ('Run Usability Testing with Beta Users', 'Conduct 10 moderated testing sessions on task management workflows.', 3, 4, 'To Do', 'Low', '2026-12-02', 10.0, None),

            # Project 4: Enterprise SSO & RBAC Security Suite (Completed)
            ('Integrate Okta & Azure AD SAML Connectors', 'Implement XML assertion verification and metadata parsing.', 4, 1, 'Completed', 'High', '2026-09-15', 28.0, '2026-09-14 18:00:00'),
            ('Build Granular Permission Middleware', 'Decorate Flask routes with role-based authorization guards.', 4, 1, 'Completed', 'High', '2026-10-05', 18.0, '2026-10-04 15:30:00'),
            ('Implement Immutable Security Audit Log', 'Record login attempts, permission escalations, and API token generations.', 4, 3, 'Completed', 'Medium', '2026-10-18', 14.0, '2026-10-18 10:00:00'),
            ('Conduct Third-Party Penetration Test', 'Resolve vulnerabilities flagged in automated OWASP ZAP scan.', 4, 5, 'Completed', 'Urgent', '2026-10-26', 22.0, '2026-10-25 12:00:00'),

            # Project 5: Legacy Billing Migration (Not Started, Due 2026-12-28)
            ('Draft Database Schema for Multi-Currency Ledger', 'Model subscriptions, invoices, payment intents, and tax tables.', 5, 1, 'To Do', 'High', '2026-11-14', 16.0, None),
            ('Build Webhook Listeners for Stripe Events', 'Handle invoice.payment_succeeded and customer.subscription.deleted.', 5, 1, 'To Do', 'High', '2026-11-22', 14.0, None),
            ('Write Data Migration Script for Historical Subscriptions', 'Extract, transform and validate 50,000 legacy records into SQLite.', 5, 6, 'To Do', 'Medium', '2026-12-05', 25.0, None),

            # Project 6: Automated End-to-End Test Suite (Delayed - Due 2026-10-30, today is 2026-11-01)
            ('Configure Playwright CI Matrix Runner', 'Setup parallel execution across Chromium, Firefox, and WebKit.', 6, 5, 'Completed', 'High', '2026-10-10', 20.0, '2026-10-09 17:00:00'),
            ('Write Smoke Tests for Project Creation Flow', 'Cover modal validations, foreign key constraints, and error toasts.', 6, 5, 'Review', 'Urgent', '2026-10-28', 14.0, None), # Overdue!
            ('Implement Synthetic Test Data Generators', 'Create deterministic fixtures for tasks, deadlines, and members.', 6, 1, 'In Progress', 'High', '2026-10-30', 16.0, None)  # Overdue!
        ]

        cursor.executemany(
            """
            INSERT INTO tasks (title, description, project_id, assigned_to, status, priority, due_date, estimated_hours, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tasks
        )

        # 6. Activities
        activities = [
            ('project_created', 'Project "Nexus AI Engine Core v2.0" was initialized by Alex Vance', 'Alex Vance', 'project', 1),
            ('task_completed', 'Alex Rivera completed "Implement Streaming Chat Response API"', 'Alex Rivera', 'task', 2),
            ('task_completed', 'Elena Rostova finished "Design High-Fidelity Design System in Figma"', 'Elena Rostova', 'task', 10),
            ('status_changed', 'Task "Configure Blue-Green Ingress Routing" moved to Review', 'Marcus Vance', 'task', 8),
            ('status_changed', 'Project "Enterprise SSO & RBAC Security Suite" was marked Completed', 'Alex Vance', 'project', 4),
            ('task_created', 'New task "Calibrate Heuristic Task Urgency Weights" assigned to Sophia Chen', 'Sophia Chen', 'task', 3),
            ('team_added', 'Jordan Taylor joined the QA Engineering division', 'Alex Vance', 'team', 5),
            ('system_alert', 'AI Alert: Project "Automated End-to-End Test Suite" has passed its deadline (2026-10-30)', 'AI Assistant', 'project', 6)
        ]

        cursor.executemany(
            """
            INSERT INTO activities (action_type, description, user_name, entity_type, entity_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            activities
        )

        conn.commit()
        print("Demo data seeded successfully!")
    finally:
        conn.close()


if __name__ == '__main__':
    init_database()
    seed_demo_data()
