import requests
from config import GEMINI_API_KEY as API_KEY
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def get_learning_recommendations(topic: str) -> str:
    if not topic.strip():
        return "Please provide a topic."
    prompt = f"Create a complete beginner-to-advanced learning roadmap for: {topic}\nInclude: Beginner, Intermediate, Advanced levels, Resources, and Learning Tips. Use Markdown."
    try:
        r = requests.post(URL, params={"key": API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {e}"