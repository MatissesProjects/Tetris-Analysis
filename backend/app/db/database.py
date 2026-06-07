import sqlite3
import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings

def get_db_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database and creates the scores table if it doesn't exist.
    """
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                score INTEGER NOT NULL,
                pps REAL NOT NULL,
                apm REAL NOT NULL,
                finesse_faults INTEGER NOT NULL,
                finesse_rate REAL NOT NULL,
                pieces_placed INTEGER NOT NULL,
                lines_cleared INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                replay_name TEXT
            )
        """)
        conn.commit()

def add_score(
    username: str,
    score: int,
    pps: float,
    apm: float,
    finesse_faults: int,
    finesse_rate: float,
    pieces_placed: int,
    lines_cleared: int,
    replay_name: Optional[str] = None,
    timestamp: Optional[str] = None
) -> int:
    """
    Adds a new score record to the database.
    Returns the ID of the newly created row.
    """
    if not timestamp:
        timestamp = datetime.datetime.now().isoformat()
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scores (
                username, score, pps, apm, finesse_faults, finesse_rate, 
                pieces_placed, lines_cleared, timestamp, replay_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username, score, pps, apm, finesse_faults, finesse_rate,
                pieces_placed, lines_cleared, timestamp, replay_name
            )
        )
        conn.commit()
        return cursor.lastrowid

def get_scores() -> List[Dict[str, Any]]:
    """
    Retrieves all score records sorted by timestamp in ascending order.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scores ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_score(score_id: int) -> bool:
    """
    Deletes a specific score record by ID.
    Returns True if a row was deleted, False otherwise.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scores WHERE id = ?", (score_id,))
        conn.commit()
        return cursor.rowcount > 0

def clear_scores() -> None:
    """
    Clears all score records from the database.
    """
    with get_db_connection() as conn:
        conn.execute("DELETE FROM scores")
        conn.commit()
