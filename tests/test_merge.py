import pytest
from services.merge import merge_partial_summaries, MergedDraft
from services.models import PartialSummary


def _ps(idx: int, words: int) -> PartialSummary:
    # Build dummy partial summaries with simple text of given word length
    text = " ".join([f"w{idx}_{i}" for i in range(words)])
    return PartialSummary(
        chunk_id=f"c{idx}",
        index=idx,
        text=text,
        word_count=words,
        compression_ratio=words / (words * 5),  # fake ratio placeholder
    )


def test_merge_empty():
    draft = merge_partial_summaries([])
    assert draft.total_summary_words == 0
    assert draft.markdown == ""
    assert draft.partial_count == 0


def test_merge_ordering_and_headings():
    # Intentionally shuffled input
    parts = [_ps(2, 5), _ps(0, 10), _ps(1, 7)]
    draft = merge_partial_summaries(parts, original_words=500)
    # Must be ordered 0,1,2 by index
    assert draft.partial_count == 3
    assert draft.total_summary_words == 5 + 10 + 7
    # Check heading presence
    md = draft.markdown.splitlines()
    headings = [l for l in md if l.startswith('## Summary of Chunk')]
    assert len(headings) == 3
    assert headings[0].endswith('1')  # chunk index +1
    assert headings[1].endswith('2')
    assert headings[2].endswith('3')
    assert draft.combined_ratio == pytest.approx(draft.total_summary_words / 500.0, rel=1e-6)


def test_merge_with_comments():
    parts = [_ps(0, 3)]
    draft = merge_partial_summaries(parts, include_index_comment=True)
    assert '<!-- chunk_id:' in draft.markdown
