import json
import re
import requests
from config import GEMINI_API_KEY as API_KEY

URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
def generate_quiz_questions(passage: str) -> list:
    if not passage.strip():
        return [{"error": "Please provide a passage."}]
    prompt = f"""Create exactly 3 MCQs from this passage. Return ONLY a JSON array, no markdown.
Format: [{{"question":"...","options":["A text","B text","C text","D text"],"correct":"A"}}]
Passage: {passage}"""
    try:
        r = requests.post(
            URL,
            params={"key": API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
)

        print("Status Code:", r.status_code)
        print("Response:", r.text)

        r.raise_for_status()

        raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"error": "Could not parse quiz. Try a different passage."}]
    except Exception as e:
        return [{"error": str(e)}]