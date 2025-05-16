from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

app = FastAPI(title="Text Autocompletion API")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutocompleteRequest(BaseModel):
    text: str
    max_tokens: int = 20  # Default to 20 tokens for completion
    mode: str = "simple"  # simple or enriched

class AutocompleteResponse(BaseModel):
    completion: str

@app.post("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    try:
        # Set up the API request to Groq
        url = "https://api.groq.com/openai/v1/chat/completions"
        # url = "https://api.groq.com/openai/v1/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Adjust system prompt based on the mode
        if request.mode == "enriched":
            system_message = (
                "You are an AI text enrichment assistant. Continue the user's text with high-quality, "
                "contextually relevant content that matches their writing style and adds value. "
                "Focus on enhancing their message with relevant details, vivid descriptions, "
                "or logical next steps in the argument or narrative."
            )
        else:  # simple mode
            system_message = (
                "You are an AI text completion assistant. Continue the user's text with a natural, "
                "contextually appropriate completion. Match their writing style and tone."
            )
        
        # Prepare data for the request
        data = {
            "model": "llama3-70b-8192",  # llama-3.1-8b-instant, llama-3.3-70b-versatile, llama3-70b-8192, mistral-saba-24b, 
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": f"user text: {request.text} \n continuation:"
                }
            ],
            "max_tokens": request.max_tokens,
            "temperature": 0.3,
            "top_p": 0.95,
            "stop": ["\n", ".", "?", "!"]  # Stop at these tokens to keep suggestions short
        }
        
        # Send request to Groq API
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, 
                                   detail=f"Groq API error: {response.text}")
            
            # Extract the completion text
            result = response.json()
            # print(result)
            completion_text = result["choices"][0]["message"]["content"].strip()
            
            # Remove any leading text that might be repeated from the input
            if completion_text.startswith(request.text):
                completion_text = completion_text[len(request.text):].strip()
            
            return AutocompleteResponse(completion=completion_text)
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Error communicating with Groq API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)