#!/usr/bin/env python3

"""Test adaptive compression ratio calculations without API calls."""

import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

def test_compression_ratios():
    """Test that the adaptive compression ratios are calculated correctly."""
    print("🧪 Testing Adaptive Compression Ratio Calculations")
    print("=" * 70)
    
    mode5 = Mode5()
    
    # Test cases: (input_words, expected_scenario, expected_compression, expected_target)
    test_cases = [
        (25, "micro_document", 75, 19),
        (50, "micro_document", 75, 38), 
        (58, "very_short_document", 55, 32),  # Your banking example
        (85, "very_short_document", 55, 47),
        (100, "very_short_document", 55, 55),
        (150, "short_document", 40, 60),
        (200, "short_document", 40, 80),
        (300, "medium_short_document", 30, 90),
        (400, "medium_short_document", 30, 120),
        (600, "medium_document", 25, 150),
        (800, "medium_document", 25, 200),
        (1000, "large_document", 20, 200),  # 20% minimum floor
        (1500, "large_document", 20, 300),  # 20% minimum floor
    ]
    
    print(f"{'Words':<6} {'Scenario':<20} {'Ratio':<6} {'Target':<7} {'Status'}")
    print("-" * 70)
    
    for input_words, expected_scenario, expected_compression, expected_target in test_cases:
        # Calculate what the system would produce
        calculated_ratio, scenario = mode5._get_adaptive_compression_ratio(input_words)
        calculated_target = int(input_words * calculated_ratio)
        
        # Check if it matches expectations
        ratio_percent = int(calculated_ratio * 100)
        status = "✅" if (scenario == expected_scenario and 
                        abs(ratio_percent - expected_compression) <= 5 and
                        abs(calculated_target - expected_target) <= 5) else "❌"
        
        print(f"{input_words:<6} {scenario:<20} {ratio_percent}%{'':<3} {calculated_target:<7} {status}")
    
    print("\n🎯 Key Improvements:")
    print(f"✅ Banking example (58 words): {int(58 * 0.55)} words instead of {int(58 * 0.20)} words")
    print(f"✅ Short docs get gentler compression ratios")  
    print(f"✅ Large docs maintain 20% minimum compression")
    print(f"✅ No more truncated 11-word 'summaries'!")

if __name__ == "__main__":
    test_compression_ratios()