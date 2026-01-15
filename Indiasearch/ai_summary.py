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

    text = ""

    for d in docs[:5]:
        text += f" {d.get('title','')} - {d.get('content','')}"

    text = clean(text)

    if len(text) < 40:
        return None

    text = shorten(text, 900)

    return f"""
AI Smart Answer 🧠

Based on your search "{query}", here is a helpful summary:

{text[:280]}...
    """.strip()


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