from sqlalchemy import case, select
from sqlalchemy.orm import Session

from models import Artist, LyricLine, Song
from schemas import MatchResult, MatchType
from text_utils import normalize_text

MAX_EXCERPT_CHARS = 300


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so a query of '%' or '_' is treated literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def exact_search(session: Session, query: str, limit: int = 10) -> list[MatchResult]:
    """Return lines containing the normalized query, in a stable order."""
    normalized = normalize_text(query)
    if not normalized:
        return []

    pattern = f"%{_escape_like(normalized)}%"
    is_whole_line = case((LyricLine.normalized_text == normalized, 0), else_=1)

    stmt = (
        select(LyricLine, Song, Artist)
        .join(Song, LyricLine.song_id == Song.id)
        .join(Artist, Song.artist_id == Artist.id)
        .where(LyricLine.normalized_text.like(pattern, escape="\\"))
        .order_by(
            is_whole_line,
            Song.title,
            Artist.name,
            LyricLine.line_number,
        )
        .limit(limit)
    )

    results = []
    for line, song, artist in session.execute(stmt):
        results.append(
            MatchResult(
                song_id=song.id,
                title=song.title,
                artist=artist.name,
                matched_excerpt=line.text[:MAX_EXCERPT_CHARS],
                similarity_score=100.0,
                match_type=MatchType.EXACT,
            )
        )
    return results