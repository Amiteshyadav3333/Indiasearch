from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai
import base64
import json
import re
import os

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])

# Gemini client — uses GEMINI_API_KEY from env
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
    # Using gemini-1.5-flash for speed and reliability
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

SYSTEM_PROMPT = """You are a nutrition expert AI for IndiaSearch, India's search engine.
Analyze the food/fruit/dish and return ONLY a valid JSON object. No markdown, no explanation, just pure JSON.

Return this exact structure:
{
  "name": "Food name in Hindi + English (e.g. समोसा / Samosa)",
  "description": "1 line description mentioning origin (Indian/Western/etc)",
  "calories": 150,
  "nutrients": {
    "protein": 5.2,
    "carbs": 28.4,
    "fat": 3.1,
    "fiber": 2.5,
    "sugar": 8.2,
    "sodium": 120
  },
  "daily_values": {
    "protein": 10,
    "carbs": 9,
    "fat": 4,
    "fiber": 10
  },
  "tags": ["High Fiber", "Low Fat", "Vitamin C Rich"],
  "tag_colors": ["green", "green", "amber"],
  "tip": "Hindi mein ek helpful nutrition tip (2-3 sentences)"
}

All numbers per 100g serving. Be accurate for Indian foods like dal, roti, samosa, biryani, chai, etc.
tag_colors must be one of: green, amber, red"""


class TextQuery(BaseModel):
    query: str


class ImageQuery(BaseModel):
    image_base64: str  # pure base64, no data:image prefix
    media_type: str = "image/jpeg"  # image/jpeg, image/png, image/webp


def parse_nutrition_response(text: str) -> dict:
    """Gemini ke response se JSON extract karo safely"""
    try:
        # Remove markdown code blocks if present
        clean = re.sub(r"```json|```", "", text).strip()
        # Find first { and last } to be extra safe
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start != -1 and end != 0:
            clean = clean[start:end]
        return json.loads(clean)
    except Exception as e:
        print(f"Parse Error: {e} | Raw: {text}")
        raise json.JSONDecodeError("Failed to parse", text, 0)


@router.post("/text")
async def analyze_by_text(body: TextQuery):
    """Text se food analyze karo — e.g. 'samosa', 'dal roti'"""
    if not model:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")
    
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query empty hai")

    try:
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nFood item: \"{body.query}\". Per 100g nutrition details do."
        )
        text = response.text
        result = parse_nutrition_response(text)
        result["intent"] = "nutrition"
        return JSONResponse(content=result)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI response parse nahi hua")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image")
async def analyze_by_image(body: ImageQuery):
    """Image se food analyze karo"""
    if not model:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")

    if not body.image_base64:
        raise HTTPException(status_code=400, detail="Image data missing hai")

    try:
        response = model.generate_content([
            {
                "mime_type": body.media_type,
                "data": base64.b64decode(body.image_base64)
            },
            f"{SYSTEM_PROMPT}\n\nIs image mein kya food hai? Uski nutrition details do."
        ])
        text = response.text
        result = parse_nutrition_response(text)
        result["intent"] = "nutrition"
        return JSONResponse(content=result)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI response parse nahi hua")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
