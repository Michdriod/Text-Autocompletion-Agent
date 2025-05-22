# Main FastAPI application entry point for the Text Autocompletion Service.
# This service provides multiple modes of text enrichment and completion using the Groq LLM API.


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from handlers.autocomplete import router as autocomplete_router

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Initialize FastAPI application with title
app = FastAPI(title="Multi-Mode Text Enrichment API")

# Configure CORS middleware to allow cross-origin requests
# Note: In production, replace "*" with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the autocomplete router which handles all text enrichment endpoints
app.include_router(autocomplete_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "modes": ["mode_1", "mode_2", "mode_3"]}

if __name__ == "__main__":
    # Run the FastAPI application using uvicorn server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)