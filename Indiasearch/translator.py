import os
import re

# ========= OPTIONAL OPENAI =========
USE_OPENAI = False   # change later when you add key

if USE_OPENAI:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ----------- BASIC LANGUAGE DETECT --------------

def detect_language(text):
    """Very simple language detector"""

    hindi_chars = re.findall(r"[\u0900-\u097F]", text)

    if len(hindi_chars) > 0:
        return "hi"

    return "en"


# ----------- SIMPLE OFFLINE TRANSLATOR -----------

# You can expand this dictionary later 🙂
BASIC_HI_EN = {
    "facebook": "facebook",
    "search": "search",
    "download": "download",
    "kya": "what",
    "kaise": "how",
    "india": "india",
    "app": "app",
    "game": "game"
}

BASIC_EN_HI = {v: k for k, v in BASIC_HI_EN.items()}


def offline_translate(text, src, target):

    words = text.lower().split()
    output = []

    for w in words:
        if src == "hi" and w in BASIC_HI_EN:
            output.append(BASIC_HI_EN[w])
        elif src == "en" and w in BASIC_EN_HI:
            output.append(BASIC_EN_HI[w])
        else:
            output.append(w)

    return " ".join(output)


# ----------- OPENAI TRANSLATION -------------------

def openai_translate(text, target_lang):

    prompt = f"""
Translate this text to language code `{target_lang}`.
Only output translated text.

Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()



# ----------- PUBLIC API FUNCTIONS -----------------

def translate_query_to_english(query):
    """
    user query → English
    """

    lang = detect_language(query)

    if lang == "en":
        return query, "en"

    # Try OpenAI first
    if USE_OPENAI:
        translated = openai_translate(query, "en")
        return translated, lang

    # Offline fallback
    translated = offline_translate(query, "hi", "en")
    return translated, lang



def translate_result(text, target_lang):
    """
    translate search result summary back to user lang
    """

    if target_lang == "en":
        return text

    if USE_OPENAI:
        return openai_translate(text, target_lang)

    # offline fallback
    return offline_translate(text, "en", "hi")