import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import re
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indiasearch_auth.db")
OTP_TTL_SECONDS = 300
SESSION_TTL_SECONDS = 60 * 60 * 24 * 14


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL UNIQUE,
                identifier_type TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                purpose TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT NOT NULL UNIQUE,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                filter_type TEXT NOT NULL,
                ai_mode INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return hmac.compare_digest(derived, expected)


def normalize_identifier(identifier: str):
    identifier = identifier.strip().lower()
    if "@" in identifier:
        return identifier, "email"
    else:
        # Keep '+' if it starts with it, and all digits
        has_plus = identifier.startswith("+")
        digits = "".join(ch for ch in identifier if ch.isdigit())
        if has_plus:
            return f"+{digits}", "phone"
        return digits, "phone"


def create_user(identifier: str, identifier_type: str, password: str):
    now = int(time.time())
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO users (identifier, identifier_type, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (identifier, identifier_type, hash_password(password), now),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_identifier(identifier: str):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE identifier = ?", (identifier,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_otp(identifier: str, purpose: str = "signup_verification") -> str:
    code = f"{secrets.randbelow(900000) + 100000}"
    now = int(time.time())
    expires_at = now + OTP_TTL_SECONDS
    conn = get_conn()
    try:
        conn.execute("DELETE FROM otp_codes WHERE identifier = ? AND purpose = ?", (identifier, purpose))
        conn.execute(
            """
            INSERT INTO otp_codes (identifier, otp_code, purpose, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (identifier, code, purpose, expires_at, now),
        )
        conn.commit()
        return code
    finally:
        conn.close()


def verify_otp(identifier: str, otp_code: str, purpose: str = "signup_verification") -> bool:
    now = int(time.time())
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT * FROM otp_codes
            WHERE identifier = ? AND otp_code = ? AND purpose = ? AND expires_at >= ?
            ORDER BY id DESC LIMIT 1
            """,
            (identifier, otp_code.strip(), purpose, now),
        ).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM otp_codes WHERE identifier = ? AND purpose = ?", (identifier, purpose))
        conn.commit()
        return True
    finally:
        conn.close()


def update_password_by_identifier(identifier: str, password: str):
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE identifier = ?",
            (hash_password(password), identifier),
        )
        conn.commit()
    finally:
        conn.close()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    expires_at = now + SESSION_TTL_SECONDS
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO sessions (user_id, session_token, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, token, expires_at, now),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def get_user_by_session(token: str) -> Optional[dict]:
    now = int(time.time())
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT users.id, users.identifier, users.identifier_type, users.created_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.session_token = ? AND sessions.expires_at >= ?
            ORDER BY sessions.id DESC LIMIT 1
            """,
            (token, now),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_session(token: str):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
        conn.commit()
    finally:
        conn.close()


def add_search_history(user_id: int, query: str, filter_type: str, ai_mode: bool):
    clean_query = (query or "").strip()
    if not clean_query:
        return

    now = int(time.time())
    conn = get_conn()
    try:
        conn.execute(
            """
            DELETE FROM search_history
            WHERE user_id = ?
              AND id NOT IN (
                  SELECT id FROM search_history
                  WHERE user_id = ?
                  ORDER BY created_at DESC, id DESC
                  LIMIT 39
              )
            """,
            (user_id, user_id),
        )
        conn.execute(
            """
            INSERT INTO search_history (user_id, query, filter_type, ai_mode, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, clean_query, filter_type or "all", int(bool(ai_mode)), now),
        )
        conn.commit()
    finally:
        conn.close()


def get_search_history(user_id: int, limit: int = 20):
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT query, filter_type, ai_mode, created_at
            FROM search_history
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
