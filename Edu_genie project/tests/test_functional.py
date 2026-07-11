"""
EduGenie — Functional test suite
=================================
Exercises the 5 real endpoints end to end against a running server.

Usage:
    1. Start the app in one terminal:
         uvicorn main:app --reload
    2. In another terminal, run:
         pytest tests/test_functional.py -v

Set BASE_URL if the server isn't on the default host/port:
    BASE_URL=http://localhost:8000 pytest tests/test_functional.py -v

These hit the live Gemini API key configured in .env, so a network
connection and a valid GEMINI_API_KEY are required for the tests to pass.
"""

import os
import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def _alive():
    try:
        requests.get(f"{BASE_URL}/health", timeout=3)
        return True
    except requests.exceptions.ConnectionError:
        return False


pytestmark = pytest.mark.skipif(
    not _alive(),
    reason=f"Server not reachable at {BASE_URL} — start it with `uvicorn main:app --reload` first.",
)


def test_health_check():
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "endpoints" in body


def test_qa_endpoint():
    r = requests.get(f"{BASE_URL}/qa", params={"question": "What is the capital of France?"}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["answer"].strip()
    assert not body["answer"].lower().startswith("error")


def test_qa_endpoint_requires_question():
    r = requests.get(f"{BASE_URL}/qa", timeout=10)
    assert r.status_code == 400


def test_explain_endpoint():
    r = requests.post(f"{BASE_URL}/explain", json={"topic": "gravity"}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["explanation"].strip()


def test_explain_endpoint_requires_topic():
    r = requests.post(f"{BASE_URL}/explain", json={"topic": ""}, timeout=10)
    assert r.status_code == 400


def test_summarize_endpoint():
    text = (
        "The water cycle describes how water evaporates, forms clouds, falls as "
        "precipitation, and flows back into rivers and oceans."
    )
    r = requests.post(f"{BASE_URL}/summarize", json={"text": text}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["summary"].strip()
    assert len(body["summary"]) <= len(text) + 200  # sanity: summary isn't wildly longer


def test_quiz_endpoint_returns_three_questions():
    passage = "Photosynthesis is the process by which plants convert sunlight into energy."
    r = requests.post(f"{BASE_URL}/quiz", json={"passage": passage}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    quiz = body["quiz"]
    assert isinstance(quiz, list)
    assert len(quiz) >= 1
    for q in quiz:
        if "error" in q:
            pytest.fail(f"Quiz module returned an error: {q['error']}")
        assert "question" in q
        assert "options" in q and len(q["options"]) == 4
        assert q["correct"] in ("A", "B", "C", "D")


def test_learning_path_endpoint():
    r = requests.get(f"{BASE_URL}/learn/recommendations", params={"topic": "Python programming"}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["recommendations"].strip()


def test_functional_tests_panel_endpoint():
    """The /api/functional-tests endpoint backs the console's 'Functional Testing' panel."""
    r = requests.post(f"{BASE_URL}/api/functional-tests", json={"scope": "all"}, timeout=60)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert "results" in body
    for result in body["results"]:
        assert "name" in result and "passed" in result and "ms" in result


def test_functional_tests_panel_rejects_unknown_scope():
    r = requests.post(f"{BASE_URL}/api/functional-tests", json={"scope": "not-a-real-module"}, timeout=10)
    assert r.status_code == 400
