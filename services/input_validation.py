"""Input validation for KB Article Generation (Mode 6)."""
import re
from typing import Optional
from config.settings import MIN_DESCRIPTION_WORDS, VAGUE_SCORE_THRESHOLD, LENGTH_RANGES


def validate_kb_inputs(
    title: str, 
    description: str, 
    length: str = 'medium',
    keywords: Optional[list[str]] = None
) -> dict:
    """
    Validate KB article generation inputs.
    Returns dict with 'valid' (bool) and optional 'suggestions' (list) if invalid.
    """
    issues = []
    suggestions = []
    
    # Title validation
    if not title or len(title.strip()) < 5:
        issues.append("Title too short")
        suggestions.append("Provide a descriptive title (at least 5 characters)")
    
    # Length validation
    if length not in LENGTH_RANGES:
        issues.append(f"Invalid length choice: {length}")
        suggestions.append(f"Choose from: {', '.join(LENGTH_RANGES.keys())}")
    
    # Description validation
    desc_words = len(description.split())
    if desc_words < MIN_DESCRIPTION_WORDS:
        issues.append(f"Description too short ({desc_words} words)")
        suggestions.extend([
            f"Provide at least {MIN_DESCRIPTION_WORDS} words with specific details",
            "Include: system/product names, versions, error messages",
            "Add: environment details (OS, platform, configuration)",
            "Describe: specific symptoms, steps, or expected behavior"
        ])
    
    # Vagueness check
    vague_score = calculate_vague_score(description)
    if vague_score >= VAGUE_SCORE_THRESHOLD:
        issues.append(f"Description too generic (vagueness: {vague_score:.2f})")
        suggestions.extend([
            "Be more specific about the technical context",
            "Add system/product name and version (e.g., 'Apache 2.4.50')",
            "Include specific error codes or messages",
            "Specify the environment (e.g., 'Ubuntu 22.04', 'Windows Server 2019')",
            "Describe concrete steps or actions taken",
            "Clarify expected vs actual behavior"
        ])
    
    if issues:
        return {
            'valid': False,
            'issues': issues,
            'suggestions': suggestions,
            'vague_score': vague_score
        }
    
    return {'valid': True}


def calculate_vague_score(text: str) -> float:
    """Calculate vagueness score (0-1). Higher = more vague."""
    if not text:
        return 1.0
    
    words = text.lower().split()
    if not words:
        return 1.0
    
    wc = len(words)
    
    # Stopwords ratio
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                 'it', 'this', 'that', 'these', 'those', 'i', 'you', 'we', 'they'}
    stopword_count = sum(1 for w in words if w in stopwords)
    stopword_ratio = stopword_count / wc
    
    # Domain term density (technical/specific words)
    domain_patterns = [
        r'\b[A-Z]{2,}\b',  # Acronyms (API, CPU, RAM)
        r'\bv?\d+\.\d+',    # Versions (v2.1, 3.0)
        r'\b\w+\.\w+\b',    # Dotted terms (config.json, api.endpoint)
        r'\b[A-Z][a-z]+[A-Z]\w*\b',  # CamelCase (JavaScript, PowerShell)
    ]
    domain_matches = sum(len(re.findall(p, text)) for p in domain_patterns)
    domain_density = min(1.0, domain_matches / max(1, wc / 10))
    
    # Repetition ratio (top 5 word frequency)
    from collections import Counter
    word_freq = Counter(words)
    top5_count = sum(count for _, count in word_freq.most_common(5))
    repetition_ratio = top5_count / wc if wc > 0 else 0
    
    # Token entropy (simplified)
    unique_ratio = len(set(words)) / wc
    entropy_norm = min(1.0, unique_ratio * 1.5)  # Higher unique = lower vagueness
    
    # Composite score
    score = (
        0.25 * (1 - min(wc / 200, 1)) +  # Penalize very short
        0.25 * stopword_ratio +           # Penalize high stopwords
        0.20 * (1 - domain_density) +     # Penalize low domain terms
        0.15 * min(repetition_ratio * 2, 1) +  # Penalize repetition
        0.15 * (1 - entropy_norm)         # Penalize low diversity
    )
    
    return min(1.0, max(0.0, score))
