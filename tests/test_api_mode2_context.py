#!/usr/bin/env python3
"""
End-to-end test for Mode2 context validation via API.
Tests the complete flow from HTTP request to response.
"""

import asyncio
import aiohttp
import json
import sys

API_BASE_URL = "http://localhost:8000"

async def test_api_aligned_content():
    """Test Mode2 API with aligned content."""
    payload = {
        "text": "hey can you send me the report? need it asap",
        "header": "Professional Email Rewrite",
        "mode": "mode_2",
        "output_format": "markdown"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE_URL}/autocomplete", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ API Aligned Content Test PASSED")
                    print(f"Response: {result['completion'][:150]}...")
                    return True
                else:
                    print(f"❌ API Aligned Content Test FAILED: Status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API Aligned Content Test FAILED: {e}")
            return False

async def test_api_misaligned_content():
    """Test Mode2 API with misaligned content that should be rejected."""
    payload = {
        "text": "The mitochondria is the powerhouse of the cell and provides energy through ATP synthesis.",
        "header": "Professional Email Rewrite", 
        "mode": "mode_2",
        "output_format": "markdown"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE_URL}/autocomplete", json=payload) as response:
                if response.status == 400:  # Should return 400 for context mismatch
                    result = await response.json()
                    print("✅ API Misaligned Content Test PASSED")
                    print(f"Error message: {result['detail']}")
                    return True
                else:
                    print(f"❌ API Misaligned Content Test FAILED: Expected 400, got {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        print(f"Unexpected success: {result['completion'][:150]}...")
                    return False
        except Exception as e:
            print(f"❌ API Misaligned Content Test FAILED: {e}")
            return False

async def test_server_connection():
    """Test if server is running and accessible."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    print("✅ Server connection test PASSED")
                    return True
                else:
                    print(f"❌ Server connection test FAILED: Status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Server connection test FAILED: {e}")
            print("Make sure the server is running with: python main.py")
            return False

async def main():
    """Run all API tests."""
    print("Testing Mode2 Context Validation via API\n")
    
    # Test server connection first
    if not await test_server_connection():
        print("\n⚠️ Server is not accessible. Please start the server first:")
        print("   python main.py")
        return False
    
    tests = [
        test_api_aligned_content,
        test_api_misaligned_content
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
        print()  # Add spacing between tests
    
    print("=== API Test Results ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All API tests passed! Mode2 context validation is working end-to-end.")
        return True
    else:
        print("⚠️ Some API tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)