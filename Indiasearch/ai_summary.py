import os
import re
from textwrap import shorten

# ========= OPTIONAL OPENAI =========
USE_OPENAI = False   # change later when you add key

if USE_OPENAI:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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


# ========= OPENAI MODE =============

def openai_summary(query, docs):

    content = ""

    for d in docs[:6]:
        content += f"\nTITLE: {d.get('title')}\nTEXT: {d.get('content')}\n"

    prompt = f"""
You are a search engine AI assistant.
Summarize the key answer for the user query:

Query: {query}

Use short, clear bullet points.
Avoid fake or unverified claims.
Then end with: "Results below 👇"

Content:
{content}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    return response.choices[0].message.content


# ===== MAIN FUNCTION TO CALL =======

def generate_ai_summary(query, docs):
    """
    query: user search string
    docs: list of elasticsearch docs
    """

    if not docs:
        return None

    try:
        if USE_OPENAI:
            return openai_summary(query, docs)

        else:
            return local_summarize(query, docs)

    except Exception as e:
        print("AI Summary Error:", e)
        return None