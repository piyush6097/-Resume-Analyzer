# db_cache.py
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "candidates_cache.db"  # change if you want the DB elsewhere

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS CANDIDATES (
    resume_hash TEXT PRIMARY KEY,
    score REAL NOT NULL,
    model_version TEXT DEFAULT 'v1',
    source_filename TEXT,
    created_at TEXT NOT NULL
);
"""

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)  # check_same_thread=False for multi-threaded WSGI
    conn.execute("PRAGMA journal_mode=WAL;")   # better concurrent access
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db(db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()

def get_cached_score(resume_hash: str, model_version: str = "v1", db_path: str = DB_PATH) -> Optional[float]:
    """
    Returns cached score (float) if present for the resume_hash and model_version.
    If you don't track model_version, pass same value when saving and checking.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT score, created_at FROM CANDIDATES WHERE resume_hash = ? AND model_version = ?", (resume_hash, model_version))
    row = cur.fetchone()
    conn.close()
    if row:
        score, created_at = row
        return float(score)
    return None

def save_score(resume_hash: str, score: float, model_version: str = "v1", source_filename: str = None, db_path: str = DB_PATH) -> None:
    """
    Save hash->score mapping (INSERT OR REPLACE to simplify concurrency).
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        "INSERT OR REPLACE INTO CANDIDATES (resume_hash, score, model_version, source_filename, created_at) VALUES (?, ?, ?, ?, ?)",
        (resume_hash, float(score), model_version, source_filename, now)
    )
    conn.commit()
    conn.close()
