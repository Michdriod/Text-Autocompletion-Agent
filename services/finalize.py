"""Final refinement service (Step 8): produce a coherent, well-structured Markdown summary at the target ratio."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from utils.generator import generate
from utils.validator import calculate_max_tokens

class FinalizedSummary(BaseModel):
    text: str = Field(..., description="Final Markdown summary")
    summary_words: int = Field(..., ge=0)
    target_words: int = Field(..., ge=1)
    achieved_ratio: float = Field(..., ge=0.0)
    model_config = {"frozen": True}


REFINE_SYSTEM_PROMPT = (
    "You are a careful summarization and editing assistant. "
    "Your job is to refine, compress, and clarify a draft summary into a single, coherent, well-structured Markdown document. "
    "Preserve all key facts, entities, and causal relationships. Use clear sectioning, bullet lists, and concise language. "
    "Do not add a title unless one is clearly present."
)

REFINE_USER_PROMPT = (
    "Refine the following text into a coherent, well-structured Markdown summary of about {target_words} words (20% of the original). "
    "Do not exceed the target by more than 5%. If the text is already concise, focus on improving clarity and flow.\n\n"
    "---\n\n"
    "{draft}"
)


async def refine_summary(
    draft_markdown: str,
    target_words: int,
    *,
    max_tokens: Optional[int] = None,
) -> FinalizedSummary:
    user_prompt = REFINE_USER_PROMPT.format(target_words=target_words, draft=draft_markdown)
    if max_tokens is None:
        token_budget = calculate_max_tokens({"type": "words", "value": target_words})
    else:
        token_budget = max_tokens
    content = await generate(
        system_prompt=REFINE_SYSTEM_PROMPT,
        user_message=user_prompt,
        max_tokens=token_budget,
        temperature=0.2,
        top_p=0.9,
    )
    wc = len(content.split())
    ratio = wc / float(target_words) if target_words else 1.0
    return FinalizedSummary(
        text=content.strip(),
        summary_words=wc,
        target_words=target_words,
        achieved_ratio=ratio,
    )

__all__ = ["FinalizedSummary", "refine_summary"]
