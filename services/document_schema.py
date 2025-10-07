"""
Schema: Document Development Request
------------------------------------
Defines request model for the Document Development (Mode 6) API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Union


class DocumentDevelopmentRequest(BaseModel):
    """
    Input schema for Mode 6 - Document Development Agent.
    """
    header: str = Field(
        ...,
        description="High-level purpose or title of the document. Example: 'AI Adoption Strategy for Banks'."
    )
    body: str = Field(
        ...,
        description="Detailed source content, notes, or bullet points describing what should go into the document."
    )
    max_output_length: Optional[Dict[Literal["type", "value"], Union[str, int]]] = Field(
        default=None,
        description=(
            "Optional output length constraint. Example: "
            "{'type': 'words', 'value': 1500} or {'type': 'characters', 'value': 3000}."
        )
    )

    class Config:
        schema_extra = {
            "example": {
                "header": "AI Transformation Roadmap for Financial Services",
                "body": (
                    "Create a professional strategy document outlining goals, "
                    "phases, and KPIs for AI integration in banking operations."
                ),
                "max_output_length": {"type": "words", "value": 1200}
            }
        }



class DocumentDevelopmentResponse(BaseModel):
    """
    Output schema for Mode 6 - Document Development Agent.
    Returned as structured JSON for client and API consumers.
    """
    status: str = Field(
        ...,
        description="Indicates whether the request succeeded or failed. Example: 'success' or 'error'."
    )
    document: str = Field(
        ...,
        description="The generated, fully formatted document text in Markdown or plain text."
    )
    meta: Optional[dict] = Field(
        default=None,
        description=(
            "Optional metadata (e.g., generation time, token count, page estimate). "
            "Can be null if not required."
        )
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "document": (
                    "AI TRANSFORMATION ROADMAP\n\n"
                    "EXECUTIVE SUMMARY\n"
                    "This document outlines a phased approach for AI integration..."
                ),
                "meta": {
                    "pages": 2.8,
                    "estimated_words": 980,
                    "model": "groq/llama3-70b",
                    "generation_time": "1.42s"
                }
            }
        }
