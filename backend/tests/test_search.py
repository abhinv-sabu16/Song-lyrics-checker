import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from matcher import exact_search
from models import Artist, Base, LyricLine, Song
from text_utils import normalize_text

SONGS = {
    ("Monsoon Window", "Artist One"): [
        "Rain is tapping on my window pane",
        "Chai is steaming in the evening light",
        "Nothing to carry but the quiet",
        "Everything is washed and bright",
    ],
    ("Paper Boats", "Artist One"): [
        "Fold a paper boat and let it go",
        "Down the river where the lanterns glow",
        "Tiny sail against the open sky",
    ],
    ("Midnight Train", "Artist Two"): [
        "Midnight train is rolling through the hills",
        "Every station dark and sleeping still",
        "I don't want to leave this town",
    ],
    ("Café Song", "Artist Three"): [
        "Meet me at the café tonight",
        "100% sure about this_one",
    ],
}


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        artists = {}
        for (title, artist_name), lines in SONGS.items():
            artist = artists.setdefault(artist_name, Artist(name=artist_name))
            song = Song(title=title, artist=artist)
            for i, text in enumerate(lines, start=1):
                song.lines.append(
                    LyricLine(line_number=i, text=text, normalized_text=normalize_text(text))
                )
            s.add(song)
        s.commit()
        yield s


def titles(results):
    return [r.title for r in results]


def test_known_exact_phrase(session):
    results = exact_search(session, "rain is tapping on my window pane")
    assert titles(results) == ["Monsoon Window"]
    assert results[0].matched_excerpt == "Rain is tapping on my window pane"
    assert results[0].artist == "Artist One"


def test_partial_phrase(session):
    assert titles(exact_search(session, "paper boat")) == ["Paper Boats"]


@pytest.mark.parametrize(
    "query",
    [
        "RAIN IS TAPPING",
        "rain is tapping",
        "Rain   is    tapping",
        "  rain is tapping  ",
        "rain, is tapping!",
    ],
)
def test_case_whitespace_and_punctuation_variations(session, query):
    assert titles(exact_search(session, query)) == ["Monsoon Window"]


def test_apostrophes_match_straight_and_curly(session):
    assert titles(exact_search(session, "don't want")) == ["Midnight Train"]
    assert titles(exact_search(session, "don\u2019t want")) == ["Midnight Train"]


def test_unicode_characters(session):
    assert titles(exact_search(session, "CAFÉ")) == ["Café Song"]


@pytest.mark.parametrize("query", ["", "   ", "!!!", "...", "?!"])
def test_empty_and_punctuation_only_queries_return_nothing(session, query):
    assert exact_search(session, query) == []


def test_no_match_returns_clean_empty_list(session):
    assert exact_search(session, "zebra unicorn spaceship") == []


def test_like_wildcards_are_literal(session):
    # normalize_text strips "%" so "%" alone is empty; underscore is a word char.
    assert exact_search(session, "%") == []
    assert titles(exact_search(session, "this_one")) == ["Café Song"]
    assert exact_search(session, "this one") == []  # "_" must not act as a wildcard


def test_limit_is_respected(session):
    results = exact_search(session, "is", limit=2)
    assert len(results) == 2


def test_result_order_is_stable(session):
    first = exact_search(session, "is")
    second = exact_search(session, "is")
    assert titles(first) == titles(second)
    assert [r.matched_excerpt for r in first] == [r.matched_excerpt for r in second]


def test_whole_line_match_ranks_first(session):
    results = exact_search(session, "Meet me at the café tonight")
    assert results[0].matched_excerpt == "Meet me at the café tonight"


def test_full_lyrics_are_never_returned(session):
    results = exact_search(session, "is")
    full_song = " ".join(SONGS[("Monsoon Window", "Artist One")])
    for r in results:
        assert r.matched_excerpt != full_song
        assert len(r.matched_excerpt) <= 300
        # An excerpt is a single line, never several joined together.
        assert r.matched_excerpt in sum(SONGS.values(), [])