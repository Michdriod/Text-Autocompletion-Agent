#!/usr/bin/env python3
"""Debug script to test per_row mode and see actual response structure."""

import asyncio
import sys
import json
from handlers.summarize_document import summarize_document_handler

async def test_per_row():
    """Test per_row mode with debug output."""
    
    print("=" * 80)
    print("Testing PostgreSQL per_row mode")
    print("=" * 80)
    
    # Mock request object
    class MockRequest:
        pass
    
    # Test parameters - ADJUST THESE TO YOUR ACTUAL DATABASE
    test_params = {
        'pg_db': 'your_database_name',  # ← CHANGE THIS
        'pg_table': 'incidents',
        'pg_id_column': 'incident_id',
        'pg_text_column': 'description',
        'pg_context_column': 'title',  # optional
        'pg_id_start': 'INC_05',
        'pg_id_end': 'INC_07',
        'pg_mode': 'per_row',
        'output_format': 'markdown',
        'target_words': 50,  # optional
    }
    
    print("\nTest Parameters:")
    print(json.dumps(test_params, indent=2))
    print("\n" + "=" * 80)
    
    try:
        # Call the handler
        result = await summarize_document_handler(
            request=MockRequest(),
            pg_db=test_params.get('pg_db'),
            pg_table=test_params.get('pg_table'),
            pg_id_column=test_params.get('pg_id_column'),
            pg_text_column=test_params.get('pg_text_column'),
            pg_context_column=test_params.get('pg_context_column'),
            pg_id_start=test_params.get('pg_id_start'),
            pg_id_end=test_params.get('pg_id_end'),
            pg_mode=test_params.get('pg_mode'),
            output_format=test_params.get('output_format'),
            target_words=test_params.get('target_words'),
        )
        
        print("\n✅ SUCCESS! Response structure:")
        print("=" * 80)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 80)
        
        # Detailed analysis
        if 'summaries' in result:
            print(f"\n📊 Found {len(result['summaries'])} summaries")
            for i, item in enumerate(result['summaries']):
                print(f"\n--- Summary {i+1} ---")
                print(f"ID: {item.get('id')}")
                print(f"Has 'result' key: {('result' in item)}")
                if 'result' in item:
                    print(f"Result keys: {list(item['result'].keys())}")
                    if 'markdown_summary' in item['result']:
                        summary = item['result']['markdown_summary']
                        print(f"Summary length: {len(summary)} chars")
                        print(f"Summary preview: {summary[:100]}...")
                    else:
                        print("⚠️ No 'markdown_summary' key in result!")
                        print(f"Available keys: {list(item['result'].keys())}")
                if 'error' in item:
                    print(f"❌ Error: {item['error']}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n⚠️  IMPORTANT: Edit this file and change 'your_database_name' to your actual database name!")
    print("Press Ctrl+C to cancel, or wait 3 seconds to continue...\n")
    
    import time
    time.sleep(3)
    
    asyncio.run(test_per_row())
