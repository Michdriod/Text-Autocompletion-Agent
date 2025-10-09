from utils.generator import generate, generate_with_continuation
from utils.validator import calculate_max_tokens
from typing import Optional
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
    """Pipeline orchestrator for full document summarization (Mode 5), with explicit prompt construction for final LLM call."""

    FINAL_SYSTEM_PROMPT = (
        "You are a careful summarization and editing assistant. "
        "Your job is to refine, compress, and clarify a draft summary into a single, coherent, well-structured Markdown document. "
        "Preserve all key facts, entities, and causal relationships. Use clear sectioning, bullet lists, and concise language. "
        "Do not add a title unless one is clearly present."
        "Be as exhaustive and detailed as you are suppose to be, dont trim any output, intelligently end every summary well with conclusion."
    )

    FINAL_USER_PROMPT_TEMPLATE = (
        "Refine the following text into a coherent, well-structured Markdown summary of about {target_words} words (20% of the original). "
        "Do not exceed the target by more than 5%. If the text is already concise, focus on improving clarity and flow.\n\n"
        "If you reach the end of your allowed output, ensure your summary is complete and ends with a proper conclusion, even if you must be more concise.\n\n"
        "If you encounter tabular data, format it as a Markdown table using pipes (|) and dashes (-) so it renders correctly.\n\n"
        "---\n\n"
        "{draft}"
    )

    async def process_document_file(self, file_path: str) -> dict:
        import logging
        logger = logging.getLogger("mode5")
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.info("[Mode5] Step 1: Ingestion started.")
        raw_text, meta = extract_text(file_path)
        logger.info("[Mode5] Step 1: Ingestion complete.")

        logger.info("[Mode5] Step 2: Preprocessing started.")
        cleaned = clean_text(raw_text)
        logger.info("[Mode5] Step 2: Preprocessing complete.")

        logger.info("[Mode5] Step 3: Baseline metrics computation started.")
        baseline = compute_baseline_metrics(cleaned)
        logger.info(f"[Mode5] Step 3: Baseline metrics: {baseline}")

        logger.info("[Mode5] Step 4: Chunking started.")
        chunks = chunk_document(cleaned)
        # print(chunks)
        logger.info(f"[Mode5] Step 4: Chunking complete. Number of chunks: {len(chunks)}")
        if not chunks:
            logger.error("[Mode5] No valid chunks produced from document.")
            raise ValueError("No valid chunks produced from document.")

        logger.info("[Mode5] Step 5: Per-chunk summarization started.")
        partials = await summarize_chunks(chunks)
        # print(partials)
        logger.info("[Mode5] Step 5: Per-chunk summarization complete.")

        logger.info("[Mode5] Step 6: Merging partial summaries started.")
        merged = merge_partial_summaries(partials, original_words=baseline.total_words)
        logger.info("[Mode5] Step 6: Merging partial summaries complete.")

        logger.info("[Mode5] Step 7: Compression check/refinement plan started.")
        decision = plan_refinement(
            summary_words=merged.total_summary_words,
            target_words=baseline.final_target_words
        )
        logger.info(f"[Mode5] Step 7: Refinement plan: {decision}")

        logger.info("[Mode5] Step 8: Final synthesis/refinement started.")
        # Add an explicit end marker instruction so continuation logic can detect completion
        end_marker = "<END_OF_DOCUMENT>"
        system_prompt = self.FINAL_SYSTEM_PROMPT + f"\n\nWhen you have finished the document, append the exact marker on its own line: {end_marker}"
        user_prompt = self.FINAL_USER_PROMPT_TEMPLATE.format(
            target_words=baseline.final_target_words,
            draft=merged.markdown
        )
        if decision.action in {"ok", "recompress", "expand"}:
            final = await refine_summary(
                draft_markdown=merged.markdown,
                target_words=baseline.final_target_words,
                max_tokens=None,  # Let refine_summary plan tokens
                # system_prompt and user_message will be overridden below
            )
            logger.info("[Mode5] Step 8: Final LLM call (generate_with_continuation) started.")
            # Use continuation-capable generator to avoid trimmed outputs
            raw = await generate_with_continuation(
                system_prompt=system_prompt,
                user_message=user_prompt,
                max_tokens=calculate_max_tokens({"type": "words", "value": baseline.final_target_words}),
                temperature=0.2,
                top_p=0.95,
                end_marker=end_marker,
                max_iterations=6,
            )
            # Remove end marker if present
            new_text = raw.replace(end_marker, "").strip()
            logger.info(f"[Mode5] Step 8: Final LLM call complete. Raw length: {len(raw.split())} words; Final length: {len(new_text.split())} words.")
            summary_words = len(new_text.split())
            achieved_ratio = summary_words / float(baseline.final_target_words)
            final = final.model_copy(update={
                'text': new_text,
                'summary_words': summary_words,
                'achieved_ratio': achieved_ratio
            })
        else:
            logger.error(f"[Mode5] Unknown refinement action: {decision.action}")
            raise RuntimeError(f"Unknown refinement action: {decision.action}")

        logger.info("[Mode5] Step 9: Output formatting started.")
        result = format_output(final, baseline.total_words)
        print(result)
        logger.info("[Mode5] Step 9: Output formatting complete.")
        return result