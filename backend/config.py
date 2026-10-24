import os


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if 0 <= value <= 100 else default


# Minimum text similarity (0-100) for a fuzzy match to be returned.
# Override per request with `min_score`, or globally with FUZZY_MIN_SCORE.
FUZZY_MIN_SCORE = _float_env("FUZZY_MIN_SCORE", 75.0)

# Queries shorter than this (after normalization) are matched exactly only.
MIN_FUZZY_QUERY_CHARS = 5