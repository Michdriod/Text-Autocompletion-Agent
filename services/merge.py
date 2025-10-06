"""Merge service (Step 6): combine per-chunk partial summaries into a single draft.

Goals:
  * Deterministic ordering by original chunk index.
  * Minimal formatting: each partial under a Markdown heading.
  * Provide a lightweight metadata model for downstream refinement / final compression.
  * Avoid re-counting source chunk words (we only care about partial + original total passed in).
"""
from __future__ import annotations

from typing import List, Sequence, Optional
from pydantic import BaseModel, Field

from services.models import PartialSummary

__all__ = ["MergedDraft", "merge_partial_summaries"]


class MergedDraft(BaseModel):
    """Represents a combined markdown draft assembled from partial summaries."""
    markdown: str = Field(..., description="Combined Markdown document")
    total_summary_words: int = Field(..., ge=0)
    partial_count: int = Field(..., ge=0)
    original_words: Optional[int] = Field(None, ge=0)
    combined_ratio: Optional[float] = Field(None, ge=0.0)

    model_config = {"frozen": True}


def merge_partial_summaries(
    partials: Sequence[PartialSummary],
    *,
    original_words: Optional[int] = None,
    heading_template: str = "## Summary of Chunk {n}",
    include_index_comment: bool = False,
) -> MergedDraft:
    """Merge ordered partial summaries into a single Markdown draft.

    Args:
        partials: Sequence of PartialSummary objects (any order). Will be sorted by index.
        original_words: Optional original full-document word count for ratio calculation.
        heading_template: Format string for each chunk heading (uses {n} => 1-based index).
        include_index_comment: If True, insert HTML comments with chunk ids for traceability.
    """
    if not partials:
        return MergedDraft(
            markdown="",
            total_summary_words=0,
            partial_count=0,
            original_words=original_words,
            combined_ratio=0.0 if original_words else None,
        )

    ordered = sorted(partials, key=lambda p: p.index)
    lines: List[str] = []
    total_words = 0

    for p in ordered:
        heading = heading_template.format(n=p.index + 1)
        lines.append(heading)
        if include_index_comment:
            lines.append(f"<!-- chunk_id: {p.chunk_id} index: {p.index} -->")
        lines.append(p.text.strip())
        lines.append("")  # blank line separator
        total_words += p.word_count

    markdown = "\n".join(lines).rstrip()
    ratio = None
    if original_words and original_words > 0:
        ratio = total_words / float(original_words)

    return MergedDraft(
        markdown=markdown,
        total_summary_words=total_words,
        partial_count=len(ordered),
        original_words=original_words,
        combined_ratio=ratio,
    )
