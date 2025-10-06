"""Preprocessing utilities (Step 2 of Mode 5 pipeline).

Goals:
    * Normalize raw extracted document text.
    * Remove low‑value noise: page markers, horizontal rules, repeated blank lines, excessive spacing.
    * Provide lightweight sentence segmentation without heavy external deps (optional nltk if present).
    * Stay deterministic & testable (pure functions; no global mutable state).

Design notes:
    * Removed prior variable‑width negative look‑behind regex (Python requires fixed width) that caused re.error.
    * New fallback: split on punctuation + space(s) + Capital letter, then merge if the previous fragment ends
        with a known title abbreviation (e.g. "Dr." -> merge with following capitalized token "Smith ...").
    * We do NOT split after inline lowercase abbreviations like "e.g." because the next token usually starts
        with lowercase. If uppercase appears and we incorrectly split after a title, merge logic repairs it.
"""
from __future__ import annotations

from typing import List, Iterable, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# --- Regex Patterns -------------------------------------------------------

# Matches common page markers or headings that survived ingestion.
PAGE_TOKEN_RE = re.compile(r"^\s*(page|pg)\s*\d+\s*$", re.IGNORECASE)
# Collapses any run of whitespace into a single space (applied line-wise first).
MULTISPACE_RE = re.compile(r"\s+")
# Sentence boundary pattern: punctuation followed by whitespace and a Capital letter.
# (We intentionally keep it simple; repair abbreviation splits later.)
SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
# Remove bullet markers at line starts (simple forms: -, *, •, numeric lists).
BULLET_RE = re.compile(r"^\s*(?:[-*•]\s+|\d+\.\s+)")
# Strip decorative horizontal rules.
RULE_RE = re.compile(r"^(?:[-=_]{4,})$")

# Title abbreviations followed by a capitalized surname that should stay in the same sentence.
ABBREVIATION_TITLES = {"dr.", "prof.", "mr.", "mrs.", "ms.", "sr.", "jr."}
# Inline abbreviations we *expect* to stay inside a sentence (included for semantic clarity; not directly used).
INLINE_ABBR = {"e.g.", "i.e.", "vs."}


# --- Core Cleaning --------------------------------------------------------

def clean_text(raw: str) -> str:
    """Normalize and strip noise from raw extracted text.

    Steps:
      1. Drop blank lines, page tokens ("Page 3"), horizontal rules.
      2. Remove simple bullet markers while keeping the content.
      3. Collapse internal multi‑spaces per line.
      4. Reassemble with single newlines and collapse multiple blank lines.
    """
    if not raw:
        return ""
    normalized_lines: List[str] = []
    for line in raw.splitlines():
        original = line
        line = line.rstrip()
        if not line.strip():
            continue
        if PAGE_TOKEN_RE.match(line):
            continue
        if RULE_RE.match(line.strip()):
            continue
        line = BULLET_RE.sub("", line)
        line = MULTISPACE_RE.sub(" ", line.strip())
        if line:
            normalized_lines.append(line)
    joined = "\n".join(normalized_lines)
    joined = re.sub(r"\n{2,}", "\n", joined)
    return joined.strip()


# --- Sentence Segmentation ------------------------------------------------

def _nltk_sentence_tokenize(text: str) -> List[str]:  # pragma: no cover (optional path)
    import nltk  # type: ignore
    try:
        from nltk.tokenize import sent_tokenize  # type: ignore
    except Exception:  # Download punkt if missing
        nltk.download("punkt")  # type: ignore
        from nltk.tokenize import sent_tokenize  # type: ignore
    return sent_tokenize(text)


def _fallback_sentence_split(text: str) -> List[str]:
    """Lightweight sentence splitter.

    Strategy:
      * Split on punctuation (.!?)+space(s)+Capital letter.
      * Merge if previous fragment ends with a title abbreviation (Dr., Prof., etc.).
    """
    txt = text.strip()
    if not txt:
        return []
    if len(txt) < 80:
        return [txt]
    parts = SPLIT_PATTERN.split(txt)
    if len(parts) <= 1:
        return parts
    merged: List[str] = []
    for part in parts:
        seg = part.strip()
        if not seg:
            continue
        if merged:
            prev_last_token = merged[-1].split()[-1].lower()
            if prev_last_token in ABBREVIATION_TITLES:
                merged[-1] = merged[-1] + " " + seg
                continue
        merged.append(seg)
    return merged


def sentence_split(text: str, prefer_nltk: bool = True) -> List[str]:
    """Split cleaned text into sentences.

    Args:
        text: Cleaned text
        prefer_nltk: If True and nltk available, use it; else fallback.
    """
    if not text.strip():
        return []

    if prefer_nltk:
        try:  # Attempt nltk path
            return _nltk_sentence_tokenize(text)
        except Exception:
            logger.debug("nltk sentence tokenizer unavailable – using fallback")
    return _fallback_sentence_split(text)


# --- Higher Level Convenience ---------------------------------------------

def preprocess(raw: str) -> Tuple[str, List[str]]:
    """Full preprocessing pipeline: clean + sentence split.

    Returns:
        (cleaned_text, sentences)
    """
    cleaned = clean_text(raw)
    sentences = sentence_split(cleaned)
    return cleaned, sentences


# --- Filtering ------------------------------------------------------------

def filter_short_sentences(sentences: Iterable[str], min_words: int = 2) -> List[str]:
    """Filter out sentences below a word threshold (keeps structure stable)."""
    out: List[str] = []
    for s in sentences:
        wc = len(s.split())
        if wc >= min_words:
            out.append(s.strip())
    return out

__all__ = ["clean_text", "sentence_split", "preprocess", "filter_short_sentences"]
