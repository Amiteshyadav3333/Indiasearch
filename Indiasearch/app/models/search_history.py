# app/models/search_history.py
# 🗄️ Search History Model — PostgreSQL
# ----------------------------------------
# Stores user search queries for:
#   1. Personalized search history UI
#   2. Trending queries analytics
#   3. Autocomplete training data
#
# Fields:
#   id         → UUID primary key
#   user_id    → FK → users.id (nullable for anonymous)
#   query      → The search string
#   lang       → Language code (e.g. 'hi', 'en')
#   created_at → Timestamp (indexed for fast recent-first queries)
#
# Indexes:
#   - (user_id, created_at DESC) → for fetching user history
#   - (query, created_at DESC)   → for trending queries

# from app.models import db


class SearchHistory:
    """
    SearchHistory model — to be implemented with SQLAlchemy.

    TODO: Replace with:
    class SearchHistory(db.Model):
        __tablename__ = "search_history"
        id         = db.Column(db.String(36), primary_key=True)
        user_id    = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
        query      = db.Column(db.String(500), nullable=False)
        lang       = db.Column(db.String(10), default="hi")
        created_at = db.Column(db.DateTime, default=db.func.now(), index=True)
    """
    pass
