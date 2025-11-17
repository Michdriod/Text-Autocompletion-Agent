"""Article length planning and section allocation."""
import math
from config.settings import (
    LENGTH_RANGES, SECTIONS_BY_LENGTH,
    SECTION_WEIGHTS, SECTION_MIN_FLOORS,
    COMPLEXITY_MULTIPLIERS
)


def plan_article_length(length_choice: str, context: dict) -> dict:
    """
    Plan article based on user's length choice.
    Returns target words, sections, and per-section allocation.
    """
    # Get target range from user choice
    if length_choice not in LENGTH_RANGES:
        length_choice = 'medium'  # Default fallback
    
    min_words, max_words = LENGTH_RANGES[length_choice]
    
    # Apply complexity multiplier for fine-tuning
    U = context.get('complexity_multiplier', 1.0)
    target_base = (min_words + max_words) // 2  # Midpoint of range
    T = round(target_base * U)
    
    # Ensure within range bounds
    T = max(min_words, min(T, max_words))
    
    # Get sections for this length
    sections = SECTIONS_BY_LENGTH.get(length_choice, ['purpose', 'steps', 'validation'])
    
    # Check if floors alone exceed target
    floor_sum = sum(SECTION_MIN_FLOORS.get(s, 50) for s in sections)
    if floor_sum > T:
        T = floor_sum  # Adjust target to meet minimum requirements
    
    # Allocate words per section
    allocation = {}
    for section in sections:
        weight = SECTION_WEIGHTS.get(section, 0.10)
        floor = SECTION_MIN_FLOORS.get(section, 50)
        allocation[section] = max(floor, round(T * weight))
    
    # Residual correction to match exact total
    current_sum = sum(allocation.values())
    diff = T - current_sum
    
    # Distribute difference (priority: steps > validation > purpose > others)
    priority = ['steps', 'validation', 'purpose', 'troubleshooting', 'notes', 
                'symptoms', 'prerequisites', 'best_practices', 'faq']
    idx = 0
    while diff != 0 and idx < len(priority) * abs(diff):
        section = priority[idx % len(priority)]
        if section in allocation:
            if diff > 0:
                allocation[section] += 1
                diff -= 1
            elif diff < 0 and allocation[section] > SECTION_MIN_FLOORS.get(section, 50):
                allocation[section] -= 1
                diff += 1
        idx += 1
    
    return {
        'total_target_words': T,
        'length_choice': length_choice,
        'word_range': (min_words, max_words),
        'sections': sections,
        'allocation': allocation,
        'complexity': context.get('complexity', 'procedural')
    }
