import pytest
from services.chunking import plan_chunk_word_spans, chunk_document

DUMMY_TEXT = " ".join([f"word{i}" for i in range(0, 3250)])  # 3250 words


def test_plan_spans_basic():
    spans = plan_chunk_word_spans(1000, target_words=1000, overlap_pct=0.1)
    # Single span fits exactly
    assert spans == [(0, 1000)]


def test_multiple_spans_with_overlap():
    spans = plan_chunk_word_spans(2500, target_words=1000, overlap_pct=0.1)
    # Expect first two spans start at 0 and 900 (since overlap=100)
    assert spans[0] == (0, 1000)
    assert spans[1][0] == 900
    assert spans[1][1] == 1900
    # Last span should end at total_words
    assert spans[-1][1] == 2500


def test_tail_merge():
    # Create total such that the last remainder would be < 40% of target
    spans = plan_chunk_word_spans(2100, target_words=1000, overlap_pct=0.1)
    # Without merge we'd have spans: (0,1000),(900,1900),(1800,2100=300 remainder <400)
    # After merge expect only 2 spans
    assert len(spans) == 2
    assert spans[-1][1] == 2100


def test_chunk_document_models():
    chunks = chunk_document(DUMMY_TEXT, target_words=1000, overlap_pct=0.1)
    assert chunks
    # Ensure ordering and overlap logic appear
    assert chunks[0].word_count <= 1000
    if len(chunks) > 1:
        assert chunks[1].index == 1
        assert chunks[1].word_count <= 1000
        # Overlap check: intersection of first two spans should be close to 100 (tolerate boundary)
        first_words = set(chunks[0].text.split())
        second_words = set(chunks[1].text.split())
        overlap = len(first_words.intersection(second_words))
        assert overlap >= 60  # allow some variation due to remainder adjustments


def test_small_text_single_chunk():
    txt = "one two three four five"
    chunks = chunk_document(txt, target_words=1000)
    assert len(chunks) == 1
    assert chunks[0].word_count == 5
