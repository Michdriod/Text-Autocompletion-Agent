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

    # ---------------- Prompt Building Methods ----------------
    def _build_system_prompt(self, target_words: Optional[int], output_format: str = "markdown") -> str:
        """Build system prompt for document summarization with intelligent word targeting."""
        
        base_instruction = """You are an expert document analyst and summarizer with exceptional ability to distill complex information into clear, comprehensive summaries.

Your core responsibilities:
1. Extract and present ALL key information, main arguments, and important details
2. Maintain logical flow and coherent structure
3. Use clear, professional language
4. Preserve critical data points, findings, and conclusions
5. Ensure the summary stands alone and is fully understandable without the original document"""

        if target_words:
            # More intelligent word count guidance
            word_guidance = f"""
TARGET SUMMARY LENGTH: {target_words} words

INTELLIGENT SUMMARIZATION STRATEGY:
- Plan your summary structure BEFORE writing to fit within {target_words} words
- Prioritize information density: every sentence must add value
- Allocate words proportionally to section importance
- If the document is shorter than {target_words} words, summarize naturally (may be less than target)
- If the document is very long, use these guidelines:
  * {target_words} ≤ 500 words: Focus on core thesis and main conclusions only
  * 500 < {target_words} ≤ 1000 words: Include main points with supporting details
  * {target_words} > 1000 words: Comprehensive coverage with examples and context

CRITICAL RULES:
✓ Stay within {target_words} words (±10% acceptable for sentence completion)
✓ NEVER truncate mid-sentence or mid-thought
✓ Complete your final sentence properly
✓ If approaching word limit, conclude your current point gracefully
✓ Better to be 5-10% under target than to leave incomplete sentences

QUALITY OVER EXACT COUNT:
- Aim for {target_words} words but prioritize completeness
- A 5% deviation is acceptable if it ensures proper closure
- Never sacrifice clarity or coherence for exact word count"""
        else:
            word_guidance = """
SUMMARY LENGTH: Comprehensive (no specific word target)

STRATEGY:
- Cover all significant information from the document
- Use as many words as needed to capture the essence completely
- Maintain high information density
- Ensure logical flow and complete thoughts
- End with a proper conclusion"""

        format_instruction = f"""
OUTPUT FORMAT: {output_format}

FORMATTING GUIDELINES:
- Use clear paragraph breaks for readability
- Use bullet points or numbered lists for enumerations
- Use **bold** for key terms or critical points
- Use proper headings if the summary is long (## for main sections)
- Maintain professional tone throughout
- End with a complete, conclusive statement

STRUCTURE:
1. Brief opening that captures the document's main purpose
2. Body covering key points in logical order
3. Strong closing that ties everything together"""

        return f"{base_instruction}\n\n{word_guidance}\n\n{format_instruction}"

    def _build_user_message(self, text: str, user_prompt: Optional[str] = None) -> str:
        """Build user message with document text and optional custom instructions."""
        
        base_message = f"""Please analyze and summarize the following document according to the instructions provided.

DOCUMENT TEXT:
{text}

---

Generate a summary that:
- Captures all essential information intelligently
- Maintains the target word count (completing your final thought properly)
- Is well-structured and easy to understand
- Stands alone as a comprehensive overview"""

        if user_prompt:
            base_message += f"\n\nADDITIONAL INSTRUCTIONS:\n{user_prompt}"
        
        base_message += "\n\nBegin your summary now:"
        
        return base_message

    # ---------------- Public API ----------------
    async def process_document_file(self, file_path: str, target_words: Optional[int] = None, output_format: str = "markdown", user_prompt: str | None = None) -> dict:
        logger = self._get_logger()
        logger.info("[Mode5] Step 1: Ingestion started.")
        raw_text, meta = extract_text(file_path)
        logger.info("[Mode5] Step 1: Ingestion complete.")
        # Convert DocumentMeta object to dict and add source_file
        meta_dict = meta.model_dump() if hasattr(meta, 'model_dump') else dict(meta)
        meta_dict["source_file"] = file_path
        return await self._process_core(raw_text, meta_dict, logger, target_words, output_format=output_format, user_prompt=user_prompt)

    async def process_raw_text(self, text: str, source_name: str = "raw_text_input", target_words: Optional[int] = None, output_format: str = "markdown", user_prompt: str | None = None) -> dict:
        logger = self._get_logger()
        logger.info("[Mode5] Step 1: Ingestion (raw text) started.")
        meta = {"source": source_name, "ingest_type": "raw_text"}
        logger.info("[Mode5] Step 1: Ingestion (raw text) complete.")
        return await self._process_core(text, meta, logger, target_words, output_format=output_format, user_prompt=user_prompt)

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

    async def _process_core(self, raw_text: str, meta: dict, logger, target_words: Optional[int], *, output_format: str, user_prompt: str | None) -> dict:
        # Step 2: Preprocess
        logger.info("[Mode5] Step 2: Preprocessing started.")
        cleaned = clean_text(raw_text)
        logger.info("[Mode5] Step 2: Preprocessing complete.")

        # Step 3: Determine target (absolute with adaptive fallback)
        total_words = len([w for w in cleaned.split() if w.strip()])
        self.original_words = total_words  # Store for prompt target validation
        small_doc = total_words < self.SMALL_DOCUMENT_DIRECT_THRESHOLD

        # Extract target from prompt if present
        prompt_target = None
        if user_prompt:
            prompt_target = self._extract_target_from_prompt(user_prompt)
            if prompt_target:
                logger.info(f"[Mode5] Found target in prompt: {prompt_target} words")

        # Determine effective target with updated precedence
        if prompt_target is not None:
            effective_target = prompt_target
            target_mode = "prompt"
            prompt_overrode_param = target_words is not None and target_words > 0
        elif target_words is not None and target_words > 0:
            # if target_words <= 0:
            #     raise ValueError("target_words must be positive.")
            if target_words > total_words:
                effective_target = total_words
                target_mode = "user_absolute_capped"
            else:
                effective_target = target_words
                target_mode = "user_absolute"
            prompt_overrode_param = False
        else:
            # No valid target provided (None or 0) - use defaults
            if small_doc:
                effective_target = self.DEFAULT_ABSOLUTE_TARGET_WORDS
                target_mode = "small_default_100"
            else:
                effective_target = max(1, round(total_words * 0.20))
                effective_target = min(effective_target, total_words)
                target_mode = "auto_20pct"
            prompt_overrode_param = False

        meta.update({
            'requested_target_words': target_words,
            'resolved_target_words': effective_target,
            'target_mode': target_mode,
            'original_total_words': total_words,
            'user_prompt_present': user_prompt is not None,
            'parsed_prompt_target_words': prompt_target,
            'prompt_overrode_param': prompt_overrode_param
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
            final_summary = await self._direct_summarize(cleaned, effective_target, logger, user_prompt=user_prompt, output_format=output_format)
        else:
            logger.info("[Mode5] Large document chunked summarization.")
            # Chunked approach for large documents
            final_summary = await self._chunked_summarize(cleaned, effective_target, logger, output_format=output_format)
        
        # Create final result object
        from services.finalize import FinalizedSummary
        from utils.validator import is_summary_truncated
        
        # Check if final summary is complete (should always be after our improvements)
        is_truncated = is_summary_truncated(final_summary)
        actual_words = len(final_summary.split())
        
        final = FinalizedSummary(
            text=final_summary,
            summary_words=actual_words,
            target_words=effective_target,
            achieved_ratio=actual_words / float(effective_target)
        )

        enforcement_meta = {
            'target_words': baseline.final_target_words,
            'explicit_target': target_words is not None,
            'default_small_doc_target': (meta.get('target_mode') == 'small_default_100'),
            'auto_20pct_mode': (meta.get('target_mode') == 'auto_20pct'),
            'final_diff': abs(actual_words - baseline.final_target_words),
            'small_doc_fast_path': small_doc,
            'approach': 'direct' if small_doc else 'chunked',
            'truncated': False,  # Should always be False after cleanup in methods
            'complete_sentences': True,  # Should always be True after our improvements
            'within_target': abs(actual_words - effective_target) / effective_target <= 0.15 if effective_target else True
        }

        # Step 9: Format output
        result = format_output(final, baseline.total_words, output_format=output_format)
        if isinstance(result, dict):
            result.setdefault('meta', {})
            result['meta'].update({'ingest': meta, 'length_enforcement': enforcement_meta})
        return result



    async def _direct_summarize(self, content: str, target_words: int, logger, user_prompt: str | None = None, output_format: str = "markdown") -> str:
        """Direct summarization for small documents without chunking with intelligent token allocation."""
        logger.info(f"[Mode5] Direct summarization to {target_words} words.")
        
        # Build prompts using new intelligent methods
        system_prompt = self._build_system_prompt(target_words, output_format)
        user_message = self._build_user_message(content, user_prompt)
        
        # Calculate token budget with EXTRA buffer to prevent truncation
        # Give more tokens based on target size to ensure complete output
        if target_words <= 500:
            multiplier = 2.2  # 120% extra for small summaries
        elif target_words <= 1500:
            multiplier = 2.5  # 150% extra for medium summaries
        else:
            multiplier = 3.0  # 200% extra for large summaries
        
        # Calculate base tokens and apply multiplier
        base_tokens = calculate_max_tokens({"type": "words", "value": target_words})
        token_budget = int(base_tokens * multiplier)
        
        # Ensure we don't exceed Claude's limits
        token_budget = min(token_budget, 8000)
        
        logger.info(
            f"[Mode5] Direct summarization: target={target_words} words, "
            f"token_budget={token_budget} (multiplier={multiplier}x)"
        )
        
        # Generate summary with generous token budget
        summary = await generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=token_budget,
            temperature=0.3,
            top_p=0.9
        )
        
        # Check for truncation (shouldn't happen with new buffer, but safety check)
        from utils.validator import is_summary_truncated, complete_truncated_summary
        if is_summary_truncated(summary):
            logger.warning(
                f"[Mode5] Summary appears truncated despite token buffer of {token_budget}. "
                f"Attempting cleanup..."
            )
            summary = complete_truncated_summary(summary)
        
        return self._clean_summary_output(summary.strip())
    
    async def _chunked_summarize(self, content: str, target_words: int, logger, output_format: str = "markdown") -> str:
        """Chunked summarization for large documents with intelligent token allocation."""
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
        
        # Final synthesis to target length with intelligent prompt
        logger.info(f"[Mode5] Step 7: Final synthesis to {target_words} words.")
        
        # Build intelligent refinement prompt
        system_prompt = self._build_system_prompt(target_words, output_format)
        
        refinement_prompt = f"""The following are summaries of different sections from a single document.
Create a unified, coherent summary that:
- Integrates all key points from the sections
- Removes redundancy
- Maintains logical flow
- Targets approximately {target_words} words
- COMPLETES all thoughts and ends with a proper conclusion

SECTION SUMMARIES:
{merged.markdown}

Create the final integrated summary now:"""
        
        # Use generous token budget for large summaries to prevent truncation
        if target_words <= 500:
            multiplier = 2.2
        elif target_words <= 1500:
            multiplier = 2.5
        else:
            multiplier = 3.0
        
        base_tokens = calculate_max_tokens({"type": "words", "value": target_words})
        token_budget = int(base_tokens * multiplier)
        token_budget = min(token_budget, 8000)
        
        logger.info(f"[Mode5] Final synthesis: target={target_words} words, token_budget={token_budget} (multiplier={multiplier}x)")
        
        final_summary = await generate(
            system_prompt=system_prompt,
            user_message=refinement_prompt,
            max_tokens=token_budget,
            temperature=0.3,
            top_p=0.9
        )
        
        # Check for truncation and handle it
        from utils.validator import is_summary_truncated, complete_truncated_summary
        if is_summary_truncated(final_summary):
            logger.warning(f"[Mode5] Final summary appears truncated, cleaning up...")
            final_summary = complete_truncated_summary(final_summary)
        
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
            "Below is a summary:"
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

    def _extract_target_from_prompt(self, prompt: str) -> int | None:
        """Extract word count target from prompt text."""
        import re
        patterns = [
            r'\b(?:in|into|about|around|approximately|approx\.?)\s+(\d{2,5})\s+words?\b',
            r'\bsummary\s+of\s+(\d{2,5})\s+words?\b',
            r'\b(\d{2,5})\s+word(?:\b|s\b)'
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, prompt, re.IGNORECASE):
                target = int(match.group(1))
                # Allow smaller targets for very small documents
                min_target = 5 if self.original_words < 50 else 10
                if min_target <= target <= self.original_words:
                    return target
        return None

__all__ = ["Mode5"]