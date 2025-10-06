# Main FastAPI application entry point for the Multi-Mode Text Enrichment Service.
# This service provides four modes of text enrichment and completion using the Groq LLM API
# with dynamic parameter support and on-demand generation.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from handlers.autocomplete import router as autocomplete_router
from handlers.summarize_document import router as summarize_document_router

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Initialize FastAPI application with enhanced metadata
app = FastAPI(
    title="Multi-Mode Text Enrichment API",
    description="Advanced text enrichment service with 4 modes: Context-Aware Completion, Structured Enrichment, Input Refinement, and Description Generation",
    version="2.0.0"
)

# Configure CORS middleware to allow cross-origin requests
# Note: In production, replace "*" with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the autocomplete router and summarize document router
app.include_router(autocomplete_router)
app.include_router(summarize_document_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multi-Mode Text Enrichment API",
        "version": "2.0.0",
        "endpoints": {
            "autocomplete": "/autocomplete",
            "health": "/health",
            "docs": "/docs"
        },
        "modes": [
            {
                "id": "mode_1",
                "name": "Context-Aware Completion",
                "description": "Intelligent text continuation based on context"
            },
            {
                "id": "mode_2", 
                "name": "Structured Enrichment",
                "description": "Text enhancement using header/topic context"
            },
            {
                "id": "mode_3",
                "name": "Input Refinement", 
                "description": "Polish messy or incomplete text"
            },
            {
                "id": "mode_4",
                "name": "Description Generator",
                "description": "Generate descriptions from structured data"
            },
            {
                "id": "mode_5",
                "name": "Document Summarization",
                "description": "Generate summary from structured data"
            },{
                "id": "mode_6",
                "name": "Document Development",
                "description": "Develop documents from user input"
            }
        ],
        "features": [
            "Dynamic minimum input word count",
            "Dynamic maximum output length (characters or words)",
            "On-demand generation (no pre-saving)",
            "Fresh suggestions on each request"
        ]
    }

if __name__ == "__main__":
    # Run the FastAPI application using uvicorn server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)