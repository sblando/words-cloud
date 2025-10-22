import re
import unicodedata
from unidecode import unidecode
from typing import List, Set, Optional

# -------------------------------------------------------------------
# English stopwords — compact, tuned for scholarly text
# -------------------------------------------------------------------
BASE_STOPWORDS_EN: Set[str] = {
    "the","and","of","to","in","a","for","is","on","that","with","as","by","it","from","an",
    "be","or","are","at","this","we","you","your","our","their","they","these","those",
    "was","were","has","have","had","can","could","may","might","will","would","shall","should",
    "however","therefore","thus","hence","into","within","between","across","via","both",
    "more","most","less","least","over","under","each","such","many","much","also","often",
    "using","used","use","based","new","one","two","three","et","al"
}


def normalize_text(text: str) -> str:
    """
    Normalize raw text for bag-of-words (English).

    Steps:
      1) Unicode NFKC normalization + lowercase.
      2) Remove URLs and emails.
      3) Remove digits.
      4) Fold diacritics to ASCII with unidecode.
      5) Remove punctuation/symbols (keep word chars + spaces).
      6) Collapse multiple spaces and trim.

    If you need to keep numbers or punctuation (e.g., hyphenated terms),
    adjust or skip the relevant regexes.
    """
    if not text:
        return ""

    # Standardize Unicode, then lowercase.
    text = unicodedata.normalize("NFKC", text).lower()

    # URLs (http/https/www)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Simple emails
    text = re.sub(r"\S+@\S+\.\S+", " ", text)

    # Digits (years, counts, etc.). Remove this step if numbers matter.
    text = re.sub(r"\d+", " ", text)

    # Diacritics → ASCII (naïve > naive, München > Munchen, São > Sao).
    text = unidecode(text)

    # Strip punctuation/symbols; keep \w (letters/digits/underscore) and spaces.
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_stopwords(extra: Optional[Set[str]] = None) -> Set[str]:
    """
    Return the base English stopword set, optionally unioned with `extra`.
    """
    sw = set(BASE_STOPWORDS_EN)
    if extra:
        sw |= set(extra)
    return sw


def tokenize(text: str) -> List[str]:
    """
    Whitespace tokenizer. Assumes you normalized beforehand if needed.
    """
    return [t for t in text.split() if t]


def strip_references(text: str) -> str:
    """
    Heuristically truncate content at the references/bibliography section.

    Detects common headings (alone on a line, optional colon), case-insensitive:
      - "References"
      - "Bibliography"
      - "Works Cited"

    Tolerant to Windows newlines (\r\n). If not found, returns the original text.
    """
    if not text:
        return text

    # Normalize newlines
    t = text.replace("\r\n", "\n")

    # Match a heading line with optional spaces and optional trailing colon.
    pattern = r"\n\s*(references|bibliography|works\s+cited)\s*:?\s*\n"
    m = re.search(pattern, t, flags=re.IGNORECASE)
    return t[:m.start()] if m else t


def clean_and_tokenize(text: str, extra_stop: Optional[Set[str]] = None) -> List[str]:
    """
    Convenience pipeline:
      strip_references → normalize_text → tokenize → remove stopwords.

    Args:
      text: Raw text (e.g., extracted from PDFs to .txt).
      extra_stop: Optional additional stopwords (e.g., {"study","results"}).

    Returns:
      List of cleaned tokens with stopwords removed.
    """
    # 1) Remove trailing references/bibliography
    txt = strip_references(text)

    # 2) Normalize
    txt = normalize_text(txt)

    # 3) Tokenize
    tokens = tokenize(txt)

    # 4) Stopword filtering
    sw = get_stopwords(extra_stop)
    tokens = [t for t in tokens if t not in sw]

    return tokens


# Optional explicit export control
__all__ = [
    "BASE_STOPWORDS_EN",
    "normalize_text",
    "get_stopwords",
    "tokenize",
    "strip_references",
    "clean_and_tokenize",
]