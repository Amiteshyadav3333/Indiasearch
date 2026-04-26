# app/main.py
import os
import sys
import logging
import aiohttp
import requests
import asyncio
import re
import json
import base64
from datetime import datetime
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import PyPDF2
from bs4 import BeautifulSoup

# --- Load Environment ---
DOTENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(DOTENV_PATH, override=True)

# --- Service & Utility Imports ---
from app.services.search_manager import run_parallel_pipeline
from app.integrations import api_client
from app.models import user as auth_store
from app.services import ai_service as ai_summary
from app.utils import translator
from app.services.crawler_service import Crawler, SEED_URLS
from app.cache import hot_query_store

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("IndiasearchAPI")

# --- App Initialization ---
app = FastAPI(title="IndiaSearch Intelligent Engine")
auth_store.init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def daily_crawler_task():
    while True:
        try:
            logger.info("[Auto-Crawler] Starting daily background web crawl...")
            crawler = Crawler(max_pages=300, max_depth=2, max_concurrency=10)
            await crawler.run(SEED_URLS)
            logger.info("[Auto-Crawler] Daily crawl complete. Sleeping for 24 hours.")
        except Exception as e:
            logger.error(f"[Auto-Crawler] Error: {e}")
        await asyncio.sleep(86400)

async def hot_cache_warmer_task():
    """Warms cache for top queries every 30 minutes."""
    await asyncio.sleep(300)  # Wait 5 min after startup for system to warm up
    while True:
        try:
            await hot_query_store.warm_hot_cache(run_parallel_pipeline, top_n=20)
        except Exception as e:
            logger.error(f"[HotCache] Warming error: {e}")
        await asyncio.sleep(1800)  # Re-warm every 30 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(daily_crawler_task())
    asyncio.create_task(hot_cache_warmer_task())
# --- Mount Static Files ---
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

# We'll mount the frontend directory at / to serve assets like app.js and style.css
# But we must do it AFTER all other routes are defined to avoid shadowing.
# So I'll move this to the bottom of the file later or just use it now and hope for the best.
# Actually, it's better to mount it last.

# In-memory store for PDF context
PDF_STORE = {}

# --- Firebase Initialization ---
FIREBASE_CREDS_JSON = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_CREDS_FILE = os.path.join(os.path.dirname(__file__), "..", "firebase-credentials.json")

if not firebase_admin._apps:
    if FIREBASE_CREDS_JSON:
        try:
            creds_dict = json.loads(FIREBASE_CREDS_JSON)
            firebase_admin.initialize_app(credentials.Certificate(creds_dict))
        except: pass
    elif os.path.exists(FIREBASE_CREDS_FILE):
        firebase_admin.initialize_app(credentials.Certificate(FIREBASE_CREDS_FILE))

# --- Pydantic Models for Auth ---
class FirebaseLoginPayload(BaseModel):
    id_token: str

class SignupRequestPayload(BaseModel):
    email: str

class SignupVerifyPayload(BaseModel):
    token: str
    password: str

class LoginPayload(BaseModel):
    identifier: str
    password: str
    captcha_code: str

class LogoutPayload(BaseModel):
    session_token: str

# --- Helper Functions ---
def normalize_session_token(token: str | None) -> str | None:
    if not token:
        return None
    token = token.strip()
    if token.lower() in {"undefined", "null", "none", ""} or token.startswith("guest_"):
        return None
    return token

def public_user(user: dict):
    return {
        "id": user.get("id"),
        "identifier": user.get("identifier"),
        "identifier_type": user.get("identifier_type"),
    }

# --- SEARCH ROUTE (The Brain) ---
@app.get("/search")
async def search(q: str, page: int = 1, filter: str = "all", ai_mode: bool = False, session_token: str | None = None, age_verified: str = "false"):
    """
    Intelligent Search Brain Entry Point.
    Orchestrates Multi-level search (Cache -> Local/Free Web -> Paid Fallback).
    """
    try:
        force_ai = (filter == "askAI" or ai_mode)
        
        # Get PDF context if any exists for this session
        valid_session_token = normalize_session_token(session_token)
        sess_key = session_token if session_token and session_token != "undefined" else "guest"
        pdf_content = PDF_STORE.get(sess_key)
        
        if pdf_content:
            logger.info(f"[Search] PDF Context ACTIVE for session {sess_key} (len: {len(pdf_content)})")

        # Execute the Intelligent Pipeline
        response = await run_parallel_pipeline(
            query=q, 
            page=page, 
            filter=filter,
            lang="en", 
            force_ai=force_ai,
            pdf_content=pdf_content,
            age_verified=(age_verified == "true")
        )
        
        # Save history if logged in
        if valid_session_token:
            user = auth_store.get_user_by_session(valid_session_token)
            if user:
                auth_store.save_search_query(user["id"], q)

        return response
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return JSONResponse({"error": "Search Brain is momentarily offline."}, status_code=500)

# --- AUTH ROUTES ---
@app.post("/auth/firebase-login")
async def firebase_login(payload: FirebaseLoginPayload):
    try:
        decoded_token = auth.verify_id_token(payload.id_token)
        identifier = decoded_token.get('email') or decoded_token.get('phone_number')
        if not identifier: return JSONResponse({"error": "Auth failed"}, 400)
        
        user = auth_store.get_user_by_identifier(identifier)
        if not user:
            auth_store.create_user(identifier, "email" if "@" in identifier else "phone", decoded_token['uid'])
            user = auth_store.get_user_by_identifier(identifier)
            
        token = auth_store.create_session(user["id"])
        return {"session_token": token, "user": public_user(user)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, 401)

@app.post("/auth/login")
async def login(payload: LoginPayload):
    if payload.captcha_code.lower() != "india":
        return JSONResponse({"error": "Invalid captcha"}, 400)
        
    user = auth_store.get_user_by_identifier(payload.identifier)
    if not user or not auth_store.verify_password(payload.password, user["password_hash"]):
        return JSONResponse({"error": "Invalid credentials"}, 401)
        
    token = auth_store.create_session(user["id"])
    return {"session_token": token, "user": public_user(user)}

@app.get("/auth/me")
async def me(session_token: str):
    user = auth_store.get_user_by_session(session_token)
    if not user: return JSONResponse({"error": "Invalid session"}, 401)
    return {"user": public_user(user)}

@app.post("/auth/logout")
async def logout(payload: LogoutPayload):
    auth_store.delete_session(payload.session_token)
    return {"message": "Success"}

# --- UTILITY ROUTES ---
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": str(datetime.now())}

@app.get("/api/quota")
async def get_quota():
    return api_client.get_quota_status()

@app.post("/visual-search")
async def visual_search(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        b64 = base64.b64encode(contents).decode('utf-8')
        identity = ai_summary.groq_vision_identify(b64)
        return {"identity": identity}
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), session_token: str | None = Form(None)):
    sess = session_token or "guest"
    try:
        reader = PyPDF2.PdfReader(file.file)
        text = "".join([p.extract_text() for p in reader.pages])
        PDF_STORE[sess] = text[:50000]
        logger.info(f"[PDF] Uploaded for session {sess}. Extracted {len(text)} chars.")
        return {"message": f"PDF Processed. {len(text)} characters extracted."}
    except Exception as e:
        logger.error(f"[PDF] Error processing for {sess}: {e}")
        return JSONResponse({"error": str(e)}, 500)

class ClearContextPayload(BaseModel):
    session_token: str | None = None

@app.post("/clear-context")
async def clear_context(payload: ClearContextPayload):
    sess = payload.session_token or "guest"
    if sess in PDF_STORE:
        del PDF_STORE[sess]
    return {"message": "Context cleared"}

@app.get("/read-article")
async def read_article(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                soup = BeautifulSoup(await resp.text(), "html.parser")
                text = "\n".join([p.get_text() for p in soup.find_all("p")])
                return {"title": soup.title.string, "content": text[:10000]}
    except:
        return {"error": "Blocked"}

# Explicit routes for favicon and SEO files (must be BEFORE StaticFiles mount)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(FRONTEND_PATH, "favicon.ico"), media_type="image/x-icon")

@app.get("/favicon-512.png", include_in_schema=False)
async def favicon_512():
    return FileResponse(os.path.join(FRONTEND_PATH, "favicon-512.png"), media_type="image/png")

@app.get("/favicon-32x32.png", include_in_schema=False)
async def favicon_32():
    return FileResponse(os.path.join(FRONTEND_PATH, "favicon-32x32.png"), media_type="image/png")

@app.get("/favicon-16x16.png", include_in_schema=False)
async def favicon_16():
    return FileResponse(os.path.join(FRONTEND_PATH, "favicon-16x16.png"), media_type="image/png")

@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon():
    return FileResponse(os.path.join(FRONTEND_PATH, "apple-touch-icon.png"), media_type="image/png")

@app.get("/manifest.json", include_in_schema=False)
async def manifest():
    return FileResponse(os.path.join(FRONTEND_PATH, "manifest.json"), media_type="application/manifest+json")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    return FileResponse(os.path.join(FRONTEND_PATH, "sitemap.xml"), media_type="application/xml")

@app.get("/robots.txt", include_in_schema=False)
async def robots():
    content = "User-agent: *\nAllow: /\nSitemap: https://indiasearch.site/sitemap.xml"
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content)

# Finally, mount the frontend directory to serve app.js, style.css, etc.
app.mount("/", StaticFiles(directory=FRONTEND_PATH), name="frontend")
