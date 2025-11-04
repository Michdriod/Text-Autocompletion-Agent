#!/usr/bin/env python3

"""Proposed implementation: Adaptive fallback when target_words > total_words"""

def proposed_target_logic(target_words, total_words):
    """Show the proposed improved logic."""
    
    print("🔄 Proposed Logic Change")
    print("=" * 50)
    
    if target_words is not None and target_words > 0:
        if target_words > total_words:
            # OLD LOGIC (current):
            # effective_target = total_words  # Caps at original
            # target_mode = "user_absolute_capped"
            
            # NEW LOGIC (your suggestion):
            # Fall back to adaptive compression instead of capping
            compression_ratio, scenario = get_adaptive_compression_ratio(total_words)
            effective_target = max(1, round(total_words * compression_ratio))
            target_mode = f"adaptive_fallback_{scenario}"
            
            print(f"📄 Document: {total_words} words")
            print(f"🎯 User Request: {target_words} words (impossible)")
            print(f"🧠 Adaptive Decision: {scenario} → {int(compression_ratio*100)}% compression")
            print(f"✅ Smart Result: {effective_target} words")
            print(f"🏷️  Mode: {target_mode}")
            
            return effective_target, target_mode
        else:
            # Normal case - target is achievable
            effective_target = target_words
            target_mode = "user_absolute"
            return effective_target, target_mode
    else:
        # No target provided - use adaptive
        compression_ratio, scenario = get_adaptive_compression_ratio(total_words)
        effective_target = max(1, round(total_words * compression_ratio))
        target_mode = f"adaptive_{scenario}"
        return effective_target, target_mode

def get_adaptive_compression_ratio(total_words):
    """Extract adaptive compression logic for testing."""
    if total_words <= 50:
        return 0.75, "micro_document"
    elif total_words <= 100:
        return 0.55, "very_short_document"
    elif total_words <= 200:
        return 0.40, "short_document"
    elif total_words <= 400:
        return 0.30, "medium_short_document"
    elif total_words <= 800:
        return 0.25, "medium_document"
    else:
        return 0.20, "large_document"

def test_improvement():
    """Test the improvement with real examples."""
    
    print(f"\n📊 Before vs After Comparison")
    print("=" * 50)
    
    test_cases = [
        (58, 100, "Banking incident"),
        (150, 200, "Meeting notes"),
        (25, 50, "Brief alert"),
        (300, 500, "Blog post")
    ]
    
    for total_words, target_request, description in test_cases:
        print(f"\n📝 {description} ({total_words} words → {target_request} words requested)")
        print("-" * 30)
        
        # Current behavior
        current_result = min(target_request, total_words)
        print(f"❌ Current (capping): {current_result} words")
        
        # Proposed behavior  
        proposed_result, mode = proposed_target_logic(target_request, total_words)
        print(f"✅ Proposed (adaptive): {proposed_result} words ({mode})")
        
        improvement = current_result - proposed_result
        if improvement > 0:
            print(f"🚀 Improvement: {improvement} fewer words = more concise!")
        else:
            print(f"📝 Same behavior (achievable target)")

if __name__ == "__main__":
    test_improvement()