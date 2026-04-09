import hashlib
import hmac
import os
import secrets
import time
import re
from typing import Optional

import psycopg2
import psycopg2.extras
from urllib.parse import urlparse, unquote

# ─── PostgreSQL Connection ─────────────────────────────────────────────────────
# Set DATABASE_URL in your .env file
# Format: postgresql://user:password@host:port/dbname
# Railway auto-injects this as DATABASE_URL when you add a PostgreSQL plugin
DATABASE_URL = os.getenv("DATABASE_URL")

OTP_TTL_SECONDS = 300
SESSION_TTL_SECONDS = 60 * 60 * 24 * 14  # 14 days


def get_conn():
    """
    Highly robust PostgreSQL connection logic.
    Handles both postgres:// and postgresql:// URL schemes.
    Handles passwords with special characters (@, #, &, +) correctly.
    """
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set.")
    
    raw = DATABASE_URL.strip().strip('"').strip("'")
    
    # Normalize: Railway uses postgres://, psycopg2 needs postgresql://
    normalized = raw.replace("postgres://", "postgresql://", 1)
    
    # Strip query params before regex parsing to avoid special chars in params
    # being confused with password chars
    base_url = normalized.split("?")[0]
    
    # Regex: postgresql://[user]:[pass]@[host]:[port]/[db]
    # Password is captured lazily (.+?) to stop at last @ before host
    pattern = r"postgresql://([^:]+):(.+)@([^:@/]+):?(\d*)?/([^?]+)"
    match = re.match(pattern, base_url)
    
    if match:
        user, password, host, port, db = match.groups()
        try:
            return psycopg2.connect(
                database=unquote(db),
                user=unquote(user),
                password=unquote(password),
                host=host,
                port=port or "5432",
                sslmode="require",
                cursor_factory=psycopg2.extras.RealDictCursor,
                connect_timeout=10
            )
        except Exception as e:
            print(f"DB CONNECTION ERROR (Parsed): {e}")
            raise e

    # Fallback: try direct DSN
    try:
        return psycopg2.connect(raw, cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        raise ValueError(f"Could not parse DATABASE_URL: {e}")




def init_db():
    """
    Create all tables if they don't exist.
    Safe to call on every startup (uses IF NOT EXISTS).
    NON-FATAL: If DB is temporarily unavailable, logs warning and continues.
    App will retry on actual requests.
    """
    import logging
    logger = logging.getLogger("IndiasearchDB")
    
    try:
        conn = get_conn()
    except Exception as e:
        logger.warning(f"⚠️  DB init skipped (will retry on requests): {e}")
        return  # Non-fatal — app starts anyway
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    id SERIAL PRIMARY KEY,
                    identifier TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expires_at BIGINT NOT NULL,
                    created_at BIGINT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    identifier TEXT NOT NULL UNIQUE,
                    identifier_type TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at BIGINT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS otp_codes (
                    id SERIAL PRIMARY KEY,
                    identifier TEXT NOT NULL,
                    otp_code TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    expires_at BIGINT NOT NULL,
                    created_at BIGINT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    session_token TEXT NOT NULL UNIQUE,
                    expires_at BIGINT NOT NULL,
                    created_at BIGINT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    query TEXT NOT NULL,
                    filter_type TEXT NOT NULL,
                    ai_mode INTEGER NOT NULL DEFAULT 0,
                    created_at BIGINT NOT NULL
                )
                """
            )
            # Indexes for performance
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id, created_at DESC)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_otp_identifier ON otp_codes(identifier, purpose)"
            )
        conn.commit()
    finally:
        conn.close()


# ─── Password Hashing (unchanged — same logic) ───────────────────────────────

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


# ─── Identifier Normalization (unchanged) ────────────────────────────────────

def normalize_identifier(identifier: str):
    identifier = identifier.strip().lower()
    if "@" in identifier:
        return identifier, "email"
    else:
        has_plus = identifier.startswith("+")
        digits = "".join(ch for ch in identifier if ch.isdigit())
        if has_plus:
            return f"+{digits}", "phone"
        return digits, "phone"


# ─── User Functions ──────────────────────────────────────────────────────────

def create_user(identifier: str, identifier_type: str, password: str):
    now = int(time.time())
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (identifier, identifier_type, password_hash, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (identifier, identifier_type, hash_password(password), now),
            )
        conn.commit()
    finally:
        conn.close()


def get_user_by_identifier(identifier: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE identifier = %s", (identifier,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


# ─── OTP Functions ───────────────────────────────────────────────────────────

def create_otp(identifier: str, purpose: str = "signup_verification") -> str:
    code = f"{secrets.randbelow(900000) + 100000}"
    now = int(time.time())
    expires_at = now + OTP_TTL_SECONDS
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Delete any existing OTP for this identifier+purpose
            cur.execute(
                "DELETE FROM otp_codes WHERE identifier = %s AND purpose = %s",
                (identifier, purpose),
            )
            cur.execute(
                """
                INSERT INTO otp_codes (identifier, otp_code, purpose, expires_at, created_at)
                VALUES (%s, %s, %s, %s, %s)
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
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM otp_codes
                WHERE identifier = %s AND otp_code = %s AND purpose = %s AND expires_at >= %s
                ORDER BY id DESC LIMIT 1
                """,
                (identifier, otp_code.strip(), purpose, now),
            )
            row = cur.fetchone()
            if not row:
                return False
            cur.execute(
                "DELETE FROM otp_codes WHERE identifier = %s AND purpose = %s",
                (identifier, purpose),
            )
        conn.commit()
        return True
    finally:
        conn.close()


# ─── Password Reset ──────────────────────────────────────────────────────────

def update_password_by_identifier(identifier: str, password: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE identifier = %s",
                (hash_password(password), identifier),
            )
        conn.commit()
    finally:
        conn.close()


# ─── Session Functions ───────────────────────────────────────────────────────

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    expires_at = now + SESSION_TTL_SECONDS
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (user_id, session_token, expires_at, created_at)
                VALUES (%s, %s, %s, %s)
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
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT users.id, users.identifier, users.identifier_type, users.created_at
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.session_token = %s AND sessions.expires_at >= %s
                ORDER BY sessions.id DESC LIMIT 1
                """,
                (token, now),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def delete_session(token: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE session_token = %s", (token,))
        conn.commit()
    finally:
        conn.close()


# ─── Search History ──────────────────────────────────────────────────────────

def add_search_history(user_id: int, query: str, filter_type: str, ai_mode: bool):
    clean_query = (query or "").strip()
    if not clean_query:
        return

    now = int(time.time())
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Keep only the latest 39 entries, then add the new one (total 40)
            cur.execute(
                """
                DELETE FROM search_history
                WHERE user_id = %s
                  AND id NOT IN (
                      SELECT id FROM search_history
                      WHERE user_id = %s
                      ORDER BY created_at DESC, id DESC
                      LIMIT 39
                  )
                """,
                (user_id, user_id),
            )
            cur.execute(
                """
                INSERT INTO search_history (user_id, query, filter_type, ai_mode, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, clean_query, filter_type or "all", int(bool(ai_mode)), now),
            )
        conn.commit()
    finally:
        conn.close()


def get_search_history(user_id: int, limit: int = 20):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT query, filter_type, ai_mode, created_at
                FROM search_history
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


# ─── Email Verification Tokens ───────────────────────────────────────────────

def create_verification_token(identifier: str) -> str:
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    expires_at = now + 1800  # 30 mins
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM verification_tokens WHERE identifier = %s",
                (identifier,),
            )
            cur.execute(
                """
                INSERT INTO verification_tokens (identifier, token, expires_at, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (identifier, token, expires_at, now),
            )
        conn.commit()
        return token
    finally:
        conn.close()


def verify_token_and_get_email(token: str) -> Optional[str]:
    now = int(time.time())
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT identifier FROM verification_tokens WHERE token = %s AND expires_at >= %s",
                (token, now),
            )
            row = cur.fetchone()
            if not row:
                return None
            return row["identifier"]
    finally:
        conn.close()


def delete_verification_token(token: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM verification_tokens WHERE token = %s", (token,))
        conn.commit()
    finally:
        conn.close()
