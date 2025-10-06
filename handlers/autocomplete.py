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
from logic.mode_6 import Mode6
# from utils.validator import (
#     validate_minimum_word_count,
#     validate_combined_word_count,
#     get_default_min_words,
#     validate_output_length,
#     trim_output
# )
from utils.validator import get_default_min_words, validate_minimum_word_count, validate_combined_word_count
router = APIRouter()

# Define available enrichment modes
class ModeType(str, Enum):
    mode_1 = "mode_1"  # Context-Aware Regenerative Completion
    mode_2 = "mode_2"  # Structured Context Enrichment
    mode_3 = "mode_3"  # Input Refinement
    mode_4 = "mode_4"  # Description Agent
    mode_5 = "mode_5"  # Document Summarization (handled by /summarize-document)
    mode_6 = "mode_6"  # Document Development

# Request model for text enrichment
class AutocompleteRequest(BaseModel):
    text: Optional[str] = None
    mode: ModeType
    header: Optional[str] = None
    body: Optional[Union[str, Dict[str, Any]]] = None 
    # body: Optional[Dict[str, Any]] = None  # For mode_4
    min_input_words: Optional[int] = None
    max_output_length: Optional[Dict[str, Union[str, int]]] = None
    # Mode 5 optional controls
    summary_style: Optional[str] = None  # 'brief' | 'balanced' | 'detailed'
    layered: Optional[bool] = False

# Response model for text enrichment
class AutocompleteResponse(BaseModel):
    completion: str  # Generated text completion
    mode: str  # Mode used for generation

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

        # Validation for Mode 6
        if request.mode == ModeType.mode_6:
            if not request.header:
                raise HTTPException(
                    status_code=422,
                    detail="Header is required for Document Development mode."
                )
            if not request.body or not isinstance(request.body, str):
                raise HTTPException(
                    status_code=422,
                    detail="Body (description) is required for Document Development mode and must be a string."
                )
            if not validate_combined_word_count(request.header, request.body, request.mode):
                raise HTTPException(
                    status_code=422,
                    detail=f"Header and body combined must contain at least {min_words} words."
                )

        # Validation for Mode 1
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
        if request.mode == ModeType.mode_1:
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
                max_output_length=request.max_output_length
            )
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
        elif request.mode == ModeType.mode_6:
            mode_logic = Mode6()
            completion = await mode_logic.process(
                header=request.header,
                body=request.body,
                max_output_length=request.max_output_length
            )

        # Validate and trim output if necessary
        # if request.max_output_length and not validate_output_length(completion, request.max_output_length):
        #     completion = trim_output(completion, request.max_output_length)

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



# async def autocomplete(request: AutocompleteRequest):
#     try:
#         min_words = request.min_input_words or get_default_min_words(request.mode)
#         if request.mode in [ModeType.mode_2, ModeType.mode_4] and not request.header:
#             raise HTTPException(
#                 status_code=422,
#                 detail=f"Header is required for {request.mode}."
#             )
#         if request.mode == ModeType.mode_4:
#             if not request.body:
#                 raise HTTPException(
#                     status_code=422,
#                     detail="Body is required for Description Agent mode."
#                 )
#         if request.mode == ModeType.mode_6:
#             if not request.body:
#                 raise HTTPException(
#                     status_code=422,
#                     details=f"Header is required for {request.mode}."
#                 )
#             if not validate_combined_word_count(request.header or "", str(request.body), request.mode):
#                 raise HTTPException(
#                     status_code=422,
#                     detail=f"Header and body combined must contain at least {min_words} words."
#                 )
#         elif request.mode == ModeType.mode_2:
#             if not request.text:
#                 raise HTTPException(
#                     status_code=422,
#                     detail="Text input is required for Structured Context Enrichment mode."
#                 )
                
#         elif request.mode == ModeType.mode_6:
#             if not request.text:
#                 raise HTTPException(
#                     status_code=422,
#                     detail="Text input is required for Document development mode."
#                 )
                
#             if not validate_combined_word_count(request.header or "", request.text, request.mode):
#                 raise HTTPException(
#                     status_code=422,
#                     detail=f"Header and text combined must contain at least {min_words} words."
#                 )
#         elif request.mode == ModeType.mode_1:
#             if not request.text:
#                 raise HTTPException(
#                     status_code=422,
#                     detail="Text input is required for Context-Aware Regenerative Completion mode."
#                 )
#             if not validate_minimum_word_count(request.text, request.mode, min_words):
#                 raise HTTPException(
#                     status_code=422,
#                     detail=f"Please provide at least {min_words} words for Context-Aware Regenerative Completion."
#                 )
#         elif request.mode == ModeType.mode_3:
#             if not request.text:
#                 raise HTTPException(
#                     status_code=422,
#                     detail="Text input is required for Input Refinement mode."
#                 )
#         elif request.mode == ModeType.mode_5:
#             if not request.text:
#                 raise HTTPException(
#                     status_code=422,
#                     detail="Text input is required for Document Summarization mode."
#                 )
#         completion = None
#         if request.mode == ModeType.mode_1:
#             mode_logic = Mode1Logic()
#             completion = await mode_logic.process(
#                 text=request.text,
#                 max_output_length=request.max_output_length
#             )
#         elif request.mode == ModeType.mode_2:
#             mode_logic = Mode2Logic()
#             completion = await mode_logic.process(
#                 text=request.text,
#                 header=request.header,
#                 max_output_length=request.max_output_length
#             )
#         elif request.mode == ModeType.mode_3:
#             mode_logic = Mode3Logic()
#             completion = await mode_logic.process(
#                 text=request.text,
#                 max_output_length=request.max_output_length
#             )
#         elif request.mode == ModeType.mode_4:
#             mode_logic = Mode4Logic()
#             completion = await mode_logic.process(
#                 header=request.header,
#                 body=request.body,
#                 max_output_length=request.max_output_length
#             )
#         elif request.mode == ModeType.mode_5:
#             mode_logic = Mode5Logic()
#             completion = await mode_logic.process(
#                 text=request.text,
#                 max_output_length=request.max_output_length
#             )
#         elif request.mode == ModeType.mode_6:
#             mode_logic = Mode6Logic()
#             completion = await mode_logic.process(
#                 text=request.text,
#                 header=request.header,
#                 max_output_length=request.max_output_length
#             )
#         if request.max_output_length and not validate_output_length(completion, request.max_output_length):
#             completion = trim_output(completion, request.max_output_length)
#         return AutocompleteResponse(
#             completion=completion,
#             mode=request.mode
#         )
#     except httpx.RequestError as e:
#         raise HTTPException(
#             status_code=503, 
#             detail=f"Error communicating with Groq API: {str(e)}"
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Internal server error: {str(e)}"
#         )

# Health check endpoint
@router.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "modes": {
            "mode_1": "Context-Aware Regenerative Completion",
            "mode_2": "Structured Context Enrichment",
            "mode_3": "Input Refinement",
            "mode_4": "Description Agent",
            "mode_5": "Document Summarization",
            "mode_6": "Document Development"
        },
        "features": {
            "dynamic_min_input_words": True,
            "dynamic_max_output_length": True,
            "on_demand_generation": True,
            "supports_characters_and_words": True,
            "mode_specific_validation": True
        }
    }