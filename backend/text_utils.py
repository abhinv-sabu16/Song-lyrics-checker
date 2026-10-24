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

COMMON_WORDS = frozenset(
    "a an and are as at be but by do for from had has have he her him his i if in is it its me my "
    "no not of oh on or our she so that the their them then there they this to up us was we were "
    "what when who will with yeah you your am been can did get got just let like more now one out "
    "all how into than too very".split()
)


def is_only_common_words(normalized: str) -> bool:
    words = normalized.split()
    return bool(words) and all(w in COMMON_WORDS for w in words)