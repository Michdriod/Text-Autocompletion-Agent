# Autocomplete handler module that manages text enrichment requests and suggestions.
# Provides endpoints for text completion, suggestion retrieval, and suggestion management.


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
import httpx

from logic.mode_1 import Mode1Logic
from logic.mode_2 import Mode2Logic
from logic.mode_3 import Mode3Logic
from utils.validator import validate_minimum_word_count

router = APIRouter()

# Define available enrichment modes
class ModeType(str, Enum):
    mode_1 = "mode_1"  # Context-Aware Completion
    mode_2 = "mode_2"  # Structured Context Enrichment
    mode_3 = "mode_3"  # Flexible Input Refinement

# Request model for text enrichment
class AutocompleteRequest(BaseModel):
    text: str  # Input text to be enriched
    mode: ModeType  # Selected enrichment mode
    header: Optional[str] = None  # Required for mode_2 (topic/context header)
    regenerate: Optional[bool] = False  # Whether to generate alternative completion
    max_tokens: Optional[int] = 50  # Maximum tokens in completion

# Response model for text enrichment
class AutocompleteResponse(BaseModel):
    completion: str  # Generated text completion
    mode: str  # Mode used for generation
    suggestion_count: Optional[int] = None  # Number of stored suggestions

# In-memory storage for suggestions (consider using Redis or database in production)
suggestion_storage: Dict[str, List[str]] = {}

def get_storage_key(mode: ModeType, text: str, header: Optional[str] = None) -> str:
    if mode == ModeType.mode_2 and header:
        return f"{mode}_{hash(text + header)}"
    return f"{mode}_{hash(text)}"

@router.post("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    try:
        # Validate minimum word count requirement
        if not validate_minimum_word_count(request.text):
            raise HTTPException(
                status_code=422,
                detail="Please provide at least 23 words before generating enrichment."
            )
        
        # Validate mode-specific requirements
        if request.mode == ModeType.mode_2 and not request.header:
            raise HTTPException(
                status_code=422,
                detail="Header is required for mode_2 (Structured Context Enrichment)."
            )
        
        # Mode 3 doesn't support regeneration
        if request.mode == ModeType.mode_3 and request.regenerate:
            raise HTTPException(
                status_code=422,
                detail="Mode 3 (Flexible Input Refinement) does not support regeneration."
            )
        
        # Process request using appropriate mode logic
        completion = None
        if request.mode == ModeType.mode_1:
            mode_logic = Mode1Logic()
            completion = await mode_logic.process(
                text=request.text,
                max_tokens=request.max_tokens or 50,
                regenerate=request.regenerate or False
            )
        elif request.mode == ModeType.mode_2:
            mode_logic = Mode2Logic()
            completion = await mode_logic.process(
                text=request.text,
                header=request.header,
                max_tokens=request.max_tokens or 50,
                regenerate=request.regenerate or False
            )
        elif request.mode == ModeType.mode_3:
            mode_logic = Mode3Logic()
            completion = await mode_logic.process(
                text=request.text,
                max_tokens=request.max_tokens or 50
            )
        
        # Store suggestions for modes 1 and 2 (up to 5 per input)
        suggestion_count = None
        if request.mode in [ModeType.mode_1, ModeType.mode_2]:
            storage_key = get_storage_key(request.mode, request.text, request.header)
            
            if storage_key not in suggestion_storage:
                suggestion_storage[storage_key] = []
            
            suggestion_storage[storage_key].append(completion)
            if len(suggestion_storage[storage_key]) > 5:
                suggestion_storage[storage_key] = suggestion_storage[storage_key][-5:]
            
            suggestion_count = len(suggestion_storage[storage_key])
        
        return AutocompleteResponse(
            completion=completion,
            mode=request.mode,
            suggestion_count=suggestion_count
        )
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Error communicating with Groq API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/suggestions/{mode}")
async def get_suggestions(mode: ModeType, text: str, header: Optional[str] = None):
    storage_key = get_storage_key(mode, text, header)
    suggestions = suggestion_storage.get(storage_key, [])
    
    return {
        "mode": mode,
        "suggestions": suggestions,
        "count": len(suggestions)
    }

@router.delete("/suggestions/{mode}")
async def clear_suggestions(mode: ModeType, text: str, header: Optional[str] = None):
    storage_key = get_storage_key(mode, text, header)
    if storage_key in suggestion_storage:
        del suggestion_storage[storage_key]
    
    return {"message": "Suggestions cleared successfully"}