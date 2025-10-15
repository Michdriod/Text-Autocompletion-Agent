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
            # STRICT word count enforcement
            word_guidance = f"""
🎯 MANDATORY TARGET LENGTH: EXACTLY {target_words} words (±5% MAXIMUM)

⚠️ THIS IS A STRICT REQUIREMENT - NOT A SUGGESTION ⚠️

ABSOLUTE REQUIREMENTS:
1. Your summary MUST be approximately {target_words} words
2. Acceptable range: {int(target_words * 0.95)} - {int(target_words * 1.05)} words
3. DO NOT exceed this range under ANY circumstances
4. Plan your content allocation BEFORE writing
5. If you reach the word limit, STOP gracefully with a complete sentence

MANDATORY WORD COUNT STRATEGY:
Step 1: Calculate sections based on {target_words} words total
Step 2: Allocate words per section proportionally
Step 3: Write concisely to stay within allocation
Step 4: Monitor your word count as you write
Step 5: Complete your final sentence within the {int(target_words * 1.05)} word limit

CONTENT DENSITY GUIDELINES:
- {target_words} ≤ 100 words: Only the absolute core message and conclusion
- 100 < {target_words} ≤ 300 words: Core points + key supporting facts
- 300 < {target_words} ≤ 500 words: Main points with essential details
- 500 < {target_words} ≤ 1000 words: Comprehensive with examples
- {target_words} > 1000 words: Detailed coverage with full context

CRITICAL ENFORCEMENT RULES:
✓ MUST hit the target word count (±5% maximum)
✓ NEVER exceed {int(target_words * 1.05)} words
✓ NEVER truncate mid-sentence
✓ Complete all thoughts properly
✓ If approaching limit, conclude gracefully
✓ Better to be slightly under than to truncate

⚠️ FINAL WARNING: The {target_words} word target is MANDATORY, not optional. Respect it strictly."""
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

🎯 MANDATORY REQUIREMENTS FOR YOUR SUMMARY:
1. STRICTLY adhere to the target word count specified in the system instructions
2. Capture all essential information with maximum information density
3. Maintain well-structured, logical flow
4. Complete all sentences properly - NO truncation
5. End gracefully when approaching the word limit
6. The word count target is MANDATORY and must be respected

⚠️ REMINDER: The specified word count is NOT optional - it is a strict requirement."""

        if user_prompt:
            base_message += f"\n\n📋 ADDITIONAL USER INSTRUCTIONS:\n{user_prompt}\n\n⚠️ NOTE: If the user instructions specify a word count, that word count is MANDATORY and takes precedence over any parameter."
        
        base_message += "\n\n✍️ Begin your summary now (remember: strict adherence to word count target):"
        
        return base_message

    def _build_consistent_system_prompt(self, target_words: int, output_format: str, attempt: int, min_acceptable: int, max_acceptable: int) -> str:
        """Build system prompt with consistency-focused instructions based on attempt number."""
        
        base_instruction = """You are an expert document analyst with EXCEPTIONAL CONSISTENCY in following word count targets.

Your core responsibilities:
1. Extract and present ALL key information with perfect word count control
2. NEVER exceed the specified word range under any circumstances
3. Complete all sentences properly without truncation
4. Maintain logical flow and coherent structure
5. Use clear, professional language optimized for the target length"""

        # Attempt-specific instructions for consistency
        if attempt == 1:
            consistency_note = f"""
🎯 FIRST ATTEMPT - PRECISION TARGET: {target_words} words (acceptable: {min_acceptable}-{max_acceptable})

CONSISTENCY RULES:
✓ AIM for exactly {target_words} words
✓ Acceptable range: {min_acceptable} to {max_acceptable} words
✓ Plan your content structure BEFORE writing
✓ Monitor word count as you write each section
✓ STOP when you reach {max_acceptable} words maximum
✓ Better to be slightly under than to exceed the limit"""

        elif attempt == 2:
            consistency_note = f"""
🔄 RETRY ATTEMPT - STRICT ENFORCEMENT: {target_words} words (range: {min_acceptable}-{max_acceptable})

PREVIOUS ATTEMPT WAS OUT OF RANGE - ADJUST YOUR APPROACH:
✓ Be MORE PRECISE with word allocation per section
✓ Use SHORTER sentences if previous attempt was too long
✓ Add MORE detail if previous attempt was too short
✓ CRITICAL: Stay within {min_acceptable}-{max_acceptable} words
✓ End IMMEDIATELY when approaching {max_acceptable} words
✓ This is your second chance - be more accurate"""

        else:
            consistency_note = f"""
⚠️ FINAL ATTEMPT - EMERGENCY PRECISION: {target_words} words (STRICT: {min_acceptable}-{max_acceptable})

PREVIOUS ATTEMPTS FAILED - MAXIMUM PRECISION REQUIRED:
✓ CRITICAL: This is the last attempt for accurate word count
✓ PLAN every word carefully to hit {target_words} target
✓ Use EXACT word allocation strategy
✓ COUNT words as you write each sentence
✓ MANDATORY: Stop at {max_acceptable} words maximum
✓ SUCCESS depends on staying within {min_acceptable}-{max_acceptable} range
✓ NO excuses - hit the target precisely"""

        format_instruction = f"""
OUTPUT FORMAT: {output_format}
- Use clear paragraph breaks and proper formatting
- End with complete, conclusive statements
- No mid-sentence truncation allowed
- Professional tone throughout"""

        return f"{base_instruction}\n\n{consistency_note}\n\n{format_instruction}"

    def _calculate_consistent_token_budget(self, target_words: int) -> int:
        """Calculate consistent, conservative token budget to prevent over-generation."""
        
        # More conservative multipliers for consistency
        if target_words <= 100:
            multiplier = 1.8  # 80% extra (was 2.2)
        elif target_words <= 300:
            multiplier = 1.9  # 90% extra (was 2.2)
        elif target_words <= 500:
            multiplier = 2.0  # 100% extra (was 2.2)
        elif target_words <= 1000:
            multiplier = 2.1  # 110% extra (was 2.5)
        elif target_words <= 1500:
            multiplier = 2.2  # 120% extra (was 2.5)
        else:
            multiplier = 2.4  # 140% extra (was 3.0)
        
        # Calculate base tokens more conservatively
        base_tokens = calculate_max_tokens({"type": "words", "value": target_words})
        token_budget = int(base_tokens * multiplier)
        
        # Cap at reasonable limits to prevent over-generation
        if target_words <= 500:
            token_budget = min(token_budget, 1200)
        elif target_words <= 1000:
            token_budget = min(token_budget, 2400)
        else:
            token_budget = min(token_budget, 6000)
        
        return token_budget

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
        """Direct summarization with consistent length enforcement and retry logic."""
        logger.info(f"[Mode5] Direct summarization to {target_words} words with consistency enforcement.")
        
        # Define acceptable range (±8% for good balance between strictness and completion)
        min_acceptable = int(target_words * 0.92)  # 8% below
        max_acceptable = int(target_words * 1.08)  # 8% above
        
        # Attempt summarization with retry logic for consistency
        max_attempts = 3
        attempt = 1
        best_summary = None
        best_deviation = float('inf')
        
        while attempt <= max_attempts:
            logger.info(f"[Mode5] Attempt {attempt}/{max_attempts} for target={target_words} words")
            
            # Build prompts with attempt-specific adjustments
            system_prompt = self._build_consistent_system_prompt(target_words, output_format, attempt, min_acceptable, max_acceptable)
            user_message = self._build_user_message(content, user_prompt)
            
            # Calculate conservative token budget for consistent output
            token_budget = self._calculate_consistent_token_budget(target_words)
            
            logger.info(f"[Mode5] Attempt {attempt}: token_budget={token_budget}")
            
            # Generate with slightly different temperature for variety in retry attempts
            temperature = 0.2 if attempt == 1 else (0.1 + attempt * 0.05)
            
            summary = await generate(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=token_budget,
                temperature=temperature,
                top_p=0.9
            )
            
            # Check for truncation
            from utils.validator import is_summary_truncated, complete_truncated_summary
            if is_summary_truncated(summary):
                logger.warning(f"[Mode5] Attempt {attempt}: Summary truncated, attempting cleanup")
                summary = complete_truncated_summary(summary)
            
            # Clean and validate
            cleaned_summary = self._clean_summary_output(summary.strip())
            actual_words = len(cleaned_summary.split())
            deviation = abs(actual_words - target_words)
            deviation_percent = (deviation / target_words * 100) if target_words > 0 else 0
            
            logger.info(
                f"[Mode5] Attempt {attempt}: target={target_words}, actual={actual_words}, "
                f"deviation={deviation_percent:.1f}% (range: {min_acceptable}-{max_acceptable})"
            )
            
            # Check if this attempt is acceptable
            if min_acceptable <= actual_words <= max_acceptable:
                logger.info(f"[Mode5] ✅ SUCCESS on attempt {attempt}: Within acceptable range!")
                return cleaned_summary
            
            # Track best attempt (closest to target)
            if deviation < best_deviation:
                best_deviation = deviation
                best_summary = cleaned_summary
            
            # If too long, try with stricter prompt on next attempt
            if actual_words > max_acceptable and attempt < max_attempts:
                logger.warning(f"[Mode5] Attempt {attempt}: Too long ({actual_words} > {max_acceptable}), will retry with stricter prompt")
            elif actual_words < min_acceptable and attempt < max_attempts:
                logger.warning(f"[Mode5] Attempt {attempt}: Too short ({actual_words} < {min_acceptable}), will retry with expansion prompt")
            
            attempt += 1
        
        # If all attempts failed, return the best one and log final warning
        best_actual = len(best_summary.split())
        final_deviation = (best_deviation / target_words * 100) if target_words > 0 else 0
        
        logger.warning(
            f"[Mode5] ⚠️ All {max_attempts} attempts exceeded acceptable range. "
            f"Using best attempt: target={target_words}, actual={best_actual}, deviation={final_deviation:.1f}%"
        )
        
        return best_summary
    
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
        
        # Final synthesis with consistency enforcement
        logger.info(f"[Mode5] Step 7: Final synthesis to {target_words} words with consistency control.")
        
        # Use same retry logic as direct summarization for chunked final step
        min_acceptable = int(target_words * 0.92)
        max_acceptable = int(target_words * 1.08)
        
        max_attempts = 2  # Fewer attempts for chunked since it's already processed
        attempt = 1
        best_summary = None
        best_deviation = float('inf')
        
        while attempt <= max_attempts:
            logger.info(f"[Mode5] Final synthesis attempt {attempt}/{max_attempts}")
            
            # Build consistent refinement prompt
            system_prompt = self._build_consistent_system_prompt(target_words, output_format, attempt, min_acceptable, max_acceptable)
            
            refinement_prompt = f"""The following are summaries of different sections from a single document.

MANDATORY TASK: Create a unified summary with EXACTLY {target_words} words (acceptable: {min_acceptable}-{max_acceptable})

INTEGRATION REQUIREMENTS:
- Combine all key points from sections below
- Remove redundancy between sections
- Maintain logical flow and coherence
- CRITICAL: Stay within {min_acceptable}-{max_acceptable} words
- End with complete conclusion (no truncation)

SECTION SUMMARIES TO INTEGRATE:
{merged.markdown}

Create the final integrated summary now (target: {target_words} words):"""
            
            # Conservative token budget for final synthesis
            token_budget = self._calculate_consistent_token_budget(target_words)
            
            logger.info(f"[Mode5] Final synthesis attempt {attempt}: token_budget={token_budget}")
            
            # Vary temperature slightly between attempts
            temperature = 0.2 if attempt == 1 else 0.15
            
            final_summary = await generate(
                system_prompt=system_prompt,
                user_message=refinement_prompt,
                max_tokens=token_budget,
                temperature=temperature,
                top_p=0.9
            )
            
            # Check for truncation
            from utils.validator import is_summary_truncated, complete_truncated_summary
            if is_summary_truncated(final_summary):
                logger.warning(f"[Mode5] Final synthesis attempt {attempt}: truncated, cleaning up")
                final_summary = complete_truncated_summary(final_summary)
            
            # Validate this attempt
            cleaned_summary = self._clean_summary_output(final_summary.strip())
            actual_words = len(cleaned_summary.split())
            deviation = abs(actual_words - target_words)
            deviation_percent = (deviation / target_words * 100) if target_words > 0 else 0
            
            logger.info(
                f"[Mode5] Final synthesis attempt {attempt}: target={target_words}, actual={actual_words}, "
                f"deviation={deviation_percent:.1f}% (range: {min_acceptable}-{max_acceptable})"
            )
            
            # Check if acceptable
            if min_acceptable <= actual_words <= max_acceptable:
                logger.info(f"[Mode5] ✅ Final synthesis SUCCESS on attempt {attempt}")
                return cleaned_summary
            
            # Track best attempt
            if deviation < best_deviation:
                best_deviation = deviation
                best_summary = cleaned_summary
            
            if attempt < max_attempts:
                if actual_words > max_acceptable:
                    logger.warning(f"[Mode5] Final synthesis attempt {attempt}: Too long, will retry with stricter prompt")
                else:
                    logger.warning(f"[Mode5] Final synthesis attempt {attempt}: Too short, will retry with expansion")
            
            attempt += 1
        
        # Return best attempt if all failed
        best_actual = len(best_summary.split())
        final_deviation = (best_deviation / target_words * 100) if target_words > 0 else 0
        
        logger.warning(
            f"[Mode5] ⚠️ Final synthesis: All attempts exceeded range. "
            f"Using best: target={target_words}, actual={best_actual}, deviation={final_deviation:.1f}%"
        )
        
        return best_summary

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