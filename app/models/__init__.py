# app/models/__init__.py
# 🗄️ Models — PostgreSQL ORM (SQLAlchemy)
# ----------------------------------------
# Database models using SQLAlchemy ORM.
# Connected to PostgreSQL in production (DATABASE_URL in .env).
# SQLite can be used for local dev.
#
# Initialize DB:
#   from app.models import db
#   db.create_all()

# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

from app.models.crawled_site import init_crawled_db, save_crawled_site, search_crawled_sites
init_crawled_db()
