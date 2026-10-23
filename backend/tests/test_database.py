import sys
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from database import init_db, make_engine  # noqa: E402
from models import Artist, LyricLine, Song  # noqa: E402
from seed_database import seed  # noqa: E402
from text_utils import normalize_text  # noqa: E402

SAMPLE = [
    {
        "title": "Test Song",
        "artist": "Test Artist",
        "lines": ["Hello   World", "Second LINE!"],
    }
]


@pytest.fixture
def engine():
    eng = make_engine("sqlite://")
    init_db(eng)
    return eng


def test_insert_retrieve_update_delete(engine):
    with Session(engine) as s:
        artist = Artist(name="A")
        song = Song(title="T", artist=artist)
        song.lines.append(LyricLine(line_number=1, text="Hi There", normalized_text="hi there"))
        s.add(song)
        s.commit()
        song_id = song.id

    with Session(engine) as s:
        song = s.get(Song, song_id)
        assert song.title == "T"
        assert song.artist.name == "A"
        assert song.lines[0].text == "Hi There"
        song.title = "T2"
        s.commit()

    with Session(engine) as s:
        assert s.get(Song, song_id).title == "T2"
        s.delete(s.get(Song, song_id))
        s.commit()

    with Session(engine) as s:
        assert s.get(Song, song_id) is None
        # Lines are removed with their song (cascade).
        assert s.scalar(select(func.count()).select_from(LyricLine)) == 0


def test_seed_twice_creates_no_duplicates(engine):
    with Session(engine) as s:
        first = seed(s, SAMPLE)
    with Session(engine) as s:
        second = seed(s, SAMPLE)
        assert first == {"added": 1, "skipped": 0}
        assert second == {"added": 0, "skipped": 1}
        assert s.scalar(select(func.count()).select_from(Song)) == 1
        assert s.scalar(select(func.count()).select_from(LyricLine)) == 2
        assert s.scalar(select(func.count()).select_from(Artist)) == 1


def test_normalized_text_is_stored_separately(engine):
    with Session(engine) as s:
        seed(s, SAMPLE)
        line = s.scalars(select(LyricLine).order_by(LyricLine.line_number)).first()
        assert line.text == "Hello   World"
        assert line.normalized_text == "hello world"


def test_duplicate_song_is_rejected_by_constraint(engine):
    with Session(engine) as s:
        artist = Artist(name="A")
        s.add_all([Song(title="T", artist=artist), Song(title="T", artist=artist)])
        with pytest.raises(IntegrityError):
            s.commit()


def test_foreign_keys_are_enforced(engine):
    with Session(engine) as s:
        s.add(Song(title="Orphan", artist_id=999))
        with pytest.raises(IntegrityError):
            s.commit()


def test_data_persists_across_connections(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'persist.db'}"
    eng1 = make_engine(db_url)
    init_db(eng1)
    with Session(eng1) as s:
        seed(s, SAMPLE)
    eng1.dispose()

    eng2 = make_engine(db_url)  # simulates restarting the backend
    with Session(eng2) as s:
        assert s.scalar(select(func.count()).select_from(Song)) == 1


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Hello,   WORLD!", "hello world"),
        ("  Don\u2019t stop  ", "don't stop"),
        ("café", "café"),
        ("", ""),
        ("!!!", ""),
    ],
)
def test_normalize_text(raw, expected):
    assert normalize_text(raw) == expected