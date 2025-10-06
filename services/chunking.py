"""Chunking service (Step 4): split cleaned document text into overlapping word-based chunks.

Design Goals:
  * Deterministic, no side-effects.
  * Word-based (not character, not page) to align with LLM planning and ratio math.
  * Sliding window with configurable target size and overlap percentage.
  * Avoid producing extremely tiny trailing chunks; merge remainder when it is small (< 40% target).
  * Provide simple extension points (future: semantic splitting, heading awareness) without changing API.
"""
from __future__ import annotations

from typing import Iterable, List, Sequence
import math
import uuid

from config.settings import CHUNK_TARGET_WORDS, CHUNK_OVERLAP_PCT
from services.models import make_chunk, Chunk

__all__ = ["chunk_document", "plan_chunk_word_spans"]


def plan_chunk_word_spans(total_words: int, target_words: int = CHUNK_TARGET_WORDS, overlap_pct: float = CHUNK_OVERLAP_PCT) -> List[tuple[int, int]]:
    """Plan (start, end) word index spans for chunks (end exclusive).

    Args:
        total_words: Number of words in the cleaned full document.
        target_words: Desired nominal size of each chunk.
        overlap_pct: Fraction of target to overlap between consecutive chunks.

    Returns:
        List of (start, end) tuples referencing word indices.
    """
    if total_words <= 0:
        return []
    target = max(50, target_words)  # guardrail: avoid overly small targets
    overlap_words = int(target * overlap_pct)
    stride = max(10, target - overlap_words)

    spans: List[tuple[int, int]] = []
    start = 0
    while start < total_words:
        end = min(total_words, start + target)
        spans.append((start, end))
        if end >= total_words:
            break
        start = start + stride

    # Merge small tail if last span too short (<40% of target) and we have >1 spans
    if len(spans) > 1:
        last_start, last_end = spans[-1]
        if (last_end - last_start) < int(target * 0.4):
            # Merge with previous
            prev_start, _ = spans[-2]
            spans[-2] = (prev_start, last_end)
            spans.pop()
    return spans


def chunk_document(cleaned_text: str, *, target_words: int = CHUNK_TARGET_WORDS, overlap_pct: float = CHUNK_OVERLAP_PCT) -> List[Chunk]:
    """Produce Chunk models from cleaned text.

    Strategy:
      1. Split words once.
      2. Plan spans.
      3. Join words for each span (preserving original word order).
      4. Build immutable Chunk objects via factory.

    Args:
        cleaned_text: Preprocessed document text.
        target_words: Desired chunk size (~1000 default).
        overlap_pct: Overlap fraction (e.g., 0.12 for 12%).
    """
    words = [w for w in cleaned_text.split() if w.strip()]
    total = len(words)
    spans = plan_chunk_word_spans(total, target_words=target_words, overlap_pct=overlap_pct)
    chunks: List[Chunk] = []
    for idx, (s, e) in enumerate(spans):
        slice_words = words[s:e]
        text = " ".join(slice_words)
        # Stable-ish id: use uuid4 but could be swapped for hash later.
        cid = uuid.uuid4().hex[:12]
        chunks.append(make_chunk(cid, idx, text))
    return chunks
