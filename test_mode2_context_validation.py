#!/usr/bin/env python3
"""
Test script for Mode2 context validation functionality.
Tests both aligned and misaligned content scenarios.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_2 import Mode2

async def test_aligned_content():
    """Test Mode2 with content that aligns with header context."""
    print("=== Testing Aligned Content ===")
    
    mode2 = Mode2()
    
    # Test case: Professional email header with email-related content
    header = "Professional Email Rewrite"
    text = "hey can you send me the report? need it asap"
    
    try:
        result = await mode2.process(
            text=text,
            header=header,
            output_format="markdown"
        )
        print(f"✅ SUCCESS - Aligned content processed")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Output: {result[:200]}{'...' if len(result) > 200 else ''}")
        print()
        return True
    except Exception as e:
        print(f"❌ FAILED - Aligned content should have worked: {e}")
        return False

async def test_misaligned_content():
    """Test Mode2 with content that doesn't align with header context."""
    print("=== Testing Misaligned Content ===")
    
    mode2 = Mode2()
    
    # Test case: Professional email header with completely unrelated content
    header = "Professional Email Rewrite"
    text = "The mitochondria is the powerhouse of the cell and provides energy through ATP synthesis."
    
    try:
        result = await mode2.process(
            text=text,
            header=header,
            output_format="markdown"
        )
        print(f"❌ FAILED - Misaligned content should have been rejected but got: {result[:200]}{'...' if len(result) > 200 else ''}")
        return False
    except ValueError as e:
        print(f"✅ SUCCESS - Misaligned content properly rejected")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Error: {e}")
        print()
        return True
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return False

async def test_borderline_content():
    """Test Mode2 with content that might be borderline aligned."""
    print("=== Testing Borderline Content ===")
    
    mode2 = Mode2()
    
    # Test case: Technical documentation header with slightly related content
    header = "Technical Documentation Enhancement"
    text = "Our API is good and fast"
    
    try:
        result = await mode2.process(
            text=text,
            header=header,
            output_format="markdown"
        )
        print(f"✅ SUCCESS - Borderline content processed (generous validation)")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Output: {result[:200]}{'...' if len(result) > 200 else ''}")
        print()
        return True
    except ValueError as e:
        print(f"⚠️  BORDERLINE - Content rejected (strict validation): {e}")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print()
        return True  # Both outcomes are acceptable for borderline cases
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return False

async def main():
    """Run all context validation tests."""
    print("Testing Mode2 Context Validation Implementation\n")
    
    tests = [
        test_aligned_content,
        test_misaligned_content, 
        test_borderline_content
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print(f"=== Test Results ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! Mode2 context validation is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)