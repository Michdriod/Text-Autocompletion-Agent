# Autocomplete handler module that manages text enrichment requests and suggestions.
# Provides endpoints for text completion with dynamic parameters and on-demand generation.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import httpx

from logic.mode_1 import Mode1Logic
from logic.mode_2 import Mode2Logic
from logic.mode_3 import Mode3Logic
from logic.mode_4 import Mode4Logic
from utils.validator import (
    validate_minimum_word_count,
    validate_combined_word_count,
    get_default_min_words,
    validate_output_length,
    trim_output
)

router = APIRouter()

# Define available enrichment modes
class ModeType(str, Enum):
    mode_1 = "mode_1"  # Context-Aware Regenerative Completion
    mode_2 = "mode_2"  # Structured Context Enrichment
    mode_3 = "mode_3"  # Input Refinement
    mode_4 = "mode_4"  # Payload Description Agent

# Request model for text enrichment
class AutocompleteRequest(BaseModel):
    text: Optional[str] = None
    mode: ModeType
    header: Optional[str] = None
    body: Optional[Dict[str, Any]] = None  # For mode_4
    min_input_words: Optional[int] = None
    max_output_length: Optional[Dict[str, Union[str, int]]] = None

# Response model for text enrichment
class AutocompleteResponse(BaseModel):
    completion: str  # Generated text completion
    mode: str  # Mode used for generation

@router.post("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    try:
        min_words = request.min_input_words or get_default_min_words(request.mode)
        if request.mode in [ModeType.mode_2, ModeType.mode_4] and not request.header:
            raise HTTPException(
                status_code=422,
                detail=f"Header is required for {request.mode}."
            )
        if request.mode == ModeType.mode_4:
            if not request.body:
                raise HTTPException(
                    status_code=422,
                    detail="Body is required for Payload Description Agent mode."
                )
            if not validate_combined_word_count(request.header or "", str(request.body), request.mode):
                raise HTTPException(
                    status_code=422,
                    detail=f"Header and body combined must contain at least {min_words} words."
                )
        elif request.mode == ModeType.mode_2:
            if not request.text:
                raise HTTPException(
                    status_code=422,
                    detail="Text input is required for Structured Context Enrichment mode."
                )
            if not validate_combined_word_count(request.header or "", request.text, request.mode):
                raise HTTPException(
                    status_code=422,
                    detail=f"Header and text combined must contain at least {min_words} words."
                )
        elif request.mode == ModeType.mode_1:
            if not request.text:
                raise HTTPException(
                    status_code=422,
                    detail="Text input is required for Context-Aware Regenerative Completion mode."
                )
            if not validate_minimum_word_count(request.text, request.mode, min_words):
                raise HTTPException(
                    status_code=422,
                    detail=f"Please provide at least {min_words} words for Context-Aware Regenerative Completion."
                )
        elif request.mode == ModeType.mode_3:
            if not request.text:
                raise HTTPException(
                    status_code=422,
                    detail="Text input is required for Input Refinement mode."
                )
        completion = None
        if request.mode == ModeType.mode_1:
            mode_logic = Mode1Logic()
            completion = await mode_logic.process(
                text=request.text,
                max_output_length=request.max_output_length
            )
        elif request.mode == ModeType.mode_2:
            mode_logic = Mode2Logic()
            completion = await mode_logic.process(
                text=request.text,
                header=request.header,
                max_output_length=request.max_output_length
            )
        elif request.mode == ModeType.mode_3:
            mode_logic = Mode3Logic()
            completion = await mode_logic.process(
                text=request.text,
                max_output_length=request.max_output_length
            )
        elif request.mode == ModeType.mode_4:
            mode_logic = Mode4Logic()
            completion = await mode_logic.process(
                header=request.header,
                body=request.body,
                max_output_length=request.max_output_length
            )
        if request.max_output_length and not validate_output_length(completion, request.max_output_length):
            completion = trim_output(completion, request.max_output_length)
        return AutocompleteResponse(
            completion=completion,
            mode=request.mode
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

# Health check endpoint
@router.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "modes": {
            "mode_1": "Context-Aware Regenerative Completion",
            "mode_2": "Structured Context Enrichment",
            "mode_3": "Input Refinement",
            "mode_4": "Payload Description Agent"
        },
        "features": {
            "dynamic_min_input_words": True,
            "dynamic_max_output_length": True,
            "on_demand_generation": True,
            "supports_characters_and_words": True,
            "mode_specific_validation": True
        }
    }