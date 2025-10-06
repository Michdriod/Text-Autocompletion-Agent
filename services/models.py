from typing import Optional
from pydantic import BaseModel, Field, field_validator

__all__ = [
    "DocumentMeta",
    "Chunk",
    "PartialSummary",
    "FinalSummary",
    "make_chunk",
]


class DocumentMeta(BaseModel):
    source_name: str = Field(..., description="Original filename or identifier")
    size_bytes: int = Field(..., ge=0)
    page_count: Optional[int] = Field(None, ge=1, description="Page count for paginated formats")
    content_hash: str = Field(..., min_length=32, max_length=64)
    original_words: int = Field(..., gt=0)

    model_config = {
        "frozen": True,  # make immutable to avoid accidental mutation
    }

    @field_validator("source_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class Chunk(BaseModel):
    id: str
    index: int = Field(..., ge=0)
    text: str
    word_count: int = Field(..., gt=0)
    token_estimate: int = Field(..., gt=0)

    model_config = {"frozen": True}

    @field_validator("text")
    @classmethod
    def non_empty_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Chunk text cannot be empty")
        return v


class PartialSummary(BaseModel):
    chunk_id: str
    index: int = Field(..., ge=0)
    text: str
    word_count: int = Field(..., gt=0)
    compression_ratio: float = Field(..., gt=0.0)

    model_config = {"frozen": True}


class FinalSummary(BaseModel):
    text: str
    summary_words: int = Field(..., gt=0)
    original_words: int = Field(..., gt=0)
    compression_ratio: float = Field(..., gt=0.0)
    chunks_used: int = Field(..., ge=1)
    passes: int = Field(..., ge=1)

    model_config = {"frozen": True}

    @field_validator("text")
    @classmethod
    def ensure_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Final summary text cannot be empty")
        return v


# --- Factory Helpers -----------------------------------------------------

def _estimate_tokens_from_words(word_count: int) -> int:
    """Rough token estimation.

    Heuristic: tokens ≈ words / 0.75 (i.e., tokens > words). We clamp to at least 1.
    """
    return max(1, int(word_count / 0.75))


def make_chunk(chunk_id: str, index: int, text: str) -> Chunk:
    """Create a Chunk model with derived word_count and token_estimate.

    Args:
        chunk_id: Stable identifier (e.g., uuid or hash segment)
        index: Sequential position in the document
        text: Raw chunk text

    Returns:
        Chunk instance (immutable Pydantic model)
    """
    stripped = text.strip()
    words = stripped.split()
    wc = len(words)
    token_estimate = _estimate_tokens_from_words(wc)
    return Chunk(id=chunk_id, index=index, text=stripped, word_count=wc, token_estimate=token_estimate)
