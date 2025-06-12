# Text validation utilities for the text enrichment service.
# Provides functions for validating text input requirements with dynamic parameters.

import re
from enum import Enum
from typing import Union, Dict, Optional

class ModeType(str, Enum):
    mode_1 = "mode_1"  # Context-Aware Regenerative Completion
    mode_2 = "mode_2"  # Structured Context Enrichment
    mode_3 = "mode_3"  # Input Refinement
    mode_4 = "mode_4"  # Description Agent

def count_words(text: str) -> int:
    """Count words in text using regex to match word boundaries."""
    if not text:
        return 0
    words = re.findall(r'\b\w+\b', text.strip())
    return len(words)

def count_characters(text: str) -> int:
    """Count characters in text, excluding leading/trailing whitespace."""
    if not text:
        return 0
    return len(text.strip())

def get_default_min_words(mode: ModeType) -> int:
    """Get default minimum word count for each mode."""
    defaults = {
        ModeType.mode_1: 20,
        ModeType.mode_2: 2,
        ModeType.mode_3: 0,
        ModeType.mode_4: 2  # Description Agent: 2 words min
    }
    return defaults.get(mode, 0)

def validate_minimum_word_count(text: str, mode: ModeType, min_words: Optional[int] = None) -> bool:
    """Validate that text meets minimum word count requirement."""
    if min_words is None:
        min_words = get_default_min_words(mode)
    
    # Mode 3 has no minimum word requirement
    if mode == ModeType.mode_3:
        return True
        
    return count_words(text) >= min_words

def validate_combined_word_count(text1: str, text2: str, mode: ModeType) -> bool:
    """Validate combined word count for modes that require multiple inputs."""
    if mode not in [ModeType.mode_2, ModeType.mode_4]:
        return True
    combined_words = count_words(text1) + count_words(text2)
    return combined_words >= get_default_min_words(mode)

def validate_output_length(text: str, max_length: Dict[str, Union[str, int]]) -> bool:
    """Validate that text meets maximum output length requirement."""
    if not max_length or not isinstance(max_length, dict):
        return True
    
    length_type = max_length.get("type")
    length_value = max_length.get("value")
    
    if not length_type or not length_value:
        return True
    
    if length_type == "characters":
        return count_characters(text) <= length_value
    elif length_type == "words":
        return count_words(text) <= length_value
    
    return True  # If type is invalid, don't enforce limit

def trim_output(text: str, max_length: Dict[str, Union[str, int]]) -> str:
    """Trim text to meet maximum output length requirement."""
    if not max_length or not isinstance(max_length, dict):
        return text
    
    length_type = max_length.get("type")
    length_value = max_length.get("value")
    
    if not length_type or not length_value:
        return text
    
    if length_type == "characters":
        if count_characters(text) > length_value:
            return text[:length_value].strip()
    elif length_type == "words":
        words = text.split()
        if len(words) > length_value:
            return " ".join(words[:length_value])
    
    return text

def calculate_max_tokens(max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> int:
    """Calculate appropriate max_tokens for API call based on output length requirements."""
    if not max_output_length:
        return 100  # Default min tokens
    
    length_type = max_output_length.get("type")
    length_value = max_output_length.get("value", 200)
    
    if length_type == "characters":
        # Rough estimate: 1 token ≈ 3-4 characters
        return max(100, min(int(length_value / 3) + 50, 300))  # Buffer, min 100, max 300
    elif length_type == "words":
        # Rough estimate: 1 token ≈ 0.75 words
        return max(100, min(int(length_value / 0.75) + 50, 300))  # Buffer, min 100, max 300
    
    return 100  # Default fallback (min)