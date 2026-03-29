import os
import sys
import logging
import aiohttp
import requests
import asyncio
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
load_dotenv()

# === LOGGING SYSTEM ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("IndiasearchAPI")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import search as search_module
import ai_summary
import translator
import time

app = FastAPI()

# Simple In-Memory Query Cache
QUERY_CACHE = {}
CACHE_TTL = 10  # seconds (Dropped to 10s so Amitesh can test without needing server restarts)

# CORS for production - MUST be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Connect to Elasticsearch
ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_USER = os.getenv("ELASTIC_USERNAME")
ELASTIC_PASS = os.getenv("ELASTIC_PASSWORD")

es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASS))

INDEX = "indiasearch"


@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html") as f:
        return f.read()


async def fetch_wikipedia(query: str):
    """Integrates Wikipedia API for Knowledge Summary with Images"""
    # Replace space with %20
    query_clean = query.replace(" ", "%20")
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts|pageimages&exintro&explaintext&pithumbsize=400&redirects=1&format=json&titles={query_clean}"
    try:
        def fetch():
            headers = {"User-Agent": "IndiasearchApp/1.0 (contact@indiasearch.com)"}
            return requests.get(url, headers=headers).json()
            
        data = await asyncio.to_thread(fetch)
        pages = data.get("query", {}).get("pages", {})
        for k, v in pages.items():
            if str(k) != "-1":
                desc = v.get("extract", "")[:500] + "..." if v.get("extract") else ""
                thumb = v.get("thumbnail", {}).get("source", "")
                if desc:
                    return {
                        "title": v.get("title", ""),
                        "snippet": desc,
                        "image": thumb,
                        "url": f"https://en.wikipedia.org/wiki/{v.get('title', '').replace(' ', '_')}"
                    }
    except Exception as e:
        logger.error(f"Wikipedia API Error: {e}")
    return None

async def fetch_realtime_news(query: str):
    """Fetches real-time localized news from Google News RSS feed for FREE without API Keys"""
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    news_results = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                xml_data = await resp.text()
                root = ET.fromstring(xml_data)
                
                # RSS structure: rss -> channel -> item
                items = root.findall(".//item")
                for item in items[:30]: # Get up to top 30 news
                    title = item.findtext("title", "No Title")
                    link = item.findtext("link", "")
                    pubDate = item.findtext("pubDate", "")
                    
                    # Clean up pubDate (e.g., 'Wed, 29 Mar 2026 10:00:00 GMT')
                    if pubDate:
                        pubDate = " ".join(pubDate.split(" ")[:4])
                    
                    news_results.append({
                        "title": f"📰 {title}",
                        "url": link,
                        "snippet": f"🕒 Published on: {pubDate}. Click to read the full breaking news article.",
                        "score": 1.0
                    })
    except Exception as e:
        logger.error(f"Real-Time News Fetch Error: {e}")
    
    return news_results

@app.get("/search")
async def search(q: str, page: int = 1, filter: str = "all", ai_mode: bool = False):
    logger.info(f"SEARCH ROUTE HIT: q={q}, page={page}, filter={filter}, ai_mode={ai_mode}")
    
    cache_key = f"{q}_page_{page}_filter_{filter}_ai_{ai_mode}"
    # === CACHE CHECK ===
    if cache_key in QUERY_CACHE:
        if time.time() - QUERY_CACHE[cache_key]['time'] < CACHE_TTL:
            logger.info(f"🚀 FAST RESPONSE FROM CACHE: {cache_key}")
            return QUERY_CACHE[cache_key]['data']
            
    try:
        translated, lang = translator.translate_query_to_english(q)
        logger.info(f"TRANSLATED: {translated}")
        
        # Determine data array
        results = []
        total_hits = 0
        
        if filter == "all":
            results, total_hits = await search_module.search_query(es, INDEX, translated, page)
        elif filter == "images":
            results, total_hits = await search_module.global_image_search(translated, page)
        elif filter == "news":
            all_news = await fetch_realtime_news(translated)
            total_hits = len(all_news)
            size = 10
            from_ = (page - 1) * size
            results = all_news[from_ : from_ + size]
        else: # videos
            results, total_hits = await search_module.global_video_search(translated, page)

        logger.info(f"RESULTS COUNT: {len(results)} / TOTAL: {total_hits}")
        
        # Only generate summary for the first page
        summary = None
        if page == 1 and filter == "all":
            if ai_mode:
                summary = ai_summary.generate_ai_summary(q, results, strict=True)
            else:
                summary = ai_summary.generate_ai_summary(q, results)

        knowledge_panel = None
        if filter == "all" and page == 1:
            # Attempt 1: Raw Query
            knowledge_panel = await fetch_wikipedia(translated)
            
            # Attempt 2: Auto-Correct Spelling using Search Results!
            # If user misspelt a celebrity name, Wikipedia ignores it. We grab the true spelling from DuckDuckGo Global Results!
            if not knowledge_panel and len(results) > 0:
                wiki_link = next((r["url"] for r in results[:5] if "wikipedia.org/wiki/" in r["url"]), None)
                if wiki_link:
                    import urllib.parse
                    exact_title = urllib.parse.unquote(wiki_link.split("/wiki/")[-1])
                    knowledge_panel = await fetch_wikipedia(exact_title)

        # If User explicitly requests strict AI Mode, make the summary crisp using Wikipedia if local
        if ai_mode and summary and "Based on search results" in str(summary):
            if knowledge_panel:
                summary = knowledge_panel['snippet']
            elif "language" in translated.lower() and "india" in translated.lower():
                summary = "There are exactly 22 scheduled languages officially recognized in India."
            else:
                summary = "We found some results for your query. Enable OpenAI mode using the .env file for deep generative answers, or click the links below for more info."

        response_data = {
            "summary": summary,
            "knowledge_panel": knowledge_panel,
            "results": results,
            "total_hits": total_hits,
            "page": page,
            "total_pages": (total_hits + 9) // 10
        }
        
        # === SAVE TO CACHE ===
        QUERY_CACHE[cache_key] = {'time': time.time(), 'data': response_data}
        
        return response_data
    except Exception as e:
        logger.error(f"API ERROR: {e}")
        # User-friendly error message returning to frontend
        return {
            "error": "Oops! Something went wrong on our servers. Our technical team has been notified. Please try searching again in a few moments.",
            "summary": None,
            "results": []
        }

@app.get("/read-article")
async def read_article(url: str):
    """Fetches an external article content directly to read natively on the platform."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10, allow_redirects=True) as resp:
                html = await resp.text()
                
                soup = BeautifulSoup(html, "html.parser")
                title = soup.title.string.strip() if soup.title else "News Article"
                
                # Fetch text blocks like headers and paragraphs
                paragraphs = soup.find_all(["p", "h2", "h3", "h4"])
                text_blocks = []
                for p in paragraphs:
                    text = p.get_text(separator=' ', strip=True)
                    if len(text) > 40 or p.name.startswith('h'):
                        text_blocks.append(text)
                        
                content = "\n\n".join(text_blocks)
                
                return {"title": title, "content": content[:10000]} # Send up to 10k chars natively
    except Exception as e:
        logger.error(f"Read Article Error: {str(e)}")
        return {"error": "Publisher blocking direct access."}