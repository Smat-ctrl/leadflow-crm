import sqlite3

DB_PATH = "leads.db"


def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            first_name TEXT,
            email TEXT UNIQUE NOT NULL,
            company TEXT,
            title TEXT,
            industry TEXT,

            status TEXT DEFAULT 'Not Contacted',
            template_variant TEXT,
            last_contacted_at TEXT,
            follow_up_date TEXT,
            reply_count INTEGER DEFAULT 0,
            notes TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    columns = [
        column[1]
        for column in cursor.execute("PRAGMA table_info(leads)").fetchall()
    ]
    if "first_nam" in columns and "first_name" not in columns:
        cursor.execute("ALTER TABLE leads RENAME COLUMN first_nam TO first_name")

    conn.commit()
    conn.close()
