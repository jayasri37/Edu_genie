"""
EduGenie Learning Assistant - Main FastAPI Application
======================================================
Architecture:
  Frontend (HTML/CSS Jinja2) --> FastAPI Backend --> AI Modules --> Response

Endpoints:
  GET  /qa                    -> QnA Module (Gemini 2.5 Flash)
  POST /explain               -> Explanation Module (Gemini 2.5 Flash)
  POST /quiz                  -> Quiz Generation Module (Gemini 2.5 Flash)
  POST /summarize             -> Summarization Module (Gemini 2.5 Flash)
  GET  /learn/recommendations -> Learning Path Module (Gemini 2.5 Flash)

Storage: File-based JSON (data/*.json) matching ER Diagram entities.

Run:
  cd edugenie
  uvicorn main:app --reload
  Then open: http://localhost:8000

FIX: Removed broken relative imports (from .module import ...).
     Relative imports only work when the package is installed or run with -m.
     Running `uvicorn main:app` treats main.py as a top-level script,
     so all imports must be absolute (from module import ...).
"""

import os
import time
import json as _json
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ─── Import AI Modules (absolute imports — NOT relative) ──────────────────────
from qna import get_answer
from explanation_module import explain_topic
from quiz_module import generate_quiz_questions
from summary_module import summarize_text
from learning_path import get_learning_recommendations

# ─── Import DB Layer ──────────────────────────────────────────────────────────
from db import (
    get_or_create_guest_user,
    save_query,
    save_ai_response,
    save_learning_path,
    save_quiz,
    save_summary,
)

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="EduGenie Learning Assistant",
    description="AI-powered educational assistant using Google Gemini 2.5 Flash",
    version="1.1.0",
)

# ─── Static Files & Templates ─────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Only mount /static if the directory exists
static_dir = os.path.join(BASE_DIR, "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)


# ─── Pydantic Request Models ──────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    topic: str

class QuizRequest(BaseModel):
    passage: str

class SummarizeRequest(BaseModel):
    text: str

class FunctionalTestRequest(BaseModel):
    scope: Optional[str] = "all"


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main EduGenie frontend."""
    return templates.TemplateResponse("index.html", {"request": request})


# ── 1. Q&A Endpoint ──────────────────────────────────────────────────────────

@app.get("/qa")
async def question_answer(question: Optional[str] = None):
    """
    GET /qa?question=...
    Answers educational questions using Gemini 2.5 Flash.
    """
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'question' is required.")

    user = get_or_create_guest_user()
    query_record = save_query(user["UserID"], "qa", question.strip())

    answer = get_answer(question.strip())

    save_ai_response(query_record["QueryID"], answer, "Gemini 2.5 Flash")

    return {"question": question.strip(), "answer": answer}


# ── 2. Explanation Endpoint ───────────────────────────────────────────────────

@app.post("/explain")
async def explain(request: ExplainRequest):
    """
    POST /explain
    Body: { "topic": "..." }
    Generates beginner-friendly concept explanations using Gemini 2.5 Flash.
    """
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Field 'topic' is required.")

    user = get_or_create_guest_user()
    query_record = save_query(user["UserID"], "explain", request.topic.strip())

    explanation = explain_topic(request.topic.strip())

    save_ai_response(query_record["QueryID"], explanation, "Gemini 2.5 Flash")

    return {"topic": request.topic.strip(), "explanation": explanation}


# ── 3. Quiz Generation Endpoint ───────────────────────────────────────────────

@app.post("/quiz")
async def generate_quiz(request: QuizRequest):
    """
    POST /quiz
    Body: { "passage": "..." }
    Generates 3 MCQs from the passage using Gemini 2.5 Flash.
    Returns structured JSON with question, options (A-D), and correct answer.
    """
    if not request.passage or not request.passage.strip():
        raise HTTPException(status_code=400, detail="Field 'passage' is required.")

    user = get_or_create_guest_user()
    query_record = save_query(user["UserID"], "quiz", request.passage.strip())

    quiz_questions = generate_quiz_questions(request.passage.strip())

    # Save to QUIZ table only if there are no errors
    has_error = any("error" in q for q in quiz_questions)
    if not has_error:
        save_quiz(query_record["QueryID"], quiz_questions)

    save_ai_response(query_record["QueryID"], _json.dumps(quiz_questions), "Gemini 2.5 Flash")

    return {"passage": request.passage.strip(), "quiz": quiz_questions}


# ── 4. Summarization Endpoint ─────────────────────────────────────────────────

@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    """
    POST /summarize
    Body: { "text": "..." }
    Summarizes educational content using Gemini 2.5 Flash.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Field 'text' is required.")

    user = get_or_create_guest_user()
    query_record = save_query(user["UserID"], "summarize", request.text.strip())

    summary = summarize_text(request.text.strip())

    save_summary(query_record["QueryID"], request.text.strip(), summary, "Gemini 2.5 Flash")
    save_ai_response(query_record["QueryID"], summary, "Gemini 2.5 Flash")

    return {"original_text": request.text.strip(), "summary": summary}


# ── 5. Learning Path Endpoint ─────────────────────────────────────────────────

@app.get("/learn/recommendations")
async def learning_recommendations(topic: Optional[str] = None):
    """
    GET /learn/recommendations?topic=...
    Generates a personalized learning roadmap using Gemini 2.5 Flash.
    """
    if not topic or not topic.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'topic' is required.")

    user = get_or_create_guest_user()
    query_record = save_query(user["UserID"], "learn", topic.strip())

    recommendations = get_learning_recommendations(topic.strip())

    save_learning_path(
        query_id=query_record["QueryID"],
        topic=topic.strip(),
        level="Beginner / Intermediate / Advanced",
        recommended_topics=recommendations,
    )
    save_ai_response(query_record["QueryID"], recommendations, "Gemini 2.5 Flash")

    return {"topic": topic.strip(), "recommendations": recommendations}


# ─── Functional Testing Endpoint ──────────────────────────────────────────────
# Used by the "Functional Testing" panel in the project console. Runs each
# AI module with a fixed sample input and reports pass/fail + latency, without
# the caller needing Python or pytest installed.

def _run_check(name: str, fn):
    """Run fn(), time it, and classify the result as pass/fail."""
    started = time.perf_counter()
    try:
        result = fn()
        ms = round((time.perf_counter() - started) * 1000)
        text = result if isinstance(result, str) else _json.dumps(result)
        is_error = isinstance(result, str) and text.strip().lower().startswith("error")
        if isinstance(result, list) and any(isinstance(x, dict) and "error" in x for x in result):
            is_error = True
        if not text or not text.strip():
            return {"name": name, "passed": False, "detail": "Empty response", "ms": ms}
        if is_error:
            return {"name": name, "passed": False, "detail": text[:160], "ms": ms}
        return {"name": name, "passed": True, "detail": f"Received {len(text)} chars", "ms": ms}
    except Exception as e:
        ms = round((time.perf_counter() - started) * 1000)
        return {"name": name, "passed": False, "detail": f"Exception: {e}", "ms": ms}


CHECKS = {
    "qa": ("Q&A — /qa", lambda: get_answer("What is the capital of France?")),
    "explain": ("Explanation — /explain", lambda: explain_topic("gravity")),
    "summarize": ("Summarization — /summarize", lambda: summarize_text(
        "The water cycle describes how water evaporates, forms clouds, falls as "
        "precipitation, and flows back into rivers and oceans."
    )),
    "quiz": ("Quiz generator — /quiz", lambda: generate_quiz_questions(
        "Photosynthesis is the process by which plants convert sunlight into energy."
    )),
    "learn": ("Learning path — /learn/recommendations", lambda: get_learning_recommendations("Python programming")),
}


@app.post("/api/functional-tests")
async def functional_tests(request: FunctionalTestRequest):
    """
    POST /api/functional-tests
    Body: { "scope": "all" | "qa" | "explain" | "summarize" | "quiz" | "learn" }
    Runs each selected module with a fixed sample input against the live
    Gemini API key configured in .env and reports pass/fail + latency.
    """
    scope = (request.scope or "all").strip().lower()
    keys = list(CHECKS.keys()) if scope == "all" else [scope]
    invalid = [k for k in keys if k not in CHECKS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown scope(s): {invalid}")

    results = []
    for key in keys:
        label, fn = CHECKS[key]
        results.append(_run_check(label, fn))

    passed = sum(1 for r in results if r["passed"])
    return {"scope": scope, "passed": passed, "total": len(results), "results": results}


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Quick health check endpoint."""
    api_key_set = bool(os.getenv("GEMINI_API_KEY", "").strip())
    return {
        "status": "ok",
        "app": "EduGenie Learning Assistant",
        "version": "1.1.0",
        "gemini_api_key_configured": api_key_set,
        "endpoints": ["/qa", "/explain", "/quiz", "/summarize", "/learn/recommendations"],
    }
