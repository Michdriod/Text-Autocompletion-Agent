import pytest

from services.baseline import count_words, compute_baseline_metrics
from services.preprocess import clean_text
from config import settings

RAW = """Page 1\nIntro section.\n\nPage 2\nThis is a simple test document with several words to ensure counting logic works correctly.\nAnother line follows here with extra   spacing.\n"""

def test_count_words_basic():
    cleaned = clean_text(RAW)
    wc = count_words(cleaned)
    assert wc > 10
    assert isinstance(wc, int)


def test_compute_baseline_metrics_defaults():
    cleaned = clean_text(RAW)
    metrics = compute_baseline_metrics(cleaned)
    assert metrics.total_words == count_words(cleaned)
    # Default final ratio guardrails apply (0.2 default in settings, within bounds)
    expected = settings.summary_target_words(metrics.total_words)
    assert metrics.final_target_words == expected
    assert metrics.per_chunk_ratio == settings.PER_CHUNK_SUMMARY_RATIO


def test_compute_baseline_metrics_override_ratio():
    cleaned = clean_text(RAW)
    metrics = compute_baseline_metrics(cleaned, final_ratio_override=0.3)
    expected = settings.summary_target_words(count_words(cleaned), ratio=0.3)
    assert metrics.final_target_words == expected
