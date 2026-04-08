# app/integrations/grok_client.py
# 🤖 Grok / AI API Client
# ----------------------------------------
# Wraps xAI Grok API (or Gemini / OpenAI as fallback).
# Used for: AI summaries, explanations, query understanding.
# API docs: https://docs.x.ai/api
#
# Required env: GROK_API_KEY (in .env)
#               GROK_MODEL   (default: grok-3-mini)

import requests
from app.config.settings import Settings


class GrokClient:
    """Grok (xAI) API wrapper for AI text generation."""

    BASE_URL = "https://api.x.ai/v1"

    @classmethod
    def chat_completion(cls, messages: list, max_tokens: int = 500) -> str:
        """
        Send a chat-completion request to Grok.
        Returns the assistant's reply as a string.
        """
        # TODO:
        # headers = {
        #     "Authorization": f"Bearer {Settings.GROK_API_KEY}",
        #     "Content-Type": "application/json",
        # }
        # payload = {
        #     "model": Settings.GROK_MODEL,
        #     "messages": messages,
        #     "max_tokens": max_tokens,
        # }
        # resp = requests.post(f"{cls.BASE_URL}/chat/completions", headers=headers, json=payload)
        # resp.raise_for_status()
        # return resp.json()["choices"][0]["message"]["content"]
        raise NotImplementedError("Migrate from Indiasearch/ai_summary.py")

    @classmethod
    def summarize(cls, text: str, lang: str = "hi") -> str:
        """Convenience method: summarize text in given language."""
        # TODO: Build prompt and call chat_completion
        raise NotImplementedError
