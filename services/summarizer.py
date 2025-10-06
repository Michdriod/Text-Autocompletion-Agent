"""Per-chunk summarization service (Step 5).

Responsibilities:
  * Provide an async API to summarize a list of Chunk objects to ~20% length each.
  * Use Markdown output requirement consistently.
  * Leverage central length planning (validator.calculate_max_tokens) for token budgeting when explicit constraint supplied.
  * Simple concurrency control to avoid flooding the LLM provider.

Design choices:
  * Stateless functions; pass dependencies (generator) explicitly for testability.
  * Rough target words = int(chunk.word_count * ratio). We still rely on prompt instruction; no hard trimming here.
  * Each summarization call uses a consistent system prompt to enforce style & Markdown.
"""
from __future__ import annotations

import asyncio
from typing import List, Sequence, Optional

from config.settings import PER_CHUNK_SUMMARY_RATIO
from services.models import Chunk, PartialSummary
from utils.validator import calculate_max_tokens
from utils.generator import generate

__all__ = ["summarize_chunk", "summarize_chunks"]

SYSTEM_PROMPT = (
    "You are a careful summarization assistant. You compress text faithfully,"
    " preserving key facts, entities, numbers, causal links, and structure."
    " Always produce clean, well-structured Markdown."
)

BASE_USER_INSTRUCTION = (
    "Summarize the following text into approximately {target_words} words (~{ratio_pct}% of its original length).\n"
    "Return ONLY the summary in Markdown (use bullet lists or short paragraphs where helpful).\n"
    "Do not add a title unless one is clearly inherent."
)


async def summarize_chunk(chunk: Chunk, *, ratio: float = PER_CHUNK_SUMMARY_RATIO, max_tokens: Optional[int] = None) -> PartialSummary:
    target_words = max(1, int(chunk.word_count * ratio))
    user_prompt = BASE_USER_INSTRUCTION.format(target_words=target_words, ratio_pct=int(ratio * 100)) + "\n\n" + chunk.text

    if max_tokens is None:
        # Plan tokens based on target words (converted through length planner)
        token_budget = calculate_max_tokens({"type": "words", "value": target_words})
    else:
        token_budget = max_tokens

    content = await generate(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_prompt,
        max_tokens=token_budget,
        temperature=0.3,
        top_p=0.9,
    )
    # Basic word count; no trimming – rely on future compression check
    wc = len(content.split())
    return PartialSummary(
        chunk_id=chunk.id,
        index=chunk.index,
        text=content.strip(),
        word_count=wc,
        compression_ratio=wc / chunk.word_count if chunk.word_count else 1.0,
    )


async def summarize_chunks(
    chunks: Sequence[Chunk],
    *,
    ratio: float = PER_CHUNK_SUMMARY_RATIO,
    concurrency: int = 3,
    max_tokens_override: Optional[int] = None,
) -> List[PartialSummary]:
    """Summarize chunks concurrently with a semaphore-bound fan-out.

    Args:
        chunks: Sequence of Chunk objects.
        ratio: Compression ratio target per chunk.
        concurrency: Max concurrent LLM calls.
        max_tokens_override: Optional fixed token budget for each call.
    """
    sem = asyncio.Semaphore(concurrency)
    results: List[Optional[PartialSummary]] = [None] * len(chunks)

    async def _one(c: Chunk):
        async with sem:
            summary = await summarize_chunk(c, ratio=ratio, max_tokens=max_tokens_override)
            results[c.index] = summary

    await asyncio.gather(*[_one(c) for c in chunks])
    # Filter in case of any unexpected None (should not happen)
    return [r for r in results if r is not None]
