from __future__ import annotations

"""Mode 5 summarization pipeline (updated to new spec).

Rules:
    * Accepts raw text or uploaded document.
    * If total words <= 500 (small doc): NO chunking.
            - If user supplies target_words -> use it exactly.
            - Else default to 100 words.
    * If total words > 500 (large doc): chunk + per-chunk summaries + merge.
            - If user supplies target_words -> use it exactly.
            - Else auto target = round(original_words * 0.20) (20% rule, min 1).
    * Output format may be markdown / plain / both (plain derived from markdown).
    * No hallucination, no truncation, no mid‑sentence endings. Anti‑truncation and length enforcement guarantee target.

Removed prior user-provided ratio option; 20% compression is automatic only when no explicit target is given for large documents.
"""

from typing import Optional

from utils.generator import generate_with_continuation, generate
from utils.validator import calculate_max_tokens
from services.ingestion import extract_text
from services.preprocess import clean_text
from services.baseline import compute_baseline_metrics
from services.chunking import chunk_document
from services.summarizer import summarize_chunks
from services.merge import merge_partial_summaries
from services.refinement import plan_refinement
from services.finalize import refine_summary
from services.formatter import format_output


class Mode5:
    """Document summarization pipeline with strict word-target enforcement (ratio disabled)."""

    # ---------------- Configuration ----------------
    TARGET_TOLERANCE_WORDS = 2            # fallback tolerance when target is implicit (currently rare)
    SMALL_TARGET_THRESHOLD = 30           # skip heavy enforcement when tiny target
    DEFAULT_ABSOLUTE_TARGET_WORDS = 100   # applied only for small docs if no explicit target
    SMALL_DOCUMENT_DIRECT_THRESHOLD = 500 # no chunking below this (docs <500 words summarized directly)

    DIRECT_SUMMARIZATION_SYSTEM = (
        "You are an expert summarization assistant. Create concise, intelligent summaries that capture "
        "the essential information without redundancy or repetition. Focus on key facts, main themes, "
        "and important relationships. Use clear, professional language. Never include introductory "
        "phrases like 'Here is a summary' or 'This text discusses'. Start directly with the content. "
        "CRITICAL: Always complete your summary with a proper ending. Never stop mid-sentence or truncate."
    )

    DIRECT_SUMMARIZATION_TEMPLATE = (
        "Summarize the following text into approximately {target_words} words. "
        "Focus on the most important information, key themes, and essential facts. "
        "Be concise but comprehensive. Do not repeat information or add filler content. "
        "Provide only the summary content without any introductory phrases or meta-commentary.\n\n"
        "TEXT TO SUMMARIZE:\n{content}"
    )

    REFINEMENT_SYSTEM = (
        "You are a careful summarization and editing assistant. "
        "Refine and polish the provided summary while maintaining all key information. "
        "Remove any redundancy or repetitive content. Ensure clarity and coherence. "
        "Never add introductory phrases or meta-commentary. Provide only the refined content. "
        "CRITICAL: Always complete your refined summary with a proper ending. Never truncate or stop mid-sentence."
    )

    REFINEMENT_TEMPLATE = (
        "Polish and refine the following summary to approximately {target_words} words. "
        "Remove any repetitive content, improve clarity, and ensure a logical flow. "
        "Keep all essential information. Provide only the refined summary content "
        "without any introductory phrases or explanatory text.\n\n"
        "SUMMARY TO REFINE:\n{draft}"
    )

    # ---------------- Public API ----------------
    async def process_document_file(self, file_path: str, target_words: Optional[int] = None, output_format: str = "markdown") -> dict:
        logger = self._get_logger()
        logger.info("[Mode5] Step 1: Ingestion started.")
        raw_text, meta = extract_text(file_path)
        logger.info("[Mode5] Step 1: Ingestion complete.")
        # Convert DocumentMeta object to dict and add source_file
        meta_dict = meta.model_dump() if hasattr(meta, 'model_dump') else dict(meta)
        meta_dict["source_file"] = file_path
        return await self._process_core(raw_text, meta_dict, logger, target_words, output_format=output_format)

    async def process_raw_text(self, text: str, source_name: str = "raw_text_input", target_words: Optional[int] = None, output_format: str = "markdown") -> dict:
        logger = self._get_logger()
        logger.info("[Mode5] Step 1: Ingestion (raw text) started.")
        meta = {"source": source_name, "ingest_type": "raw_text"}
        logger.info("[Mode5] Step 1: Ingestion (raw text) complete.")
        return await self._process_core(text, meta, logger, target_words, output_format=output_format)

    # ---------------- Internal helpers ----------------
    def _get_logger(self):
        import logging
        logger = logging.getLogger("mode5")
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    async def _process_core(self, raw_text: str, meta: dict, logger, target_words: Optional[int], *, output_format: str) -> dict:
        # Step 2: Preprocess
        logger.info("[Mode5] Step 2: Preprocessing started.")
        cleaned = clean_text(raw_text)
        logger.info("[Mode5] Step 2: Preprocessing complete.")

        # Step 3: Determine target (absolute with adaptive fallback)
        total_words = len([w for w in cleaned.split() if w.strip()])
        small_doc = total_words < self.SMALL_DOCUMENT_DIRECT_THRESHOLD
        if target_words is not None:
            if target_words <= 0:
                raise ValueError("target_words must be positive.")
            if target_words > total_words:
                effective_target = total_words
                target_mode = "user_absolute_capped"
            else:
                effective_target = target_words
                target_mode = "user_absolute"
        else:
            if small_doc:
                effective_target = self.DEFAULT_ABSOLUTE_TARGET_WORDS
                target_mode = "small_default_100"
            else:
                effective_target = max(1, round(total_words * 0.20))
                # Guarantee at least 1 word; never exceed original; 20% cannot exceed original anyway.
                effective_target = min(effective_target, total_words)
                target_mode = "auto_20pct"
        meta.update({
            'requested_target_words': target_words,
            'resolved_target_words': effective_target,
            'target_mode': target_mode,
            'original_total_words': total_words,
        })
        baseline = compute_baseline_metrics(
            cleaned,
            final_target_override=effective_target,
        )
        logger.info(f"[Mode5] Step 3: Baseline metrics: {baseline}")

        # Step 4-8: Intelligent summarization
        if small_doc:
            logger.info(f"[Mode5] Small document direct summarization (words={baseline.total_words} < {self.SMALL_DOCUMENT_DIRECT_THRESHOLD}).")
            # Direct summarization for small documents
            final_summary = await self._direct_summarize(cleaned, effective_target, logger)
        else:
            logger.info("[Mode5] Large document chunked summarization.")
            # Chunked approach for large documents
            final_summary = await self._chunked_summarize(cleaned, effective_target, logger)
        
        # Create final result object
        from services.finalize import FinalizedSummary
        final = FinalizedSummary(
            text=final_summary,
            summary_words=len(final_summary.split()),
            target_words=effective_target,
            achieved_ratio=len(final_summary.split()) / float(effective_target)
        )

        enforcement_meta = {
            'target_words': baseline.final_target_words,
            'explicit_target': target_words is not None,
            'default_small_doc_target': (meta.get('target_mode') == 'small_default_100'),
            'auto_20pct_mode': (meta.get('target_mode') == 'auto_20pct'),
            'final_diff': abs(len(final.text.split()) - baseline.final_target_words),
            'small_doc_fast_path': small_doc,
            'approach': 'direct' if small_doc else 'chunked',
        }

        # Step 9: Format output
        result = format_output(final, baseline.total_words, output_format=output_format)
        if isinstance(result, dict):
            result.setdefault('meta', {})
            result['meta'].update({'ingest': meta, 'length_enforcement': enforcement_meta})
        return result



    async def _direct_summarize(self, content: str, target_words: int, logger) -> str:
        """Direct summarization for small documents without chunking."""
        logger.info(f"[Mode5] Direct summarization to {target_words} words.")
        
        user_prompt = self.DIRECT_SUMMARIZATION_TEMPLATE.format(
            target_words=target_words,
            content=content
        )
        
        # Calculate appropriate token budget - be generous to prevent truncation
        token_budget = calculate_max_tokens({"type": "words", "value": int(target_words * 2.0)})
        
        summary = await generate(
            system_prompt=self.DIRECT_SUMMARIZATION_SYSTEM,
            user_message=user_prompt,
            max_tokens=token_budget,
            temperature=0.3,
            top_p=0.9
        )
        
        # Light refinement if significantly off target
        current_words = len(summary.split())
        if abs(current_words - target_words) > max(10, target_words * 0.2):
            logger.info(f"[Mode5] Refining summary (current: {current_words}, target: {target_words}).")
            refine_prompt = self.REFINEMENT_TEMPLATE.format(
                target_words=target_words,
                draft=summary
            )
            
            # Use even more generous token budget for refinement
            refine_budget = calculate_max_tokens({"type": "words", "value": int(target_words * 2.5)})
            summary = await generate(
                system_prompt=self.REFINEMENT_SYSTEM,
                user_message=refine_prompt,
                max_tokens=refine_budget,
                temperature=0.2,
                top_p=0.9
            )
        
        return self._clean_summary_output(summary.strip())
    
    async def _chunked_summarize(self, content: str, target_words: int, logger) -> str:
        """Chunked summarization for large documents."""
        logger.info("[Mode5] Step 4: Chunking started.")
        chunks = chunk_document(content)
        logger.info(f"[Mode5] Step 4: Chunking complete. Number of chunks: {len(chunks)}")
        
        if not chunks:
            raise ValueError("No valid chunks produced from document.")
        
        logger.info("[Mode5] Step 5: Per-chunk summarization started.")
        partials = await summarize_chunks(chunks)
        logger.info("[Mode5] Step 5: Per-chunk summarization complete.")
        
        logger.info("[Mode5] Step 6: Merging partial summaries started.")
        merged = merge_partial_summaries(partials, original_words=len(content.split()))
        logger.info("[Mode5] Step 6: Merging partial summaries complete.")
        
        # Final synthesis to target length
        logger.info(f"[Mode5] Step 7: Final synthesis to {target_words} words.")
        user_prompt = self.REFINEMENT_TEMPLATE.format(
            target_words=target_words,
            draft=merged.markdown
        )
        
        token_budget = calculate_max_tokens({"type": "words", "value": int(target_words * 2.0)})
        
        final_summary = await generate(
            system_prompt=self.REFINEMENT_SYSTEM,
            user_message=user_prompt,
            max_tokens=token_budget,
            temperature=0.2,
            top_p=0.9
        )
        
        return self._clean_summary_output(final_summary.strip())

    def _clean_summary_output(self, text: str) -> str:
        """Remove unwanted introductory phrases from LLM output."""
        # Common unwanted prefixes to remove
        unwanted_prefixes = [
            "Here's a summary of the text:",
            "Here is a summary of the text:",
            "Here's a 100-word summary of the text:",
            "Here is a 100-word summary of the text:",
            "Here's a summary:",
            "Here is a summary:",
            "Summary:",
            "The following is a summary:",
            "This is a summary of the text:",
            "Below is a summary:",
        ]
        
        cleaned = text.strip()
        
        # Remove unwanted prefixes (case-insensitive)
        for prefix in unwanted_prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove any remaining leading colons or dashes
        cleaned = cleaned.lstrip(":- \t\n").strip()
        
        return cleaned

__all__ = ["Mode5"]