import requests
from config import GEMINI_API_KEY as API_KEY
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def get_answer(question: str) -> str:
    if not question.strip():
        return "Please provide a question."
    try:
        r = requests.post(URL, params={"key": API_KEY},
            json={"contents": [{"parts": [{"text": question}]}]}, timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {e}"