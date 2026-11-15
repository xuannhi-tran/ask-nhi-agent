from fastapi.testclient import TestClient

from agent.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"ok": True}


def test_ask_rejects_long_questions():
    assert client.post("/ask", json={"question": "x" * 301}).status_code == 422


def test_match_rejects_short_jd():
    assert client.post("/match", json={"job_description": "too short"}).status_code == 422
