"""Final refinement service (Step 8): produce a coherent, well-structured Markdown summary at the absolute target word count.

Ratio-based wording has been removed. This stage focuses on polishing the draft while safeguarding:
    * Fidelity (no hallucinations)
    * Conciseness (remove redundancy, keep essential facts)
    * Structural clarity (logical sections, bullets / tables when helpful)
    * Non-truncation (never end mid-sentence)
    * Deterministic length hand-off (close to target; strict enforcement occurs later)
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from utils.generator import generate_with_continuation
from utils.validator import calculate_max_tokens

class FinalizedSummary(BaseModel):
    text: str = Field(..., description="Final Markdown summary")
    summary_words: int = Field(..., ge=0)
    target_words: int = Field(..., ge=1)
    achieved_ratio: float = Field(..., ge=0.0)
    model_config = {"frozen": True}


END_MARKER = "<END_OF_DOCUMENT>"

REFINE_SYSTEM_PROMPT = (
    "You are a precise, professional summarization and editing assistant. "
    "Refine the supplied draft into a polished, coherent Markdown summary. "
    "Preserve all key facts, figures, entities, causal relationships, and critical nuances. "
    "Eliminate redundancy, tighten phrasing, and improve clarity WITHOUT omitting essential information. "
    "Do not hallucinate or invent facts. Do not copy large blocks verbatim—paraphrase succinctly. "
    "Use Markdown structures (short paragraphs, bullet lists, tables) only where they truly improve readability. "
    "Do not add a title unless one is clearly present in the draft. "
    "Always finish with a complete concluding sentence. Never end mid-sentence or with trailing punctuation. "
    f"Append the marker {END_MARKER} on a new line at the very end when you are fully done."
)

REFINE_USER_PROMPT = (
    "Refine the following draft into a coherent Markdown summary of EXACTLY {target_words} words (±2 words ONLY if exact match is impossible without harming clarity). "
    "If it is already near the target, focus only on polish and structure. "
    "Do NOT introduce new facts. Do NOT truncate. Ensure professional tone and completeness.\n\n"
    "--- DRAFT START ---\n"
    "{draft}\n"
    "--- DRAFT END ---"
)


async def refine_summary(
    draft_markdown: str,
    target_words: int,
    *,
    max_tokens: Optional[int] = None,
) -> FinalizedSummary:
    user_prompt = REFINE_USER_PROMPT.format(target_words=target_words, draft=draft_markdown)

    # Provide a slightly larger token budget (1.25x) to reduce premature cutoffs; enforcement adjusts later.
    if max_tokens is None:
        token_budget = int(calculate_max_tokens({"type": "words", "value": int(target_words * 1.25)}))
    else:
        token_budget = max_tokens

    content = await generate_with_continuation(
        system_prompt=REFINE_SYSTEM_PROMPT,
        user_message=user_prompt + "\n\nEnsure output is complete and not cut off mid-sentence.",
        max_tokens=token_budget,
        temperature=0.2,
        top_p=0.95,
        end_marker=END_MARKER,
        max_iterations=4,
    )
    content = content.replace(END_MARKER, "").strip()
    wc = len(content.split())
    ratio = wc / float(target_words) if target_words else 1.0
    return FinalizedSummary(text=content, summary_words=wc, target_words=target_words, achieved_ratio=ratio)

__all__ = ["FinalizedSummary", "refine_summary"]
