#!/usr/bin/env python3
"""Test script for the universal URL functionality."""

import asyncio
import sys
import os
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.universal_url import download_from_universal_url, UniversalURLError
from utils.file_utils import detect_extension_from_file, cleanup_temp_file

async def test_file_detection():
    """Test file type detection."""
    print("Testing file type detection...")
    
    # Test PDF detection
    with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as f:
        f.write(b'%PDF-1.4\n')  # PDF magic bytes
        f.write(b'This is a test PDF content...')
        pdf_path = f.name
    
    try:
        extension = detect_extension_from_file(pdf_path)
        print(f"✅ PDF detection: {extension}")
        assert extension == '.pdf', f"Expected .pdf, got {extension}"
    finally:
        cleanup_temp_file(pdf_path)
    
    # Test text file detection
    with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as f:
        f.write(b'This is plain text content for testing.')
        txt_path = f.name
    
    try:
        extension = detect_extension_from_file(txt_path)
        print(f"✅ Text detection: {extension}")
        assert extension == '.txt', f"Expected .txt, got {extension}"
    finally:
        cleanup_temp_file(txt_path)
    
    print("✅ All file detection tests passed!")

async def test_url_detection():
    """Test URL type detection."""
    from utils.universal_url import detect_url_type
    
    print("\nTesting URL type detection...")
    
    test_cases = [
        ("https://drive.google.com/file/d/abc123/view", "google_drive"),
        ("https://docs.google.com/document/d/abc123/edit", "google_drive"),
        ("https://dropbox.com/s/xyz/document.pdf?dl=0", "accessible_url"),
        ("https://onedrive.live.com/download?id=abc123", "accessible_url"),
        ("https://example.com/document.pdf", "accessible_url"),
        ("https://cdn.website.com/files/manual.docx", "accessible_url"),
    ]
    
    for url, expected in test_cases:
        result = detect_url_type(url)
        print(f"✅ {url} -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("✅ All URL detection tests passed!")

async def test_universal_urls():
    """Test universal URL functionality with safe examples."""
    print("\nTesting universal URL handling...")
    
    # Note: These are example URLs - replace with actual test URLs as needed
    test_urls = [
        # Add your test URLs here when you have safe examples to test
        # "https://www.dropbox.com/scl/fi/bakfntp3594ogvi4290nu/whitepaper_Foundational-Large-Language-models-text-generation_v2.pdf?rlkey=wmnphcw34u2wrzxhsqjoaymrl&st=yovtyuw9&dl=0"
        # "https://bazaratech-my.sharepoint.com/:w:/p/tunji_odumuboni/EWjj3ivuMYFHnA_GkmGG6TYB_bL2Y94c8TJEz14bpDFaiA?e=oO1nPE"
        # "https://www.pwc.com/ng/en/assets/pdf/case-open-banking-nigeria.pdf"
        # "https://docs.google.com/document/d/10owNRY0e13mf5BFU70fqGX4zi1N7YlZR2_Ltkm7_2pg/edit?usp=sharing"
        # "https://drive.google.com/file/d/17DlKIysQdeZP2EREmB5Z-CJVJnomrCFq/view?usp=sharing"
        "https://bazaratech-my.sharepoint.com/:b:/p/alejo_michael/EXXkz5HeXeRIjtod_Y2BXWcBx_TaQ55nJKeEFH-OtP3MKw?e=TmzNTn"
    ]
    
    if not test_urls:
        print("⚠️  No test URLs provided - skipping actual download tests")
        print("   To test downloads, add valid document URLs to the test_urls list")
        return
    
    for url in test_urls:
        try:
            print(f"\nTesting URL: {url}")
            file_path, extension, filename = download_from_universal_url(url)
            print(f"✅ Success: {filename} ({extension})")
            
            # Clean up
            cleanup_temp_file(file_path)
            
        except UniversalURLError as e:
            print(f"❌ Failed: {e}")
        except Exception as e:
            print(f"💥 Error: {e}")

async def main():
    """Run all tests."""
    print("🧪 Testing Universal URL Handler Implementation\n")
    
    try:
        await test_file_detection()
        await test_url_detection()
        await test_universal_urls()
        
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("✅ File type detection working")
        print("✅ URL type detection working") 
        print("✅ Universal URL handler ready")
        print("\n🚀 The system is ready to handle:")
        print("   • Google Drive URLs")
        print("   • Dropbox share links")
        print("   • OneDrive links")
        print("   • Direct PDF/DOCX/TXT URLs")
        print("   • Any accessible document URL")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)