# app/models/crawled_site.py
# PostgreSQL model for storing crawled website data
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

class CrawledSite(Base):
    __tablename__ = "crawled_sites"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, index=True)
    title = Column(String(500))
    content_100_words = Column(Text)  # 100-word AI summary
    full_content = Column(Text)
    domain = Column(String(255))
    crawled_at = Column(DateTime, default=datetime.utcnow)

def init_crawled_db():
    if engine:
        Base.metadata.create_all(bind=engine)

def save_crawled_site(url: str, title: str, content_100_words: str, full_content: str):
    if not SessionLocal:
        return False
    session = SessionLocal()
    try:
        # Check if exists
        existing = session.query(CrawledSite).filter(CrawledSite.url == url).first()
        if existing:
            existing.title = title
            existing.content_100_words = content_100_words
            existing.full_content = full_content
            existing.crawled_at = datetime.utcnow()
        else:
            site = CrawledSite(
                url=url,
                title=title,
                content_100_words=content_100_words,
                full_content=full_content,
                domain=url.split('/')[2] if '/' in url else url
            )
            session.add(site)
        session.commit()
        return True
    except Exception as e:
        print(f"[DB] Error saving crawled site: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_crawled_site(url: str):
    if not SessionLocal:
        return None
    session = SessionLocal()
    try:
        return session.query(CrawledSite).filter(CrawledSite.url == url).first()
    finally:
        session.close()

def search_crawled_sites(query: str, limit: int = 10):
    if not SessionLocal:
        return []
    session = SessionLocal()
    try:
        return session.query(CrawledSite).filter(
            (CrawledSite.title.contains(query)) | 
            (CrawledSite.content_100_words.contains(query))
        ).limit(limit).all()
    finally:
        session.close()