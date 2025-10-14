# Text validation utilities for the text enrichment service.
# Provides functions for validating text input requirements with dynamic parameters.

import re
from enum import Enum
from typing import Union, Dict, Optional, Any

class ModeType(str, Enum):
    mode_1 = "mode_1"  # Context-Aware Regenerative Completion
    mode_2 = "mode_2"  # Structured Context Enrichment
    mode_3 = "mode_3"  # Input Refinement
    mode_4 = "mode_4"  # Description Agent
    mode_5 = "mode_5"  # Document Summarization
    mode_6 = "mode_6"  # Document Development


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
        ModeType.mode_1: 2,
        ModeType.mode_2: 2,
        ModeType.mode_3: 0,
        ModeType.mode_4: 2,  # Description Agent: 2 words min
        ModeType.mode_5: 20,
        ModeType.mode_6: 2
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

def validate_prompt_length(prompt: str | None, max_length: int) -> tuple[str | None, bool]:
    """
    Validate and optionallly truncates user promt.
    Returns: (cleaned_prompt, was_truncated)
    """
    if not prompt or not prompt.strip():
        return None, False
    
    cleaned = prompt.strip()
    if len(cleaned) > max_length:
        return cleaned[:max_length], True
    return cleaned, False

def validate_combined_word_count(text1: str, text2: str, mode: ModeType) -> bool:
    """Validate combined word count for modes that require multiple inputs."""
    if mode not in [ModeType.mode_2, ModeType.mode_4, ModeType.mode_6]:
        return True
    combined_words = count_words(text1) + count_words(text2)
    return combined_words >= get_default_min_words(mode)

def build_length_instruction(max_output_length: Optional[Dict[str, Union[str, int]]]) -> str:
    if not max_output_length:
        return ""
    lt = max_output_length.get("type", "words")
    lv =  max_output_length.get("value", 300)
    return (
        f"\n\nConstraint: Do not exceed {lv} {lt}. Allocate space intelligently; prioritize core meaning over minor detail. "
        "Finish with a complete final sentence; do not end mid-thought or mid-list."
    )

def calculate_max_tokens(max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> int:
    """
    Convert a (type,value) length constraint into a safe token budget.
    Guarantees a reasonable lower bound so the model can produce content.
    """
    if not max_output_length:
        return 300  # default general budget

    length_type = max_output_length.get("type", "words")
    length_value = int(max_output_length.get("value", 300) or 300)

    # Clamp absurd user values
    length_value = max(20, min(length_value, 20000))

    # if length_type == "characters":
    #     # ≈4 chars per token -> character target / 4, add 20% buffer
    #     est = int(max(1, length_value // 4) * 1.2)
    # else:  # words
    #     # ≈0.75 words per token -> words / 0.75, add 20% buffer
    #     est = int((length_value / 0.75) * 1.2)
        
    if length_type == "characters":
        # ≈4 chars per token -> character target / 4
        est = max(1, length_value // 4)
    else:  # words
        # ≈0.75 words per token -> words / 0.75
        est = int(length_value / 0.75)

    # Final safety bounds - increased upper limit for summarization
    return max(60, min(est, 8000))


def plan_output_length(mode: str, max_output_length: Optional[Dict[str, Union[str, int]]] = None, **kwargs) -> Dict[str, Any]:
    """
    Plan the output length for a given mode. If max_output_length is not provided,
    infer a reasonable default based on the mode and input context.
    """
    if max_output_length:
        token_budget = calculate_max_tokens(max_output_length)
        return {"constraint": max_output_length, "token_budget": token_budget}
    
    # Default planning logic per mode
    if mode == "mode_1":
        inferred_words = max(40, min(160, int(len(kwargs.get("text", "")) * 0.4)))
    elif mode == "mode_2":
        inferred_words = 110
    elif mode == "mode_3":
        inferred_words = max(30, min(300, len(kwargs.get("text", ""))))
    elif mode == "mode_4":
        inferred_words = 40
    elif mode == "mode_5":
        inferred_words = 120  # Default balanced style
    elif mode == "mode_6":
        inferred_words = max(400, min(1200, int(len(kwargs.get("body", "")) * 0.5)))
    else:
        inferred_words = 100
        
    # Ensure a minimum token budget
    token_budget = calculate_max_tokens({"type": "words", "value": inferred_words})
    return {"constraint": {"type": "words", "value": inferred_words}, "token_budget": token_budget}
    


# def plan_output_length(
#     mode: Union[str, ModeType],
#     user_max_length: Optional[Dict[str, Union[str, int]]],
#     **kwargs
# ) -> Dict[str, Union[int, Dict[str, Union[str, int]], str]]:
#     """Unified length planning across modes.

#     Returns a planning dictionary with:
#       - constraint: the (possibly synthetic) max_output_length dict used downstream
#       - token_budget: int safe token budget
#       - rationale: brief string explaining inference (diagnostic – not yet surfaced externally)

#     Heuristics (word-oriented unless user supplies characters):
#       mode_1 (completion): ~40% of input word count, bounded 40–160
#       mode_2 (enrichment): 110–180 depending on input size
#       mode_3 (refinement): ≈input length (bounded 30–300)
#       mode_4 (description): fixed 40 words default
#       mode_5 (summarization): style-based (brief 40, balanced 120, detailed 240)
#       mode_6 (document development): 50% of body length bounded 400–1200 (min body scaling fallback)

#     If user_max_length provided, it is honored exactly (converted to token budget) – no synthetic expansion.
#     """
#     # Normalize mode to string key
#     mode_key = mode.value if isinstance(mode, ModeType) else str(mode)

#     if user_max_length:
#         # Honor user specification directly
#         budget = calculate_max_tokens(user_max_length)
#         return {
#             "constraint": user_max_length,
#             "token_budget": budget,
#             "rationale": "user-specified"
#         }

    # # Helper to create constraint dict
    # def words_constraint(words: int) -> Dict[str, Union[str, int]]:
    #     return {"type": "words", "value": int(words)}

    # def clamp(v, lo, hi):
    #     return max(lo, min(hi, v))

    # constraint: Dict[str, Union[str, int]]
    # rationale = "inferred"

    # if mode_key == "mode_1":  # completion – proportion of input
    #     source = kwargs.get("text", "")
    #     wc = count_words(source)
    #     target = clamp(int(wc * 0.4), 40, 160)
    #     constraint = words_constraint(target)
    #     rationale += f" (≈40% of input {wc} words)"

    # elif mode_key == "mode_2":  # enrichment
    #     source = kwargs.get("text", "")
    #     wc = count_words(source)
    #     base = 110 if wc < 150 else 180
    #     constraint = words_constraint(base)
    #     rationale += f" (enrichment default; input {wc} words)"

    # elif mode_key == "mode_3":  # refinement – keep similar length
    #     source = kwargs.get("text", "")
    #     wc = count_words(source)
    #     target = clamp(wc, 30, 300)
    #     constraint = words_constraint(target)
    #     rationale += f" (match input length {wc} words)"

    # elif mode_key == "mode_4":  # description agent
    #     constraint = words_constraint(40)
    #     rationale += " (concise description)"

    # elif mode_key == "mode_5":  # summarization – style aware
    #     style = (kwargs.get("summary_style") or "balanced").lower()
    #     style_map = {"brief": 40, "balanced": 120, "detailed": 240}
    #     target = style_map.get(style, 120)
    #     constraint = words_constraint(target)
    #     rationale += f" (summary style={style})"

    # elif mode_key == "mode_6":  # document development
    #     body = kwargs.get("body", "") or ""
    #     wc = count_words(body)
    #     if wc == 0:
    #         target = 600  # fallback
    #         rationale += " (fallback default 600 words)"
    #     else:
    #         target = clamp(int(wc * 0.5), 400, 1200)
    #         rationale += f" (≈50% of body {wc} words)"
    #     constraint = words_constraint(target)

    # else:  # unknown -> general fallback
    #     constraint = words_constraint(300)
    #     rationale += " (generic fallback)"

    # token_budget = calculate_max_tokens(constraint)
    # return {
    #     "constraint": constraint,
    #     "token_budget": token_budget,
    #     "rationale": rationale
    # }


# def calculate_max_tokens(max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> int:
#     if not max_output_length:
#         return 300
#     length_type = max_output_length.get("type", "words")
#     length_value = int(max_output_length.get("value", 300) or 300)
#     length_value = max(10, min(length_value, 8000))
#     if length_type == "characters":
#         est = length_value // 4      # ≈4 chars per token
#     else:  # words
#         est = int(length_value / 0.75)  # ≈0.75 words per token
#     return max(50, min(est, 4000))




# def calculate_max_tokens(max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> int:
#     """Calculate appropriate max_tokens for API call based on output length requirements."""
#     if not max_output_length:
#         return 100  # Default min tokens
    
#     length_type = max_output_length.get("type")
#     length_value = max_output_length.get("value", 200)
    
#     if length_type == "characters":
#         # Rough estimate: 1 token ≈ 3-4 characters
#         return max(100, min(int(length_value / 3) + 50, 300))  # Buffer, min 100, max 300
#     elif length_type == "words":
#         # Rough estimate: 1 token ≈ 0.75 words
#         return max(100, min(int(length_value / 0.75) + 50, 300))  # Buffer, min 100, max 300
    
#     return 100  # Default fallback (min)