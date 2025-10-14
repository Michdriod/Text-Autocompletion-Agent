"""Quick test to verify Mode5 intelligent summarization works."""

import asyncio
from logic.mode_5 import Mode5

# Test text - simulate a document
test_document = """
Artificial Intelligence and Machine Learning have revolutionized modern computing.
Machine learning algorithms enable computers to learn from data without explicit programming.
Deep learning, a subset of machine learning, uses neural networks with multiple layers.
These technologies power applications from image recognition to natural language processing.

The field has seen tremendous growth in recent years, driven by increased computational power,
large datasets, and algorithmic improvements. Companies across industries are adopting AI
to improve efficiency, make better decisions, and create innovative products.

Neural networks consist of interconnected nodes that process information similar to human brains.
Training involves adjusting weights and biases to minimize prediction errors. Various architectures
exist, including convolutional neural networks for images and recurrent networks for sequences.

Applications span healthcare, finance, transportation, and entertainment. Self-driving cars use
computer vision and sensor fusion. Medical diagnosis systems analyze images and patient data.
Recommendation systems personalize content for users. The future promises even more integration
of AI into daily life, with ethical considerations becoming increasingly important.
""" * 50  # Repeat to make it longer

async def test_mode5():
    """Test Mode5 with different target word counts."""
    
    mode5 = Mode5()
    
    print("="*80)
    print("Testing Mode 5 Intelligent Summarization")
    print("="*80)
    print()
    
    # Test 1: Small summary
    print("Test 1: Small Document Summary (500 words)")
    print("-"*80)
    try:
        result = await mode5.process_raw_text(
            text=test_document[:2000],  # Use smaller portion
            target_words=100,
            output_format="markdown"
        )
        
        summary = result.get('markdown_summary', '')
        meta = result.get('meta', {})
        enforcement = meta.get('length_enforcement', {})
        
        print(f"✅ Summary generated: {len(summary.split())} words")
        print(f"   Target: 100 words")
        print(f"   Truncated: {enforcement.get('truncated', 'N/A')}")
        print(f"   Complete: {enforcement.get('complete_sentences', 'N/A')}")
        print(f"   Within Target: {enforcement.get('within_target', 'N/A')}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    # Test 2: Medium summary
    print("Test 2: Medium Summary (500 words)")
    print("-"*80)
    try:
        result = await mode5.process_raw_text(
            text=test_document,
            target_words=500,
            output_format="markdown"
        )
        
        summary = result.get('markdown_summary', '')
        meta = result.get('meta', {})
        enforcement = meta.get('length_enforcement', {})
        
        print(f"✅ Summary generated: {len(summary.split())} words")
        print(f"   Target: 500 words")
        print(f"   Truncated: {enforcement.get('truncated', 'N/A')}")
        print(f"   Complete: {enforcement.get('complete_sentences', 'N/A')}")
        print(f"   Within Target: {enforcement.get('within_target', 'N/A')}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    # Test 3: Large summary
    print("Test 3: Large Summary (1000 words)")
    print("-"*80)
    try:
        result = await mode5.process_raw_text(
            text=test_document,
            target_words=1000,
            output_format="markdown"
        )
        
        summary = result.get('markdown_summary', '')
        meta = result.get('meta', {})
        enforcement = meta.get('length_enforcement', {})
        
        print(f"✅ Summary generated: {len(summary.split())} words")
        print(f"   Target: 1000 words")
        print(f"   Truncated: {enforcement.get('truncated', 'N/A')}")
        print(f"   Complete: {enforcement.get('complete_sentences', 'N/A')}")
        print(f"   Within Target: {enforcement.get('within_target', 'N/A')}")
        
        # Check last sentence is complete
        last_char = summary.strip()[-1] if summary.strip() else ''
        if last_char in '.!?':
            print(f"   ✅ Ends with proper punctuation: '{last_char}'")
        else:
            print(f"   ⚠️  Does not end properly: '{last_char}'")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    print("="*80)
    print("✅ All tests completed!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_mode5())
