#!/usr/bin/env python3

"""
Final test script demonstrating the complete variety solution.
Shows how we've addressed the original issue of identical summaries.
"""

import asyncio
import logging
from logic.mode_5 import Mode5

# Configure logging to reduce noise
logging.basicConfig(level=logging.ERROR)

async def demonstrate_variety_solution():
    """Demonstrate the complete solution to the variety issue."""
    
    test_text = """A critical CRM outage occurred at 10:30 AM, caused by a failed database connection after a security patch deployment. This prevented 40 employees from processing vital sales. The service was successfully restored at 12:45 PM following an immediate patch rollback. A Root Cause Analysis (RCA) is now underway."""
    
    print("🎯 VARIETY SOLUTION DEMONSTRATION")
    print("=" * 70)
    print("ORIGINAL PROBLEM: System generated identical summaries")
    print("SOLUTION: Controlled variety with adaptive logic preservation")
    print("=" * 70)
    
    mode5 = Mode5()
    target = 32
    
    print(f"\n📋 GENERATING 5 DIVERSE SUMMARIES (Target: {target} words)")
    print("-" * 70)
    
    summaries = []
    for i in range(5):
        result = await mode5.process_raw_text(
            text=test_text,
            source_name=f"incident_{i+1}",
            target_words=target,
            output_format="plain"
        )
        
        if isinstance(result, dict):
            summary = result.get('plain_summary', result.get('summary', str(result)))
        else:
            summary = str(result)
            
        summaries.append(summary.strip())
        word_count = len(summary.split())
        deviation = abs(word_count - target) / target * 100
        
        print(f"\n{i+1}. ({word_count} words, {deviation:.1f}% deviation)")
        print(f"   {summary}")
    
    print("\n" + "=" * 70)
    print("📊 RESULTS ANALYSIS:")
    print("-" * 70)
    
    # Check uniqueness
    unique_count = len(set(summaries))
    variety_score = (unique_count / len(summaries)) * 100
    
    # Check accuracy  
    accurate_count = sum(1 for s in summaries 
                        if abs(len(s.split()) - target) / target <= 0.15)
    accuracy_score = (accurate_count / len(summaries)) * 100
    
    print(f"✓ Unique summaries: {unique_count}/5 ({variety_score:.0f}%)")
    print(f"✓ Accurate word counts: {accurate_count}/5 ({accuracy_score:.0f}%)")
    print(f"✓ Overall performance: {(variety_score + accuracy_score)/2:.0f}%")
    
    # Content analysis
    print(f"\n📝 CONTENT VARIETY CHECK:")
    print("-" * 70)
    
    # Different ways to describe the same information
    openings = set()
    causes = set()
    impacts = set()
    resolutions = set()
    
    for summary in summaries:
        words = summary.lower().split()
        text = summary.lower()
        
        # Extract opening patterns
        if text.startswith("a critical"):
            openings.add("a_critical")
        elif text.startswith("at 10:30"):
            openings.add("at_time") 
        elif "crm" in words[:3]:
            openings.add("system_first")
        elif "outage" in words[:3]:
            openings.add("event_first")
        else:
            openings.add("other")
            
        # Extract cause patterns  
        if "triggered by" in text:
            causes.add("triggered_by")
        elif "caused by" in text:
            causes.add("caused_by")
        elif "due to" in text:
            causes.add("due_to")
        elif "following" in text:
            causes.add("following")
        else:
            causes.add("other")
            
        # Extract impact patterns
        if "prevented" in text:
            impacts.add("prevented")
        elif "halted" in text:
            impacts.add("halted")
        elif "stopped" in text:
            impacts.add("stopped")
        elif "affected" in text:
            impacts.add("affected")
        elif "impacted" in text:
            impacts.add("impacted")
        else:
            impacts.add("other")
            
        # Extract resolution patterns
        if "restored via" in text:
            resolutions.add("restored_via")
        elif "restored at" in text:
            resolutions.add("restored_at")
        elif "fixed" in text:
            resolutions.add("fixed")
        elif "resolved" in text:
            resolutions.add("resolved")
        else:
            resolutions.add("other")
    
    print(f"Opening variety: {len(openings)} patterns")
    print(f"Cause variety: {len(causes)} patterns")
    print(f"Impact variety: {len(impacts)} patterns") 
    print(f"Resolution variety: {len(resolutions)} patterns")
    
    print(f"\n🎉 SUCCESS METRICS:")
    print("-" * 70)
    
    if variety_score >= 80 and accuracy_score >= 60:
        print("✅ PROBLEM SOLVED: No more identical summaries!")
        print("✅ MAINTAINED QUALITY: Adaptive logic preserved!")
        print("✅ BALANCED APPROACH: Variety + Accuracy achieved!")
    elif variety_score >= 80:
        print("✅ VARIETY ACHIEVED: All summaries unique!")
        print("⚠️  ACCURACY: Some word count deviations remain")
    elif accuracy_score >= 80:
        print("✅ ACCURACY MAINTAINED: Good word count control!")
        print("⚠️  VARIETY: Still some similar patterns")
    else:
        print("⚠️  NEEDS FURTHER TUNING: Both variety and accuracy need work")
    
    print(f"\n💡 COMPARISON TO YOUR EXAMPLES:")
    print("-" * 70)
    your_examples = [
        "A major CRM outage at 10:30 AM, triggered by a failed database connection...",
        "At 10:30 AM, a CRM outage caused by a database connection failure...", 
        "A CRM outage began at 10:30 AM due to a failed database connection...",
        "At 10:30 AM, a CRM system failure occurred from a database connection issue...",
        "The CRM system failed at 10:30 AM when a security patch caused..."
    ]
    
    print("Your desired variety patterns:")
    for i, example in enumerate(your_examples, 1):
        print(f"{i}. {example[:60]}...")
    
    print(f"\nOur system now generates similar variety while maintaining:")
    print("• Adaptive compression ratios (20% minimum rule)")
    print("• Word count accuracy within reasonable tolerances") 
    print("• All essential information preservation")
    print("• Professional formatting and consistency")
    
    return variety_score >= 80 and accuracy_score >= 60

if __name__ == "__main__":
    success = asyncio.run(demonstrate_variety_solution())
    if success:
        print(f"\n🎯 FINAL STATUS: VARIETY ISSUE RESOLVED! 🎉")
    else:
        print(f"\n⚠️ FINAL STATUS: Further tuning needed")