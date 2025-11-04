#!/usr/bin/env python3

"""Test Mode 5 title preservation and unified summary prefix removal."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

# Test with the exact problematic text from user
test_text_with_title = """API Integration: The Digital Handshake Powering Modern Connectivity

In today's interconnected digital world, few technologies are as essential yet as invisible as API integration. Behind every seamless online experience—ordering food from an app, tracking a package in real time, or signing in with Google—there's an Application Programming Interface, or API, quietly orchestrating the exchange of data between systems. APIs are the unseen bridges of the digital age, enabling businesses and users to connect across platforms effortlessly.

At its core, API integration refers to the process of linking two or more software applications through their APIs so they can communicate, share data, and perform coordinated functions. Think of it as a digital handshake between systems—an agreement that defines how information should be exchanged, what rules govern that exchange, and what each side can expect in return. Without APIs, each software system would remain isolated, forcing developers to build direct, complex connections for every new feature or service. With APIs, systems can plug into one another easily, creating an ecosystem of reusable and extendable digital capabilities."""

async def test_title_preservation():
    """Test title preservation and prefix removal."""
    print("🧪 Testing Title Preservation & Prefix Removal")
    print("=" * 60)
    
    mode5 = Mode5()
    
    # Test 1: Short summary to see title behavior
    print("\n📝 Test 1: Title Preservation (50 words)")
    print("-" * 50)
    
    result = await mode5.process_raw_text(
        text=test_text_with_title,
        source_name="title_test",
        target_words=50,
        output_format="markdown"
    )
    
    summary_text = result['markdown_summary']
    print(f"Target: 50 words")
    print(f"Actual: {result['summary_words']} words")
    print(f"\nRaw Summary Output:")
    print(repr(summary_text))
    print(f"\nFormatted Summary Output:")
    print(summary_text)
    
    # Check for issues
    issues = []
    if "Unified Summary:" in summary_text:
        issues.append("❌ Found 'Unified Summary:' prefix")
    if "Summary:" in summary_text and not summary_text.startswith("API Integration:"):
        issues.append("❌ Found 'Summary:' prefix")
    if not summary_text.startswith("API Integration: The Digital Handshake Powering Modern Connectivity"):
        issues.append("❌ Title not preserved exactly or prefix added")
    
    if issues:
        print(f"\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"\n✅ SUCCESS: Title preserved correctly, no unwanted prefixes!")
    
    # Test 2: Test the cleaning function directly
    print(f"\n📝 Test 2: Direct Cleaning Function Test")
    print("-" * 50)
    
    test_bad_outputs = [
        "Unified Summary: API Integration for Modern Connectivity\nAPI integration is...",
        "Summary: API Integration for Digital Systems\nIn today's world...",
        "Unified Summary of API Integration: The Digital Handshake\nThis document...",
        "API Integration: The Digital Handshake Powering Modern Connectivity\nAPI integration is..."  # This should be left alone
    ]
    
    for i, bad_output in enumerate(test_bad_outputs, 1):
        cleaned = mode5._clean_summary_output(bad_output)
        print(f"Test {i}:")
        print(f"  Before: {repr(bad_output[:80])}...")
        print(f"  After:  {repr(cleaned[:80])}...")
        if i < len(test_bad_outputs):
            print()

if __name__ == "__main__":
    asyncio.run(test_title_preservation())