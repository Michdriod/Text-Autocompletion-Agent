#!/usr/bin/env python3
"""
Test the refactored Mode 6 with real user examples
"""
import asyncio
import time
from logic.mode_6 import Mode6

async def test_real_examples():
    """Test Mode 6 with actual user examples"""
    
    mode6 = Mode6()
    
    # Test cases from user
    test_cases = [
        {
            "name": "Docker Installation Guide",
            "title": "How to Install and Configure Docker",
            "description": "Complete installation guide for Docker Engine on Windows 11, an end-to-step process for Docker on Windows, Includes Docker Compose installation, user permissions, and basic container deployment.",
            "keywords": "Docker, install, container, Docker Compose",
            "length": "medium",
            "audience": "IT administrators and developers"
        },
        {
            "name": "Employee Onboarding Workflow", 
            "title": "New Employee Onboarding Workflow",
            "description": "We want to document the full onboarding workflow for new hires, including account setup, policy training, system access, and verification. This article should help HR and IT follow a consistent process.",
            "keywords": "onboarding,workflow,HR,IT process,Active Directory,Workday,onboarding,access provisioning",
            "length": "long",
            "audience": "HR staff and IT administrators"
        },
        {
            "name": "Two-Factor Authentication Setup",
            "title": "How to Enable Two-Factor Authentication on Company Accounts", 
            "description": "We want employees to set up 2FA on their work accounts using the Authenticator app. The goal is to improve account security and reduce unauthorized access. Include steps and best practices.",
            "keywords": "Authenticator,security,employee account",
            "length": "medium",
            "audience": "All employees"
        }
    ]
    
    print("🚀 Testing refactored Mode 6 with real examples...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print(f"Title: {test_case['title']}")
        print(f"Length: {test_case['length']}")
        print(f"Keywords: {test_case['keywords']}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            
            # Generate article using new Mode 6
            markdown = await mode6.generate_article(
                title=test_case['title'],
                description=test_case['description'],
                keywords=test_case['keywords'],
                length_mode=test_case['length'],
                audience=test_case['audience']
            )
            
            elapsed = time.time() - start_time
            
            # Count words
            word_count = len(markdown.split())
            
            print(f"✅ Generation successful!")
            print(f"📊 Words: {word_count}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            print(f"\n📄 Generated Article Preview (first 500 chars):")
            print("-" * 40)
            print(markdown[:500] + ("..." if len(markdown) > 500 else ""))
            print("-" * 40)
            
            # Save full article to file
            filename = f"test_output_{i}_{test_case['name'].lower().replace(' ', '_')}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Test Case {i}: {test_case['name']}\n\n")
                f.write(f"**Length:** {test_case['length']}\n")
                f.write(f"**Words:** {word_count}\n")
                f.write(f"**Generation Time:** {elapsed:.2f}s\n\n")
                f.write("---\n\n")
                f.write(markdown)
            
            print(f"💾 Full article saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_real_examples())