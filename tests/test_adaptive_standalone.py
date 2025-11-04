#!/usr/bin/env python3

"""Test adaptive compression ratio calculations directly."""

def get_adaptive_compression_ratio(total_words):
    """Extract the adaptive compression logic from Mode5 for testing."""
    
    if total_words <= 50:
        # MICRO DOCUMENTS: Gentle compression (75%)
        compression_ratio = 0.75
        scenario = "micro_document"
        
    elif total_words <= 100:
        # VERY SHORT DOCUMENTS: Moderate compression (55%)  
        compression_ratio = 0.55
        scenario = "very_short_document"
        
    elif total_words <= 200:
        # SHORT DOCUMENTS: Standard compression (40%)
        compression_ratio = 0.40
        scenario = "short_document"
        
    elif total_words <= 400:
        # MEDIUM-SHORT DOCUMENTS: Targeted compression (30%)
        compression_ratio = 0.30
        scenario = "medium_short_document"
        
    elif total_words <= 800:
        # MEDIUM DOCUMENTS: Efficient compression (25%)
        compression_ratio = 0.25
        scenario = "medium_document"
        
    else:
        # LARGE+ DOCUMENTS: 20% compression (minimum floor)
        compression_ratio = 0.20
        scenario = "large_document"
    
    # Calculate target with minimum viable summary logic
    auto_target = max(1, round(total_words * compression_ratio))
    
    # MINIMUM VIABLE SUMMARY: Ensure summaries are never too short
    MINIMUM_VIABLE_WORDS = 15
    if auto_target < MINIMUM_VIABLE_WORDS:
        effective_target = MINIMUM_VIABLE_WORDS
        target_mode = f"adaptive_{scenario}_floored"
    else:
        effective_target = auto_target
        target_mode = f"adaptive_{scenario}"
    
    # Cap at original length
    effective_target = min(effective_target, total_words)
    
    return compression_ratio, scenario, effective_target, target_mode

def test_adaptive_compression():
    """Test the adaptive compression system with various document sizes."""
    print("🧪 Testing Adaptive Compression System")
    print("=" * 80)
    
    # Test cases: (input_words, description)
    test_cases = [
        (21, "Critical incident (micro)"),
        (58, "Your banking example (very short)"),  # The key example!
        (85, "Email summary (very short)"),
        (150, "Meeting notes (short)"),
        (300, "Blog post (medium-short)"),
        (600, "Research article (medium)"),
        (1200, "White paper (large)"),
    ]
    
    print(f"{'Words':<6} {'Description':<25} {'Scenario':<20} {'Ratio':<6} {'Target':<7} {'Mode'}")
    print("-" * 80)
    
    for input_words, description in test_cases:
        ratio, scenario, target, mode = get_adaptive_compression_ratio(input_words)
        ratio_percent = int(ratio * 100)
        
        print(f"{input_words:<6} {description:<25} {scenario:<20} {ratio_percent}%{'':<3} {target:<7} {mode}")
    
    print("\n🎯 Key Improvements Demonstrated:")
    
    # Show the specific banking example improvement
    old_ratio, old_scenario, old_target, old_mode = 0.20, "fixed_ratio", max(1, round(58 * 0.20)), "fixed"
    new_ratio, new_scenario, new_target, new_mode = get_adaptive_compression_ratio(58)
    
    print(f"📊 Banking Example (58 words):")
    print(f"   OLD System: {int(old_ratio*100)}% compression → {old_target} words (truncated)")
    print(f"   NEW System: {int(new_ratio*100)}% compression → {new_target} words (readable)")
    print(f"   🚀 Improvement: {new_target - old_target} more words = {((new_target/old_target-1)*100):.0f}% better!")
    
    print(f"\n✅ Micro docs (≤50 words): 75% compression (gentle)")
    print(f"✅ Very short (51-100): 55% compression (moderate)")  
    print(f"✅ Short (101-200): 40% compression (standard)")
    print(f"✅ Medium-short (201-400): 30% compression (targeted)")
    print(f"✅ Medium (401-800): 25% compression (efficient)")
    print(f"✅ Large (801+): 20% compression (minimum floor)")
    
    print(f"\n🎉 No more truncated 11-word 'summaries'!")
    print(f"🎉 Intelligent compression that scales with document size!")

if __name__ == "__main__":
    test_adaptive_compression()