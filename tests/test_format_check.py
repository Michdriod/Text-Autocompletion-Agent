#!/usr/bin/env python3

"""Simple test to check Mode 5 output format."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

test_text = """API Integration: The Digital Handshake Powering Modern Connectivity

In today's interconnected digital world, few technologies are as essential yet as invisible as API integration. Behind every seamless online experience—ordering food from an app, tracking a package in real time, or signing in with Google—there's an Application Programming Interface, or API, quietly orchestrating the exchange of data between systems."""

async def check_output_format():
    """Check the output format of Mode 5."""
    print("🔍 Checking Mode 5 Output Format")
    print("=" * 50)
    
    mode5 = Mode5()
    
    result = await mode5.process_raw_text(
        text=test_text,
        source_name="test_format_check",
        target_words=50,
        output_format="markdown"
    )
    
    print("Result keys:", list(result.keys()))
    print("\nResult structure:")
    for key, value in result.items():
        print(f"  {key}: {type(value)} - {str(value)[:100]}...")
        
    return result

if __name__ == "__main__":
    asyncio.run(check_output_format())