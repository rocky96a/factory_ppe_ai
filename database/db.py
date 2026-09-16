import sqlite3
import os
from config import Config


def get_connection():
    db_dir = os.path.dirname(Config.DATABASE_PATH)

    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(
        Config.DATABASE_PATH,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    conn = get_connection()

    # Cameras table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            stream_url TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Violations table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            location TEXT NOT NULL,
            tracking_id INTEGER,
            detection TEXT NOT NULL,
            confidence REAL,
            evidence_path TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'OPEN',
            email_status TEXT DEFAULT 'PENDING',
            email_sent_at TEXT
        )
    """)

    # ---------------------------------------------------------
    # Database migration for existing installations
    # ---------------------------------------------------------

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(violations)"
        ).fetchall()
    }

    if "email_status" not in columns:
        conn.execute("""
            ALTER TABLE violations
            ADD COLUMN email_status TEXT DEFAULT 'PENDING'
        """)

    if "email_sent_at" not in columns:
        conn.execute("""
            ALTER TABLE violations
            ADD COLUMN email_sent_at TEXT
        """)

    conn.commit()
    conn.close()


def add_violation(
    camera_id,
    location,
    tracking_id,
    detection,
    confidence,
    evidence_path
):
    conn = get_connection()

    cursor = conn.execute("""
        INSERT INTO violations (
            camera_id,
            location,
            tracking_id,
            detection,
            confidence,
            evidence_path,
            email_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        camera_id,
        location,
        tracking_id,
        detection,
        confidence,
        evidence_path,
        "PENDING"
    ))

    conn.commit()

    violation_id = cursor.lastrowid

    conn.close()

    return violation_id


def update_email_status(
    violation_id,
    status,
    sent_at=None
):
    conn = get_connection()

    conn.execute("""
        UPDATE violations
        SET
            email_status = ?,
            email_sent_at = ?
        WHERE id = ?
    """, (
        status,
        sent_at,
        violation_id
    ))

    conn.commit()
    conn.close()


def get_violations(limit=100):
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM violations
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_violation(violation_id):
    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM violations
        WHERE id = ?
    """, (violation_id,)).fetchone()

    conn.close()

    return dict(row) if row else None


def add_camera(
    camera_id,
    name,
    location,
    stream_url
):
    conn = get_connection()

    conn.execute("""
        INSERT OR REPLACE INTO cameras (
            camera_id,
            name,
            location,
            stream_url,
            enabled
        )
        VALUES (?, ?, ?, ?, 1)
    """, (
        camera_id,
        name,
        location,
        stream_url
    ))

    conn.commit()
    conn.close()


def get_cameras():
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM cameras
        ORDER BY id
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_camera(camera_id):
    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM cameras
        WHERE camera_id = ?
    """, (camera_id,)).fetchone()

    conn.close()

    return dict(row) if row else None


def delete_camera(camera_id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM cameras
        WHERE camera_id = ?
    """, (camera_id,))

    conn.commit()
    conn.close()