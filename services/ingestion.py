"""Document ingestion / extraction service (Step 1 of Mode 5 pipeline).

Responsibilities:
 1. Validate file size & MIME type.
 2. Extract raw textual content from PDF / DOCX / TXT.
 3. Normalize lines (remove simple headers/footers & blank lines).
 4. Perform PDF density heuristic to reject likely image-only scans.
 5. Return cleaned text + immutable metadata (DocumentMeta).

Security considerations:
 - Best-effort MIME sniffing (python-magic if available, else mimetypes).
 - No execution of embedded content; pure text extraction.
 - Early rejection for large or low-density files.
"""

import os
import re
import hashlib
import time
import mimetypes
import logging
from typing import Tuple, Optional
from services.models import DocumentMeta
from config.settings import (
    MAX_FILE_MB,
    MIN_EXTRACTED_WORDS,
    ALLOWED_MIME_TYPES,
    PDF_MIN_CHARS_PER_PAGE,
)

try:  # PDF parser (text extraction)
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover
    pdfplumber = None

try:  # DOCX parser
    from docx import Document  # type: ignore
except ImportError:  # pragma: no cover
    Document = None

try:  # Optional: better MIME sniffing
    import magic  # type: ignore
except ImportError:  # pragma: no cover
    magic = None

logger = logging.getLogger(__name__)

HEADER_FOOTER_PATTERN = re.compile(r'^\s*(page\s+\d+(\s+of\s+\d+)?|\d+)\s*$', re.IGNORECASE)


def _hash(content: str) -> str:
    """Stable SHA-256 hash of normalized content for caching / idempotency."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _normalize_lines(text: str) -> str:
    """Remove blank lines & simple page header/footer patterns; retain semantic content."""
    cleaned = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if HEADER_FOOTER_PATTERN.match(s.lower()):
            continue
        cleaned.append(s)
    return "\n".join(cleaned)


def _sniff_mime(file_path: str) -> Optional[str]:
    """Best-effort MIME type detection; returns None if unknown."""
    if magic:  # pragma: no branch
        try:
            m = magic.Magic(mime=True)
            return m.from_file(file_path)  # type: ignore
        except Exception:  # pragma: no cover
            pass
    guessed, _ = mimetypes.guess_type(file_path)
    return guessed


def _validate_mime(file_path: str) -> str:
    mime = _sniff_mime(file_path)
    if mime and mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Disallowed MIME type detected: {mime}")
    return mime or "unknown"


def extract_text(file_path: str) -> Tuple[str, DocumentMeta]:
    """Extract normalized text + metadata from a supported document.

    Steps:
      1. Existence & size check.
      2. MIME sniff + extension guard.
      3. Format-specific extraction.
      4. PDF density heuristic (reject scanned image PDFs with too little text).
      5. Normalization + length validation.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    size_bytes = os.path.getsize(file_path)
    if size_bytes > MAX_FILE_MB * 1024 * 1024:
        raise ValueError(f"File too large: {size_bytes} bytes exceeds {MAX_FILE_MB}MB limit")

    start_time = time.perf_counter()
    sniffed_mime = _validate_mime(file_path)

    ext = os.path.splitext(file_path)[1].lower()
    raw = ""
    page_count = None

    if ext == '.pdf':
        if not pdfplumber:
            raise RuntimeError("pdfplumber not installed (pip install pdfplumber)")
        char_tallies = []
        with pdfplumber.open(file_path) as pdf:  # type: ignore
            page_count = len(pdf.pages)
            for p in pdf.pages:
                page_text = (p.extract_text() or "")
                raw += page_text + "\n"
                char_tallies.append(len(page_text.strip()))
        if page_count and char_tallies:
            avg_chars = sum(char_tallies) / page_count
            if avg_chars < PDF_MIN_CHARS_PER_PAGE:
                raise ValueError(
                    f"PDF appears low-density (avg {avg_chars:.1f} chars/page < {PDF_MIN_CHARS_PER_PAGE}); likely scanned images."
                )
    elif ext == '.docx':
        if not Document:
            raise RuntimeError("python-docx not installed (pip install python-docx)")
        doc = Document(file_path)  # type: ignore
        for para in doc.paragraphs:
            raw += para.text + "\n"
    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Normalize & length validation
    normalized = _normalize_lines(raw)
    words = len(normalized.split())
    if words < MIN_EXTRACTED_WORDS:
        raise ValueError(
            f"Extracted text too short to summarize (min {MIN_EXTRACTED_WORDS} words, got {words})."
        )

    meta = DocumentMeta(
        source_name=os.path.basename(file_path),
        size_bytes=size_bytes,
        page_count=page_count,
        content_hash=_hash(normalized),
        original_words=words,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "ingestion.extract",
        extra={
            "file": meta.source_name,
            "mime": sniffed_mime,
            "size_bytes": size_bytes,
            "pages": page_count or 0,
            "words": words,
            "elapsed_ms": round(elapsed_ms, 2),
        },
    )
    return normalized, meta
