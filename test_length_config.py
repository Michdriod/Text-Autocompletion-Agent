#!/usr/bin/env python3
"""
Test length configuration to verify it's working from frontend selection
"""
import asyncio
from logic.mode_6 import Mode6

async def test_length_modes():
    """Test different length modes to verify configuration"""
    
    mode6 = Mode6()
    
    # Test all length modes
    length_modes = ['short', 'medium', 'long', 'very_long']
    
    print("🔍 Testing Length Configuration...")
    print("=" * 50)
    
    for length_mode in length_modes:
        print(f"\n📏 Testing '{length_mode}' mode")
        
        try:
            # Calculate expected max tokens
            expected_tokens = mode6._get_max_tokens_for_length(length_mode)
            print(f"Expected max tokens: {expected_tokens}")
            
            # Generate a short test article
            markdown = await mode6.generate_article(
                title="Test Article",
                description="This is a test article to verify length configuration is working correctly.",
                keywords="test, configuration, length",
                length_mode=length_mode
            )
            
            word_count = len(markdown.split())
            print(f"Generated words: {word_count}")
            
            # Check if it's in expected range
            from config.settings import LENGTH_RANGES
            min_words, max_words = LENGTH_RANGES[length_mode]
            print(f"Target range: {min_words}-{max_words} words")
            
            if min_words <= word_count <= max_words:
                print(f"✅ SUCCESS: Within target range")
            else:
                print(f"❌ ISSUE: Outside target range")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)
    
    print("\n🎯 Length configuration test completed!")

if __name__ == "__main__":
    asyncio.run(test_length_modes())