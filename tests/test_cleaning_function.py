#!/usr/bin/env python3

"""Test the cleaning function directly."""

import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

def test_cleaning_function():
    """Test the _clean_summary_output function directly."""
    print("🧪 Testing Cleaning Function Directly")
    print("=" * 60)
    
    mode5 = Mode5()
    
    # Test cases that should be cleaned
    test_cases = [
        "Here is a summary of the document in exactly 50 words:\nBanking as a Service...",
        "42 word range:\nBanking as a Service integrates...",
        "50-word summary:\nBanking as a Service (BaaS)...", 
        "**Summary of Banking as a Service (BaaS)**\nBanking as a Service...",
        "Unified Summary:\nBanking as a Service integrates...",
        "Here's a summary:\nBanking as a Service..."
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Input:  '{test_case[:60]}...'")
        
        cleaned = mode5._clean_summary_output(test_case)
        print(f"Output: '{cleaned[:60]}...'")
        
        if cleaned.startswith("Banking as a Service"):
            print("✅ CLEANED - Unwanted prefix removed!")
        else:
            print("❌ NOT CLEANED - Prefix still present")

if __name__ == "__main__":
    test_cleaning_function()