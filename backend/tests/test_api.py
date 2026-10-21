import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_valid_search_returns_predictable_empty_response():
    r = client.post("/api/search", json={"query": "hello world"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "hello world"
    assert body["total_results"] == 0
    assert body["results"] == []
    assert body["message"] == "No matches found."


def test_query_whitespace_is_trimmed():
    r = client.post("/api/search", json={"query": "  hello   "})
    assert r.status_code == 200
    assert r.json()["query"] == "hello"


@pytest.mark.parametrize(
    "payload",
    [
        {},                                   # missing query
        {"query": ""},                        # empty
        {"query": "   "},                     # whitespace only
        {"query": "x" * 201},                 # too long
        {"query": 123},                       # wrong type
        {"query": None},                      # null
        {"query": "hi", "limit": 0},          # limit too small
        {"query": "hi", "limit": 51},         # limit too large
        {"query": "hi", "min_score": 101},    # score out of range
        {"query": "hi", "min_score": -1},
        {"query": "hi", "unknown_field": 1},  # extra field forbidden
    ],
)
def test_invalid_payloads_are_rejected(payload):
    r = client.post("/api/search", json=payload)
    assert r.status_code == 422


def test_malformed_json_is_rejected():
    r = client.post(
        "/api/search",
        content="{not json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 422


def test_wrong_method_is_rejected():
    assert client.get("/api/search").status_code == 405