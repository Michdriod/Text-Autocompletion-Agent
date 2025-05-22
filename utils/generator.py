# Groq LLM Generator utility for text generation.
# Provides a wrapper for making API calls to the Groq language model
# with support for various generation parameters and error handling.


import httpx
import os
from fastapi import HTTPException

class GroqGenerator:
    # Wrapper class for interacting with the Groq LLM API.
    # Handles API calls, parameter management, and response processing.    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
    
    async def generate(self, system_prompt: str, user_message: str, max_tokens: int, 
                      temperature: float, top_p: float) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(self.base_url, json=data, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Groq API error: {response.text}"
                )
            
            result = response.json()
            completion_text = result["choices"][0]["message"]["content"].strip()
            
            # Remove user message if it appears at the start of completion
            if completion_text.startswith(user_message):
                completion_text = completion_text[len(user_message):].strip()
                
            return completion_text