"""Central hard-coded configuration for the document summarization pipeline (Mode 5 extension).

These constants are intentionally NOT driven by environment variables to keep deployment
simple. Adjust values here when tuning behavior. Do NOT hard-code secrets (API keys) in
this file—leave those in environment variables (.env) for security.
"""

# Chunking parameters
CHUNK_TARGET_WORDS: int = 1000      # Target words per chunk before summarization
CHUNK_OVERLAP_PCT: float = 0.12     # Fractional overlap between chunks (12%)

# Summarization compression ratios (ADAPTIVE SYSTEM)
PER_CHUNK_SUMMARY_RATIO: float = 0.20        # Each chunk compressed to ~20% of its original words
# NOTE: FINAL_SUMMARY_RATIO is now ADAPTIVE based on document size:
# ≤50 words: 75%, 51-100: 55%, 101-200: 40%, 201-400: 30%, 401-800: 25%, 801+: 20%

# File handling limits
MAX_FILE_MB: int = 10               # Reject files larger than this size (MB)
MAX_FINAL_WORDS: int = 2000         # Safety cap for final summary length

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


# PostgreSQL adapter configuration (server-side credentials only)
# Template for read-only database connections. The {db} placeholder will be substituted
# with the client-provided database name. Example:
#   POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://readonly_user:password@db-host:5432/{db}"
# Set this in your environment or override here. Clients never send credentials.
POSTGRES_READONLY_DSN_TEMPLATE: str | None = "postgresql://postgres:michwaleh@localhost:5432/{db}"