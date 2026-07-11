from dotenv import load_dotenv
import os

# Load environment variables from .env (if present)
load_dotenv()

# Public config values
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
