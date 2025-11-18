# Autocomplete handler module that manages text enrichment requests and suggestions.
# Provides endpoints for text completion with dynamic parameters and on-demand generation.

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import httpx

from logic.mode_1 import Mode1
from logic.mode_2 import Mode2
from logic.mode_3 import Mode3
from logic.mode_4 import Mode4

from utils.validator import get_default_min_words, validate_minimum_word_count, validate_combined_word_count
router = APIRouter()


def validate_min_words_mode1(text: str, min_words: int) -> None:
    """Validate that text meets minimum word requirement for Mode 1."""
    if not text or not text.strip():
        return  # Empty text is handled elsewhere
    
    word_count = len(text.strip().split())
    if word_count < min_words:
        raise HTTPException(
            status_code=400,
            detail=f"Input text must have at least {min_words} words. Current: {word_count} words."
        )


def get_effective_min_words_mode1(request_min_words: Optional[int]) -> int:
    """Get the effective minimum words for Mode 1 - use request value or default to 2."""
    if request_min_words is not None and request_min_words >= 0:
        return request_min_words
    return 2  # Default minimum for Mode 1


# Define available enrichment modes
class ModeType(str, Enum):
    mode_1 = "mode_1"  # Intelligent Text Autocomplete
    mode_2 = "mode_2"  # Structured Context Enrichment
    mode_3 = "mode_3"  # Input Refinement
    mode_4 = "mode_4"  # Description Agent
    mode_5 = "mode_5"  # Document Summarization (handled by /summarize-document)


# Request model for text enrichment
class AutocompleteRequest(BaseModel):
    text: Optional[str] = None
    mode: ModeType
    header: Optional[str] = None
    body: Optional[Union[str, Dict[str, Any]]] = None 
    # body: Optional[Dict[str, Any]] = None  # For mode_4
    min_input_words: Optional[int] = None
    max_output_length: Optional[Dict[str, Union[str, int]]] = None
    output_format: Optional[str] = "markdown"  # New field for output format


# Response model for text enrichment
class AutocompleteResponse(BaseModel):
    completion: str  # Generated text completion
    mode: str  # Mode used for generation
    # New fields for multi-format support
    markdown_summary: Optional[str] = None
    plain_summary: Optional[str] = None  
    html_summary: Optional[str] = None
    output_format: Optional[str] = None
    min_words_used: Optional[int] = None  # For Mode 1 feedback

@router.post("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    try:
        min_words = request.min_input_words or get_default_min_words(request.mode)

        # Validation for Mode 2 and Mode 4
        if request.mode in [ModeType.mode_2, ModeType.mode_4] and not request.header:
            raise HTTPException(
                status_code=422,
                detail=f"Header is required for {request.mode}."
            )

        # Validation for Mode 4
        if request.mode == ModeType.mode_4:
            if not request.body:
                raise HTTPException(
                    status_code=422,
                    detail="Body is required for Description Agent mode."
                )

        # Validation for Mode 1
        if request.mode == ModeType.mode_1:
            if not request.text:
                raise HTTPException(
                    status_code=422,
                    detail="Text input is required for Intelligent Text Autocomplete mode."
                )
            if not validate_minimum_word_count(request.text, request.mode, min_words):
                raise HTTPException(
                    status_code=422,
                    detail=f"Please provide at least {min_words} words for Intelligent Text Autocomplete."
                )

        # Validation for Mode 3
        elif request.mode == ModeType.mode_3:
            if not request.text:
                raise HTTPException(
                    status_code=422,
                    detail="Text input is required for Input Refinement mode."
                )

        # Validation for Mode 5
        # Mode 5 is now handled by /summarize-document endpoint (file upload)
        elif request.mode == ModeType.mode_5:
            raise HTTPException(
                status_code=422,
                detail="For Mode 5 (Document Summarization), use the /summarize-document endpoint and upload a file."
            )

        # Process the request based on the mode
        completion = None
        effective_min_words_mode1 = None
        
        if request.mode == ModeType.mode_1:
            # Get effective minimum words (frontend value or default of 2)
            effective_min_words_mode1 = get_effective_min_words_mode1(request.min_input_words)
            
            # Validate minimum words for Mode 1
            validate_min_words_mode1(request.text, effective_min_words_mode1)
            
            mode_logic = Mode1()
            completion = await mode_logic.process(
                text=request.text,
                max_output_length=request.max_output_length
            )
        elif request.mode == ModeType.mode_2:
            mode_logic = Mode2()
            completion = await mode_logic.process(
                text=request.text,
                header=request.header,
                max_output_length=request.max_output_length,
                output_format=request.output_format or "markdown"
            )
            
            # Handle output formatting for Mode 2 if requested format is not default
            if request.output_format and request.output_format != "markdown":
                from services.formatter import format_output
                from services.finalize import FinalizedSummary
                
                # Create a FinalizedSummary-like object for the formatter
                finalized = FinalizedSummary(
                    text=completion,
                    summary_words=len(completion.split()),
                    target_words=request.max_output_length.get("value", len(completion.split())) if request.max_output_length else len(completion.split()),
                    achieved_ratio=1.0
                )
                
                # Format the output
                formatted_result = format_output(finalized, None, request.output_format)
                
                # Return formatted response
                response_data = {
                    "completion": completion,  # Keep original for backward compatibility
                    "mode": request.mode,
                    "output_format": request.output_format
                }
                
                # Add format-specific fields
                if request.output_format == "html":
                    response_data["html_summary"] = formatted_result.get("html_summary", completion)
                    response_data["completion"] = formatted_result.get("html_summary", completion)
                elif request.output_format == "plain":
                    response_data["plain_summary"] = formatted_result.get("plain_summary", completion)
                    response_data["completion"] = formatted_result.get("plain_summary", completion)
                elif request.output_format == "both":
                    response_data["markdown_summary"] = formatted_result.get("markdown_summary", completion)
                    response_data["plain_summary"] = formatted_result.get("plain_summary", completion)
                elif request.output_format == "all":
                    response_data["markdown_summary"] = formatted_result.get("markdown_summary", completion)
                    response_data["plain_summary"] = formatted_result.get("plain_summary", completion)
                    response_data["html_summary"] = formatted_result.get("html_summary", completion)
                
                return AutocompleteResponse(**response_data)
        elif request.mode == ModeType.mode_3:
            mode_logic = Mode3()
            completion = await mode_logic.process(
                text=request.text,
                max_output_length=request.max_output_length
            )
        elif request.mode == ModeType.mode_4:
            mode_logic = Mode4()
            completion = await mode_logic.process(
                header=request.header,
                body=request.body,
                max_output_length=request.max_output_length
            )

        # Return standard response (Mode 2 with formatting handled above)
        return AutocompleteResponse(
            completion=completion,
            mode=request.mode,
            output_format=request.output_format if request.output_format != "markdown" else None,
            min_words_used=effective_min_words_mode1 if request.mode == ModeType.mode_1 else None
        )
    except ValueError as e:
        # Handle context validation errors from Mode2
        raise HTTPException(
            status_code=400,
            detail=str(e)
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
            "mode_1": "Intelligent Text Autocomplete",
            "mode_2": "Structured Context Enrichment",
            "mode_3": "Input Refinement",
            "mode_4": "Description Agent",
            "mode_5": "Document Summarization"
        },
        "features": {
            "dynamic_min_input_words": True,
            "dynamic_max_output_length": True,
            "on_demand_generation": True,
            "supports_characters_and_words": True,
            "mode_specific_validation": True
        }
    }