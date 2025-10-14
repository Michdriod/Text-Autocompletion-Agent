"""Central hard-coded configuration for the document summarization pipeline (Mode 5 extension).

These constants are intentionally NOT driven by environment variables to keep deployment
simple. Adjust values here when tuning behavior. Do NOT hard-code secrets (API keys) in
this file—leave those in environment variables (.env) for security.
"""

# Chunking parameters
CHUNK_TARGET_WORDS: int = 1000      # Target words per chunk before summarization
CHUNK_MIN_WORDS: int = 750          # Minimum words to accept a chunk (unused yet – reserved)
CHUNK_OVERLAP_PCT: float = 0.12     # Fractional overlap between chunks (12%)

# Summarization compression ratios
PER_CHUNK_SUMMARY_RATIO: float = 0.20        # Each chunk compressed to ~20% of its original words
FINAL_SUMMARY_RATIO_DEFAULT: float = 0.20    # Final target ratio vs original full document

# File handling limits
MAX_FILE_MB: int = 10               # Reject files larger than this size (MB)
MAX_FINAL_WORDS: int = 2000         # Safety cap for final summary length

# Future tuning constants (placeholders for later stages)
FINAL_REFINEMENT_MAX_TOKENS: int = 3000      # Max tokens budget for final refinement pass (planner will clamp)
CHUNK_SUMMARY_MAX_TOKENS: int = 600          # Max tokens budget per chunk summarization call

# Validation thresholds
MIN_EXTRACTED_WORDS: int = 20       # Minimum viable document length
LOW_DENSITY_RECHECK_RATIO: float = 0.95  # If final summary < 95% of target, allow optional expansion
HIGH_DENSITY_RECOMPRESS_RATIO: float = 1.05  # If >105% of target, trigger compression pass

# MIME validation & PDF density heuristics
ALLOWED_MIME_TYPES = {
	"application/pdf",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	"text/plain",
}

# Reject PDFs that appear to be image-only (scanned) with too little extracted text.
# Threshold is minimum non-whitespace characters per page.
PDF_MIN_CHARS_PER_PAGE: int = 120


# Maximum length for user-provided prompts
MAX_PROMPT_LENGTH: int = 2000  # characters


def summary_target_words(original_words: int, ratio: float | None = None) -> int:
	"""Compute the word target for the final summary.

	Args:
		original_words: Total words in cleaned full document.
		ratio: Optional override ratio (defaults to FINAL_SUMMARY_RATIO_DEFAULT).

	Returns:
		Integer target word count (bounded by MAX_FINAL_WORDS)
	"""
	r = ratio if ratio is not None else FINAL_SUMMARY_RATIO_DEFAULT
	r = max(0.05, min(r, 0.5))  # guardrail: no less than 5%, no more than 50%
	target = int(original_words * r)
	if MAX_FINAL_WORDS:
		target = min(target, MAX_FINAL_WORDS)
	return max(MIN_EXTRACTED_WORDS, target)