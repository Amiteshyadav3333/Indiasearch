import os
import re
from textwrap import shorten

from groq import Groq

# ========= GROQ CONFIG =========
GROQ_API_KEY = os.getenv("Grok_api_key") # Re-using user's key name
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

# ============ CLEANER ==============

def clean(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============ LOCAL AI =============

def local_summarize(query, docs):
    """
    Free fallback summary system
    """
    if not docs or len(docs) == 0:
        return None

    # Combine content from top results
    combined_text = ""
    for d in docs[:3]:
        title = d.get('title', '')
        snippet = d.get('snippet', '') or d.get('content', '')[:200]
        combined_text += f"{title}. {snippet} "

    combined_text = clean(combined_text)

    if len(combined_text) < 50:
        return f"Found {len(docs)} results for '{query}'. Check the links below for detailed information."

    # Create smart summary
    summary_text = combined_text[:300]
    
    return f"Based on search results: {summary_text}... See detailed results below."


# ========= GROQ MODE =============

def groq_vision_identify(b64_image):
    if not client:
        return None
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify what is in this image. If it's a person, give their full name and social media search keywords. If it's an object, name it. If it contains a QR code, barcode, or text, try to extract and summarize the information or link. Output ONLY the identification or extracted content string for search engine use."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Groq Vision Error: {e}")
        return None

def groq_chat(query, docs, lang="English", pdf_content=None):
    if not client:
        return None

    # Combine context
    context = ""
    if docs:
        for d in docs[:8]:
            context += f"\nTITLE: {d.get('title')}\nURL: {d.get('url')}\nTEXT: {d.get('content') or d.get('snippet')}\n"

    # PDF Context (Absolute Priority)
    pdf_info = f"\n--- CORE DOCUMENT CONTENT (SOURCE OF TRUTH) ---\n{pdf_content}\n" if pdf_content else ""

    # User's language and length instructions
    prompt = f"""
        User Query: {query}
        User Language: {lang}
        
        {pdf_info}
        
        STRICT INSTRUCTIONS FOR AI:
        1. IF A DOCUMENT (CORE DOCUMENT CONTENT) IS PROVIDED ABOVE, IT IS YOUR TOTAL FOCUS. RETAIN ALL INFORMATION FOR EVERY QUESTION.
        2. IF NO DOCUMENT IS PROVIDED, USE SEARCH CONTEXT OR YOUR INTERNAL KNOWLEDGE IMMEDIATELY.
        3. DO NOT ASK THE USER TO UPLOAD A FILE. NEVER SAY 'Please upload a PDF'. 
        4. IF NO FILE IS THERE, JUST GIVE THE BEST ANSWER FROM YOUR OWN BRAIN.
        5. FOR GENERAL QUESTIONS, PROVIDE A ROBUST 5-LINE ANSWER.
        6. NO META-TALK. DON'T SAY 'Understood' OR 'Processing'. START THE ANSWER NOW.
        7. Respond in {lang}.
        
        General Search Context:
        {context}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are IndiaSearch Precise Engine. You provide sharp, high-fidelity answers. For general overview questions, you give 4-5 lines of informative text. For specific entity requests, you give only the entity name."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3, # Slightly higher for better narrative flow in 4-5 lines
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        return None

# ===== MAIN FUNCTION TO CALL =======

def generate_ai_summary(query, docs, ai_mode=False, lang="English", pdf_content=None):
    """
    query: user search string
    docs: list of search results
    ai_mode: if true, provide the advanced chat experience
    """

    if not docs and not ai_mode and not pdf_content:
        return None

    try:
        if client:
            return groq_chat(query, docs, lang, pdf_content)
        else:
            return local_summarize(query, docs)

    except Exception as e:
        print("AI Summary Error:", e)
        return local_summarize(query, docs)
