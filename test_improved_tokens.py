#!/usr/bin/env python3

"""
Test script focused on the content types that needed token budget improvements.
Specifically testing product descriptions and research abstracts.
"""

import asyncio
import logging
from logic.mode_5 import Mode5

# Configure logging to reduce noise
logging.basicConfig(level=logging.ERROR)

async def test_improved_token_budgets():
    """Test the improved token budgets on previously problematic content types."""
    
    print("🔧 IMPROVED TOKEN BUDGET TEST")
    print("=" * 70)
    print("Testing enhanced token budgets for product descriptions and research abstracts")
    print("=" * 70)
    
    mode5 = Mode5()
    
    # Focus on the content types that were having token budget issues
    test_cases = [
        {
            "title": "💡 PRODUCT DESCRIPTION (Previous Issues)",
            "content": """The UltraBook Pro features a 15.6-inch 4K OLED display with 100% DCI-P3 color accuracy, perfect for creative professionals. Powered by the latest Intel i9 processor and 32GB DDR5 RAM, it delivers exceptional performance for video editing and 3D rendering. The laptop includes a dedicated NVIDIA RTX 4080 graphics card, 2TB NVMe SSD storage, and advanced cooling system. Battery life extends up to 12 hours with fast charging capability. The aluminum chassis weighs just 3.2 pounds while maintaining military-grade durability standards. Starting price is $2,499 with free shipping.""",
            "target": 30,
            "previous_issues": "Token budget too small (45), causing truncation"
        },
        {
            "title": "🔬 RESEARCH ABSTRACT (Previous Issues)", 
            "content": """This study investigates the impact of microplastics on marine ecosystem biodiversity using advanced spectroscopic analysis. We collected 2,400 water samples from 12 locations across the Pacific Ocean over 18 months. Results reveal microplastic concentrations averaging 4.2 particles per liter, with highest levels near urban coastlines. Species diversity decreased by 23% in high-contamination areas compared to pristine waters. Phytoplankton populations showed 31% reduction in contaminated zones, affecting the entire food chain. The findings suggest urgent need for plastic waste reduction policies and advanced filtration technologies.""",
            "target": 45,
            "previous_issues": "Token budget insufficient (67), leading to incomplete summaries"
        },
        {
            "title": "📰 NEWS ARTICLE (Control - Was Working Well)",
            "content": """Scientists at MIT have developed a new artificial intelligence system that can predict protein folding with unprecedented accuracy. The breakthrough, published in Nature, could revolutionize drug discovery and treatment of genetic diseases. The AI model, called AlphaFold3, achieved 95% accuracy in predicting protein structures, surpassing previous methods by 40%. Pharmaceutical companies are already licensing the technology for cancer research and Alzheimer's treatment development. The research team expects clinical applications within five years.""",
            "target": 35,
            "previous_issues": "None - was working well, using as control"
        }
    ]
    
    print(f"\n🧪 TESTING WITH IMPROVED TOKEN BUDGETS")
    print("-" * 70)
    
    for test_case in test_cases:
        print(f"\n{test_case['title']}")
        print(f"Target: {test_case['target']} words")
        print(f"Previous Issue: {test_case['previous_issues']}")
        print("-" * 50)
        
        # Generate 3 summaries to test both variety and completion
        summaries = []
        token_budgets = []
        
        for i in range(3):
            # We'll capture the token budget from the logs
            result = await mode5.process_raw_text(
                text=test_case["content"],
                source_name=f"test_{i+1}",
                target_words=test_case["target"],
                output_format="plain"
            )
            
            if isinstance(result, dict):
                summary = result.get('plain_summary', result.get('summary', str(result)))
            else:
                summary = str(result)
            
            summaries.append(summary.strip())
        
        # Analyze results
        target = test_case["target"]
        word_counts = [len(s.split()) for s in summaries]
        deviations = [abs(wc - target) / target * 100 for wc in word_counts]
        
        # Check for improvements
        complete_summaries = sum(1 for s in summaries if not s.endswith('...') and len(s.split()) >= target * 0.7)
        accurate_summaries = sum(1 for dev in deviations if dev <= 15)
        unique_summaries = len(set(summaries))
        
        print(f"\n📊 RESULTS ANALYSIS:")
        for i, (summary, wc, dev) in enumerate(zip(summaries, word_counts, deviations), 1):
            status = "✅" if dev <= 15 else "⚠️" if dev <= 25 else "❌"
            complete = "✓" if len(summary.split()) >= target * 0.7 else "✗ (incomplete)"
            print(f"  {i}. {status} {wc} words ({dev:.1f}% dev) {complete}")
            print(f"     {summary[:65]}{'...' if len(summary) > 65 else ''}")
        
        # Performance metrics
        completion_rate = (complete_summaries / 3) * 100
        accuracy_rate = (accurate_summaries / 3) * 100
        variety_rate = (unique_summaries / 3) * 100
        
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"  • Completion Rate: {completion_rate:.0f}% (summaries with adequate content)")
        print(f"  • Accuracy Rate: {accuracy_rate:.0f}% (within 15% of target)")
        print(f"  • Variety Rate: {variety_rate:.0f}% (unique summaries)")
        
        overall_improvement = (completion_rate + accuracy_rate + variety_rate) / 3
        
        if overall_improvement >= 85:
            print(f"  🎉 EXCELLENT: {overall_improvement:.0f}% - Token budget fix successful!")
        elif overall_improvement >= 70:
            print(f"  ✅ GOOD: {overall_improvement:.0f}% - Significant improvement achieved")
        elif overall_improvement >= 50:
            print(f"  ⚠️ MODERATE: {overall_improvement:.0f}% - Some improvement, may need further tuning")
        else:
            print(f"  ❌ POOR: {overall_improvement:.0f}% - Token budget still insufficient")
    
    print(f"\n" + "=" * 70)
    print("🎯 OVERALL TOKEN BUDGET IMPROVEMENT ASSESSMENT")
    print("-" * 70)
    
    print("✅ CHANGES MADE:")
    print("  • Short summaries (≤50 words): 50% → 80% overhead")
    print("  • Token cap increased: 85 → 110 tokens")  
    print("  • Very short summaries (≤15 words): 100% → 120% overhead")
    print("  • Very short cap increased: 50 → 60 tokens")
    
    print(f"\n💡 EXPECTED IMPROVEMENTS:")
    print("  • Product descriptions should have fewer truncations")
    print("  • Research abstracts should complete more consistently")  
    print("  • Better variety while maintaining accuracy")
    print("  • More room for comprehensive content coverage")
    
    print(f"\n🔄 NEXT STEPS:")
    print("  • Monitor performance on production content")
    print("  • Fine-tune if specific domains still have issues")
    print("  • Consider domain-specific token budget adjustments if needed")

if __name__ == "__main__":
    asyncio.run(test_improved_token_budgets())