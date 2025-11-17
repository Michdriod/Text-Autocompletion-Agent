"""Tests for KB Article Generation (Mode 6)."""
import pytest
from services.input_validation import validate_kb_inputs, calculate_vague_score
from services.context_extraction import extract_context, classify_complexity
from services.article_planner import plan_article_length
from services.coverage_audit import check_keyword_coverage


def test_validation_rejects_short_title():
    """Should reject titles < 5 chars."""
    with pytest.raises(ValueError, match="at least 5 characters"):
        validate_kb_inputs("Test", "This is a valid description with enough words to pass validation.")


def test_validation_rejects_short_description():
    """Should reject descriptions < MIN_DESCRIPTION_WORDS."""
    with pytest.raises(ValueError, match="too short"):
        validate_kb_inputs("Valid Title", "Too short desc")


def test_validation_rejects_vague_description():
    """Should reject vague descriptions."""
    vague_text = "Please fix the problem with the thing that is not working properly."
    with pytest.raises(ValueError, match="too generic"):
        validate_kb_inputs("Fix Issue", vague_text)


def test_validation_accepts_good_inputs():
    """Should accept valid inputs."""
    title = "Configure SSL on Apache"
    desc = "Install SSL certificate on Apache 2.4 server running Ubuntu 20.04. Use Let's Encrypt certbot for automatic renewal."
    validate_kb_inputs(title, desc, ["SSL", "Apache"])  # Should not raise


def test_vague_score_calculation():
    """Vague score should be higher for generic text."""
    vague = "Please fix the issue with the system."
    specific = "Install SSL certificate v2.1 on Apache server using certbot command at /etc/apache2/sites-enabled/"
    
    score_vague = calculate_vague_score(vague)
    score_specific = calculate_vague_score(specific)
    
    assert score_vague > score_specific
    assert score_specific < 0.6


def test_complexity_classification():
    """Should classify complexity correctly."""
    troubleshooting = "Fix error 500 when server crashes during deployment"
    procedural = "Install and configure PostgreSQL database on Ubuntu server"
    simple = "Overview of cloud storage benefits for small businesses"
    
    assert classify_complexity(troubleshooting) == ('troubleshooting', 1.3)
    assert classify_complexity(procedural) == ('procedural', 1.1)
    assert classify_complexity(simple) == ('simple', 0.9)


def test_context_extraction():
    """Should extract keywords and entities."""
    desc = "Install SSL v2.1 certificate at /etc/ssl/certs/ to fix ERR-500 error"
    context = extract_context(desc, ["SSL", "Apache"])
    
    assert "SSL" in context['keywords']
    assert "Apache" in context['keywords']
    assert len(context['entities']['versions']) > 0
    assert len(context['entities']['paths']) > 0
    assert len(context['entities']['error_codes']) > 0
    assert context['complexity'] == 'troubleshooting'


def test_length_planning():
    """Should calculate reasonable article length."""
    desc = "Install SSL certificate on Apache server using certbot"
    context = {
        'complexity_multiplier': 1.1,
        'complexity': 'procedural',
        'entity_count': 3,
        'keywords': ['SSL', 'Apache']
    }
    
    plan = plan_article_length(len(desc.split()), context)
    
    assert 450 <= plan['total_target_words'] <= 2800
    assert 'purpose' in plan['sections']
    assert 'steps' in plan['sections']
    assert 'validation' in plan['sections']
    assert sum(plan['allocation'].values()) == plan['total_target_words']


def test_length_planning_includes_symptoms_for_troubleshooting():
    """Troubleshooting articles should include symptoms section."""
    context = {
        'complexity_multiplier': 1.3,
        'complexity': 'troubleshooting',
        'entity_count': 5,
        'keywords': ['error', 'fix']
    }
    
    plan = plan_article_length(100, context)
    
    assert 'symptoms' in plan['sections']


def test_section_allocation_respects_floors():
    """Section allocation should respect minimum floors."""
    context = {
        'complexity_multiplier': 0.9,
        'complexity': 'simple',
        'entity_count': 1,
        'keywords': []
    }
    
    plan = plan_article_length(50, context)
    
    # Check that steps section has at least its floor
    assert plan['allocation']['steps'] >= 300


def test_coverage_audit():
    """Should check keyword coverage correctly."""
    article = "This article covers SSL certificates, Apache configuration, and certbot installation."
    keywords = ["SSL", "Apache", "certbot"]
    
    result = check_keyword_coverage(article, keywords)
    
    assert result['coverage'] == 1.0
    assert result['passed'] is True
    assert len(result['missing']) == 0


def test_coverage_audit_fails_below_threshold():
    """Should fail when coverage is too low."""
    article = "This article covers SSL certificates."
    keywords = ["SSL", "Apache", "certbot", "Ubuntu", "firewall"]
    
    result = check_keyword_coverage(article, keywords)
    
    assert result['coverage'] < 0.75
    assert result['passed'] is False
    assert len(result['missing']) > 0


def test_coverage_audit_with_no_keywords():
    """Should pass when no keywords provided."""
    result = check_keyword_coverage("Any text", [])
    
    assert result['coverage'] == 1.0
    assert result['passed'] is True
