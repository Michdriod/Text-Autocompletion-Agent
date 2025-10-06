import pytest
from services.refinement import plan_refinement, RefinementDecision

def test_ok_case():
    # Within 95% - 105%
    dec = plan_refinement(summary_words=100, target_words=100)
    assert dec.action == "ok"
    assert dec.ratio == pytest.approx(1.0, rel=1e-6)
    assert "acceptable" in dec.reason

def test_recompress_case():
    # Over 105%
    dec = plan_refinement(summary_words=111, target_words=100)
    assert dec.action == "recompress"
    assert dec.ratio > 1.05
    assert "too long" in dec.reason

def test_expand_case():
    # Under 95%
    dec = plan_refinement(summary_words=80, target_words=100)
    assert dec.action == "expand"
    assert dec.ratio < 0.95
    assert "too short" in dec.reason


def test_zero_target_raises():
    with pytest.raises(ValueError):
        plan_refinement(summary_words=10, target_words=0)
