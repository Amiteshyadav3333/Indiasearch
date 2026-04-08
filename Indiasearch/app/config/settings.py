# app/config/settings.py
# ⚙️ Settings — Environment Variable Loader
# ----------------------------------------
# Single source of truth for all environment config.
# Loads from .env via python-dotenv.
#
# CRITICAL: Never hardcode secrets here. Always use env vars.
# Add all keys to .env.example (without values) for documentation.

import os
from dotenv import load_dotenv

# Load .env file (local dev). In production (Railway/Vercel), set env vars directly.
load_dotenv()


class Settings:
    """Central configuration class. All env vars read here."""

    # ── Flask ─────────────────────────────────────────────────────
    FLASK_ENV        = os.getenv("FLASK_ENV", "production")
    SECRET_KEY       = os.getenv("SECRET_KEY", "change-me-in-production")
    PORT             = int(os.getenv("PORT", 5000))

    # ── JWT ───────────────────────────────────────────────────────
    JWT_SECRET_KEY   = os.getenv("JWT_SECRET_KEY", "change-jwt-secret")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))

    # ── PostgreSQL ────────────────────────────────────────────────
    DATABASE_URL     = os.getenv("DATABASE_URL", "sqlite:///indiasearch_dev.db")

    # ── Redis ─────────────────────────────────────────────────────
    REDIS_URL        = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── Elasticsearch ─────────────────────────────────────────────
    ELASTICSEARCH_URL   = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "indiasearch_pages")

    # ── AI (Grok) ─────────────────────────────────────────────────
    GROK_API_KEY     = os.getenv("GROK_API_KEY", "")
    GROK_MODEL       = os.getenv("GROK_MODEL", "grok-3-mini")

    # ── Weather ───────────────────────────────────────────────────
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

    # ── Cricket ───────────────────────────────────────────────────
    CRICKET_API_KEY  = os.getenv("CRICKET_API_KEY", "")

    # ── Finance ───────────────────────────────────────────────────
    ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")

    # ── Celery / Background Workers ───────────────────────────────
    CELERY_BROKER_URL    = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND= os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # ── Firebase (existing) ───────────────────────────────────────
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "firebase-credentials.json")

    # ── Logging ───────────────────────────────────────────────────
    LOG_LEVEL        = os.getenv("LOG_LEVEL", "INFO")

    # ── CORS ──────────────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins
    CORS_ORIGINS     = os.getenv("CORS_ORIGINS", "https://indiasearch.vercel.app,http://localhost:3000").split(",")
