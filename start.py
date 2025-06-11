#!/usr/bin/env python3
# Startup script for the Multi-Mode Text Enrichment System
# Handles initialization, health checks, and graceful startup

import asyncio
import sys
import os
import signal
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging_config import setup_logging
from utils.generator import get_generator
from utils.cache import get_cache

async def check_dependencies():
    """Check if all required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    try:
        # Check Groq API connectivity
        generator = get_generator()
        api_healthy = await generator.health_check()
        
        if api_healthy:
            print("✅ Groq API connection: OK")
        else:
            print("❌ Groq API connection: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Groq API connection: FAILED - {e}")
        return False
    
    # Check cache
    try:
        cache = get_cache()
        cache.clear()  # Test cache operations
        print("✅ Cache system: OK")
    except Exception as e:
        print(f"❌ Cache system: FAILED - {e}")
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = ["logs", "data", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directory created: {directory}")

def validate_environment():
    """Validate environment variables and configuration."""
    print("🔧 Validating environment...")
    
    config = get_config()
    
    # Check required environment variables
    if not config.groq_api_key:
        print("❌ GROQ_API_KEY environment variable not set")
        return False
    
    print("✅ Environment variables: OK")
    
    # Validate configuration
    if config.api_port < 1 or config.api_port > 65535:
        print(f"❌ Invalid API port: {config.api_port}")
        return False
    
    print("✅ Configuration: OK")
    return True

async def startup_sequence():
    """Execute the complete startup sequence."""
    print("🚀 Starting Multi-Mode Text Enrichment System v2.1.0")
    print("=" * 60)
    
    # Step 1: Create directories
    create_directories()
    
    # Step 2: Validate environment
    if not validate_environment():
        print("❌ Environment validation failed")
        return False
    
    # Step 3: Setup logging
    config = get_config()
    logger = setup_logging(log_file="logs/app.log")
    print("✅ Logging system initialized")
    
    # Step 4: Check dependencies
    if not await check_dependencies():
        print("❌ Dependency check failed")
        return False
    
    print("=" * 60)
    print("✅ All startup checks passed!")
    print(f"🌐 Starting server on {config.api_host}:{config.api_port}")
    print(f"📊 Cache enabled: {config.cache_enabled}")
    print(f"📝 Log level: {config.log_level}")
    print("=" * 60)
    
    return True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    
    # Cleanup operations
    try:
        from utils.cache import get_cache
        cache = get_cache()
        cache.clear()
        print("✅ Cache cleared")
    except:
        pass
    
    print("👋 Goodbye!")
    sys.exit(0)

async def main():
    """Main startup function."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run startup sequence
    if not await startup_sequence():
        print("❌ Startup failed")
        sys.exit(1)
    
    # Import and start the FastAPI application
    try:
        import uvicorn
        from main import app
        
        config = get_config()
        
        # Start the server
        uvicorn.run(
            app,
            host=config.api_host,
            port=config.api_port,
            reload=config.api_reload,
            log_level=config.log_level.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the startup sequence
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
