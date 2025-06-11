# Main FastAPI application entry point for the Multi-Mode Text Enrichment Service.
# This service provides four modes of text enrichment and completion using the Groq LLM API
# with dynamic parameter support and on-demand generation.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

from handlers.autocomplete import router as autocomplete_router
from config import get_config
from utils.logging_config import setup_logging, RequestLoggingMiddleware
from utils.exceptions import TextEnrichmentError

# Load environment variables from .env file
load_dotenv()

# Initialize configuration
config = get_config()

# Setup logging
logger = setup_logging(log_file="logs/app.log")

# Initialize FastAPI application with enhanced metadata
app = FastAPI(
    title="Multi-Mode Text Enrichment API",
    description="Advanced text enrichment service with 4 modes: Context-Aware Completion, Structured Enrichment, Input Refinement, and Description Generation",
    version="2.1.0"
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=config.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for custom exceptions
@app.exception_handler(TextEnrichmentError)
async def text_enrichment_exception_handler(request, exc: TextEnrichmentError):
    logger.error(f"Text enrichment error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": exc.__class__.__name__}
    )

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "InternalServerError"}
    )

# Include the autocomplete router which handles all text enrichment endpoints
app.include_router(autocomplete_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multi-Mode Text Enrichment API",
        "version": "2.1.0",
        "status": "operational",
        "endpoints": {
            "autocomplete": "/autocomplete",
            "health": "/health",
            "docs": "/docs",
            "cache_stats": "/cache/stats"
        },
        "modes": [
            {
                "id": "mode_1",
                "name": "Context-Aware Completion",
                "description": "Intelligent text continuation based on context",
                "min_words": config.mode_1_min_words
            },
            {
                "id": "mode_2",
                "name": "Structured Enrichment",
                "description": "Text enhancement using header/topic context",
                "min_words": config.mode_2_min_words
            },
            {
                "id": "mode_3",
                "name": "Input Refinement",
                "description": "Polish messy or incomplete text",
                "min_words": config.mode_3_min_words
            },
            {
                "id": "mode_4",
                "name": "Description Generator",
                "description": "Generate descriptions from structured data",
                "min_words": config.mode_4_min_words
            }
        ],
        "features": [
            "Dynamic minimum input word count",
            "Dynamic maximum output length (characters or words)",
            "On-demand generation with caching",
            "Fresh suggestions on each request",
            "Comprehensive error handling",
            "Performance monitoring"
        ],
        "configuration": {
            "cache_enabled": config.cache_enabled,
            "max_input_length": config.max_input_length,
            "max_output_tokens": config.max_output_tokens
        }
    }

# Add cache statistics endpoint
@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    from utils.cache import get_cache
    cache = get_cache()
    stats = cache.get_stats()
    return {
        "cache_enabled": config.cache_enabled,
        "cache_ttl": config.cache_ttl,
        **stats
    }

if __name__ == "__main__":
    # Run the FastAPI application using uvicorn server
    import uvicorn
    logger.info(f"Starting Multi-Mode Text Enrichment API v2.1.0")
    logger.info(f"Cache enabled: {config.cache_enabled}")
    logger.info(f"Log level: {config.log_level}")

    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        reload=config.api_reload,
        log_level=config.log_level.lower()
    )