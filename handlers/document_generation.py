"""
KB Article Generation Handler (Mode 6)
---------------------------------------
Handles API requests to generate structured IT knowledge base articles.

Endpoint:
    POST /generate-article

Expected JSON:
    {
        "title": "How to Configure SSL Certificates",
        "description": "Users need steps to install SSL certificates on Apache server...",
        "length": "medium",  # Options: short, medium, long, very_long
        "keywords": ["SSL", "Apache", "certificate"],
        "output_format": "markdown"
    }

Returns:
    {
        "success": true,
        "title": "...",
        "markdown": "...",
        "html": "..." (optional),
        "metrics": {...}
    }
    
    OR (if validation fails):
    {
        "success": false,
        "error": "Validation failed",
        "suggestions": [...]
    }
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from logic.mode_6 import Mode6
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)


class ArticleRequest(BaseModel):
    title: str = Field(..., description="Article title (min 5 chars)")
    description: str = Field(..., description="Detailed description (min 12 words)")
    length: str = Field(default="medium", description="Article length: short, medium, long, very_long")
    keywords: list[str] | None = Field(default=None, description="Optional keywords")
    output_format: str = Field(default="markdown", description="Output format: markdown, html, or all")


class ArticleResponse(BaseModel):
    success: bool
    title: str | None = None
    markdown: str | None = None
    html: str | None = None
    metrics: dict | None = None
    error: str | None = None
    suggestions: list[str] | None = None


@router.post("/generate-article", response_model=ArticleResponse)
async def generate_article(req: ArticleRequest):
    """Generate a structured IT KB article from title and description."""
    try:
        start = time.time()
        logger.info(f"[Mode6] Generating {req.length} article: {req.title[:50]}...")
        
        mode6 = Mode6()
        result = await mode6.generate_article(
            title=req.title,
            description=req.description,
            length=req.length,
            keywords=req.keywords,
            output_format=req.output_format
        )
        
        elapsed = round(time.time() - start, 2)
        logger.info(f"[Mode6] Article generated | Words: {result['metrics']['total_words']} | Time: {elapsed}s")
        
        return ArticleResponse(
            success=True,
            title=result['title'],
            markdown=result['markdown'],
            html=result.get('html'),
            metrics={**result['metrics'], 'generation_time': f"{elapsed}s"}
        )
        
    except ValueError as e:
        logger.warning(f"[Mode6] Validation error: {e}")
        error_msg = str(e)
        suggestions = []
        
        # Extract suggestions from error message
        if "Suggestions:" in error_msg:
            parts = error_msg.split("Suggestions:")
            if len(parts) > 1:
                suggestions = [s.strip().lstrip('•-') for s in parts[1].strip().split('\n') if s.strip()]
        
        return ArticleResponse(
            success=False,
            error=error_msg.split("\n\nSuggestions:")[0] if suggestions else error_msg,
            suggestions=suggestions if suggestions else None
        )
    except Exception as e:
        logger.error(f"[Mode6] Generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Article generation failed")
