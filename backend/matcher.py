from dataclasses import dataclass

from rapidfuzz import fuzz, process
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from config import FUZZY_MIN_SCORE, MIN_FUZZY_QUERY_CHARS
from models import Artist, LyricLine, Song
from schemas import MatchResult, MatchType
from text_utils import is_only_common_words, normalize_text

MAX_EXCERPT_CHARS = 300

# (scorer, weight). Weights slightly discount looser comparisons so a
# near-identical line always outranks a loosely similar one.
# token_set_ratio is deliberately NOT used: it returns 100 whenever the
# query's words are a subset of the line's, which floods results for
# common phrases like "is the".
_SCORERS = (
    (fuzz.ratio, 1.0),
    (fuzz.token_sort_ratio, 0.95),
    (fuzz.partial_ratio, 0.90),
)


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
        .order_by(is_whole_line, Song.title, Artist.name, LyricLine.line_number)
        .limit(limit)
    )

    return [
        MatchResult(
            song_id=song.id,
            title=song.title,
            artist=artist.name,
            matched_excerpt=line.text[:MAX_EXCERPT_CHARS],
            similarity_score=100.0,
            match_type=MatchType.EXACT,
        )
        for line, song, artist in session.execute(stmt)
    ]


@dataclass(frozen=True)
class _Candidate:
    line: LyricLine
    song: Song
    artist: Artist
    score: float
    match_type: MatchType

    def sort_key(self, whole_line: bool):
        return (
            -self.score,
            0 if whole_line else 1,
            self.song.title,
            self.artist.name,
            self.line.line_number,
        )


def _fuzzy_scores(query: str, choices: dict[int, str], threshold: float) -> dict[int, float]:
    """Best weighted similarity per line id, for lines scoring >= threshold."""
    best: dict[int, float] = {}
    for scorer, weight in _SCORERS:
        pool = choices
        if scorer is fuzz.partial_ratio:
            # partial_ratio finds the query *inside* a line. If the line is
            # shorter than the query it would match any query that merely
            # contains the line (e.g. "yeah"), so skip those lines.
            pool = {k: v for k, v in choices.items() if len(v) >= len(query)}
        cutoff = min(100.0, threshold / weight)
        for _text, raw, line_id in process.extract(
            query, pool, scorer=scorer, score_cutoff=cutoff, limit=None
        ):
            weighted = min(100.0, raw * weight)
            if weighted >= threshold and weighted > best.get(line_id, 0.0):
                best[line_id] = weighted
    return best


def search(
    session: Session,
    query: str,
    limit: int = 10,
    min_score: float | None = None,
) -> list[MatchResult]:
    """Exact + fuzzy line search. Ranked by similarity, deduplicated."""
    normalized = normalize_text(query)
    if not normalized:
        return []
    threshold = FUZZY_MIN_SCORE if min_score is None else min_score

    rows = session.execute(
        select(LyricLine, Song, Artist)
        .join(Song, LyricLine.song_id == Song.id)
        .join(Artist, Song.artist_id == Artist.id)
    ).all()
    by_id = {line.id: (line, song, artist) for line, song, artist in rows}

    candidates: list[_Candidate] = []
    exact_ids: set[int] = set()
    for line_id, (line, song, artist) in by_id.items():
        if normalized in line.normalized_text:
            exact_ids.add(line_id)
            candidates.append(_Candidate(line, song, artist, 100.0, MatchType.EXACT))

    fuzzy_allowed = len(normalized) >= MIN_FUZZY_QUERY_CHARS and not is_only_common_words(
        normalized
    )
    if fuzzy_allowed:
        choices = {i: row[0].normalized_text for i, row in by_id.items() if i not in exact_ids}
        for line_id, score in _fuzzy_scores(normalized, choices, threshold).items():
            line, song, artist = by_id[line_id]
            candidates.append(_Candidate(line, song, artist, score, MatchType.FUZZY))

    candidates.sort(key=lambda c: c.sort_key(c.line.normalized_text == normalized))

    results: list[MatchResult] = []
    seen: set[tuple[int, str]] = set()
    for c in candidates:
        # A chorus repeated inside one song should appear once.
        key = (c.song.id, c.line.normalized_text)
        if key in seen:
            continue
        seen.add(key)
        results.append(
            MatchResult(
                song_id=c.song.id,
                title=c.song.title,
                artist=c.artist.name,
                matched_excerpt=c.line.text[:MAX_EXCERPT_CHARS],
                similarity_score=round(c.score, 1),
                match_type=c.match_type,
            )
        )
        if len(results) >= limit:
            break
    return results