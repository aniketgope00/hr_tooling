import sqlite3
from sqlite3 import Error
import os

# Define the database file path
DB_FILE = "parent.db"

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        # Connect to the database file (will create it if it doesn't exist)
        conn = sqlite3.connect(db_file)
        # Enable foreign key support (important for data integrity)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables(conn):
    """Create all necessary tables for the HR AI Assistant application."""

    # SQL statements to create the tables based on the schema design
    sql_create_tables = [
        # 1. Organizations Table
        """CREATE TABLE IF NOT EXISTS Organizations (
            org_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            industry TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""",

        # 2. Users Table
        """CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            org_id INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL, -- e.g., HR_MANAGER, ADMIN, RECRUITER
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (org_id) REFERENCES Organizations (org_id)
        );""",

        # 3. Job_Posts Table
        """CREATE TABLE IF NOT EXISTS Job_Posts (
            job_id INTEGER PRIMARY KEY,
            org_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            requirements TEXT, -- Stored as TEXT, can hold JSON/structured data
            status TEXT NOT NULL DEFAULT 'DRAFT', -- e.g., OPEN, CLOSED, DRAFT
            created_by_user_id INTEGER,
            FOREIGN KEY (org_id) REFERENCES Organizations (org_id),
            FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id)
        );""",

        # 4. Candidates Table
        """CREATE TABLE IF NOT EXISTS Candidates (
            candidate_id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            cv_file_path TEXT, -- URL or path to the stored CV file
            ats_score REAL, -- AI-generated score (0.00-100.00)
            ai_feedback TEXT, -- Detailed AI summary/justification
            current_stage TEXT NOT NULL DEFAULT 'CV_SCREEN',
            FOREIGN KEY (job_id) REFERENCES Job_Posts (job_id)
        );""",

        # 5. Interviews Table (Handles scheduling and preparation)
        """CREATE TABLE IF NOT EXISTS Interviews (
            interview_id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            scheduled_by_user_id INTEGER,
            type TEXT NOT NULL, -- e.g., AI_SCREEN, HR_SCREEN, TECHNICAL
            scheduled_time TEXT, -- Stored in ISO format
            status TEXT NOT NULL DEFAULT 'PENDING',
            FOREIGN KEY (candidate_id) REFERENCES Candidates (candidate_id),
            FOREIGN KEY (scheduled_by_user_id) REFERENCES Users (user_id)
        );""",

        # 6. Online Assessments (OAs) Table
        """CREATE TABLE IF NOT EXISTS Assessments (
            assessment_id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            type TEXT NOT NULL, -- e.g., Code, Aptitude, Writing
            generated_by_ai INTEGER DEFAULT 0, -- 1 for True, 0 for False
            status TEXT NOT NULL DEFAULT 'PENDING',
            FOREIGN KEY (candidate_id) REFERENCES Candidates (candidate_id)
        );""",

        # 7. Assessment_Results Table
        """CREATE TABLE IF NOT EXISTS Assessment_Results (
            result_id INTEGER PRIMARY KEY,
            assessment_id INTEGER NOT NULL,
            score REAL,
            ai_evaluation TEXT, -- Detailed AI feedback/grading on answers (can be JSON)
            completed_at TEXT,
            FOREIGN KEY (assessment_id) REFERENCES Assessments (assessment_id)
        );""",

        # 8. AI_Interview_Transcripts Table
        # Note: interview_id is set as UNIQUE to enforce a one-to-one relationship with Interviews
        """CREATE TABLE IF NOT EXISTS AI_Interview_Transcripts (
            transcript_id INTEGER PRIMARY KEY,
            interview_id INTEGER UNIQUE NOT NULL,
            full_transcript TEXT, -- Raw conversation transcript
            ai_sentiment_score REAL, -- AI analysis of candidate sentiment
            ai_key_insights TEXT, -- Structured AI analysis (can be JSON)
            FOREIGN KEY (interview_id) REFERENCES Interviews (interview_id)
        );"""
    ]

    try:
        cursor = conn.cursor()
        for sql in sql_create_tables:
            cursor.execute(sql)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")

def initialize_db():
    """Main function to initialize the database."""
    print(f"Initializing SQLite database: {DB_FILE}...")
    conn = create_connection(DB_FILE)

    if conn is not None:
        create_tables(conn)
        conn.close()
        print(f"Database initialized successfully. Tables created.")
    else:
        print("Could not establish a database connection. Initialization failed.")

# Execute the initialization when the script is run directly
if __name__ == '__main__':
    # Check if the file exists and optionally delete it for a clean start
    if os.path.exists(DB_FILE):
        print(f"Existing database file '{DB_FILE}' found. Deleting for fresh initialization.")
        os.remove(DB_FILE)

    initialize_db()