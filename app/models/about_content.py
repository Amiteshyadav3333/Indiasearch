import time
import logging
from typing import List, Dict
from app.models.user import get_conn

logger = logging.getLogger(__name__)

def init_about_db():
    try:
        conn = get_conn()
    except Exception as e:
        logger.warning(f"About DB init skipped: {e}")
        return

    try:
        with conn.cursor() as cur:
            # Table for Research Papers & Books
            cur.execute("""
                CREATE TABLE IF NOT EXISTS about_publications (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    file_url TEXT NOT NULL,
                    pub_type TEXT DEFAULT 'paper', -- 'paper' or 'book'
                    topic TEXT,
                    research_duration TEXT,
                    unique_points TEXT,
                    owner_session_token TEXT,
                    owner_identifier TEXT,
                    created_at BIGINT NOT NULL
                )
            """)
            cur.execute("ALTER TABLE about_publications ADD COLUMN IF NOT EXISTS topic TEXT")
            cur.execute("ALTER TABLE about_publications ADD COLUMN IF NOT EXISTS research_duration TEXT")
            cur.execute("ALTER TABLE about_publications ADD COLUMN IF NOT EXISTS unique_points TEXT")
            cur.execute("ALTER TABLE about_publications ADD COLUMN IF NOT EXISTS owner_session_token TEXT")
            cur.execute("ALTER TABLE about_publications ADD COLUMN IF NOT EXISTS owner_identifier TEXT")
            # Table for Media/Videos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS about_media (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    video_url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    created_at BIGINT NOT NULL
                )
            """)
            conn.commit()
    finally:
        conn.close()

def add_publication(
    title: str,
    description: str,
    file_url: str,
    pub_type: str = 'paper',
    topic: str = "",
    research_duration: str = "",
    unique_points: str = "",
    owner_session_token: str = "",
    owner_identifier: str = ""
):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO about_publications
              (title, description, file_url, pub_type, topic, research_duration, unique_points, owner_session_token, owner_identifier, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (title, description, file_url, pub_type, topic, research_duration, unique_points, owner_session_token, owner_identifier, int(time.time()))
        )
        pub_id = cur.fetchone()['id']
        conn.commit()
    conn.close()
    return pub_id

def add_media(title: str, video_url: str, thumbnail_url: str = None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO about_media (title, video_url, thumbnail_url, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
            (title, video_url, thumbnail_url, int(time.time()))
        )
        media_id = cur.fetchone()['id']
        conn.commit()
    conn.close()
    return media_id

def get_about_content():
    content = {"publications": [], "media": []}
    try:
        conn = get_conn()
    except Exception:
        return content

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM about_publications ORDER BY created_at DESC")
            content["publications"] = cur.fetchall()
            cur.execute("SELECT * FROM about_media ORDER BY created_at DESC")
            content["media"] = cur.fetchall()
    finally:
        conn.close()
    return content

def get_publication(pub_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM about_publications WHERE id = %s", (pub_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()

def delete_publication(pub_id: int):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM about_publications WHERE id = %s", (pub_id,))
        conn.commit()
    conn.close()

def delete_media(media_id: int):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM about_media WHERE id = %s", (media_id,))
        conn.commit()
    conn.close()
