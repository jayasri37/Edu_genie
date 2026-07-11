"""
EduGenie - File-based JSON Storage Layer
Matches the ER Diagram exactly:
  USER (1) --> (1) USER_QUERY (1) --> (1) AI_RESPONSE
  USER_QUERY (1) --> (m) LEARNING_PATH
  USER_QUERY (1) --> (m) QUIZ
  USER_QUERY (1) --> (m) SUMMARY
"""

import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FILES = {
    "users":          os.path.join(DATA_DIR, "users.json"),
    "user_queries":   os.path.join(DATA_DIR, "user_queries.json"),
    "ai_responses":   os.path.join(DATA_DIR, "ai_responses.json"),
    "learning_paths": os.path.join(DATA_DIR, "learning_paths.json"),
    "quizzes":        os.path.join(DATA_DIR, "quizzes.json"),
    "summaries":      os.path.join(DATA_DIR, "summaries.json"),
}


def _load(key: str) -> list:
    path = FILES[key]
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save(key: str, data: list):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FILES[key], "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.utcnow().isoformat()


# ─── USER ───────────────────────────────────────────────────────────────────

def get_or_create_guest_user() -> dict:
    """Return the default guest user, creating it if needed."""
    users = _load("users")
    for u in users:
        if u["UserName"] == "guest":
            return u
    user = {
        "UserID":       _new_id(),
        "UserName":     "guest",
        "Email":        "guest@edugenie.local",
        "PasswordHash": "",
        "CreatedAt":    _now(),
    }
    users.append(user)
    _save("users", users)
    return user


# ─── USER_QUERY ──────────────────────────────────────────────────────────────

def save_query(user_id: str, query_type: str, query_text: str) -> dict:
    """
    query_type: one of 'qa' | 'explain' | 'quiz' | 'summarize' | 'learn'
    """
    queries = _load("user_queries")
    record = {
        "QueryID":   _new_id(),
        "UserID":    user_id,
        "QueryType": query_type,
        "QueryText": query_text,
        "CreatedAt": _now(),
    }
    queries.append(record)
    _save("user_queries", queries)
    return record


# ─── AI_RESPONSE ─────────────────────────────────────────────────────────────

def save_ai_response(query_id: str, response_text: str, model_used: str) -> dict:
    responses = _load("ai_responses")
    record = {
        "ResponseID":   _new_id(),
        "QueryID":      query_id,
        "ResponseText": response_text,
        "ModelUsed":    model_used,
        "CreatedAt":    _now(),
    }
    responses.append(record)
    _save("ai_responses", responses)
    return record


# ─── LEARNING_PATH ────────────────────────────────────────────────────────────

def save_learning_path(query_id: str, topic: str, level: str, recommended_topics: str) -> dict:
    paths = _load("learning_paths")
    record = {
        "PathID":            _new_id(),
        "QueryID":           query_id,
        "Topic":             topic,
        "Level":             level,
        "RecommendedTopics": recommended_topics,
        "CreatedAt":         _now(),
    }
    paths.append(record)
    _save("learning_paths", paths)
    return record


# ─── QUIZ ─────────────────────────────────────────────────────────────────────

def save_quiz(query_id: str, questions: list) -> list:
    """
    questions: list of dicts with keys question, options (list), correct
    """
    quizzes = _load("quizzes")
    saved = []
    for q in questions:
        opts = q.get("options", ["", "", "", ""])
        record = {
            "QuizID":        _new_id(),
            "QueryID":       query_id,
            "QuestionText":  q.get("question", ""),
            "OptionA":       opts[0] if len(opts) > 0 else "",
            "OptionB":       opts[1] if len(opts) > 1 else "",
            "OptionC":       opts[2] if len(opts) > 2 else "",
            "OptionD":       opts[3] if len(opts) > 3 else "",
            "CorrectOption": q.get("correct", "A"),
            "CreatedAt":     _now(),
        }
        quizzes.append(record)
        saved.append(record)
    _save("quizzes", quizzes)
    return saved


# ─── SUMMARY ─────────────────────────────────────────────────────────────────

def save_summary(query_id: str, original_text: str, summary_text: str, model_used: str) -> dict:
    summaries = _load("summaries")
    record = {
        "SummaryID":    _new_id(),
        "QueryID":      query_id,
        "OriginalText": original_text,
        "SummaryText":  summary_text,
        "ModelUsed":    model_used,
        "CreatedAt":    _now(),
    }
    summaries.append(record)
    _save("summaries", summaries)
    return record
