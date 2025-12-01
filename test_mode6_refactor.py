#!/usr/bin/env python3
"""
Test script for refactored Mode 6 - single LLM call knowledge article generation.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.mode_6 import Mode6

async def test_mode6_refactor():
    """Test the refactored Mode 6 functionality."""
    
    print("🧪 Testing Refactored Mode 6 - Knowledge Article Generator")
    print("=" * 70)
    
    mode6 = Mode6()
    
    # Test case: How-to guide
    test_cases = [
        {
            "title": "How to Reset Employee Password",
            "description": "Step-by-step guide for IT administrators to reset user passwords in Active Directory when employees forget their credentials or are locked out",
            "keywords": ["password", "reset", "Active Directory", "IT", "administrator"],
            "length_mode": "medium",
            "audience": "IT Administrator"
        },
        {
            "title": "Troubleshooting Network Connection Issues",
            "description": "Common network connectivity problems in the office environment and how to diagnose and resolve them",
            "keywords": ["network", "connectivity", "troubleshooting", "diagnosis"],
            "length_mode": "short"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['title']}")
        print(f"   Length: {test_case['length_mode']}")
        print(f"   Keywords: {', '.join(test_case['keywords'])}")
        print("-" * 50)
        
        try:
            # Generate article
            markdown = await mode6.generate_article(
                title=test_case["title"],
                description=test_case["description"],
                keywords=test_case["keywords"],
                length_mode=test_case["length_mode"],
                audience=test_case.get("audience")
            )
            
            # Validate output
            lines = markdown.split('\n')
            
            # Check for level-1 heading
            has_h1 = any(line.startswith('# ') for line in lines)
            
            # Check for level-2 headings
            h2_count = sum(1 for line in lines if line.startswith('## '))
            
            # Check for Steps section with numbered list
            has_steps_section = False
            has_numbered_list = False
            
            for i, line in enumerate(lines):
                if 'steps' in line.lower() and line.startswith('##'):
                    has_steps_section = True
                    # Look for numbered list in next 10 lines
                    for j in range(i+1, min(i+11, len(lines))):
                        if lines[j].strip().startswith(('1.', '2.', '3.')):
                            has_numbered_list = True
                            break
            
            word_count = len(markdown.split())
            
            print(f"✅ Generated Successfully!")
            print(f"   Word Count: {word_count}")
            print(f"   Has H1 Header: {'✅' if has_h1 else '❌'}")
            print(f"   H2 Sections: {h2_count}")
            print(f"   Has Steps Section: {'✅' if has_steps_section else '❌'}")
            print(f"   Has Numbered List: {'✅' if has_numbered_list else '❌'}")
            
            # Show first few lines as preview
            print(f"\n📖 Preview (first 5 lines):")
            for line in lines[:5]:
                if line.strip():
                    print(f"   {line}")
            
            # Validation summary
            validations_passed = sum([has_h1, h2_count >= 1, has_steps_section, has_numbered_list])
            print(f"\n🎯 Validations: {validations_passed}/4 passed")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("🏁 Mode 6 refactor testing complete!")

if __name__ == "__main__":
    asyncio.run(test_mode6_refactor())