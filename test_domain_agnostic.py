#!/usr/bin/env python3
"""
Test domain-agnostic validation for Mode2.
Ensures the system works for any domain while maintaining strict header alignment.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_2 import Mode2

# Test scenarios for domain-agnostic validation
DOMAIN_AGNOSTIC_TESTS = [
    {
        "description": "Medical domain with medical content (should ACCEPT)",
        "header": "Enhance the given medical equipment description for healthcare management. Make it more descriptive, correct grammatical errors, and improve technical specifications and documentation details.",
        "text": "cardiac monitor ECG machine",
        "expected": "accept"
    },
    {
        "description": "Medical domain with IT content (should REJECT)",
        "header": "Enhance the given medical equipment description for healthcare management. Make it more descriptive, correct grammatical errors, and improve technical specifications and documentation details.",
        "text": "Dell PowerEdge server",
        "expected": "reject"
    },
    {
        "description": "IT domain with IT content (should ACCEPT)", 
        "header": "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details.",
        "text": "Dell PowerEdge server",
        "expected": "accept"
    },
    {
        "description": "IT domain with medical content (should REJECT)",
        "header": "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details.", 
        "text": "cardiac monitor ECG machine",
        "expected": "reject"
    },
    {
        "description": "Legal domain with legal content (should ACCEPT)",
        "header": "Enhance the given legal document description for compliance management. Make it more descriptive, correct grammatical errors, and improve legal accuracy and documentation clarity.",
        "text": "employment contract agreement",
        "expected": "accept"
    },
    {
        "description": "Legal domain with casual content (should REJECT)",
        "header": "Enhance the given legal document description for compliance management. Make it more descriptive, correct grammatical errors, and improve legal accuracy and documentation clarity.",
        "text": "cat goes to school",
        "expected": "reject"
    },
    {
        "description": "Marketing domain with business content (should ACCEPT)",
        "header": "Enhance the given marketing copy for product promotion. Make it more descriptive, correct grammatical errors, and improve persuasive messaging and customer engagement.",
        "text": "new smartphone features",
        "expected": "accept"
    },
    {
        "description": "Marketing domain with scientific content (should REJECT)",
        "header": "Enhance the given marketing copy for product promotion. Make it more descriptive, correct grammatical errors, and improve persuasive messaging and customer engagement.",
        "text": "mitochondrial ATP synthesis process",
        "expected": "reject"
    },
    {
        "description": "Cross-domain but contextually relevant (borderline case)",
        "header": "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details.",
        "text": "network security appliance for medical records",
        "expected": "accept"  # IT equipment for medical use should be accepted for IT context
    }
]

async def test_domain_agnostic_validation():
    """Test that validation works correctly across different domains."""
    print("DOMAIN-AGNOSTIC MODE2 VALIDATION TEST")
    print("Testing that the system works for any domain while maintaining header alignment")
    print("="*80)
    
    mode2 = Mode2()
    results = []
    
    for i, test_case in enumerate(DOMAIN_AGNOSTIC_TESTS):
        print(f"\nTest {i+1}: {test_case['description']}")
        print(f"Header: {test_case['header'][:100]}...")
        print(f"Text: '{test_case['text']}'")
        print(f"Expected: {test_case['expected'].upper()}")
        
        try:
            result = await mode2.process(
                text=test_case['text'],
                header=test_case['header'],
                max_output_length={"type": "words", "value": 100},
                output_format="markdown"
            )
            
            actual = "accept"
            print(f"✅ PROCESSED: {result[:80]}{'...' if len(result) > 80 else ''}")
            
        except ValueError as e:
            actual = "reject"
            print(f"❌ REJECTED: {e}")
        except Exception as e:
            actual = "error"
            print(f"🔥 ERROR: {e}")
        
        # Check if result matches expectation
        if actual == test_case['expected']:
            print(f"✅ CORRECT: Got {actual} as expected")
            results.append(True)
        else:
            print(f"❌ INCORRECT: Expected {test_case['expected']} but got {actual}")
            results.append(False)
        
        print("-" * 40)
    
    # Summary
    correct = sum(results)
    total = len(results)
    
    print(f"\n{'='*80}")
    print("DOMAIN-AGNOSTIC VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"Tests passed: {correct}/{total} ({correct/total*100:.1f}%)")
    
    if correct == total:
        print("🎉 ALL TESTS PASSED! Domain-agnostic validation is working correctly.")
        print("The system properly aligns content with header context regardless of domain.")
    else:
        failed = total - correct
        print(f"⚠️ {failed} tests failed. The validation logic may need adjustment.")
    
    return correct == total

async def main():
    """Run the domain-agnostic validation test."""
    success = await test_domain_agnostic_validation()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)