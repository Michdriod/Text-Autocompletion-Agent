"""Refinement planning (Step 7): decide if merged summary needs recompression or expansion."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from config.settings import LOW_DENSITY_RECHECK_RATIO, HIGH_DENSITY_RECOMPRESS_RATIO

class RefinementDecision(BaseModel):
    action: str = Field(..., description="ok | recompress | expand")
    target_words: int = Field(..., ge=1)
    actual_words: int = Field(..., ge=0)
    ratio: float = Field(..., ge=0.0)
    reason: Optional[str] = None
    model_config = {"frozen": True}


def plan_refinement(
    summary_words: int,
    target_words: int,
    *,
    low_ratio: float = LOW_DENSITY_RECHECK_RATIO,
    high_ratio: float = HIGH_DENSITY_RECOMPRESS_RATIO,
) -> RefinementDecision:
    """Decide if the summary needs recompression, expansion, or is OK.

    Args:
        summary_words: Actual word count of merged summary.
        target_words: Planned/desired word count.
        low_ratio: Lower bound (default from config).
        high_ratio: Upper bound (default from config).
    Returns:
        RefinementDecision(action, target_words, actual_words, ratio, reason)
    """
    if target_words <= 0:
        raise ValueError("target_words must be > 0")
    ratio = summary_words / float(target_words)
    if ratio > high_ratio:
        return RefinementDecision(
            action="recompress",
            target_words=target_words,
            actual_words=summary_words,
            ratio=ratio,
            reason=f"Summary too long ({summary_words} > {int(target_words*high_ratio)})"
        )
    elif ratio < low_ratio:
        return RefinementDecision(
            action="expand",
            target_words=target_words,
            actual_words=summary_words,
            ratio=ratio,
            reason=f"Summary too short ({summary_words} < {int(target_words*low_ratio)})"
        )
    else:
        return RefinementDecision(
            action="ok",
            target_words=target_words,
            actual_words=summary_words,
            ratio=ratio,
            reason="Summary within acceptable range."
        )

__all__ = ["RefinementDecision", "plan_refinement"]
