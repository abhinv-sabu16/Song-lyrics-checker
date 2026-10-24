import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from matcher import search
from models import Artist, Base, LyricLine, Song
from schemas import MatchType
from text_utils import is_only_common_words, normalize_text

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
    ("Champions", "Artist Four"): [
        "We are the champions of the night",
        "Keep on fighting till the end",
        "We are the champions of the night",  # repeated chorus
        "We are the champions of the night",
        "Yeah",
    ],
    ("Amazing Grace", "John Newton"): [
        "Amazing grace how sweet the sound",
        "That saved a wretch like me",
        "I once was lost but now am found",
        "Was blind but now I see",
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


# --- exact vs fuzzy ---------------------------------------------------------

def test_exact_query_is_labelled_exact_with_full_score(session):
    r = search(session, "rain is tapping on my window pane")[0]
    assert r.match_type == MatchType.EXACT
    assert r.similarity_score == 100.0


@pytest.mark.parametrize(
    "query, expected_title",
    [
        ("rain is tapin on my windo pane", "Monsoon Window"),      # missing letters
        ("amazin grace how sweat the sound", "Amazing Grace"),     # typos
        ("midnite train is rolin", "Midnight Train"),              # partial + typos
        ("fold a paper bote", "Paper Boats"),                      # partial + typo
        ("sweet the sound how grace amazing", "Amazing Grace"),    # word order
    ],
)
def test_misspelled_and_partial_queries_find_the_song(session, query, expected_title):
    results = search(session, query)
    assert results, f"no results for {query!r}"
    assert results[0].title == expected_title
    assert results[0].match_type == MatchType.FUZZY
    assert 75 <= results[0].similarity_score < 100


def test_fuzzy_score_is_lower_than_exact_score(session):
    exact = search(session, "amazing grace how sweet the sound")[0]
    fuzzy = search(session, "amazin grace how sweat the sound")[0]
    assert fuzzy.similarity_score < exact.similarity_score


# --- unrelated / false positives -------------------------------------------

@pytest.mark.parametrize(
    "query",
    ["zebra unicorn spaceship", "quantum physics lecture", "banana smoothie recipe", "xyzzy plugh"],
)
def test_unrelated_queries_return_nothing(session, query):
    assert search(session, query) == []


@pytest.mark.parametrize("query", ["is the", "in the", "i am", "yeah yeah yeah", "to be or not to be"])
def test_common_phrases_do_not_produce_fuzzy_matches(session, query):
    results = search(session, query)
    assert all(r.match_type == MatchType.EXACT for r in results)


def test_short_queries_are_exact_only(session):
    results = search(session, "gra")
    assert all(r.match_type == MatchType.EXACT for r in results)


def test_short_line_is_not_matched_by_a_longer_query(session):
    # "Yeah" is a whole line in one song; a long query containing it must not match it.
    results = search(session, "oh yeah baby tonight")
    assert "Champions" not in titles(results)


def test_helper_is_only_common_words():
    assert is_only_common_words("is the")
    assert not is_only_common_words("is the night")
    assert not is_only_common_words("")


# --- threshold --------------------------------------------------------------

def test_min_score_is_configurable(session):
    query = "rain is tapin on my windo pane"  # ~95 similarity
    assert search(session, query, min_score=99) == []
    assert titles(search(session, query, min_score=90)) == ["Monsoon Window"]


def test_lower_threshold_never_returns_fewer_results(session):
    query = "midnite train is rolin"
    strict = search(session, query, min_score=90)
    loose = search(session, query, min_score=60)
    assert len(loose) >= len(strict)


def test_min_score_100_returns_only_exact_matches(session):
    assert search(session, "amazin grace how sweat the sound", min_score=100) == []
    assert titles(search(session, "amazing grace", min_score=100)) == ["Amazing Grace"]


# --- deduplication ----------------------------------------------------------

def test_repeated_chorus_is_returned_once_exact(session):
    assert titles(search(session, "we are the champions")) == ["Champions"]


def test_repeated_chorus_is_returned_once_fuzzy(session):
    results = search(session, "we are the champons of the nite")
    assert titles(results) == ["Champions"]
    assert results[0].match_type == MatchType.FUZZY


# --- ranking / stability ----------------------------------------------------

def test_results_are_sorted_by_score_descending(session):
    scores = [r.similarity_score for r in search(session, "the night", limit=50)]
    assert scores == sorted(scores, reverse=True)


def test_same_input_gives_same_ranking(session):
    first = search(session, "the sound how sweat grace", limit=20)
    second = search(session, "the sound how sweat grace", limit=20)
    assert [(r.title, r.matched_excerpt, r.similarity_score) for r in first] == [
        (r.title, r.matched_excerpt, r.similarity_score) for r in second
    ]


def test_limit_is_respected(session):
    assert len(search(session, "the", limit=2)) == 2


def test_scores_stay_between_0_and_100(session):
    for r in search(session, "the", limit=50) + search(session, "amazin grace", limit=50):
        assert 0 <= r.similarity_score <= 100


@pytest.mark.parametrize("query", ["", "   ", "!!!"])
def test_empty_queries_return_nothing(session, query):
    assert search(session, query) == []


def test_excerpt_is_a_single_line(session):
    all_lines = sum(SONGS.values(), [])
    for r in search(session, "amazin grace how sweat the sound", limit=50):
        assert r.matched_excerpt in all_lines