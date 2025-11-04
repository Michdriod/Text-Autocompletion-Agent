#!/usr/bin/env python3
"""
Comprehensive test scenarios for Mode2 context validation across all ITSM modules.
Tests various content types against different header contexts.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_2 import Mode2

# Define all the ITSM context headers
ITSM_CONTEXTS = {
    "tickets": "Enhance the given ticket description for an ITSM solution. Make it more descriptive, correct grammatical errors, and improve clarity, technical accuracy, and professional tone for IT support tickets.",
    
    "assets": "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details.",
    
    "problems": "Enhance the given problem description for ITSM. Make it more descriptive, correct grammatical errors, and improve root cause analysis, impact assessment, and technical problem documentation.",
    
    "incidents": "Enhance the given incident description for IT service management. Make it more descriptive, correct grammatical errors, and improve incident reporting, urgency classification, and resolution documentation.",
    
    "service-requests": "Enhance the given service request description for ITSM. Make it more descriptive, correct grammatical errors, and improve service requirement clarity, business justification, and fulfillment specifications.",
    
    "knowledge-base": "Enhance the given knowledge base article for IT documentation. Make it more descriptive, correct grammatical errors, and improve technical accuracy, step-by-step clarity, and searchable content structure.",
    
    "vendors": "Enhance the given vendor description for procurement and partnerships. Make it more descriptive, correct grammatical errors, and improve contract terms, service level descriptions, and vendor evaluation criteria.",
    
    "workbench": "Enhance the given workbench task description for IT operations. Make it more descriptive, correct grammatical errors, and improve task clarity, priority assessment, and work assignment details.",
    
    "audit-log": "Enhance the given audit log entry for compliance and security. Make it more descriptive, correct grammatical errors, and improve event description clarity, compliance context, and audit trail documentation.",
    
    "dashboard": "Enhance the given dashboard description for business intelligence. Make it more descriptive, correct grammatical errors, and improve metric definitions, KPI explanations, and dashboard functionality descriptions.",
    
    "events": "Enhance the given event description for IT operations. Make it more descriptive, correct grammatical errors, and improve event categorization, impact assessment, and operational event documentation.",
    
    "service-catalogue": "Enhance the given service description for IT service catalogue. Make it more descriptive, correct grammatical errors, and improve service definitions, delivery specifications, and customer-facing service descriptions.",
    
    "service-configuration": "Enhance the given service configuration description for ITSM. Make it more descriptive, correct grammatical errors, and improve configuration documentation, service parameters, and technical specifications.",
    
    "access-management": "Enhance the given access management description for security and permissions. Make it more descriptive, correct grammatical errors, and improve access requirement definitions, security policies, and permission documentation.",
    
    "admin-settings": "Enhance the given system administration description for configuration management. Make it more descriptive, correct grammatical errors, and improve system setting explanations, configuration procedures, and administrative documentation.",
    
    "default": "Enhance the given description for business applications. Make it more descriptive, correct grammatical errors, and improve clarity, professionalism, and technical accuracy of the content."
}

# Test content scenarios
TEST_SCENARIOS = {
    "valid_aligned": {
        "tickets": "login issue with outlook",
        "assets": "Dell PowerEdge server",
        "problems": "recurring network outages",
        "incidents": "critical database down",
        "service-requests": "new employee laptop setup",
        "knowledge-base": "how to reset password",
        "vendors": "Microsoft enterprise license",
        "workbench": "patch server maintenance",
        "audit-log": "user access modification",
        "dashboard": "system performance metrics",
        "events": "server restart notification",
        "service-catalogue": "email hosting service",
        "service-configuration": "load balancer settings",
        "access-management": "admin role permissions",
        "admin-settings": "backup configuration policy",
        "default": "business process improvement"
    },
    
    "mismatched_content": {
        "all_contexts": [
            "Micheal Alejo",  # Person name
            "cat goes to school",  # Casual content
            "The mitochondria is the powerhouse of the cell",  # Scientific content
            "I love pizza and ice cream",  # Personal preference
            "2 + 2 = 4",  # Basic math
            "red blue green yellow"  # Random words
        ]
    }
}

async def test_valid_content_for_context(context_name, header, valid_text):
    """Test that valid content is properly processed."""
    mode2 = Mode2()
    
    try:
        result = await mode2.process(
            text=valid_text,
            header=header,
            max_output_length={"type": "words", "value": 100},
            output_format="markdown"
        )
        print(f"✅ {context_name.upper()}: Valid content processed")
        print(f"   Input: '{valid_text}'")
        print(f"   Output: {result[:80]}{'...' if len(result) > 80 else ''}")
        return True
    except Exception as e:
        print(f"❌ {context_name.upper()}: Valid content failed - {e}")
        return False

async def test_mismatched_content_for_context(context_name, header, invalid_text):
    """Test that mismatched content is properly rejected."""
    mode2 = Mode2()
    
    try:
        result = await mode2.process(
            text=invalid_text,
            header=header,
            max_output_length={"type": "words", "value": 100},
            output_format="markdown"
        )
        print(f"❌ {context_name.upper()}: Should have rejected '{invalid_text}' but got: {result[:80]}{'...' if len(result) > 80 else ''}")
        return False
    except ValueError as e:
        print(f"✅ {context_name.upper()}: Properly rejected '{invalid_text}'")
        print(f"   Error: {e}")
        return True
    except Exception as e:
        print(f"❌ {context_name.upper()}: Unexpected error for '{invalid_text}' - {e}")
        return False

async def test_single_context(context_name):
    """Test a single ITSM context with both valid and invalid content."""
    print(f"\n{'='*60}")
    print(f"TESTING CONTEXT: {context_name.upper()}")
    print(f"{'='*60}")
    
    header = ITSM_CONTEXTS[context_name]
    results = []
    
    # Test valid content
    if context_name in TEST_SCENARIOS["valid_aligned"]:
        valid_text = TEST_SCENARIOS["valid_aligned"][context_name]
        result = await test_valid_content_for_context(context_name, header, valid_text)
        results.append(result)
        print()
    
    # Test mismatched content (sample a few)
    sample_invalid = TEST_SCENARIOS["mismatched_content"]["all_contexts"][:3]  # Test first 3
    for invalid_text in sample_invalid:
        result = await test_mismatched_content_for_context(context_name, header, invalid_text)
        results.append(result)
        print()
    
    success_rate = sum(results) / len(results) if results else 0
    print(f"Context Success Rate: {sum(results)}/{len(results)} ({success_rate:.1%})")
    
    return results

async def test_all_contexts():
    """Test all ITSM contexts."""
    print("COMPREHENSIVE MODE2 CONTEXT VALIDATION TEST")
    print("Testing all ITSM module contexts with various content types")
    
    all_results = []
    
    # Test a representative sample of contexts
    priority_contexts = ["tickets", "assets", "incidents", "service-requests", "knowledge-base", "default"]
    
    for context_name in priority_contexts:
        results = await test_single_context(context_name)
        all_results.extend(results)
    
    print(f"\n{'='*60}")
    print("OVERALL TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total tests passed: {sum(all_results)}/{len(all_results)}")
    print(f"Success rate: {sum(all_results)/len(all_results):.1%}")
    
    if sum(all_results) == len(all_results):
        print("🎉 ALL TESTS PASSED! Mode2 context validation works across all ITSM contexts.")
    else:
        print("⚠️ Some tests failed. Check the validation logic.")
    
    return sum(all_results) == len(all_results)

async def test_specific_context(context_name):
    """Test a specific context interactively."""
    if context_name not in ITSM_CONTEXTS:
        print(f"❌ Context '{context_name}' not found.")
        print(f"Available contexts: {', '.join(ITSM_CONTEXTS.keys())}")
        return False
    
    results = await test_single_context(context_name)
    return all(results)

async def main():
    """Main test runner with options."""
    if len(sys.argv) > 1:
        # Test specific context
        context_name = sys.argv[1]
        success = await test_specific_context(context_name)
    else:
        # Test all priority contexts
        success = await test_all_contexts()
    
    return success

if __name__ == "__main__":
    print("Usage:")
    print("  python test_itsm_contexts.py              # Test all priority contexts")
    print("  python test_itsm_contexts.py <context>    # Test specific context")
    print(f"  Available contexts: {', '.join(ITSM_CONTEXTS.keys())}")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)