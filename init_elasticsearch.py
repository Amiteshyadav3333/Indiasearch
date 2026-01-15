#!/usr/bin/env python3
"""
Initialize Elasticsearch index for Indiasearch
Run this once to create the index
"""

import os
from elasticsearch import Elasticsearch

# Elasticsearch credentials
ELASTIC_URL = os.getenv("ELASTIC_URL", "https://606ffdc0ae1d4bd1901e6b4b9d84df28.ap-south-1.aws.elastic-cloud.com:443")
ELASTIC_USER = os.getenv("ELASTIC_USERNAME", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "mRxpkXduHB0A0MvOLS2IABmX")

INDEX_NAME = "indiasearch"

# Connect to Elasticsearch
es = Elasticsearch(
    ELASTIC_URL,
    basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
    request_timeout=30
)

def create_index():
    """Create indiasearch index with proper mappings"""
    
    # Check if index already exists
    if es.indices.exists(index=INDEX_NAME):
        print(f"✅ Index '{INDEX_NAME}' already exists!")
        return
    
    # Create index with mappings
    index_body = {
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
    
    es.indices.create(index=INDEX_NAME, body=index_body)
    print(f"✅ Index '{INDEX_NAME}' created successfully!")

def add_sample_data():
    """Add some sample documents for testing"""
    
    sample_docs = [
        {
            "title": "Welcome to Indiasearch",
            "content": "Indiasearch is an AI-powered search engine with multi-language support. Search anything in English or Hindi and get intelligent results with AI summaries.",
            "url": "https://indiasearch.vercel.app",
            "language": "en",
            "fake_risk": 0,
            "is_spam": False
        },
        {
            "title": "India - Wikipedia",
            "content": "India, officially the Republic of India, is a country in South Asia. It is the seventh-largest country by area, the most populous country, and the most populous democracy in the world.",
            "url": "https://en.wikipedia.org/wiki/India",
            "language": "en",
            "fake_risk": 0,
            "is_spam": False
        },
        {
            "title": "Python Programming Language",
            "content": "Python is a high-level, interpreted programming language. It emphasizes code readability and allows programmers to express concepts in fewer lines of code.",
            "url": "https://www.python.org",
            "language": "en",
            "fake_risk": 0,
            "is_spam": False
        },
        {
            "title": "Google Search Engine",
            "content": "Google is the world's most popular search engine. It uses advanced algorithms to provide relevant search results to billions of users worldwide.",
            "url": "https://www.google.com",
            "language": "en",
            "fake_risk": 0,
            "is_spam": False
        },
        {
            "title": "Artificial Intelligence",
            "content": "Artificial Intelligence (AI) is the simulation of human intelligence by machines. AI systems can learn, reason, and solve problems autonomously.",
            "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "language": "en",
            "fake_risk": 0,
            "is_spam": False
        }
    ]
    
    for doc in sample_docs:
        es.index(index=INDEX_NAME, document=doc)
    
    print(f"✅ Added {len(sample_docs)} sample documents!")

if __name__ == "__main__":
    print("🚀 Initializing Elasticsearch index...\n")
    
    try:
        # Test connection
        if es.ping():
            print("✅ Connected to Elasticsearch!")
        else:
            print("❌ Failed to connect to Elasticsearch")
            exit(1)
        
        # Create index
        create_index()
        
        # Add sample data
        add_sample_data()
        
        # Verify
        count = es.count(index=INDEX_NAME)
        print(f"\n✅ Total documents in index: {count['count']}")
        print("\n🎉 Initialization complete!")
        print("\nYou can now search at: https://indiasearch.vercel.app")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
