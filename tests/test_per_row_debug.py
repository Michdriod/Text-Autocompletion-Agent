#!/usr/bin/env python3
"""
Test the specific scenario from the user's payload.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_2 import Mode2

async def test_name_scenario():
    """Test the name scenario."""
    print("=== Testing Name Scenario (Should Reject) ===")
    
    mode2 = Mode2()
    
    # Name scenario
    header = "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details."
    text = "Micheal Alejo"
    
    try:
        result = await mode2.process(
            text=text,
            header=header,
            max_output_length={"type": "words", "value": 100},
            output_format="markdown"
        )
        print(f"❌ FAILED - Should have been rejected but got:")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Output: {result}")
        return False
    except ValueError as e:
        print(f"✅ SUCCESS - Properly rejected the mismatched content")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Error: {e}")
        return True
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return False

async def test_casual_content_scenario():
    """Test casual content that doesn't match technical context."""
    print("\n=== Testing Casual Content Scenario (Should Reject) ===")
    
    mode2 = Mode2()
    
    # Casual content scenario
    header = "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details."
    text = "cat goes to school"
    
    try:
        result = await mode2.process(
            text=text,
            header=header,
            max_output_length={"type": "words", "value": 100},
            output_format="markdown"
        )
        print(f"❌ FAILED - Should have been rejected but got:")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Output: {result}")
        return False
    except ValueError as e:
        print(f"✅ SUCCESS - Properly rejected the mismatched content")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Error: {e}")
        return True
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return False

async def test_similar_valid_content():
    """Test with content that should be accepted."""
    print("\n=== Testing Valid IT Asset Content ===")
    
    mode2 = Mode2()
    
    # Valid content for the same header
    header = "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details."
    text = "Dell server rack unit"
    
    try:
        result = await mode2.process(
            text=text,
            header=header,
            max_output_length={"type": "words", "value": 100},
            output_format="markdown"
        )
        print(f"✅ SUCCESS - Valid content processed")
        print(f"Header: {header}")
        print(f"Input: {text}")
        print(f"Output: {result[:200]}{'...' if len(result) > 200 else ''}")
        return True
    except Exception as e:
        print(f"❌ FAILED - Valid content should have worked: {e}")
        return False

async def main():
    """Run the specific test scenarios."""
    print("Testing Mode2 Context Validation - Multiple Scenarios\n")
    
    tests = [
        test_name_scenario,
        test_casual_content_scenario,
        test_similar_valid_content
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print(f"\n=== Test Results ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! The validation now properly handles name vs. technical content.")
        return True
    else:
        print("⚠️ Some tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
