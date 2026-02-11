"""
LLMFactory v4.0 — Three-tier model routing.

- default:        google/gemini-3-flash-preview (OpenRouter) — Main executor
- fast_thinking:  llama-3.1-8b-instant (Groq) — Quick classification & critique
- deep_thinking:  tngtech/deepseek-r1t2-chimera:free (OpenRouter) — Deep reasoning
"""

import os
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq


class LLMFactory:

    @staticmethod
    def _ensure_openai_key():
        """Hack for LangChain validation — sets OPENAI_API_KEY env var."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    @staticmethod
    def get_default_model():
        """Main executor — Gemini 3 Flash via OpenRouter."""
        LLMFactory._ensure_openai_key()
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        # print(f"[LLM] Default Model: {bool(api_key)}")
        return ChatOpenAI(
            model="google/gemini-3-flash-preview",
            openai_api_key=api_key, # Explicit new param
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://aurora.agent.ai", # Required for OpenRouter
                "X-Title": "Aurora Agent", # Required for OpenRouter
            },
            temperature=0.3, # Slightly elevated for creativity
            request_timeout=60,
        )

    @staticmethod
    def get_fast_thinking_model():
        """Quick thinking — Groq Llama 3.1 8B Instant."""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                # print("[LLM] Using Groq for Fast Thinking")
                return ChatGroq(
                    temperature=0.0,
                    model_name="llama-3.1-8b-instant",
                    groq_api_key=api_key,
                    max_tokens=500,
                    request_timeout=15,
                )
            except Exception as e:
                print(f"[LLM] Groq init failed: {e}")
                pass

        # Fallback to default model
        print("[LLM] Fast Thinking Fallback to Default")
        return LLMFactory.get_default_model()

    @staticmethod
    def get_voice_model():
        """Voice synthesis — Groq Llama for natural speech generation."""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                # print("[LLM] Using Groq for Voice")
                return ChatGroq(
                    temperature=0.7,
                    model_name="llama-3.1-8b-instant",
                    groq_api_key=api_key,
                    max_tokens=1000,
                    request_timeout=15,
                )
            except Exception:
                pass

        # Fallback to default model
        return LLMFactory.get_default_model()

    @staticmethod
    def get_deep_thinking_model():
        """Deep reasoning — Llama 3.3 70B via Groq."""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                return ChatGroq(
                    temperature=0.2, # Low temp for reasoning
                    model_name="llama-3.3-70b-versatile",
                    groq_api_key=api_key,
                    max_tokens=2048,
                    request_timeout=30,
                )
            except Exception as e:
                print(f"[LLM] Groq deep thinking init failed: {e}")
                pass

        # Fallback to default model
        print("[LLM] Deep Thinking Fallback to Default")
        return LLMFactory.get_default_model()
