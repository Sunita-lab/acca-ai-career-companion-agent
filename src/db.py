"""SQLite storage for students and uploaded resumes."""
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "acca.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                raw_text TEXT,
                uploaded_at TEXT NOT NULL
            );
            """
        )


def create_student(name: str, email: str, phone: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO students (name, email, phone, created_at) VALUES (?, ?, ?, ?)",
            (name, email, phone, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def save_resume(student_id: int, file_name: str, file_path: str, raw_text: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO resumes (student_id, file_name, file_path, raw_text, uploaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (student_id, file_name, file_path, raw_text,
             datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def list_students():
    with get_conn() as conn:
        return conn.execute(
            "SELECT s.id, s.name, s.email, r.file_name, r.uploaded_at "
            "FROM students s LEFT JOIN resumes r ON r.student_id = s.id "
            "ORDER BY s.id DESC"
        ).fetchall()