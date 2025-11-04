#!/usr/bin/env python3

"""
Test script to demonstrate and fix the summary variety issue.
The current system generates identical summaries due to low temperature settings.
We need controlled variability while maintaining accuracy and adaptive logic.
"""

import asyncio
import logging
from logic.mode_5 import Mode5

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_summary_variety():
    """Test that summaries have variety while maintaining accuracy."""
    
    # Your example text
    test_text = """A critical CRM outage occurred at 10:30 AM, caused by a failed database connection after a security patch deployment. This prevented 40 employees from processing vital sales. The service was successfully restored at 12:45 PM following an immediate patch rollback. A Root Cause Analysis (RCA) is now underway."""
    
    print("🔍 TESTING SUMMARY VARIETY")
    print("=" * 60)
    print(f"Original text ({len(test_text.split())} words):")
    print(f'"{test_text}"')
    print("\n" + "=" * 60)
    
    mode5 = Mode5()
    
    # Test with target word count (should use adaptive compression)
    target = 32  # Similar to your example
    
    print(f"\n🎯 GENERATING {5} SUMMARIES (Target: {target} words)")
    print("-" * 60)
    
    summaries = []
    
    for i in range(5):
        print(f"\n📝 Summary {i+1}:")
        
        result = await mode5.process_raw_text(
            text=test_text,
            source_name=f"incident_report_{i+1}",
            target_words=target,
            output_format="plain"
        )
        
        # Extract the actual summary text properly
        if isinstance(result, dict):
            summary_text = result.get('plain_summary', result.get('summary', result.get('text', str(result))))
        else:
            summary_text = str(result)
        
        # Clean and count words
        clean_summary = summary_text.strip()
        word_count = len(clean_summary.split())
        
        summaries.append(clean_summary)
        
        print(f"({word_count} words): {clean_summary}")
    
    print("\n" + "=" * 60)
    print("🔍 VARIETY ANALYSIS:")
    print("-" * 60)
    
    # Check for variety
    unique_summaries = set(summaries)
    variety_percentage = (len(unique_summaries) / len(summaries)) * 100
    
    print(f"Total summaries: {len(summaries)}")
    print(f"Unique summaries: {len(unique_summaries)}")
    print(f"Variety score: {variety_percentage:.1f}%")
    
    if variety_percentage < 60:
        print("❌ LOW VARIETY DETECTED - Summaries are too similar/identical")
    elif variety_percentage < 80:
        print("⚠️  MODERATE VARIETY - Some repetition detected")
    else:
        print("✅ GOOD VARIETY - Summaries show appropriate variation")
    
    # Check for word count accuracy
    target_hits = 0
    for i, summary in enumerate(summaries):
        word_count = len(summary.split())
        deviation = abs(word_count - target) / target * 100
        print(f"Summary {i+1}: {word_count} words (deviation: {deviation:.1f}%)")
        if deviation <= 8:  # Within 8% tolerance
            target_hits += 1
    
    accuracy_percentage = (target_hits / len(summaries)) * 100
    print(f"\nWord count accuracy: {accuracy_percentage:.1f}% ({target_hits}/{len(summaries)} within 8% tolerance)")
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATION:")
    if variety_percentage < 60:
        print("❗ ISSUE: Need to implement controlled variability")
        print("   - Current temperature too low (0.1-0.2)")
        print("   - System too deterministic")
        print("   - Need variety techniques while maintaining accuracy")
    else:
        print("✅ System provides good balance of variety and accuracy")

if __name__ == "__main__":
    asyncio.run(test_summary_variety())