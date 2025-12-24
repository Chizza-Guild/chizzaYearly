"""
Database initialization script for Hypixel Guild Wrapped.
Creates the SQLite database schema.
"""

import sqlite3
import os
from pathlib import Path


def init_database(db_path: str = "data/wrapped.db"):
    """Initialize the SQLite database with required tables."""

    # Create data directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create wrapped_snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wrapped_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hypixel_data_path TEXT,
            discord_data_path TEXT
        )
    """)

    # Create member_stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS member_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            member_uuid TEXT,
            member_name TEXT,
            guild_xp INTEGER DEFAULT 0,
            discord_messages INTEGER DEFAULT 0,
            times_pinged INTEGER DEFAULT 0,
            joined_this_year BOOLEAN DEFAULT 0,
            joined_date TEXT,
            FOREIGN KEY (snapshot_id) REFERENCES wrapped_snapshots(id)
        )
    """)

    # Create index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_member_stats_snapshot
        ON member_stats(snapshot_id)
    """)

    # Create guild_stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            total_members INTEGER DEFAULT 0,
            total_xp INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            new_members_count INTEGER DEFAULT 0,
            most_active_day TEXT,
            FOREIGN KEY (snapshot_id) REFERENCES wrapped_snapshots(id)
        )
    """)

    conn.commit()
    conn.close()

    print(f"✅ Database initialized successfully at {db_path}")


if __name__ == "__main__":
    init_database()
