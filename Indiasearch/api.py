import os
import sys
import logging
import aiohttp
import requests
import asyncio
import xml.etree.ElementTree as ET
import re
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth, credentials

load_dotenv()

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "indiasearch-975e1")

# Initialize Firebase via service account if possible, else use project ID
FIREBASE_CREDS_PATH = os.path.join(os.path.dirname(__file__), "firebase-credentials.json")
if os.path.exists(FIREBASE_CREDS_PATH):
    firebase_admin.initialize_app(credentials.Certificate(FIREBASE_CREDS_PATH))
else:
    # Use project ID if no credentials file found
    try:
        if not firebase_admin._apps:
           firebase_admin.initialize_app(options={'projectId': FIREBASE_PROJECT_ID})
    except Exception as e:
        print(f"Firebase initialization failed: {e}")

# === LOGGING SYSTEM ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("IndiasearchAPI")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = CURRENT_DIR
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import time

try:
    from . import ai_summary, search as search_module, translator
    from . import auth_store
except ImportError:
    import ai_summary
    import search as search_module
    import translator
    import auth_store

app = FastAPI()
auth_store.init_db()

# Simple In-Memory Query Cache
QUERY_CACHE = {}
CACHE_TTL = 10  # seconds (Dropped to 10s so Amitesh can test without needing server restarts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Elasticsearch
ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_USER = os.getenv("ELASTIC_USERNAME")
ELASTIC_PASS = os.getenv("ELASTIC_PASSWORD")

es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASS))

INDEX = "indiasearch"


class FirebaseLoginPayload(BaseModel):
    id_token: str

class SignupRequestPayload(BaseModel):
    identifier: str

class SignupVerifyPayload(BaseModel):
    identifier: str
    otp_code: str
    password: str

class LoginPayload(BaseModel):
    identifier: str
    password: str

class IdentifierPayload(BaseModel):
    identifier: str

class LogoutPayload(BaseModel):
    session_token: str

class PasswordResetConfirmPayload(BaseModel):
    identifier: str
    otp_code: str
    new_password: str

def normalize_and_validate_identifier(raw: str):
    identifier, id_type = auth_store.normalize_identifier(raw)
    if id_type == "email":
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", identifier):
            raise ValueError("Invalid email address.")
    else:
        digit_count = sum(c.isdigit() for c in identifier)
        if not (10 <= digit_count <= 15):
             raise ValueError("Invalid phone number format.")
    return identifier, id_type

def public_user(user: dict):
    return {
        "id": user.get("id"),
        "identifier": user.get("identifier"),
        "identifier_type": user.get("identifier_type"),
    }

def send_sms_message(phone: str, message: str):
    provider = (os.getenv("SMS_PROVIDER") or "").strip().lower()
    if not provider:
        return {"sent": False, "dev_mode": True}

    if provider != "twilio":
        raise RuntimeError(f"Unsupported SMS_PROVIDER '{provider}'. Use 'twilio'.")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    if not account_sid or not auth_token or not from_number:
        raise RuntimeError("Twilio SMS is enabled but credentials are missing.")

    to_number = phone if phone.startswith("+") else f"+{phone}"
    response = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
        auth=(account_sid, auth_token),
        data={"From": from_number, "To": to_number, "Body": message},
        timeout=15,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Twilio request failed with status {response.status_code}.")

    return {"sent": True, "dev_mode": False}

def issue_otp(identifier: str, identifier_type: str, purpose: str, message_prefix: str):
    otp_code = auth_store.create_otp(identifier, purpose=purpose)
    logger.info(f"DEV OTP for {identifier} [{purpose}]: {otp_code}")
    sms_result = {"sent": False, "dev_mode": True}

    if identifier_type == "phone":
        try:
            sms_result = send_sms_message(identifier, f"{message_prefix}: {otp_code}. Valid for 5 minutes.")
        except Exception as exc:
            logger.error(f"SMS delivery failed for {identifier}: {exc}")
    else:
        logger.info(f"Simulating email delivery to {identifier}: {otp_code}")
        sms_result["sent"] = True # Mocking email sending for dev

    return {
        "identifier": identifier,
        "otp_code": otp_code,
        "sms_result": sms_result,
    }


@app.get("/")
async def home():
    return {
        "service": "Indiasearch API",
        "status": "ok",
        "frontend": "Deploy the frontend/ directory on Vercel and point it to this Railway backend."
    }


@app.post("/auth/firebase-login")
async def firebase_login(payload: FirebaseLoginPayload):
    try:
        # Verify Token
        decoded_token = auth.verify_id_token(payload.id_token)
        uid = decoded_token['uid']
        
        # Determine the identifier (Phone or Email)
        identifier = decoded_token.get('email') or decoded_token.get('phone_number')
        if not identifier:
             return JSONResponse({"error": "Identifier not found in Firebase token."}, status_code=400)

        # Map to local account system
        identifier_type = "email" if "@" in identifier else "phone"
        
        user = auth_store.get_user_by_identifier(identifier)
        if not user:
            # Auto-create local user if not exists (using UID as dummy password)
            auth_store.create_user(identifier, identifier_type, uid)
            user = auth_store.get_user_by_identifier(identifier)
        
        session_token = auth_store.create_session(user["id"])
        return {
            "message": "Firebase login success.",
            "session_token": session_token,
            "user": public_user(user)
        }
    except Exception as e:
        logger.error(f"Firebase Auth Error: {e}")
        return JSONResponse({"error": f"Authentication failed: {str(e)}"}, status_code=401)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/request-signup-otp")
async def request_signup_otp(payload: SignupRequestPayload):
    try:
        identifier, id_type = normalize_and_validate_identifier(payload.identifier)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    if auth_store.get_user_by_identifier(identifier):
        return JSONResponse({"error": "An account with this identifier already exists."}, status_code=400)

    otp_data = issue_otp(identifier, id_type, "signup_verification", "Your IndiaSearch verification code")
    return {
        "message": f"Verification code sent to {identifier}.",
        "identifier": identifier,
        "dev_otp": otp_data["otp_code"] if otp_data["sms_result"]["dev_mode"] else None,
    }


@app.post("/auth/verify-and-signup")
async def verify_and_signup(payload: SignupVerifyPayload):
    try:
        identifier, id_type = normalize_and_validate_identifier(payload.identifier)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    if len(payload.password) < 8:
        return JSONResponse({"error": "Password must be at least 8 characters long."}, status_code=400)

    if auth_store.get_user_by_identifier(identifier):
        return JSONResponse({"error": "An account with this identifier already exists."}, status_code=400)

    if not auth_store.verify_otp(identifier, payload.otp_code, purpose="signup_verification"):
        return JSONResponse({"error": "Invalid or expired OTP."}, status_code=400)

    auth_store.create_user(identifier, id_type, payload.password)
    user = auth_store.get_user_by_identifier(identifier)
    session_token = auth_store.create_session(user["id"])
    return {
        "message": "Account created successfully.",
        "session_token": session_token,
        "user": public_user(user)
    }


@app.post("/auth/login")
async def login(payload: LoginPayload):
    try:
        identifier, id_type = normalize_and_validate_identifier(payload.identifier)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    user = auth_store.get_user_by_identifier(identifier)
    if not user or not auth_store.verify_password(payload.password, user["password_hash"]):
        return JSONResponse({"error": "Invalid credentials."}, status_code=401)

    session_token = auth_store.create_session(user["id"])
    return {
        "message": "Login successful.",
        "session_token": session_token,
        "user": public_user(user)
    }


@app.get("/auth/me")
async def me(session_token: str):
    user = auth_store.get_user_by_session(session_token)
    if not user:
        return JSONResponse({"error": "Session expired or invalid."}, status_code=401)
    return {"user": public_user(user)}


@app.get("/auth/profile")
async def profile(session_token: str):
    user = auth_store.get_user_by_session(session_token)
    if not user:
        return JSONResponse({"error": "Session expired or invalid."}, status_code=401)
    history = auth_store.get_search_history(user["id"], limit=12)
    return {"user": public_user(user), "history": history}


@app.get("/auth/history")
async def history(session_token: str):
    user = auth_store.get_user_by_session(session_token)
    if not user:
        return JSONResponse({"error": "Session expired or invalid."}, status_code=401)
    return {"history": auth_store.get_search_history(user["id"], limit=20)}


@app.post("/auth/logout")
async def logout(payload: LogoutPayload):
    auth_store.delete_session(payload.session_token)
    return {"message": "Logged out successfully."}


@app.post("/auth/request-password-reset")
async def request_password_reset(payload: IdentifierPayload):
    try:
        identifier, id_type = normalize_and_validate_identifier(payload.identifier)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    
    user = auth_store.get_user_by_identifier(identifier)
    if not user:
        return JSONResponse({"error": "No account found for this identifier."}, status_code=404)

    otp_data = issue_otp(identifier, id_type, "password_reset", "Your IndiaSearch password reset code")
    return {
        "message": "Password reset code sent.",
        "identifier": identifier,
        "dev_otp": otp_data["otp_code"] if otp_data["sms_result"]["dev_mode"] else None,
    }


@app.post("/auth/reset-password")
async def reset_password(payload: PasswordResetConfirmPayload):
    try:
        identifier, id_type = normalize_and_validate_identifier(payload.identifier)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    
    user = auth_store.get_user_by_identifier(identifier)
    if not user:
        return JSONResponse({"error": "No account found for this identifier."}, status_code=404)
    if len(payload.new_password) < 8:
        return JSONResponse({"error": "Password must be at least 8 characters long."}, status_code=400)
    if not auth_store.verify_otp(identifier, payload.otp_code, purpose="password_reset"):
        return JSONResponse({"error": "Invalid or expired reset code."}, status_code=400)

    auth_store.update_password_by_identifier(identifier, payload.new_password)
    return {"message": "Password updated successfully. Please login with your new password."}


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
async def search(q: str, page: int = 1, filter: str = "all", ai_mode: bool = False, session_token: str | None = None):
    # Enforce Auth
    if not session_token:
        return JSONResponse({"error": "Authentication required. Please login or signup to use IndiaSearch."}, status_code=401)
        
    user = auth_store.get_user_by_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required. Please login or signup to use IndiaSearch."}, status_code=401)
        
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
        search_warning = None
        search_suggestions = []
        
        # Determine data array
        results = []
        total_hits = 0
        
        if filter == "all":
            results, total_hits = await search_module.search_query(es, INDEX, translated, page)
        elif filter == "images":
            results, total_hits = await search_module.global_image_search(translated, page)
            if results and any("Fallback Preview" in str(item.get("snippet", "")) for item in results):
                search_warning = "No live image results, showing related sources."
        elif filter == "news":
            all_news = await fetch_realtime_news(translated)
            total_hits = len(all_news)
            size = 10
            from_ = (page - 1) * size
            results = all_news[from_ : from_ + size]
        else: # videos
            results, total_hits = await search_module.global_video_search(translated, page)

        logger.info(f"RESULTS COUNT: {len(results)} / TOTAL: {total_hits}")

        if total_hits == 0:
            if getattr(search_module, "DDGS", None) is None:
                search_warning = (
                    "Live web search fallback is unavailable in the current Python environment, "
                    "so only indexed results can be shown right now."
                )
            else:
                search_warning = (
                    "We could not find matching indexed results for this query right now."
                )

            search_suggestions = [
                f"Try a shorter query than '{q}'",
                "Use a simpler spelling or broader keywords",
                "Switch between All, News, Images, and Videos filters"
            ]
        
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
            "total_pages": (total_hits + 9) // 10,
            "warning": search_warning,
            "suggestions": search_suggestions
        }

        if session_token:
            user = auth_store.get_user_by_session(session_token)
            if user and page == 1:
                auth_store.add_search_history(user["id"], q, filter, ai_mode)
        
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
