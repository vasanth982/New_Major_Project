"""
Database module for Checkup Buddy (v2).
Provides SQLite connection management, parameterized CRUD queries,
and schema initialization according to clinical specifications.
"""

import sqlite3
import os
import json
from datetime import datetime

def _resolve_db_path() -> str:
    """
    Resolves the SQLite database path:
    1. st.secrets["DATABASE_PATH"] (if provided)
    2. os.getenv("DATABASE_PATH") (if provided)
    3. Project root relative path: checkup_buddy.db (default, cross-platform)
    """
    try:
        import streamlit as st
        if "DATABASE_PATH" in st.secrets and st.secrets["DATABASE_PATH"]:
            return str(st.secrets["DATABASE_PATH"]).strip()
    except Exception:
        pass

    env_path = os.getenv("DATABASE_PATH")
    if env_path and env_path.strip():
        return env_path.strip()

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkup_buddy.db")


DB_PATH = _resolve_db_path()


def get_db_connection(db_path=DB_PATH):
    """Returns a connection to SQLite database with row_factory set to Row."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=DB_PATH):
    """Initializes the database schema."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL CHECK(role IN ('patient','owner')),
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mobile TEXT,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        email_verified INTEGER DEFAULT 0,
        mobile_verified INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)

    # 2. profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        full_name TEXT,
        age INTEGER,
        gender TEXT CHECK(gender IN ('Male','Female','Other','Prefer not to say')),
        date_of_birth TEXT,
        blood_group TEXT,
        address TEXT,
        profile_pic_path TEXT,
        updated_at TEXT
    );
    """)

    # 3. vitals_sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vitals_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        patient_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        body_temp REAL NOT NULL,
        blood_pressure_sys INTEGER NOT NULL,
        blood_pressure_dia INTEGER NOT NULL,
        blood_sugar REAL NOT NULL,
        height_cm REAL,
        weight_kg REAL,
        created_at TEXT NOT NULL
    );
    """)

    # 4. prediction_history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        vitals_session_id INTEGER REFERENCES vitals_sessions(id) ON DELETE SET NULL,
        disease TEXT NOT NULL,
        result_text TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        inputs_json TEXT,
        advice TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    # 5. owner_access_log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS owner_access_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        viewed_user_id INTEGER NOT NULL,
        accessed_at TEXT NOT NULL
    );
    """)

    # 6. otp_tokens table for dual-channel verification
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        channel TEXT NOT NULL CHECK(channel IN ('email','mobile')),
        token_hash TEXT NOT NULL,
        attempts INTEGER DEFAULT 0,
        max_attempts INTEGER DEFAULT 3,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()


# ---------------- USER FUNCTIONS ----------------

def create_user(role, username, email, mobile, password_hash, salt, email_verified=0, mobile_verified=0, db_path=DB_PATH):
    """Creates a new user record and returns the new user id."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO users (role, username, email, mobile, password_hash, salt, email_verified, mobile_verified, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (role, username, email, mobile, password_hash, salt, email_verified, mobile_verified, now))
    user_id = cursor.lastrowid
    
    # Initialize empty profile record
    cursor.execute("""
        INSERT OR IGNORE INTO profiles (user_id, full_name, updated_at)
        VALUES (?, ?, ?)
    """, (user_id, username, now))

    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email, db_path=DB_PATH):
    """Retrieves user by email address."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username, db_path=DB_PATH):
    """Retrieves user by username."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_mobile(mobile, db_path=DB_PATH):
    """Retrieves user by mobile phone number."""
    if not mobile:
        return None
    cleaned = "".join(filter(str.isdigit, str(mobile)))
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE mobile = ? OR mobile = ?", (mobile.strip(), cleaned))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id, db_path=DB_PATH):
    """Retrieves user by user ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_password(user_id, password_hash, salt, db_path=DB_PATH):
    """Updates the password hash and salt for a user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET password_hash = ?, salt = ? WHERE id = ?
    """, (password_hash, salt, user_id))
    conn.commit()
    conn.close()


# ---------------- PROFILE FUNCTIONS ----------------

def get_profile(user_id, db_path=DB_PATH):
    """Fetches user profile combined with basic account info."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.role, u.username, u.email, u.mobile, u.email_verified, u.mobile_verified, u.created_at,
               p.full_name, p.age, p.gender, p.date_of_birth, p.blood_group, p.address, p.profile_pic_path, p.updated_at
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE u.id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_profile(user_id, full_name, age, gender, date_of_birth, blood_group, address, profile_pic_path=None, db_path=DB_PATH):
    """Updates profile attributes for a given user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    if profile_pic_path is not None:
        cursor.execute("""
            INSERT INTO profiles (user_id, full_name, age, gender, date_of_birth, blood_group, address, profile_pic_path, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                age = excluded.age,
                gender = excluded.gender,
                date_of_birth = excluded.date_of_birth,
                blood_group = excluded.blood_group,
                address = excluded.address,
                profile_pic_path = excluded.profile_pic_path,
                updated_at = excluded.updated_at
        """, (user_id, full_name, age, gender, date_of_birth, blood_group, address, profile_pic_path, now))
    else:
        cursor.execute("""
            INSERT INTO profiles (user_id, full_name, age, gender, date_of_birth, blood_group, address, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                age = excluded.age,
                gender = excluded.gender,
                date_of_birth = excluded.date_of_birth,
                blood_group = excluded.blood_group,
                address = excluded.address,
                updated_at = excluded.updated_at
        """, (user_id, full_name, age, gender, date_of_birth, blood_group, address, now))

    conn.commit()
    conn.close()


# ---------------- VITALS SESSIONS FUNCTIONS ----------------

def create_vitals_session(user_id, patient_name, age, gender, body_temp, bp_sys, bp_dia, blood_sugar, height_cm=None, weight_kg=None, db_path=DB_PATH):
    """Inserts a mandatory vitals intake session and returns its ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO vitals_sessions (user_id, patient_name, age, gender, body_temp, blood_pressure_sys, blood_pressure_dia, blood_sugar, height_cm, weight_kg, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, patient_name, age, gender, body_temp, bp_sys, bp_dia, blood_sugar, height_cm, weight_kg, now))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_latest_vitals_session(user_id, db_path=DB_PATH):
    """Fetches the most recent vitals intake session for a given user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM vitals_sessions
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_vitals_session_by_id(session_id, db_path=DB_PATH):
    """Fetches a specific vitals intake session by ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vitals_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_vitals_history(user_id, db_path=DB_PATH):
    """Fetches all vitals sessions for a patient."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM vitals_sessions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- PREDICTION HISTORY FUNCTIONS ----------------

def save_prediction(user_id, vitals_session_id, disease, result_text, risk_level, inputs_dict, advice, db_path=DB_PATH):
    """Saves a diagnostic prediction record."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    inputs_json = json.dumps(inputs_dict) if isinstance(inputs_dict, dict) else str(inputs_dict)
    
    cursor.execute("""
        INSERT INTO prediction_history (user_id, vitals_session_id, disease, result_text, risk_level, inputs_json, advice, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, vitals_session_id, disease, result_text, risk_level, inputs_json, advice, now))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_user_predictions(user_id, limit=50, db_path=DB_PATH):
    """Fetches prediction history for a specific patient."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, v.patient_name, v.body_temp, v.blood_pressure_sys, v.blood_pressure_dia, v.blood_sugar, v.height_cm, v.weight_kg
        FROM prediction_history p
        LEFT JOIN vitals_sessions v ON p.vitals_session_id = v.id
        WHERE p.user_id = ?
        ORDER BY p.id DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_prediction_by_id(prediction_id, db_path=DB_PATH):
    """Fetches a specific prediction report record by ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, v.patient_name, v.age as vitals_age, v.gender as vitals_gender,
               v.body_temp, v.blood_pressure_sys, v.blood_pressure_dia, v.blood_sugar,
               v.height_cm, v.weight_kg, u.email, u.mobile
        FROM prediction_history p
        LEFT JOIN vitals_sessions v ON p.vitals_session_id = v.id
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    """, (prediction_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------- OWNER (ADMIN) & AUDIT FUNCTIONS ----------------

def log_owner_access(owner_id, viewed_user_id, db_path=DB_PATH):
    """Logs an audit record whenever an owner inspects a patient record."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO owner_access_log (owner_id, viewed_user_id, accessed_at)
        VALUES (?, ?, ?)
    """, (owner_id, viewed_user_id, now))
    conn.commit()
    conn.close()


def get_all_patients_summary(search_query="", db_path=DB_PATH):
    """Retrieves all registered patients with their test counts and profile details."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = """
        SELECT u.id, u.username, u.email, u.mobile, u.created_at,
               p.full_name, p.age, p.gender, p.blood_group,
               COUNT(ph.id) as test_count,
               MAX(ph.timestamp) as last_test_date
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        LEFT JOIN prediction_history ph ON u.id = ph.user_id
        WHERE u.role = 'patient'
    """
    params = []
    if search_query.strip():
        query += " AND (LOWER(u.username) LIKE ? OR LOWER(u.email) LIKE ? OR LOWER(p.full_name) LIKE ? OR u.mobile LIKE ?)"
        q = f"%{search_query.strip().lower()}%"
        params.extend([q, q, q, q])
        
    query += " GROUP BY u.id ORDER BY u.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_aggregate_stats(db_path=DB_PATH):
    """Calculates platform-wide statistics for the Owner dashboard."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'patient'")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prediction_history")
    total_tests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vitals_sessions")
    total_vitals = cursor.fetchone()[0]

    cursor.execute("""
        SELECT disease, COUNT(*) as count
        FROM prediction_history
        GROUP BY disease
        ORDER BY count DESC
    """)
    disease_counts = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT risk_level, COUNT(*) as count
        FROM prediction_history
        GROUP BY risk_level
    """)
    risk_distribution = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT o.id, o.owner_id, u_owner.username as owner_username,
               o.viewed_user_id, u_patient.username as patient_username,
               o.accessed_at
        FROM owner_access_log o
        LEFT JOIN users u_owner ON o.owner_id = u_owner.id
        LEFT JOIN users u_patient ON o.viewed_user_id = u_patient.id
        ORDER BY o.id DESC LIMIT 15
    """)
    recent_logs = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "total_patients": total_patients,
        "total_tests": total_tests,
        "total_vitals": total_vitals,
        "disease_counts": disease_counts,
        "risk_distribution": risk_distribution,
        "recent_logs": recent_logs
    }


# ---------------- OTP PERSISTENCE FUNCTIONS ----------------

def store_otp_token(identifier, channel, token_hash, expires_at_iso, db_path=DB_PATH):
    """Stores an encrypted OTP token record for an identifier and channel."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO otp_tokens (identifier, channel, token_hash, attempts, max_attempts, expires_at, created_at)
        VALUES (?, ?, ?, 0, 3, ?, ?)
    """, (identifier.strip().lower(), channel, token_hash, expires_at_iso, now))
    conn.commit()
    conn.close()


def get_active_otp_token(identifier, channel, db_path=DB_PATH):
    """Retrieves the latest OTP token record for an identifier and channel."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM otp_tokens
        WHERE LOWER(identifier) = LOWER(?) AND channel = ?
        ORDER BY id DESC LIMIT 1
    """, (identifier.strip(), channel))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_otp_token_attempts(otp_id, attempts, db_path=DB_PATH):
    """Updates attempt count for an OTP token."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE otp_tokens SET attempts = ? WHERE id = ?", (attempts, otp_id))
    conn.commit()
    conn.close()


def delete_otp_token(otp_id, db_path=DB_PATH):
    """Removes an OTP token once verified or expired."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM otp_tokens WHERE id = ?", (otp_id,))
    conn.commit()
    conn.close()
