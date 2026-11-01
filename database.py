"""
database.py - SQLite Database Interface for AI-Powered Software Management System
Enforces foreign keys, provides parameterized query helpers, and handles connections.
"""

import sqlite3
import os
from contextlib import contextmanager
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'software_management.db')


def get_db_connection():
    """Returns a SQLite connection with foreign keys enabled and row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for SQLite connections with automatic commit/rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(query, args=()):
    """Executes a query and returns all rows as list of dicts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def query_one(query, args=()):
    """Executes a query and returns a single row as dict or None."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        row = cursor.fetchone()
        return dict(row) if row else None


def execute_commit(query, args=()):
    """Executes an INSERT, UPDATE, or DELETE query and returns lastrowid and rowcount."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        return {
            "lastrowid": cursor.lastrowid,
            "rowcount": cursor.rowcount
        }


def record_activity(action_type, description, user_name="Admin", entity_type=None, entity_id=None):
    """Logs system and user actions for audit and dashboard activity feed."""
    try:
        execute_commit(
            """
            INSERT INTO activities (action_type, description, user_name, entity_type, entity_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (action_type, description, user_name, entity_type, entity_id)
        )
    except Exception as e:
        print(f"Error logging activity: {e}")
