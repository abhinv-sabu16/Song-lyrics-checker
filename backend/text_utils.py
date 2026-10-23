import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[^\w\s']", re.UNICODE)


def normalize_text(text: str) -> str:
    """Lowercase, Unicode-normalize, drop punctuation, collapse whitespace.

    Apostrophes are kept so words like "don't" stay intact.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u2019", "'")  # curly apostrophe -> straight
    text = text.casefold()
    text = _PUNCTUATION.sub(" ", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()