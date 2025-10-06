"""Output formatter (Step 9): produce final JSON with Markdown and metadata."""
from __future__ import annotations
from typing import Dict
from services.finalize import FinalizedSummary

def format_output(
    finalized: FinalizedSummary,
    original_words: int,
) -> Dict[str, object]:
    """Return summary and metadata as a JSON-serializable dict.

    Args:
        finalized: FinalizedSummary model (from refine_summary)
        original_words: Word count of the original document
    Returns:
        Dict with keys: original_words, summary_words, percent, markdown_summary
    """
    percent = finalized.summary_words / float(original_words) if original_words else 1.0
    return {
        "original_words": original_words,
        "summary_words": finalized.summary_words,
        "percent": percent,
        "markdown_summary": finalized.text,
    }

__all__ = ["format_output"]
