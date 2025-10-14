"""Test script to verify truncation detection and handling."""

from utils.validator import is_summary_truncated, complete_truncated_summary, calculate_max_tokens

# Test 1: Complete summary (should NOT be truncated)
complete_summary = """
This is a complete summary that ends properly. It contains multiple sentences
and covers all the key points. The document discusses important topics and
provides valuable insights. All ideas are fully expressed and concluded.
"""

print("Test 1: Complete Summary")
print(f"Truncated: {is_summary_truncated(complete_summary)}")
print(f"Expected: False")
print()

# Test 2: Truncated summary (ends mid-sentence)
truncated_summary = """
This summary starts well and covers the main points. However, it suddenly ends
without completing the final thought and
"""

print("Test 2: Truncated Summary (mid-sentence)")
print(f"Truncated: {is_summary_truncated(truncated_summary)}")
print(f"Expected: True")
print()

# Test 3: Truncated summary (ends with conjunction)
truncated_conjunction = """
The document covers several important topics. It discusses the background and
context of the issue. The analysis shows clear trends but
"""

print("Test 3: Truncated Summary (ends with 'but')")
print(f"Truncated: {is_summary_truncated(truncated_conjunction)}")
print(f"Expected: True")
print()

# Test 4: Complete truncated summary
print("Test 4: Complete Truncated Summary")
completed = complete_truncated_summary(truncated_summary)
print(f"Original: {truncated_summary[:100]}...")
print(f"Completed: {completed}")
print(f"Is completed version truncated: {is_summary_truncated(completed)}")
print()

# Test 5: Token budget calculation
print("Test 5: Token Budget Calculation")
print(f"For 100 words: {calculate_max_tokens({'type': 'words', 'value': 100})} tokens")
print(f"For 500 words: {calculate_max_tokens({'type': 'words', 'value': 500})} tokens")
print(f"For 1000 words: {calculate_max_tokens({'type': 'words', 'value': 1000})} tokens")
print(f"For 2000 words: {calculate_max_tokens({'type': 'words', 'value': 2000})} tokens")
print(f"For 5000 words: {calculate_max_tokens({'type': 'words', 'value': 5000})} tokens")
print()

# Test 6: Large summary token calculation
print("Test 6: Large Summary Token Budget (Mode 5 scenario)")
target_words = 2000
multiplier = 2.5  # For large summaries
token_value = int(target_words * multiplier)
token_budget = calculate_max_tokens({'type': 'words', 'value': token_value})
print(f"Target words: {target_words}")
print(f"Multiplier: {multiplier}")
print(f"Token calculation input: {token_value} words")
print(f"Final token budget: {token_budget} tokens")
print(f"This allows for: ~{int(token_budget * 0.75)} words of actual output")
print()

print("✅ All tests completed!")
