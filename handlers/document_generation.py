"""
Document Development Handler (Mode 6)
-------------------------------------
Handles incoming API requests to generate fully developed, 
professional documents based on a title (header) and description (body).

Endpoint:
    POST /api/document/develop

Expected JSON:
    {
        "header": "Proposal for AI-driven Customer Support",
        "body": "We aim to build an AI assistant that...",
        "max_output_length": {"type": "words", "value": 800}
    }

Returns:
    {
        "success": true,
        "content": "<formatted document output>"
    }
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from logic.mode_6 import Mode6
import logging
from services.document_schema import DocumentDevelopmentRequest, DocumentDevelopmentResponse

# --- Initialize Router & Logger ---
router = APIRouter()
logger = logging.getLogger(__name__)

# --- Request Schema ---
class DocumentDevelopmentRequest(BaseModel):
    header: str = Field(..., description="The document's title or main purpose.")
    body: str = Field(..., description="Descriptive content or user-provided notes.")
    max_output_length: dict | None = Field(
        default=None,
        description="Optional constraint for max output length (words or characters)."
    )

# --- API Endpoint ---
@router.post("/api/document/develop")
async def develop_document(req: DocumentDevelopmentRequest):
    """
    POST /api/document/develop
    Generates a professionally structured document from given header and body.
    """
    try:
        logger.info("🟢 Received new Mode 6 document development request.")
        
        mode6 = Mode6()
        result = await mode6.process(
            header=req.header,
            body=req.body,
            max_output_length=req.max_output_length
        )

        logger.info("✅ Document successfully developed.")
        return {
            "success": True,
            "mode": "document_development",
            "content": result
        }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"❌ Document development failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.post("/api/document/develop", response_model=DocumentDevelopmentResponse)
async def develop_document(request: DocumentDevelopmentRequest):
    """
    API endpoint for Mode 6 - Document Development Agent.
    Generates a polished, professional document from the given header and body.
    """
    try:
        start_time = time.time()
        mode6 = Mode6()

        # Run the async generation process
        document_output = await mode6.process(
            header=request.header,
            body=request.body,
            max_output_length=request.max_output_length
        )

        # --- Logging (internal only) ---
        elapsed = round(time.time() - start_time, 2)
        word_count = len(document_output.split())
        approx_pages = round(word_count / 350, 2)

        logger.info(
            f"[Mode 6] Document generated successfully | "
            f"Words: {word_count} | Pages: {approx_pages} | "
            f"Duration: {elapsed}s"
        )

        # --- Response ---
        return DocumentDevelopmentResponse(
            status="success",
            document=document_output,
            meta={
                "approx_pages": approx_pages,
                "estimated_words": word_count,
                "generation_time": f"{elapsed}s"
            }
        )

    except Exception as e:
        logger.error(f"[Mode 6] Document generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
