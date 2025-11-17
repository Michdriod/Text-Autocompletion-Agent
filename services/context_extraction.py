"""Context extraction for KB Article Generation."""
import re
from typing import Optional
from config.settings import COMPLEXITY_MULTIPLIERS


def extract_context(description: str, keywords: Optional[list[str]] = None) -> dict:
    """Extract keywords, entities, and classify complexity."""
    desc_lower = description.lower()
    
    # User keywords + augmented
    all_keywords = list(keywords) if keywords else []
    
    # Extract entities
    entities = {
        'paths': re.findall(r'[/\\][\w/\\.-]+|[A-Z]:\\[\w\\.-]+', description),
        'versions': re.findall(r'v?\d+\.\d+(?:\.\d+)?', description),
        'error_codes': re.findall(r'[A-Z]{2,5}[-_]?\d{3,5}', description),
        'commands': re.findall(r'`[^`]+`', description),
    }
    
    # Classify complexity
    complexity, multiplier = classify_complexity(desc_lower)
    
    return {
        'keywords': all_keywords,
        'entities': entities,
        'entity_count': sum(len(v) for v in entities.values()),
        'complexity': complexity,
        'complexity_multiplier': multiplier
    }


def classify_complexity(desc_lower: str) -> tuple[str, float]:
    """Returns (category, multiplier) using config settings."""
    troubleshooting_kw = ['error', 'failure', 'crash', 'issue', 'problem', 'fix', 
                          'debug', 'troubleshoot', 'not working', 'broken', 'failed']
    if any(kw in desc_lower for kw in troubleshooting_kw):
        return ('troubleshooting', COMPLEXITY_MULTIPLIERS['troubleshooting'])
    
    procedural_kw = ['install', 'configure', 'setup', 'deploy', 'create', 'implement',
                     'build', 'integrate', 'migrate', 'upgrade', 'enable']
    if any(kw in desc_lower for kw in procedural_kw):
        return ('procedural', COMPLEXITY_MULTIPLIERS['procedural'])
    
    return ('simple', COMPLEXITY_MULTIPLIERS['simple'])
