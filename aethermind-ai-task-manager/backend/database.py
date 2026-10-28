import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(__file__).resolve().parent / "aethermind.db"

def database_path() -> str:
    configured = os.getenv("DATABASE_PATH", "").strip()
    if not configured:
        return str(DEFAULT_DB)
    path = Path(configured)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)

def connect(db_path: str | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path or database_path(), timeout=10)
    connection.row_factory = sqlite3.Row
    return connection

def init_db(db_path: str | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_date TEXT NULL,
                priority TEXT NOT NULL CHECK(priority IN ('Low','Medium','High')),
                notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK(status IN ('Pending','Completed')),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
            )
        """)

def create_task(task: dict[str, Any], db_path: str | None = None) -> dict[str, Any]:
    init_db(db_path)
    due_date = task.get("due_date")
    due_date = due_date.isoformat() if hasattr(due_date, "isoformat") else due_date
    with connect(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO tasks(title,due_date,priority,notes,status)
               VALUES(?,?,?,?, 'Pending')""",
            (task["title"], due_date, task["priority"], task.get("notes", "")),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (cursor.lastrowid,)).fetchone()
        return dict(row)

def list_tasks(db_path: str | None = None) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY CASE status WHEN 'Pending' THEN 0 ELSE 1 END, id DESC"
        ).fetchall()
        return [dict(row) for row in rows]

def update_status(task_id: int, status: str, db_path: str | None = None) -> dict[str, Any] | None:
    init_db(db_path)
    with connect(db_path) as conn:
        cursor = conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row)

def delete_task(task_id: int, db_path: str | None = None) -> bool:
    init_db(db_path)
    with connect(db_path) as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        return cursor.rowcount > 0
