import os
import sqlite3

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(DB_DIR, "civiq.db")



# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    # enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# =========================================================
# CREATE TABLES
# =========================================================

def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    # =====================================================
    # USERS TABLE
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        role TEXT NOT NULL,

        department TEXT,
        
        phone_number TEXT,

        profile_picture TEXT DEFAULT 'default.jpg',

        status TEXT,

        created_at TEXT 

        
    )
    """)


    # =====================================================
    # COMPLAINTS TABLE
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        complaint_text TEXT NOT NULL,

        category TEXT,

        severity TEXT,

        location TEXT,

        priority INTEGER DEFAULT 1,

        support_count INTEGER DEFAULT 0,

        status TEXT DEFAULT 'open',

        created_at TEXT,

        image_path TEXT,

        image_valid INTEGER DEFAULT 0,

        official_summary TEXT,

        priority_explanation TEXT,

        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)


    # =====================================================
    # COMMENTS TABLE
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS comments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        complaint_id INTEGER NOT NULL,

        user_id INTEGER NOT NULL,

        comment_text TEXT NOT NULL,

        created_at TEXT,

        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,

        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # =====================================================
    # COMPLAINT LIKES TABLE (PREVENT DUPLICATES)
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaint_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TEXT,
        UNIQUE(complaint_id, user_id),
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()