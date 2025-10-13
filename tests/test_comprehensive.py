#!/usr/bin/env python3
"""Test both small and large documents to ensure no truncation."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_5 import Mode5

# Small document test
SMALL_DOC = """Digital transformation in banking has revolutionized the financial services industry. Traditional banks have evolved from paper-based systems to sophisticated digital platforms. Mobile banking apps now allow customers to perform complex transactions from anywhere. Artificial intelligence powers fraud detection systems and personalized financial advice. Cloud computing enables scalable infrastructure and real-time processing. Regulatory frameworks like open banking promote innovation while ensuring security. The future of banking lies in seamless integration of digital technologies with human expertise to create superior customer experiences."""

# Medium document that might get chunked
MEDIUM_DOC = SMALL_DOC * 3

async def test_comprehensive():
    """Test both approaches thoroughly."""
    print("Comprehensive Truncation Test")
    print("=" * 50)
    
    mode5 = Mode5()
    
    # Test 1: Small document, direct path
    print(f"\nTest 1: Small document ({len(SMALL_DOC.split())} words), 100 words target")
    print("-" * 40)
    
    result1 = await mode5.process_raw_text(
        text=SMALL_DOC,
        source_name="small_banking_doc",
        target_words=100,
        output_format="plain"
    )
    
    print(f"Summary: {result1['plain_summary']}")
    print(f"Word count: {result1['summary_words']} (target: {result1['meta']['ingest']['resolved_target_words']})")
    print(f"Approach: {result1['meta']['length_enforcement']['approach']}")
    print(f"Ends properly: {'✅' if result1['plain_summary'][-1] in '.!?' else '❌'}")
    
    # Test 2: Medium document, chunked path
    print(f"\n\nTest 2: Medium document ({len(MEDIUM_DOC.split())} words), 150 words target")
    print("-" * 40)
    
    result2 = await mode5.process_raw_text(
        text=MEDIUM_DOC,
        source_name="medium_banking_doc",
        target_words=150,
        output_format="plain"
    )
    
    print(f"Summary: {result2['plain_summary']}")
    print(f"Word count: {result2['summary_words']} (target: {result2['meta']['ingest']['resolved_target_words']})")
    print(f"Approach: {result2['meta']['length_enforcement']['approach']}")
    print(f"Ends properly: {'✅' if result2['plain_summary'][-1] in '.!?' else '❌'}")
    
    # Test 3: Large document, auto 20% mode
    print(f"\n\nTest 3: Large document ({len(MEDIUM_DOC.split())} words), auto 20% target")
    print("-" * 40)
    
    result3 = await mode5.process_raw_text(
        text=MEDIUM_DOC,
        source_name="large_banking_doc",
        target_words=None,  # Should use 20% rule
        output_format="plain"
    )
    
    print(f"Summary: {result3['plain_summary']}")
    print(f"Word count: {result3['summary_words']} (target: {result3['meta']['ingest']['resolved_target_words']})")
    print(f"Target mode: {result3['meta']['ingest']['target_mode']}")
    print(f"Approach: {result3['meta']['length_enforcement']['approach']}")
    print(f"Ends properly: {'✅' if result3['plain_summary'][-1] in '.!?' else '❌'}")

if __name__ == "__main__":
    asyncio.run(test_comprehensive())