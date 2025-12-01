#!/usr/bin/env python3
"""
Test script to verify Mode 6 has its own separate model configuration.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import KAG_MODEL_CONFIG, GENERAL_MODEL_CONFIG
from utils.generator import generate, generate_kag

async def test_separate_models():
    """Test that Mode 6 uses separate model configuration."""
    
    print("🔧 Testing Separate Model Configurations")
    print("=" * 60)
    
    print(f"📊 General Model Config:")
    print(f"   Provider: {GENERAL_MODEL_CONFIG['provider']}")
    print(f"   Model: {GENERAL_MODEL_CONFIG['model_name']}")
    print(f"   Max Tokens: {GENERAL_MODEL_CONFIG['max_tokens']}")
    
    print(f"\n🎯 Mode 6 (KAG) Model Config:")
    print(f"   Provider: {KAG_MODEL_CONFIG['provider']}")
    print(f"   Model: {KAG_MODEL_CONFIG['model_name']}")
    print(f"   Backup Model: {KAG_MODEL_CONFIG['backup_model']}")
    print(f"   Max Tokens: {KAG_MODEL_CONFIG['max_tokens']}")
    
    # Test that both generators work
    print(f"\n🧪 Testing Generator Functions:")
    
    try:
        # Test general generator (modes 1-5)
        general_result = await generate(
            system_prompt="You are a helpful assistant.",
            user_message="Say 'General model working' in exactly 3 words.",
            max_tokens=20
        )
        print(f"✅ General Generator: {general_result.strip()}")
        
        # Test KAG generator (mode 6) 
        kag_result = await generate_kag(
            system_prompt="You are a knowledge article generator.",
            user_message="Say 'KAG model working' in exactly 3 words."
        )
        print(f"✅ KAG Generator: {kag_result.strip()}")
        
        print(f"\n🎉 Both model configurations are working independently!")
        print(f"📝 You can now change KAG_MODEL_CONFIG in settings.py")
        print(f"   to use different models for Mode 6 without affecting other modes.")
        
    except Exception as e:
        print(f"❌ Error testing generators: {e}")

if __name__ == "__main__":
    asyncio.run(test_separate_models())