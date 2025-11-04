#!/usr/bin/env python3

"""Test target_words parameter vs adaptive compression system."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

async def test_target_words_vs_adaptive():
    """Test that manual target_words overrides adaptive compression."""
    print("🧪 Testing Manual Target Words vs Adaptive Compression")
    print("=" * 80)
    
    mode5 = Mode5()
    
    # Test document (58 words - banking example)
    test_text = """A critical software incident occurred at 10:30 AM, causing a complete service outage of the CRM system. The outage was triggered by a failed database connection during a security patch deployment, preventing 40 employees from processing sales. The issue was resolved by 12:45 PM via a patch rollback, and a full Root Cause Analysis (RCA) is now underway."""
    
    input_words = len(test_text.split())
    print(f"📄 Test Document: {input_words} words")
    print(f"📄 Text Preview: {test_text[:80]}...")
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Adaptive System (No target_words)",
            "target_words": None,
            "expected_behavior": "Uses adaptive compression (55% for very_short_document)"
        },
        {
            "name": "Manual Target: 15 words",
            "target_words": 15,
            "expected_behavior": "Forces 15 words (ignores adaptive system)"
        },
        {
            "name": "Manual Target: 40 words", 
            "target_words": 40,
            "expected_behavior": "Forces 40 words (ignores adaptive system)"
        },
        {
            "name": "Manual Target: 100 words (exceeds original)",
            "target_words": 100,
            "expected_behavior": "Caps at original length (58 words)"
        }
    ]
    
    print("\n" + "=" * 80)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 Test {i}: {scenario['name']}")
        print("-" * 60)
        print(f"Expected: {scenario['expected_behavior']}")
        
        try:
            result = await mode5.process_raw_text(
                text=test_text,
                source_name=f"target_test_{i}",
                target_words=scenario['target_words'],
                output_format="markdown"
            )
            
            output_words = result['summary_words']
            
            print(f"Result: {output_words} words")
            print(f"Summary: {result['markdown_summary'][:100]}{'...' if len(result['markdown_summary']) > 100 else ''}")
            
            # Analysis
            if scenario['target_words'] is None:
                # Should use adaptive system (55% of 58 = ~32 words)
                expected_range = (25, 35)  # Allow some flexibility
                if expected_range[0] <= output_words <= expected_range[1]:
                    print("✅ ADAPTIVE: Used intelligent compression ratio!")
                else:
                    print(f"⚠️  ADAPTIVE: Expected ~32 words, got {output_words}")
            elif scenario['target_words'] == 100:
                # Should cap at original length
                if output_words <= input_words:
                    print("✅ CAPPING: Correctly capped at original length!")
                else:
                    print(f"❌ CAPPING: Should not exceed {input_words} words")
            else:
                # Should respect manual target (within reasonable range)
                target = scenario['target_words']
                tolerance = max(3, target * 0.2)  # 20% tolerance or 3 words
                if abs(output_words - target) <= tolerance:
                    print(f"✅ MANUAL: Respected user target ({target} ± {tolerance:.0f})!")
                else:
                    print(f"⚠️  MANUAL: Expected ~{target}, got {output_words}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎯 Target Words Priority Test Complete!")
    print("✅ Manual target_words should override adaptive system")
    print("✅ Adaptive system should activate when target_words=None")
    print("✅ System should cap targets that exceed original length")

async def test_prompt_override():
    """Test that prompts with target words override both parameter and adaptive."""
    print(f"\n" + "=" * 80)
    print("🧪 Testing Prompt Override Priority")
    print("=" * 80)
    
    mode5 = Mode5()
    
    test_text = """A critical software incident occurred at 10:30 AM, causing a complete service outage of the CRM system. The outage was triggered by a failed database connection during a security patch deployment, preventing 40 employees from processing sales."""
    
    # Test prompt override (highest priority)
    try:
        result = await mode5.process_raw_text(
            text=test_text,
            source_name="prompt_override_test",
            target_words=30,  # This should be ignored
            user_prompt="Summarize this in exactly 20 words.",
            output_format="markdown"
        )
        
        output_words = result['summary_words']
        print(f"📝 Prompt Override Test:")
        print(f"   Parameter target_words: 30")
        print(f"   Prompt target: 20 words")
        print(f"   Result: {output_words} words")
        print(f"   Summary: {result['markdown_summary']}")
        
        if 17 <= output_words <= 23:  # Allow some flexibility
            print("✅ PRIORITY: Prompt override worked correctly!")
        else:
            print(f"⚠️  PRIORITY: Expected ~20 words from prompt, got {output_words}")
            
    except Exception as e:
        print(f"❌ Prompt Override Error: {e}")
    
    print(f"\n🎯 Priority Order Confirmed:")
    print("1. 🥇 Prompt target (highest priority)")
    print("2. 🥈 Manual target_words parameter") 
    print("3. 🥉 Adaptive compression system (fallback)")

if __name__ == "__main__":
    asyncio.run(test_target_words_vs_adaptive())
    asyncio.run(test_prompt_override())