#!/usr/bin/env python3

"""
Enhanced test script to demonstrate improved summary variety with content analysis.
Shows how the new system creates unique, varied summaries while maintaining accuracy.
"""

import asyncio
import logging
from logic.mode_5 import Mode5

# Configure logging to show less noise
logging.basicConfig(level=logging.WARNING)

async def test_enhanced_variety():
    """Test improved variety system with detailed content analysis."""
    
    # Your example text
    test_text = """A critical CRM outage occurred at 10:30 AM, caused by a failed database connection after a security patch deployment. This prevented 40 employees from processing vital sales. The service was successfully restored at 12:45 PM following an immediate patch rollback. A Root Cause Analysis (RCA) is now underway."""
    
    print("🔍 ENHANCED SUMMARY VARIETY TEST")
    print("=" * 80)
    print(f"Original text ({len(test_text.split())} words):")
    print(f'"{test_text}"')
    print("\n" + "=" * 80)
    
    mode5 = Mode5()
    
    # Test with target word count (should use adaptive compression)
    target = 32  # Similar to your example
    
    print(f"\n🎯 GENERATING VARIED SUMMARIES (Target: {target} words)")
    print("Demonstrating controlled variety while maintaining adaptive logic")
    print("-" * 80)
    
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
        
        # Show word count and deviation
        deviation = abs(word_count - target) / target * 100
        status = "✅" if deviation <= 15 else "⚠️" if deviation <= 25 else "❌"
        
        print(f"{status} ({word_count} words, {deviation:.1f}% deviation)")
        print(f"   {clean_summary}")
    
    print("\n" + "=" * 80)
    print("🎨 VARIETY ANALYSIS:")
    print("-" * 80)
    
    # Check for variety
    unique_summaries = set(summaries)
    variety_percentage = (len(unique_summaries) / len(summaries)) * 100
    
    print(f"✓ Total summaries: {len(summaries)}")
    print(f"✓ Unique summaries: {len(unique_summaries)}")
    print(f"✓ Variety score: {variety_percentage:.1f}%")
    
    # Check for word count accuracy
    accurate_count = 0
    for i, summary in enumerate(summaries):
        word_count = len(summary.split())
        deviation = abs(word_count - target) / target * 100
        if deviation <= 15:  # Within 15% tolerance (relaxed for variety)
            accurate_count += 1
    
    accuracy_percentage = (accurate_count / len(summaries)) * 100
    print(f"✓ Word count accuracy: {accuracy_percentage:.1f}% (within 15% tolerance)")
    
    print("\n" + "=" * 80)
    print("🔍 CONTENT VARIETY ANALYSIS:")
    print("-" * 80)
    
    # Analyze opening words
    opening_words = [' '.join(summary.split()[:3]) for summary in summaries]
    unique_openings = len(set(opening_words))
    
    # Analyze key phrase variations
    key_phrases = {
        "time_mention": [],
        "cause_description": [],
        "impact_description": [],
        "resolution_description": []
    }
    
    for summary in summaries:
        lower_summary = summary.lower()
        
        # Time mentions
        if "10:30 am" in lower_summary or "10:30am" in lower_summary:
            if "occurred at" in lower_summary:
                key_phrases["time_mention"].append("occurred at")
            elif "began at" in lower_summary:
                key_phrases["time_mention"].append("began at")
            else:
                key_phrases["time_mention"].append("other")
        
        # Cause descriptions  
        if "database connection" in lower_summary:
            if "failed database" in lower_summary:
                key_phrases["cause_description"].append("failed database")
            elif "database connection failure" in lower_summary:
                key_phrases["cause_description"].append("connection failure")
            else:
                key_phrases["cause_description"].append("other database")
        
        # Impact descriptions
        if "40 employees" in lower_summary:
            if "prevented" in lower_summary:
                key_phrases["impact_description"].append("prevented employees")
            elif "impacted" in lower_summary:
                key_phrases["impact_description"].append("impacted employees")
            elif "stopped" in lower_summary:
                key_phrases["impact_description"].append("stopped employees")
            else:
                key_phrases["impact_description"].append("other impact")
    
    print(f"✓ Opening phrase variety: {unique_openings}/5 unique")
    
    for phrase_type, phrases in key_phrases.items():
        unique_phrases = len(set(phrases))
        if phrases:  # Only show if we found relevant phrases
            print(f"✓ {phrase_type.replace('_', ' ').title()} variety: {unique_phrases}/{len(phrases)} unique")
    
    print("\n" + "=" * 80)
    print("🎯 SUMMARY:")
    
    overall_score = (variety_percentage + accuracy_percentage) / 2
    
    if overall_score >= 80:
        print("🎉 EXCELLENT: High variety with good accuracy!")
        print("   The system successfully creates diverse summaries while maintaining quality.")
    elif overall_score >= 60:
        print("✅ GOOD: Balanced variety and accuracy.")
        print("   The system shows improvement in generating varied content.")
    else:
        print("⚠️ NEEDS IMPROVEMENT: Either variety or accuracy needs work.")
    
    print(f"\nOverall Performance Score: {overall_score:.1f}%")
    print(f"Variety Achievement: {variety_percentage:.1f}%")
    print(f"Accuracy Achievement: {accuracy_percentage:.1f}%")
    
    # Compare with your desired examples
    print("\n" + "=" * 80)
    print("📋 COMPARISON WITH YOUR DESIRED VARIETY EXAMPLES:")
    print("-" * 80)
    print("Your examples showed:")
    print("- Different opening phrases ('A major CRM outage', 'At 10:30 AM', etc.)")
    print("- Varied cause descriptions ('triggered by', 'caused by', 'due to')")
    print("- Different impact phrasings ('halted operations', 'stopped employees', 'prevented processing')")
    print("- Alternative resolution descriptions ('fixed by', 'restored via', 'resolved through')")
    print(f"\nOur system achieved {variety_percentage:.1f}% variety while maintaining adaptive compression logic!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_variety())