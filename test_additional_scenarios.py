#!/usr/bin/env python3
"""
Additional edge case scenarios for Mode2 context validation.
Tests challenging and borderline cases to ensure robust validation.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_2 import Mode2

# Additional challenging test scenarios
EDGE_CASE_SCENARIOS = {
    "borderline_cases": {
        "description": "Content that might be borderline between valid and invalid",
        "tests": [
            {
                "context": "assets",
                "header": "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details.",
                "inputs": [
                    "server",  # Very minimal but technically valid
                    "computer broken",  # Minimal but asset-related
                    "network equipment needs fixing",  # Valid but informal
                    "IT stuff",  # Too vague
                    "hardware",  # Very generic
                ]
            },
            {
                "context": "tickets", 
                "header": "Enhance the given ticket description for an ITSM solution. Make it more descriptive, correct grammatical errors, and improve clarity, technical accuracy, and professional tone for IT support tickets.",
                "inputs": [
                    "help",  # Too minimal
                    "broken",  # Too vague
                    "not working",  # Vague but could be ticket-related
                    "urgent fix needed",  # Vague but urgent ticket-like
                    "system issue",  # Valid but minimal
                ]
            }
        ]
    },
    
    "mixed_content": {
        "description": "Content that mixes valid and invalid elements",
        "tests": [
            {
                "context": "incidents",
                "header": "Enhance the given incident description for IT service management. Make it more descriptive, correct grammatical errors, and improve incident reporting, urgency classification, and resolution documentation.", 
                "inputs": [
                    "John reported server down",  # Name + valid content
                    "Database crashed at 3pm today",  # Valid with timestamp
                    "Email from Sarah about login issues",  # Name + valid content
                    "Meeting about network problems",  # Valid but not incident
                    "Database server crash affecting 500 users",  # Clearly valid
                ]
            }
        ]
    },
    
    "technical_but_wrong_domain": {
        "description": "Technical content but for wrong domain",
        "tests": [
            {
                "context": "assets",
                "header": "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details.",
                "inputs": [
                    "cardiac monitor ECG machine",  # Medical equipment
                    "industrial conveyor belt system",  # Manufacturing equipment  
                    "automotive engine diagnostics tool",  # Automotive equipment
                    "laboratory microscope analysis",  # Lab equipment
                    "kitchen refrigeration unit",  # Kitchen equipment
                ]
            }
        ]
    },
    
    "numbers_and_codes": {
        "description": "Numeric inputs, codes, and identifiers",
        "tests": [
            {
                "context": "tickets",
                "header": "Enhance the given ticket description for an ITSM solution. Make it more descriptive, correct grammatical errors, and improve clarity, technical accuracy, and professional tone for IT support tickets.",
                "inputs": [
                    "12345",  # Just numbers
                    "INC-2024-001",  # Incident code
                    "Error 404",  # Error code
                    "Windows 10 update failed",  # OS version + issue
                    "Server 192.168.1.100 not responding",  # IP address + issue
                    "REQ-001: laptop replacement",  # Request code + description
                ]
            }
        ]
    }
}

async def test_edge_case_scenario(scenario_name, scenario_data):
    """Test a specific edge case scenario."""
    print(f"\n{'='*80}")
    print(f"EDGE CASE SCENARIO: {scenario_name.upper().replace('_', ' ')}")
    print(f"Description: {scenario_data['description']}")
    print(f"{'='*80}")
    
    mode2 = Mode2()
    all_results = []
    
    for test_case in scenario_data['tests']:
        context = test_case['context']
        header = test_case['header']
        
        print(f"\n--- Testing Context: {context.upper()} ---")
        
        for i, input_text in enumerate(test_case['inputs']):
            print(f"\nTest {i+1}: '{input_text}'")
            
            try:
                result = await mode2.process(
                    text=input_text,
                    header=header,
                    max_output_length={"type": "words", "value": 100},
                    output_format="markdown"
                )
                
                print(f"✅ PROCESSED: {result[:100]}{'...' if len(result) > 100 else ''}")
                all_results.append(("processed", input_text, context))
                
            except ValueError as e:
                print(f"❌ REJECTED: {e}")
                all_results.append(("rejected", input_text, context))
                
            except Exception as e:
                print(f"🔥 ERROR: {e}")
                all_results.append(("error", input_text, context))
    
    # Summary for this scenario
    processed = sum(1 for r in all_results if r[0] == "processed")
    rejected = sum(1 for r in all_results if r[0] == "rejected") 
    errors = sum(1 for r in all_results if r[0] == "error")
    
    print(f"\n--- Scenario Summary ---")
    print(f"Processed: {processed}")
    print(f"Rejected: {rejected}")
    print(f"Errors: {errors}")
    print(f"Total: {len(all_results)}")
    
    return all_results

async def test_all_edge_cases():
    """Test all edge case scenarios."""
    print("COMPREHENSIVE EDGE CASE TESTING FOR MODE2 CONTEXT VALIDATION")
    print("Testing challenging and borderline scenarios")
    
    all_results = []
    
    for scenario_name, scenario_data in EDGE_CASE_SCENARIOS.items():
        results = await test_edge_case_scenario(scenario_name, scenario_data)
        all_results.extend(results)
    
    # Overall analysis
    print(f"\n{'='*80}")
    print("OVERALL EDGE CASE RESULTS")
    print(f"{'='*80}")
    
    processed = sum(1 for r in all_results if r[0] == "processed")
    rejected = sum(1 for r in all_results if r[0] == "rejected")
    errors = sum(1 for r in all_results if r[0] == "error")
    
    print(f"Total tests: {len(all_results)}")
    print(f"Processed: {processed} ({processed/len(all_results)*100:.1f}%)")
    print(f"Rejected: {rejected} ({rejected/len(all_results)*100:.1f}%)")
    print(f"Errors: {errors} ({errors/len(all_results)*100:.1f}%)")
    
    if errors == 0:
        print(f"\n🎉 ALL EDGE CASES HANDLED WITHOUT ERRORS!")
        print(f"The system shows good robustness with {processed} successful processes and {rejected} appropriate rejections.")
    else:
        print(f"\n⚠️ {errors} errors detected. Review the error cases above.")
    
    return errors == 0

async def main():
    """Main test runner."""
    success = await test_all_edge_cases()
    return success

if __name__ == "__main__":
    print("Additional Edge Case Testing for Mode2 Context Validation")
    print("This tests borderline cases, mixed content, and challenging scenarios\n")
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)