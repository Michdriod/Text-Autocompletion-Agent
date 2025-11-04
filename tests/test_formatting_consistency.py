#!/usr/bin/env python3

"""Test formatting consistency with incident report."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

async def test_incident_formatting():
    """Test formatting with your incident report."""
    print("🧪 Testing Incident Report Formatting")
    print("=" * 60)
    
    mode5 = Mode5()
    
    # Your incident report
    incident_text = """A critical CRM outage occurred at 10:30 AM due to a failed database connection after a security patch deployment. This prevented 40 employees from processing vital sales. The service was restored at 12:45 PM following a patch rollback."""
    
    print(f"📄 Input ({len(incident_text.split())} words):")
    print(f"   {incident_text}")
    
    print(f"\n🎯 Expected Output (flowing paragraph):")
    print(f"   A critical CRM outage occurred at 10:30 AM due to a failed database connection after a security patch deployment. This prevented 40 employees from processing vital sales. The service was restored at 12:45 PM following a patch rollback.")
    
    print(f"\n🔍 Testing Multiple Runs for Consistency:")
    print("-" * 60)
    
    for i in range(3):
        print(f"\n📝 Test Run {i+1}:")
        
        try:
            result = await mode5.process_raw_text(
                text=incident_text,
                source_name=f"incident_test_{i}",
                target_words=None,  # Use adaptive
                output_format="markdown"
            )
            
            output = result['markdown_summary']
            word_count = result['summary_words']
            
            print(f"   Result ({word_count} words): {output}")
            
            # Check if formatted as single paragraph or multiple lines
            if '\n' in output.strip() and output.count('\n') > 1:
                print(f"   📊 Format: ❌ Multi-line/separated sentences")
            elif output.count('.') >= 2 and '\n' not in output.strip():
                print(f"   📊 Format: ✅ Single flowing paragraph")
            else:
                print(f"   📊 Format: 🤔 Other structure")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n💡 Issue Analysis:")
    print(f"   • Problem: AI inconsistently formats short summaries")
    print(f"   • Sometimes: Separate sentences on different lines")  
    print(f"   • Sometimes: Flowing paragraph (preferred)")
    print(f"   • Need: Explicit paragraph formatting for short summaries")

if __name__ == "__main__":
    asyncio.run(test_incident_formatting())