"""Baseline metrics computation (Step 3: measure document length & target summary size).

This module is intentionally lean: it provides reusable helpers that later stages
(chunking, per-chunk summarization, final synthesis) can rely upon without duplicating
logic about ratios or guardrails.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from config.settings import PER_CHUNK_SUMMARY_RATIO, summary_target_words


class BaselineMetrics(BaseModel):
    """Immutable metrics snapshot about the document size & targets."""
    total_words: int
    final_target_words: int
    per_chunk_ratio: float

    model_config = dict(frozen=True)

    @property
    def per_chunk_multiplier(self) -> float:  # backward-friendly alias
        return self.per_chunk_ratio


def count_words(text: str) -> int:
    """Robust word counter (splits on whitespace, filters empty tokens)."""
    if not text:
        return 0
    return sum(1 for t in text.split() if t.strip())


def compute_baseline_metrics(cleaned_text: str, final_ratio_override: Optional[float] = None) -> BaselineMetrics:
    """Compute baseline metrics for a cleaned document.

    Args:
        cleaned_text: Document text after preprocessing (clean_text output concatenated).
        final_ratio_override: Optional override for final summary ratio.

    Returns:
        BaselineMetrics(total_words, final_target_words, per_chunk_ratio)
    """
    total = count_words(cleaned_text)
    final_target = summary_target_words(total, ratio=final_ratio_override)
    return BaselineMetrics(
        total_words=total,
        final_target_words=final_target,
        per_chunk_ratio=PER_CHUNK_SUMMARY_RATIO,
    )

__all__ = [
    "BaselineMetrics",
    "count_words",
    "compute_baseline_metrics",
]
