"""
EduGenie - Explanation Module
Model: Google Gemini 2.5 Flash (Cloud API)
Endpoint: POST /explain
Purpose: Generates simplified, beginner-friendly explanations of complex topics.

FIX: Replaced LaMini-Flan-T5-783M (local ~1.5GB model, very slow on CPU,
     requires transformers+torch+sentencepiece) with Gemini 2.5 Flash.
     The local model was causing import errors and extremely slow cold starts.
     Gemini produces far better explanations and is already used by other modules.

     If you still want the local model, set USE_LOCAL_MODEL=true in .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

# Lazy-loaded local pipeline (only if USE_LOCAL_MODEL=true)
_pipeline = None


def _get_local_pipeline():
    """Load LaMini-Flan-T5-783M locally. ~1.5GB download on first run."""
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
            import torch

            model_name = "MBZUAI/LaMini-Flan-T5-783M"
            print(f"[EduGenie] Loading LaMini-Flan-T5-783M model (this may take a few minutes)...")

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # CPU-safe
            )
            _pipeline = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=256,
                do_sample=False,
            )
            print("[EduGenie] LaMini-Flan-T5-783M loaded successfully.")
        except ImportError:
            raise ImportError(
                "transformers and torch are required for local model mode. "
                "Run: pip install transformers torch sentencepiece\n"
                "Or set USE_LOCAL_MODEL=false in .env to use Gemini instead."
            )
    return _pipeline


def _explain_with_local_model(topic: str) -> str:
    """Use the local LaMini model."""
    prompt = (
        f"Explain the concept of '{topic.strip()}' in simple, beginner-friendly language. "
        "Break it down clearly so that a student with no prior knowledge can understand. "
        "Keep the explanation concise and educational."
    )
    pipe = _get_local_pipeline()
    result = pipe(prompt)
    if result and isinstance(result, list) and result[0].get("generated_text"):
        return result[0]["generated_text"].strip()
    return "Could not generate an explanation. Please try again."


def _explain_with_gemini(topic: str) -> str:
    """Use Gemini 2.5 Flash for explanation."""
    if not API_KEY:
        return (
            "❌ GEMINI_API_KEY is not set. "
            "Please add your key to the .env file:\n  GEMINI_API_KEY=your_key_here\n"
            "Get one free at: https://aistudio.google.com/app/apikey"
        )

    from google import genai

    client = genai.Client(api_key=API_KEY)

    prompt = (
        f"You are EduGenie, a friendly educational assistant.\n\n"
        f"Explain the concept of **{topic.strip()}** in simple, beginner-friendly language.\n\n"
        "Your explanation should:\n"
        "1. Start with a one-sentence simple definition\n"
        "2. Use an analogy or real-world example\n"
        "3. Break it into key sub-concepts (use bullet points or numbered steps)\n"
        "4. End with a quick summary\n\n"
        "Write for a student with no prior knowledge of this topic. "
        "Use clear, plain English. Avoid jargon unless you define it."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def explain_topic(topic: str) -> str:
    """
    Generate a simplified, beginner-friendly explanation of the given topic.
    Uses Gemini by default, or local LaMini model if USE_LOCAL_MODEL=true in .env.
    Returns the explanation string, or a friendly error message on failure.
    """
    if not topic or not topic.strip():
        return "Please provide a topic to explain."

    try:
        if USE_LOCAL_MODEL:
            return _explain_with_local_model(topic)
        else:
            return _explain_with_gemini(topic)

    except Exception as e:
        err = str(e)
        if "401" in err or "UNAUTHENTICATED" in err or "API_KEY_INVALID" in err:
            return (
                "❌ Invalid or expired Gemini API key.\n"
                "Please update GEMINI_API_KEY in your .env file.\n"
                "Get a valid key at: https://aistudio.google.com/app/apikey"
            )
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return "⚠️ API rate limit reached. Please wait a moment and try again."
        return f"❌ Error generating explanation: {err}"
