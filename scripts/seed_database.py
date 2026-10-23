"""Repeatable seed script. Safe to run any number of times.

Usage (from the project root, venv active):
    python scripts/seed_database.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from database import engine, init_db  # noqa: E402
from models import Artist, LyricLine, Song  # noqa: E402
from text_utils import normalize_text  # noqa: E402

DEFAULT_DATA = ROOT / "data" / "sample_lyrics.json"


def seed(session: Session, songs_data: list[dict]) -> dict:
    added = skipped = 0
    for item in songs_data:
        artist = session.scalar(select(Artist).where(Artist.name == item["artist"]))
        if artist is None:
            artist = Artist(name=item["artist"])
            session.add(artist)
            session.flush()

        existing = session.scalar(
            select(Song).where(Song.title == item["title"], Song.artist_id == artist.id)
        )
        if existing is not None:
            skipped += 1
            continue

        song = Song(
            title=item["title"],
            artist=artist,
            language=item.get("language", "en"),
            source=item.get("source", "unknown"),
            license=item.get("license", "unknown"),
        )
        for number, text in enumerate(item["lines"], start=1):
            song.lines.append(
                LyricLine(line_number=number, text=text, normalized_text=normalize_text(text))
            )
        session.add(song)
        added += 1
    session.commit()
    return {"added": added, "skipped": skipped}


def main(path: Path = DEFAULT_DATA) -> None:
    init_db()
    songs_data = json.loads(path.read_text(encoding="utf-8"))
    with Session(engine) as session:
        result = seed(session, songs_data)
    print(f"Seed complete: {result['added']} added, {result['skipped']} already present.")


if __name__ == "__main__":
    main()