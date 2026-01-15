from elasticsearch import Elasticsearch
import re
from langdetect import detect, LangDetectException

es = Elasticsearch("http://localhost:9200")

INDEX_NAME = "indiasearch"


# ---------- CLEAN TEXT ----------
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------- SIMPLE SPAM DETECTOR ----------
def is_spam(url, content):
    spam_words = [
        "casino", "betting", "loan fast", "xxx",
        "earn money fast", "porn", "viagra"
    ]

    text = (url + " " + content).lower()

    return any(w in text for w in spam_words)


# ---------- FAKE NEWS RISK (BASIC) ----------
def fake_news_risk(content):
    suspicious_words = [
        "shocking truth", "exposed", "fake news", "rumor",
        "viral claim", "unverified", "controversial"
    ]

    score = sum(content.lower().count(w) for w in suspicious_words)

    return min(score, 10)  # 0–10 scale


# ---------- LANGUAGE DETECT ----------
def detect_lang(text):
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


# ---------- CREATE INDEX IF NOT EXISTS ----------
def init_index():
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "url": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "fake_risk": {"type": "integer"},
                        "is_spam": {"type": "boolean"}
                    }
                }
            }
        )


# ---------- MAIN SAVE FUNCTION ----------
def index_document(url, title, content):

    init_index()

    title = clean_text(title)
    content = clean_text(content)

    lang = detect_lang(content)

    spam = is_spam(url, content)

    risk = fake_news_risk(content)

    doc = {
        "title": title,
        "url": url,
        "content": content,
        "language": lang,
        "fake_risk": risk,
        "is_spam": spam
    }

    if spam:
        print("🚨 SPAM BLOCKED:", url)
        return

    es.index(index=INDEX_NAME, document=doc)

    print(f"✔ Indexed: {title}   ({lang})")