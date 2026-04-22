import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

# ── LLM selection ─────────────────────────────────────────────────────────────
# Priority: Gemini 1.5 Flash (free, officially listed in assignment spec)
#           → Groq/llama-3.1-8b-instant (free, used as fallback)
# Set whichever key you have in .env — the agent auto-detects.
# ──────────────────────────────────────────────────────────────────────────────

if GEMINI_API_KEY:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.3
    )
    print("[LLM] Using: Gemini 1.5 Flash (Google AI)")

elif GROQ_API_KEY:
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=GROQ_API_KEY,
        temperature=0.3
    )
    print("[LLM] Using: Groq - llama-3.1-8b-instant")

else:
    raise ValueError(
        "No LLM API key found.\n"
        "Set GEMINI_API_KEY (https://aistudio.google.com) — free & assignment-approved.\n"
        "OR set GROQ_API_KEY (https://console.groq.com) — free fallback."
    )
