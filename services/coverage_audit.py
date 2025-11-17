"""Coverage audit for KB article generation."""
from config.settings import COVERAGE_THRESHOLD


def check_keyword_coverage(article_text: str, keywords: list[str]) -> dict:
    """Calculate keyword coverage. Returns coverage score and missing keywords."""
    if not keywords:
        return {'coverage': 1.0, 'missing': [], 'passed': True}
    
    article_lower = article_text.lower()
    present = [kw for kw in keywords if kw.lower() in article_lower]
    missing = [kw for kw in keywords if kw.lower() not in article_lower]
    
    coverage = len(present) / len(keywords) if keywords else 1.0
    passed = coverage >= COVERAGE_THRESHOLD
    
    return {
        'coverage': coverage,
        'present': present,
        'missing': missing,
        'passed': passed
    }
