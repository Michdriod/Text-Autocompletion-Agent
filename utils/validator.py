# Text validation utilities for the text enrichment service.
# Provides functions for validating text input requirements.


import re

def count_words(text: str) -> int:
    words = re.findall(r'\b\w+\b', text.strip())
    return len(words)

def validate_minimum_word_count(text: str) -> bool:
    return count_words(text) >= 23