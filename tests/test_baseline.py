import pytest

from services.baseline import count_words, compute_baseline_metrics
from services.preprocess import clean_text

RAW = """Page 1\nIntro section.\n\nPage 2\nThis is a simple test document with several words to ensure counting logic works correctly.\nAnother line follows here with extra   spacing.\n"""

def test_count_words_basic():
    cleaned = clean_text(RAW)
    wc = count_words(cleaned)
    assert wc > 10
    assert isinstance(wc, int)


def test_compute_baseline_metrics_requires_target():
    cleaned = clean_text(RAW)
    with pytest.raises(ValueError):
        compute_baseline_metrics(cleaned)


def test_compute_baseline_metrics_with_explicit_target():
    cleaned = clean_text(RAW)
    metrics = compute_baseline_metrics(cleaned, final_target_override=120)
    assert metrics.final_target_words == 120
    assert metrics.total_words == count_words(cleaned)
