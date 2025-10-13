#!/usr/bin/env python3
"""Test the improved Mode 5 summarization with the user's example."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_5 import Mode5

# User's test content
TEST_CONTENT = """The Evolution of Modern Banking and the Digital Transformation of Financial Services

The global banking industry has evolved dramatically over recent decades, driven by technology, customer expectations, and new regulations. Traditional banks once known for paperwork and queues have transformed into digital ecosystems offering seamless and secure financial experiences.

The digital banking journey began in the late 1990s with online portals that enabled customers to view balances and transfer funds. The rise of smartphones in the 2000s accelerated this shift, as mobile apps made banking accessible from anywhere. In emerging markets, mobile money platforms like M-Pesa in Kenya brought millions of unbanked individuals into the financial system.

Today, digital transformation extends beyond mobile transactions. Artificial intelligence (AI), data analytics, and machine learning are central to risk management, fraud detection, and personalized services. AI-powered chatbots now handle routine queries, while predictive algorithms strengthen cybersecurity and enhance decision-making. Cloud computing has also enabled banks to deploy scalable, secure systems and collaborate with fintech startups to deliver innovative products.

Regulatory frameworks such as the EU's General Data Protection Regulation (GDPR) and open banking initiatives promote data transparency and consumer trust. In developing regions like Nigeria and India, digital banking drives financial inclusion by expanding access to credit, savings, and payments despite challenges such as limited digital literacy and infrastructure.

Emerging trends like decentralized finance (DeFi), central bank digital currencies (CBDCs), and environmental, social, and governance (ESG) initiatives are shaping the next phase of banking. The future belongs to institutions that balance innovation, security, and customer trust. Digital transformation is no longer optional—it is the foundation for a more inclusive, intelligent, and sustainable financial ecosystem."""

async def test_summarization():
    """Test the new summarization approach."""
    print("Testing New Mode 5 Summarization")
    print("=" * 50)
    
    mode5 = Mode5()
    
    # Test 1: Small document with user-specified 100 words
    print("\nTest 1: Small document, 100 words target")
    print("-" * 40)
    
    result = await mode5.process_raw_text(
        text=TEST_CONTENT,
        source_name="test_banking_article",
        target_words=100,
        output_format="plain"
    )
    
    print(f"Summary: {result['plain_summary']}")
    print(f"Actual word count: {result['summary_words']}")
    print(f"Target was: {result['meta']['ingest']['resolved_target_words']}")
    print(f"Approach: {result['meta']['length_enforcement']['approach']}")
    
    # Test 2: Small document with default 100 words (no target specified)
    print("\n\nTest 2: Small document, default target")
    print("-" * 40)
    
    result2 = await mode5.process_raw_text(
        text=TEST_CONTENT,
        source_name="test_banking_article",
        target_words=None,
        output_format="plain"
    )
    
    print(f"Summary: {result2['plain_summary']}")
    print(f"Actual word count: {result2['summary_words']}")
    print(f"Target was: {result2['meta']['ingest']['resolved_target_words']}")
    print(f"Approach: {result2['meta']['length_enforcement']['approach']}")
    
    # Test 3: Test with larger document (>500 words) to test chunking
    large_content = TEST_CONTENT * 3  # Make it >500 words
    print(f"\n\nTest 3: Large document ({len(large_content.split())} words), 20% auto target")
    print("-" * 40)
    
    result3 = await mode5.process_raw_text(
        text=large_content,
        source_name="test_large_banking_article",
        target_words=None,
        output_format="plain"
    )
    
    print(f"Summary: {result3['plain_summary']}")
    print(f"Actual word count: {result3['summary_words']}")
    print(f"Target was: {result3['meta']['ingest']['resolved_target_words']}")
    print(f"Approach: {result3['meta']['length_enforcement']['approach']}")
    print(f"Target mode: {result3['meta']['ingest']['target_mode']}")

if __name__ == "__main__":
    asyncio.run(test_summarization())