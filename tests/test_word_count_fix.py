#!/usr/bin/env python3

"""Test the word count prefix removal fix."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

# Your Banking as a Service text
baas_text = """Banking as a Service (BaaS) integrates regulated financial services into non-bank businesses' products through APIs. This model democratizes access to financial services, allowing companies to embed banking functionalities like accounts, payments, and lending into their applications. BaaS simplifies product creation, driving innovation and expanding financial inclusion through secure data exchange."""

async def test_word_count_prefix_fix():
    """Test the fix for word count prefixes like '42 word range:'."""
    print("🧪 Testing Word Count Prefix Removal")
    print("=" * 60)
    
    mode5 = Mode5()
    
    # Test with exactly 50 words target
    print("\n📝 Testing with 50-word target")
    print("-" * 50)
    
    result = await mode5.process_raw_text(
        text=baas_text,
        source_name="baas_test",
        target_words=50,
        output_format="markdown"
    )
    
    summary_text = result['markdown_summary']
    print(f"Target: 50 words")
    print(f"Actual: {result['summary_words']} words")
    
    print(f"\n📄 Summary Output:")
    print("'" + summary_text + "'")
    
    # Check for word count prefixes
    print(f"\n🔍 Prefix Check:")
    
    # Check for various word count prefix patterns
    unwanted_patterns = [
        "word range:",
        "word target:",
        "word summary:",
        "50 word",
        "42 word", 
        "Here's a summary",
        "Here is a summary",
        "Summary:",
        "Unified Summary:"
    ]
    
    issues_found = []
    for pattern in unwanted_patterns:
        if pattern.lower() in summary_text.lower():
            issues_found.append(pattern)
    
    if issues_found:
        print(f"❌ Found unwanted prefixes/patterns: {issues_found}")
    else:
        print("✅ No unwanted word count prefixes found!")
        
    # Check that it starts directly with content
    if summary_text.startswith("Banking as a Service"):
        print("✅ Starts directly with content")
    elif summary_text.startswith("**Banking"):
        print("✅ Starts directly with content (bold formatting)")
    else:
        print(f"⚠️  Unexpected start: {summary_text[:50]}...")
    
    print(f"\n🎯 Result: {'✅ PERFECT!' if not issues_found else '❌ Needs fixing'}")

if __name__ == "__main__":
    asyncio.run(test_word_count_prefix_fix())