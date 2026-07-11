import requests
from config import GEMINI_API_KEY as API_KEY
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def summarize_text(text: str) -> str:
    if not text.strip():
        return "Please provide some text."
    try:
        r = requests.post(URL, params={"key": API_KEY},
            json={"contents": [{"parts": [{"text": f"Summarize this clearly:\n\n{text}"}]}]}, timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {e}"