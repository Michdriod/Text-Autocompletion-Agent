#!/usr/bin/env python3

"""Analyze the behavior: Capping vs Adaptive fallback when target_words > total_words"""

def analyze_scenarios():
    """Compare current capping behavior vs potential adaptive fallback."""
    
    print("🤔 Analysis: Capping vs Adaptive Fallback")
    print("=" * 80)
    
    # Example scenarios
    scenarios = [
        {
            "document_words": 58,
            "target_request": 100,
            "adaptive_would_give": int(58 * 0.55),  # 55% for very_short_document
            "current_caps_to": 58,
            "description": "Banking incident (very short doc)"
        },
        {
            "document_words": 150, 
            "target_request": 200,
            "adaptive_would_give": int(150 * 0.40),  # 40% for short_document
            "current_caps_to": 150,
            "description": "Meeting notes (short doc)"
        },
        {
            "document_words": 25,
            "target_request": 50, 
            "adaptive_would_give": int(25 * 0.75),  # 75% for micro_document
            "current_caps_to": 25,
            "description": "Brief alert (micro doc)"
        },
        {
            "document_words": 300,
            "target_request": 400,
            "adaptive_would_give": int(300 * 0.30),  # 30% for medium_short_document  
            "current_caps_to": 300,
            "description": "Blog post (medium-short doc)"
        }
    ]
    
    print(f"{'Doc':<4} {'Request':<7} {'Current':<8} {'Adaptive':<9} {'Better?':<8} {'Description'}")
    print("-" * 80)
    
    for s in scenarios:
        # Is adaptive better than capping?
        adaptive_better = s['adaptive_would_give'] < s['current_caps_to']
        better_marker = "✅ Yes" if adaptive_better else "❌ No"
        
        print(f"{s['document_words']:<4} {s['target_request']:<7} {s['current_caps_to']:<8} "
              f"{s['adaptive_would_give']:<9} {better_marker:<8} {s['description']}")
    
    print(f"\n🎯 Analysis Results:")
    
    print(f"\n✅ **Adaptive Fallback Advantages:**")
    print(f"   • Provides actual summarization instead of near-full text")
    print(f"   • Consistent with system's intelligent compression philosophy") 
    print(f"   • User gets a meaningful summary even with 'impossible' requests")
    print(f"   • More useful output (32 words vs 54 words for banking example)")
    
    print(f"\n❌ **Current Capping Advantages:**") 
    print(f"   • Preserves maximum information content")
    print(f"   • Clear predictable behavior (never exceeds original)")
    print(f"   • Avoids 'ignoring' user's explicit request")
    
    print(f"\n🤔 **User Intent Analysis:**")
    print(f"   • When user asks for target_words=100 on 58-word doc:")
    print(f"     - Do they want: Maximum detail preservation? → Current capping")
    print(f"     - Do they want: Actual summarization? → Adaptive fallback")
    print(f"     - Are they confused about doc length? → Either could work")

def propose_solution():
    """Propose a hybrid approach."""
    
    print(f"\n💡 **PROPOSED SOLUTION: Hybrid Approach**")
    print("=" * 80)
    
    print(f"Instead of just capping OR just using adaptive, provide CHOICE:")
    
    print(f"\n```python")
    print(f"# When target_words > total_words:")
    print(f"if target_words > total_words:")
    print(f"    # Option 1: Strict user preference (current behavior)")
    print(f"    effective_target = total_words")
    print(f"    target_mode = 'user_absolute_capped'")
    print(f"    ")
    print(f"    # Option 2: Adaptive fallback (your suggestion)")  
    print(f"    # compression_ratio, scenario = get_adaptive_ratio(total_words)")
    print(f"    # effective_target = int(total_words * compression_ratio)")
    print(f"    # target_mode = f'adaptive_fallback_{{scenario}}'")
    print(f"```")
    
    print(f"\n🎯 **Recommendation: Use Adaptive Fallback**")
    print(f"✅ **Reasoning:**")
    print(f"   1. User asking for 100 words from 58-word doc likely wants 'summary'")
    print(f"   2. Returning 32 intelligently-compressed words is more useful than 54")
    print(f"   3. Consistent with adaptive system philosophy")
    print(f"   4. Still respects user intent (they get a summary, just smarter)")
    
    print(f"\n📝 **Example Comparison:**")
    print(f"   Banking doc (58 words) + target_words=100:")
    print(f"   • Current: 54 words (barely summarized)")
    print(f"   • Proposed: 32 words (meaningfully summarized)")
    print(f"   • Winner: Proposed (more useful output)")

if __name__ == "__main__":
    analyze_scenarios()
    propose_solution()