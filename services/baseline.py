"""Baseline metrics computation (Step 3: measure document length & target summary size).

This module is intentionally lean: it provides reusable helpers that later stages
(chunking, per-chunk summarization, final synthesis) can rely upon without duplicating
logic about ratios or guardrails.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from config.settings import PER_CHUNK_SUMMARY_RATIO, MIN_EXTRACTED_WORDS, MAX_FINAL_WORDS


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


def compute_baseline_metrics(
    cleaned_text: str,
    final_target_override: Optional[int] = None,
) -> BaselineMetrics:
    """Compute baseline metrics (ratio disabled).

    Args:
        cleaned_text: preprocessed full document text.
        final_target_override: explicit final summary length in words (mandatory unless caller handles defaults).

    Behavior:
        * If final_target_override provided -> clamp within global bounds.
        * If not provided -> raise ValueError (callers must decide defaults, e.g. small-doc fallback).
    """
    total = count_words(cleaned_text)
    if final_target_override is None or final_target_override <= 0:
        raise ValueError(
            "final_target_override is required (ratio-based targeting disabled). Provide explicit target words or a default before calling compute_baseline_metrics."
        )
    target = final_target_override
    if MAX_FINAL_WORDS:
        target = min(target, MAX_FINAL_WORDS)
    final_target = max(MIN_EXTRACTED_WORDS, target)
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
