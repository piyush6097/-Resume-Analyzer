# db_cache.py
import sqlite3
from datetime import datetime
from typing import Optional, Tuple

DB_PATH = "candidates_cache.db"

CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS JOB_DESCRIPTIONS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS CANDIDATES (
    resume_hash TEXT PRIMARY KEY,
    score REAL NOT NULL,
    model_version TEXT DEFAULT 'v1',
    jd_id INTEGER,
    source_filename TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (jd_id) REFERENCES JOB_DESCRIPTIONS(id) ON DELETE SET NULL
);
"""

# ------------------------- DATABASE SETUP -------------------------
def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    conn.executescript(CREATE_TABLES_SQL)
    conn.commit()
    conn.close()

# ------------------------- JOB DESCRIPTION FUNCTIONS -------------------------
def add_job_description(name: str, description: str, db_path: str = DB_PATH) -> int:
    """Add a new JD or update existing by name. Returns JD ID."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        "INSERT OR REPLACE INTO JOB_DESCRIPTIONS (name, description, created_at) VALUES (?, ?, ?)",
        (name, description, now),
    )
    conn.commit()
    cur.execute("SELECT id FROM JOB_DESCRIPTIONS WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def list_job_descriptions(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, created_at FROM JOB_DESCRIPTIONS ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_job_description(jd_id: int, db_path: str = DB_PATH) -> Optional[Tuple]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, created_at FROM JOB_DESCRIPTIONS WHERE id=?", (jd_id,))
    row = cur.fetchone()
    conn.close()
    return row

# ------------------------- RESUME CACHE FUNCTIONS -------------------------
def get_cached_score(resume_hash: str, model_version: str = "v1", db_path: str = DB_PATH) -> Optional[float]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT score FROM CANDIDATES WHERE resume_hash=? AND model_version=?",
        (resume_hash, model_version),
    )
    row = cur.fetchone()
    conn.close()
    return float(row[0]) if row else None

def save_score(
    resume_hash: str,
    score: float,
    model_version: str = "v1",
    jd_id: int = None,
    source_filename: str = None,
    db_path: str = DB_PATH,
):
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        "INSERT OR REPLACE INTO CANDIDATES (resume_hash, score, model_version, jd_id, source_filename, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (resume_hash, float(score), model_version, jd_id, source_filename, now),
    )
    conn.commit()
    conn.close()

def list_cached_candidates(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT resume_hash, score, model_version, jd_id, source_filename, created_at FROM CANDIDATES ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_cached(resume_hash: str, db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM CANDIDATES WHERE resume_hash=?", (resume_hash,))
    conn.commit()
    conn.close()
