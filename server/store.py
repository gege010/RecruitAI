"""Single-workspace transactional store. No CV files are persisted."""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect():
    path = Path(os.getenv("RECRUITAI_DB", "var/recruitai.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY, data TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS candidates (
          id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
          data TEXT NOT NULL, fingerprint TEXT, version INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, UNIQUE(job_id,fingerprint));
        CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
          snapshot TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
          subject TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, expires REAL NOT NULL);
        """)


def unpack(row):
    return {
        **json.loads(row["data"]),
        "id": row["id"],
        "version": row["version"],
        "created_at": row["created_at"],
    }


def audit(db, action, subject, now):
    db.execute(
        "INSERT INTO audit(action,subject,created_at) VALUES(?,?,?)",
        (action, subject, now),
    )
