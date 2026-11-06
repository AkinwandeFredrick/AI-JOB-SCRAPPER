import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jobs.db")

def get_db_connection():
    """Returns a connection to the SQLite database with timeout handling for concurrency."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema exactly as required."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        external_id TEXT,
        title TEXT,
        company TEXT,
        location TEXT,
        url TEXT,
        description TEXT,
        scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'new',
        UNIQUE(source, external_id)
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tailored_cvs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        tailored_json TEXT,
        pdf_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        applied_at TEXT,
        method TEXT,
        notes TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
