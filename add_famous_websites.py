#!/usr/bin/env python3
"""
Add famous websites to Indiasearch
"""

import os
from elasticsearch import Elasticsearch

# Elasticsearch credentials
ELASTIC_URL = os.getenv("ELASTIC_URL", "https://606ffdc0ae1d4bd1901e6b4b9d84df28.ap-south-1.aws.elastic-cloud.com:443")
ELASTIC_USER = os.getenv("ELASTIC_USERNAME", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "mRxpkXduHB0A0MvOLS2IABmX")

INDEX_NAME = "indiasearch"

es = Elasticsearch(
    ELASTIC_URL,
    basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
    request_timeout=30
)

# Famous websites data
FAMOUS_WEBSITES = [
    # Search Engines
    {
        "title": "Google - Search Engine",
        "content": "Google is the world's most popular search engine. Search the web, find images, videos, news, and more. Google Search helps you find information quickly and easily.",
        "url": "https://www.google.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Bing - Microsoft Search Engine",
        "content": "Bing is Microsoft's search engine. Search the web with Bing for images, videos, news, and maps. Powered by AI and machine learning.",
        "url": "https://www.bing.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Social Media
    {
        "title": "Facebook - Social Network",
        "content": "Facebook is the world's largest social networking site. Connect with friends and family, share photos and videos, join groups and communities.",
        "url": "https://www.facebook.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Instagram - Photo & Video Sharing",
        "content": "Instagram is a photo and video sharing social networking service. Share your moments, follow friends, discover content from creators worldwide.",
        "url": "https://www.instagram.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Twitter (X) - Social Media Platform",
        "content": "Twitter (now X) is a social media platform for sharing short messages, news, and updates. Follow trending topics, connect with people worldwide.",
        "url": "https://twitter.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "LinkedIn - Professional Network",
        "content": "LinkedIn is the world's largest professional network. Build your career, find jobs, connect with professionals, share your expertise.",
        "url": "https://www.linkedin.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Video Platforms
    {
        "title": "YouTube - Video Sharing Platform",
        "content": "YouTube is the world's largest video sharing platform. Watch, upload, and share videos. Find music, tutorials, entertainment, news, and more.",
        "url": "https://www.youtube.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # E-commerce
    {
        "title": "Amazon - Online Shopping",
        "content": "Amazon is the world's largest online marketplace. Shop for electronics, books, clothing, groceries, and millions of products with fast delivery.",
        "url": "https://www.amazon.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Flipkart - India's Shopping Destination",
        "content": "Flipkart is India's leading e-commerce platform. Shop for mobiles, electronics, fashion, home appliances, books, and more with great deals.",
        "url": "https://www.flipkart.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # News & Information
    {
        "title": "Wikipedia - Free Encyclopedia",
        "content": "Wikipedia is a free online encyclopedia with millions of articles. Find information on any topic, written collaboratively by volunteers worldwide.",
        "url": "https://www.wikipedia.org",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "BBC News - World News",
        "content": "BBC News provides trusted world and UK news. Get breaking news, analysis, features, and videos on politics, business, entertainment, and more.",
        "url": "https://www.bbc.com/news",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "NDTV - Indian News Channel",
        "content": "NDTV is India's leading news channel. Get latest news on India, world, business, cricket, videos, photos, and election results.",
        "url": "https://www.ndtv.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Times of India - Indian Newspaper",
        "content": "Times of India is India's largest English newspaper. Read latest news, breaking news, India news, business, sports, entertainment, and more.",
        "url": "https://timesofindia.indiatimes.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Technology
    {
        "title": "GitHub - Developer Platform",
        "content": "GitHub is the world's leading software development platform. Host code, collaborate on projects, build software together with millions of developers.",
        "url": "https://github.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Stack Overflow - Programming Q&A",
        "content": "Stack Overflow is the largest online community for programmers. Ask questions, find answers, learn programming, and share knowledge.",
        "url": "https://stackoverflow.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Education
    {
        "title": "Khan Academy - Free Education",
        "content": "Khan Academy offers free online courses, lessons, and practice in math, science, computing, arts, and more. Learn anything for free.",
        "url": "https://www.khanacademy.org",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Coursera - Online Courses",
        "content": "Coursera offers online courses from top universities and companies. Learn new skills, earn certificates, advance your career.",
        "url": "https://www.coursera.org",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Entertainment
    {
        "title": "Netflix - Streaming Service",
        "content": "Netflix is the world's leading streaming entertainment service. Watch TV shows, movies, documentaries, and more on any device.",
        "url": "https://www.netflix.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Spotify - Music Streaming",
        "content": "Spotify is a digital music streaming service. Listen to millions of songs, podcasts, and playlists. Discover new music and artists.",
        "url": "https://www.spotify.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # India Specific
    {
        "title": "India - Wikipedia",
        "content": "India, officially the Republic of India, is a country in South Asia. It is the seventh-largest country by area, the most populous country, and the most populous democracy in the world. Capital: New Delhi. Population: 1.4 billion.",
        "url": "https://en.wikipedia.org/wiki/India",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Government of India Portal",
        "content": "Official portal of Government of India. Access government services, schemes, departments, and information. Digital India initiative.",
        "url": "https://www.india.gov.in",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Programming
    {
        "title": "Python.org - Python Programming",
        "content": "Python is a high-level, interpreted programming language. Official Python website with documentation, downloads, tutorials, and community resources.",
        "url": "https://www.python.org",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "MDN Web Docs - Web Development",
        "content": "MDN Web Docs provides information about web technologies including HTML, CSS, and JavaScript. Learn web development with tutorials and references.",
        "url": "https://developer.mozilla.org",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Cloud & Services
    {
        "title": "AWS - Amazon Web Services",
        "content": "Amazon Web Services (AWS) is the world's most comprehensive cloud platform. Cloud computing services for storage, databases, analytics, AI, and more.",
        "url": "https://aws.amazon.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Microsoft Azure - Cloud Computing",
        "content": "Microsoft Azure is a cloud computing platform. Build, deploy, and manage applications with Microsoft's global network of datacenters.",
        "url": "https://azure.microsoft.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    
    # Communication
    {
        "title": "WhatsApp - Messaging App",
        "content": "WhatsApp is a free messaging and calling app. Send messages, make voice and video calls, share photos and videos with friends and family.",
        "url": "https://www.whatsapp.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
    {
        "title": "Gmail - Email Service",
        "content": "Gmail is Google's free email service. Send and receive emails, organize your inbox, get 15 GB of storage, and access from any device.",
        "url": "https://mail.google.com",
        "language": "en",
        "fake_risk": 0,
        "is_spam": False
    },
]

def add_websites():
    """Add all famous websites to Elasticsearch"""
    
    print(f"🚀 Adding {len(FAMOUS_WEBSITES)} famous websites...\n")
    
    success_count = 0
    for website in FAMOUS_WEBSITES:
        try:
            es.index(index=INDEX_NAME, document=website)
            print(f"✅ Added: {website['title']}")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed: {website['title']} - {e}")
    
    print(f"\n✅ Successfully added {success_count}/{len(FAMOUS_WEBSITES)} websites!")
    
    # Verify total count
    count = es.count(index=INDEX_NAME)
    print(f"📊 Total documents in index: {count['count']}")

if __name__ == "__main__":
    try:
        if es.ping():
            print("✅ Connected to Elasticsearch!\n")
        else:
            print("❌ Failed to connect to Elasticsearch")
            exit(1)
        
        add_websites()
        
        print("\n🎉 Done! Your search engine now has famous websites!")
        print("\nTry searching:")
        print("  - 'google'")
        print("  - 'facebook'")
        print("  - 'india'")
        print("  - 'python'")
        print("  - 'netflix'")
        print("\nVisit: https://indiasearch.vercel.app")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
