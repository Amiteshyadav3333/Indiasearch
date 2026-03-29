import os
import sys
from dotenv import load_dotenv
load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
import search as search_module
import ai_summary
import translator

app = FastAPI()

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


@app.get("/search")
async def search(q: str):
    print(f"SEARCH ROUTE HIT: q={q}")
    try:
        translated, lang = translator.translate_query_to_english(q)
        print(f"TRANSLATED: {translated}")
        
        results = search_module.search_query(es, INDEX, translated)
        print(f"RESULTS COUNT: {len(results)}")
        
        summary = ai_summary.generate_ai_summary(q, results)
        
        return {
            "summary": summary,
            "results": results
        }
    except Exception as e:
        print(f"API ERROR: {e}")
        return {
            "error": str(e),
            "summary": None,
            "results": []
        }