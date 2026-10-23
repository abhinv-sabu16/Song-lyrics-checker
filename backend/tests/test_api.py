import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from database import get_db
from main import app
from models import Artist, Base, LyricLine, Song
from text_utils import normalize_text


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as s:
        artist = Artist(name="Test Artist")
        song = Song(title="Test Song", artist=artist)
        for i, text in enumerate(
            ["Hello World tonight", "Second line here", "Don't stop believing"], start=1
        ):
            song.lines.append(
                LyricLine(line_number=i, text=text, normalized_text=normalize_text(text))
            )
        s.add(song)
        s.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_valid_search_returns_predictable_empty_response(client):
    r = client.post("/api/search", json={"query": "zebra unicorn"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "zebra unicorn"
    assert body["total_results"] == 0
    assert body["results"] == []
    assert body["message"] == "No matches found."


def test_query_whitespace_is_trimmed(client):
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
def test_invalid_payloads_are_rejected(client, payload):
    r = client.post("/api/search", json=payload)
    assert r.status_code == 422


def test_malformed_json_is_rejected(client):
    r = client.post(
        "/api/search",
        content="{not json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 422


def test_wrong_method_is_rejected(client):
    assert client.get("/api/search").status_code == 405
    
def test_api_finds_known_phrase(client):
    r = client.post("/api/search", json={"query": "hello world"})
    assert r.status_code == 200
    body = r.json()
    assert body["total_results"] == 1
    assert body["message"] is None
    result = body["results"][0]
    assert result["title"] == "Test Song"
    assert result["matched_excerpt"] == "Hello World tonight"
    assert result["match_type"] == "exact"


def test_api_case_and_spacing_do_not_matter(client):
    r = client.post("/api/search", json={"query": "  HELLO    world!! "})
    assert r.json()["total_results"] == 1


def test_api_limit_is_applied(client):
    r = client.post("/api/search", json={"query": "e", "limit": 1})
    assert r.json()["total_results"] == 1