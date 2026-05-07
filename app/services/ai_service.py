import os
import groq
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- Engines Initialization ---
groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("Grok_api_key")
groq_client = groq.Groq(api_key=groq_api_key) if groq_api_key else None

gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

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

def gemini_chat(query, docs, lang="English", pdf_content=None, intent="general", history=None):
    if not gemini_model: return None

    # Combine context
    context = ""
    if docs:
        for idx, d in enumerate(docs[:8], start=1):
            context += f"\nSOURCE [{idx}]\nTITLE: {d.get('title')}\nURL: {d.get('url')}\nTEXT: {d.get('content') or d.get('snippet')}\n"

    pdf_info = f"\n--- CORE DOCUMENT CONTENT ---\n{pdf_content}\n" if pdf_content else ""

    if intent == "nutrition":
        system_msg = """You are IndiaSearch Nutritionist. For the given food query, provide nutritional analysis EXCLUSIVELY in JSON format:
        { "intent": "nutrition", "name": "Hindi + English", "calories": 100, "nutrients": {"protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}, "daily_values": {"protein": 0, "carbs": 0, "fat": 0}, "tags": [], "tip": "..." }"""
    else:
        system_msg = f"""You are IndiaSearch Precise Engine. Answer clearly in {lang}. Use citations [1], [2]. 4-5 lines max.
        
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
        response = gemini_model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def groq_chat(query, docs, lang="English", pdf_content=None, intent="general", history=None):
    if not groq_client: return None
    
    context = ""
    if docs:
        for idx, d in enumerate(docs[:8], start=1):
            context += f"\nSOURCE [{idx}]\nTITLE: {d.get('title')}\nURL: {d.get('url')}\nTEXT: {d.get('content') or d.get('snippet')}\n"

    pdf_info = f"\n--- CORE DOCUMENT CONTENT ---\n{pdf_content}\n" if pdf_content else ""
    
    if intent == "nutrition":
        system_msg = "You are IndiaSearch Nutritionist. Return nutritional analysis in JSON format."
    else:
        system_msg = f"""You are IndiaSearch Precise Engine. Answer in {lang}. 4-5 lines. Citations [1], [2].
        
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
    
    # Fallback to Groq
    return groq_chat(query, docs, lang, pdf_content, intent, history) or "I'm sorry, I couldn't generate a summary."
