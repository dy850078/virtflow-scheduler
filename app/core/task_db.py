import sqlite3
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(BASE_DIR, "db", "task.db")


def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_status (
            task_id TEXTㄋPRIMARY KEY,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            error TEXT
        )
    """)
    conn.commit()
    conn.close()

def create_task(task_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO task_status (task_id, status, timestamp)
        VALUES (?, ?, ?)
    """, (task_id, "queued", datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def update_task_status(task_id: str, status: str, error: str = None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE task_status
        SET status = ?, timestamp = ?, error = ?
        WHERE task_id = ?
    """, (status, datetime.utcnow().isoformat(), error, task_id))
    conn.commit()
    conn.close()

def get_task_status(task_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT task_id, status, timestamp, error FROM task_status WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "task_id": row[0],
            "status": row[1],
            "timestamp": row[2],
            "error": row[3]
        }
    else:
        return {"error": "Task not found"}