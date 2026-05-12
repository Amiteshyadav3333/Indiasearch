import os
import re
import groq
from google import genai
from dotenv import load_dotenv
from app.utils import translator

load_dotenv()

# --- Engines Initialization ---
groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("Grok_api_key")
groq_client = groq.Groq(api_key=groq_api_key, timeout=12.0) if groq_api_key else None

gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    gemini_client = genai.Client(api_key=gemini_api_key)
else:
    gemini_client = None

def groq_vision_identify(image_b64):
    """Fallback vision identify using Groq"""
    if not groq_client: return None
    try:
        completion = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "What food is in this image? Provide full nutritional analysis in JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            }],
            model="llama-3.2-11b-vision-preview",
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Groq Vision Error: {e}")
        return None

def _source_context(docs, limit=8):
    context = ""
    if docs:
        for idx, d in enumerate(docs[:limit], start=1):
            context += f"\nSOURCE [{idx}]\nTITLE: {d.get('title')}\nURL: {d.get('url')}\nTEXT: {d.get('content') or d.get('snippet')}\n"
    return context


def _extractive_summary(query, docs, lang="English", advanced=False):
    usable = []
    for idx, d in enumerate((docs or [])[:8], start=1):
        title = (d.get("title") or "").strip()
        text = (d.get("snippet") or d.get("content") or "").strip()
        url = (d.get("url") or "").strip()
        if title or text:
            usable.append((idx, title, text, url))

    if not usable:
        answer = (
            f"I could not reach the live AI provider right now, but I also did not receive enough web sources for '{query}'. "
            "Try a more specific query or switch to All/News for broader sources."
        )
        return translator.translate_result(answer, _language_name_to_code(lang)) if lang != "English" else answer

    if advanced:
        bullets = []
        for idx, title, text, _ in usable[:6]:
            summary = text or title
            summary = re.sub(r"\s+", " ", summary)[:260]
            bullets.append(f"- **{title or 'Source'}** [{idx}]: {summary}")
        answer = (
            f"## Answer\nBased on the strongest available sources for **{query}**, here is the clearest synthesis.\n\n"
            + "\n".join(bullets)
            + "\n\n## What to check next\nOpen the cited sources for the latest details, dates, prices, or official notices."
        )
        return translator.translate_result(answer, _language_name_to_code(lang)) if lang != "English" else answer

    first = usable[0]
    supporting = " ".join((text or title) for _, title, text, _ in usable[:3])
    supporting = re.sub(r"\s+", " ", supporting)[:520]
    answer = f"{supporting} [{first[0]}]"
    return translator.translate_result(answer, _language_name_to_code(lang)) if lang != "English" else answer


def _language_name_to_code(name="English"):
    reverse = {
        "English": "en", "Hindi": "hi", "Assamese": "as", "Bengali": "bn",
        "Bodo": "brx", "Dogri": "doi", "Gujarati": "gu", "Kannada": "kn",
        "Kashmiri": "ks", "Konkani": "gom", "Maithili": "mai", "Malayalam": "ml",
        "Manipuri": "mni", "Marathi": "mr", "Nepali": "ne", "Odia": "or",
        "Punjabi": "pa", "Sanskrit": "sa", "Santali": "sat", "Sindhi": "sd",
        "Tamil": "ta", "Telugu": "te", "Urdu": "ur", "Bhojpuri": "bho"
    }
    return reverse.get(name, "en")


def gemini_chat(query, docs, lang="English", pdf_content=None, intent="general", history=None):
    if not gemini_client: return None

    # Combine context
    context = _source_context(docs)

    pdf_info = f"\n--- CORE DOCUMENT CONTENT ---\n{pdf_content}\n" if pdf_content else ""

    if intent == "nutrition":
        system_msg = f"""You are IndiaSearch Nutritionist. For the given food query, provide nutritional analysis EXCLUSIVELY in JSON format.
        All human-readable values such as name, tags, description, and tip must be in {lang}.
        {{ "intent": "nutrition", "name": "food name in {lang}", "calories": 100, "nutrients": {{"protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}}, "daily_values": {{"protein": 0, "carbs": 0, "fat": 0}}, "tags": [], "tip": "..." }}"""
    elif intent == "advanced":
        system_msg = f"""You are IndiaSearch Advanced Research. Produce a Perplexity-style answer in {lang}.
        Use the supplied sources only, cite claims with [1], [2], and organize the response with short sections:
        Overview, Key points, Details, Sources to verify. Be direct, useful, and complete.
        The full final answer must be in {lang}, even if sources are in another language.
        """
    else:
        system_msg = f"""You are IndiaSearch Precise Engine. Answer clearly in {lang}. Use citations [1], [2]. 4-5 lines max.
        The full final answer must be in {lang}, even if the search sources are in another language.
        
        OFFICIAL INFO ABOUT INDIASEARCH (MANDATORY):
        - Created by: Amitesh Kumar Yadav and students of Gurukul Kangri University.
        - Mission: To promote India's local businesses and optimized for job search.
        - Services: AI Search Engine, downloader.indiasearch, and chat.indiasearch.site.
        - Motto: Built with love in India.
        """

    # Build prompt with history
    full_prompt = f"{system_msg}\n\n"
    if history:
        for msg in history:
            full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
    
    full_prompt += f"CONTEXT:\n{pdf_info}\n{context}\n\nUSER QUERY: {query}"

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def groq_chat(query, docs, lang="English", pdf_content=None, intent="general", history=None):
    if not groq_client: return None
    
    context = _source_context(docs)

    pdf_info = f"\n--- CORE DOCUMENT CONTENT ---\n{pdf_content}\n" if pdf_content else ""
    
    if intent == "nutrition":
        system_msg = f"You are IndiaSearch Nutritionist. Return nutritional analysis in JSON format. All human-readable values must be in {lang}."
    elif intent == "advanced":
        system_msg = f"""You are IndiaSearch Advanced Research. Produce a Perplexity-style answer in {lang}.
        Use citations [1], [2]. Include short sections: Overview, Key points, Details, Sources to verify.
        The full final answer must be in {lang}, even if sources are in another language.
        """
    else:
        system_msg = f"""You are IndiaSearch Precise Engine. Answer in {lang}. 4-5 lines. Citations [1], [2].
        The full final answer must be in {lang}, even if the search sources are in another language.
        
        OFFICIAL INFO ABOUT INDIASEARCH (MANDATORY):
        - Created by: Amitesh Kumar Yadav and students of Gurukul Kangri University.
        - Mission: To promote India's local businesses and optimized for job search.
        - Services: AI Search Engine, downloader.indiasearch, and chat.indiasearch.site.
        - Motto: Built with love in India.
        """

    messages = [{"role": "system", "content": system_msg}]
    if history:
        for msg in history: messages.append(msg)
    
    messages.append({"role": "user", "content": f"CONTEXT:\n{pdf_info}\n{context}\n\nQUERY: {query}"})

    try:
        completion = groq_client.chat.completions.create(messages=messages, model="llama-3.3-70b-versatile")
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Groq Error: {e}")
        return None

def generate_ai_summary(query, docs, ai_mode=False, lang="English", pdf_content=None, intent="general", history=None):
    # PRIORITIZE GEMINI for Advanced and Nutrition as requested
    if intent == "nutrition" or ai_mode:
        res = gemini_chat(query, docs, lang, pdf_content, intent, history)
        if res: return res
    
    # Fallback to Groq, then a deterministic source-based answer so Ask AI never dead-ends.
    return (
        groq_chat(query, docs, lang, pdf_content, intent, history)
        or _extractive_summary(query, docs, lang, advanced=(intent == "advanced"))
    )
