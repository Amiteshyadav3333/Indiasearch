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
import time
from datetime import datetime
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
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
from app.api import nutrition
from app.models import about_content

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("IndiasearchAPI")

# --- App Initialization ---
app = FastAPI(title="IndiaSearch Intelligent Engine")

# Ensure required directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs(os.path.join("uploads", "about"), exist_ok=True)

app.include_router(nutrition.router)
auth_store.init_db()
about_content.init_about_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

IS_RENDER = os.getenv("RENDER", "false").lower() == "true"
DISABLE_CRAWLER = os.getenv("DISABLE_CRAWLER", "false").lower() == "true" or IS_RENDER

async def daily_crawler_task():
    if DISABLE_CRAWLER:
        logger.info("[Auto-Crawler] Disabled on Render/low-memory environment. Skipping crawl.")
        return
    while True:
        try:
            logger.info("[Auto-Crawler] Starting daily background web crawl...")
            # Reduced limits on cloud deployment to save memory
            crawler = Crawler(max_pages=50, max_depth=1, max_concurrency=3)
            await crawler.run(SEED_URLS)
            logger.info("[Auto-Crawler] Daily crawl complete. Sleeping for 24 hours.")
        except Exception as e:
            logger.error(f"[Auto-Crawler] Error: {e}")
        await asyncio.sleep(86400)

async def hot_cache_warmer_task():
    """Warms cache for top queries. Reduced frequency on Render free tier."""
    # Wait longer on Render to let server stabilize before using memory
    wait_time = 600 if IS_RENDER else 300
    await asyncio.sleep(wait_time)
    while True:
        try:
            # Warm fewer queries on Render to save RAM
            top_n = 5 if IS_RENDER else 20
            await hot_query_store.warm_hot_cache(run_parallel_pipeline, top_n=top_n)
        except Exception as e:
            logger.error(f"[HotCache] Warming error: {e}")
        # Re-warm every 60 min on Render, 30 min locally
        await asyncio.sleep(3600 if IS_RENDER else 1800)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(daily_crawler_task())
    if not DISABLE_CRAWLER:  # Only warm cache when crawler is active
        asyncio.create_task(hot_cache_warmer_task())
    elif not IS_RENDER:
        asyncio.create_task(hot_cache_warmer_task())
    logger.info(f"[Startup] Render={IS_RENDER} | Crawler={'OFF' if DISABLE_CRAWLER else 'ON'}")


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
async def search(q: str, page: int = 1, filter: str = "all", lang: str = "en", output_lang: str | None = None, ai_mode: bool = False, advanced_mode: bool = False, session_token: str | None = None, age_verified: str = "false", history: str | None = None, lat: float | None = None, lon: float | None = None, limit: int = 10):
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

        # Parse History if provided
        history_list = None
        if history:
            try:
                history_list = json.loads(history)
            except:
                logger.warning("[Search] Failed to parse history JSON")

        # Execute the Intelligent Pipeline
        response = await run_parallel_pipeline(
            query=q, 
            page=page, 
            filter=filter,
            lang=output_lang or lang or "en", 
            force_ai=force_ai,
            pdf_content=pdf_content,
            age_verified=(age_verified == "true"),
            advanced_mode=advanced_mode,
            history=history_list,
            lat=lat,
            lon=lon,
            limit=limit
        )
        
        # Save history if logged in
        if valid_session_token:
            user = auth_store.get_user_by_session(valid_session_token)
            if user:
                auth_store.add_search_history(user["id"], q, filter, ai_mode)

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
                title = soup.title.string if soup.title and soup.title.string else "Untitled"
                return {"title": title, "content": text[:10000]}
    except Exception as e:
        logger.warning(f"[ReadArticle] Failed to read {url}: {e}")
        return {"error": "Blocked"}

@app.get("/download-image")
async def download_image(url: str):
    if not url.startswith(("http://", "https://", "/")):
        return JSONResponse({"error": "Invalid image URL"}, 400)

    try:
        if url.startswith("/"):
            local_path = url.lstrip("/")
            if not os.path.exists(local_path):
                return JSONResponse({"error": "Image not found"}, 404)
            filename = os.path.basename(local_path) or "IndiaSearch_Image.jpg"
            return FileResponse(local_path, filename=filename, media_type="application/octet-stream")

        headers = {
            "User-Agent": "Mozilla/5.0 (IndiaSearch Image Downloader)",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        upstream = requests.get(url, headers=headers, stream=True, timeout=15)
        upstream.raise_for_status()

        content_type = upstream.headers.get("content-type", "image/jpeg").split(";")[0]
        ext = {
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
            "image/svg+xml": "svg",
            "image/jpeg": "jpg",
        }.get(content_type, "jpg")
        filename = f"IndiaSearch_Image_{int(time.time())}.{ext}"

        return StreamingResponse(
            upstream.iter_content(chunk_size=8192),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.warning(f"[ImageDownload] Failed for {url}: {e}")
        return JSONResponse({"error": "Image download failed"}, 500)

# ── About Content Management (Admin Only) ──
@app.get("/about-content")
async def get_about_data():
    return about_content.get_about_content()

def is_admin(session_token: str | None):
    if not session_token: return False
    try:
        user = auth_store.get_user_by_session(session_token)
        if not user: return False
        # The founder's email/identifier should be set in environment
        admin_id = os.getenv("ADMIN_IDENTIFIER", "amitesh@indiasearch.site")
        return user["identifier"] == admin_id
    except Exception:
        return False

def get_session_user(session_token: str | None):
    valid_session = normalize_session_token(session_token)
    if not valid_session:
        return None
    try:
        return auth_store.get_user_by_session(valid_session)
    except Exception:
        return None

@app.post("/about-content/publication")
async def upload_publication(
    title: str = Form(...),
    description: str = Form(...),
    topic: str = Form(...),
    research_duration: str = Form(...),
    unique_points: str = Form(...),
    pub_type: str = Form("paper"),
    file: UploadFile = File(...),
    session_token: str = Form(...)
):
    if not session_token or session_token.strip().lower() in {"undefined", "null", "none", ""}:
        return JSONResponse({"error": "Session missing. Please refresh and try again."}, 400)
    
    try:
        # Save file locally
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if file_ext != "pdf":
            return JSONResponse({"error": "Only PDF research papers are allowed."}, 400)

        safe_name = f"pub_{int(time.time())}.{file_ext}"
        save_path = os.path.join("uploads", "about", safe_name)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        
        file_url = f"/uploads/about/{safe_name}"
        user = get_session_user(session_token)
        owner_identifier = user["identifier"] if user else ""
        about_content.add_publication(
            title=title,
            description=description,
            file_url=file_url,
            pub_type=pub_type,
            topic=topic,
            research_duration=research_duration,
            unique_points=unique_points,
            owner_session_token=session_token,
            owner_identifier=owner_identifier
        )
        return {"message": "Research paper uploaded successfully", "url": file_url}
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)

@app.post("/about-content/media")
async def upload_media(
    title: str = Form(...),
    video_url: str = Form(...), # Usually a YouTube link
    thumbnail: UploadFile = File(None),
    session_token: str = Form(...)
):
    if not is_admin(session_token):
        return JSONResponse({"error": "Admin access required"}, 403)
    
    try:
        thumb_url = None
        if thumbnail:
            file_ext = thumbnail.filename.split(".")[-1]
            safe_name = f"thumb_{int(time.time())}.{file_ext}"
            save_path = os.path.join("uploads", "about", safe_name)
            with open(save_path, "wb") as f:
                f.write(await thumbnail.read())
            thumb_url = f"/uploads/about/{safe_name}"
        
        about_content.add_media(title, video_url, thumb_url)
        return {"message": "Media added successfully"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)

@app.delete("/about-content/publication/{pub_id}")
async def delete_pub(pub_id: int, session_token: str):
    publication = about_content.get_publication(pub_id)
    if not publication:
        return JSONResponse({"error": "Publication not found"}, 404)

    user = get_session_user(session_token)
    owns_publication = bool(session_token and publication.get("owner_session_token") == session_token)
    if user and publication.get("owner_identifier"):
        owns_publication = owns_publication or publication.get("owner_identifier") == user.get("identifier")
    if not owns_publication and not is_admin(session_token):
        return JSONResponse({"error": "You can delete only your own research paper"}, 403)

    about_content.delete_publication(pub_id)
    file_url = publication.get("file_url") or ""
    if file_url.startswith("/uploads/about/"):
        try:
            os.remove(file_url.lstrip("/"))
        except OSError:
            pass
    return {"message": "Deleted"}

@app.delete("/about-content/media/{media_id}")
async def delete_med(media_id: int, session_token: str):
    if not is_admin(session_token):
        return JSONResponse({"error": "Admin access required"}, 403)
    about_content.delete_media(media_id)
    return {"message": "Deleted"}

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
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/", StaticFiles(directory=FRONTEND_PATH), name="frontend")
