import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "database" / "cyberhunt.db"))


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT,
        role TEXT NOT NULL DEFAULT 'participant' CHECK(role IN ('admin','participant')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS Event (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'IDLE' CHECK(status IN ('IDLE','RUNNING','PAUSED','ENDED')),
        started_at TEXT,
        paused_at TEXT,
        ended_at TEXT,
        duration_seconds INTEGER NOT NULL DEFAULT 7200,
        remaining_seconds INTEGER NOT NULL DEFAULT 7200,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS Challenge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        flag TEXT NOT NULL,
        points INTEGER NOT NULL CHECK(points >= 0),
        hint TEXT DEFAULT '',
        category TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS ChallengeDependency (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenge_id INTEGER NOT NULL,
        dependency_challenge_id INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(challenge_id, dependency_challenge_id),
        FOREIGN KEY(challenge_id) REFERENCES Challenge(id) ON DELETE CASCADE,
        FOREIGN KEY(dependency_challenge_id) REFERENCES Challenge(id) ON DELETE CASCADE,
        CHECK(challenge_id <> dependency_challenge_id)
    );
    CREATE TABLE IF NOT EXISTS Participant (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        current_challenge_id INTEGER,
        total_score INTEGER NOT NULL DEFAULT 0,
        solved_challenges INTEGER NOT NULL DEFAULT 0,
        hints_used INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'idle' CHECK(status IN ('active','idle','offline')),
        last_activity TEXT,
        joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES User(id) ON DELETE CASCADE,
        FOREIGN KEY(current_challenge_id) REFERENCES Challenge(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS Announcement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        created_by INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(created_by) REFERENCES User(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS Submission (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_id INTEGER NOT NULL,
        challenge_id INTEGER NOT NULL,
        submitted_flag TEXT,
        result TEXT NOT NULL CHECK(result IN ('accepted','wrong')),
        score_awarded INTEGER NOT NULL DEFAULT 0,
        submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(participant_id) REFERENCES Participant(id) ON DELETE CASCADE,
        FOREIGN KEY(challenge_id) REFERENCES Challenge(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS ScoreTransaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_id INTEGER NOT NULL,
        submission_id INTEGER,
        amount INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(participant_id) REFERENCES Participant(id) ON DELETE CASCADE,
        FOREIGN KEY(submission_id) REFERENCES Submission(id) ON DELETE SET NULL
    );
    """)
    # Upgrade databases created by the earlier schema.
    columns = {r[1] for r in conn.execute("PRAGMA table_info(Event)").fetchall()}
    if "duration_seconds" not in columns:
        conn.execute("ALTER TABLE Event ADD COLUMN duration_seconds INTEGER NOT NULL DEFAULT 7200")
    if "remaining_seconds" not in columns:
        conn.execute("ALTER TABLE Event ADD COLUMN remaining_seconds INTEGER NOT NULL DEFAULT 7200")
    conn.execute("UPDATE Event SET duration_seconds=7200 WHERE duration_seconds IS NULL OR duration_seconds=14400")
    conn.execute("UPDATE Event SET remaining_seconds=duration_seconds WHERE remaining_seconds IS NULL")
    if conn.execute("SELECT COUNT(*) FROM Event").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO Event(name,status,duration_seconds,remaining_seconds) VALUES(?,?,?,?)",
            ("CyberHunt Demo Event", "IDLE", 7200, 7200),
        )
    conn.commit()
    conn.close()


def query(sql, params=()):
    conn = get_connection()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def execute(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
