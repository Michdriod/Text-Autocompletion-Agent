from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from logic.mode_5 import Mode5
from config.settings import MAX_PROMPT_LENGTH
from utils.validator import validate_prompt_length
from utils.universal_url import download_from_universal_url, UniversalURLError
import os
import tempfile
import shutil
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/summarize-document")
async def summarize_document(
    file: UploadFile | None = File(default=None),
    raw_text: str | None = Form(default=None),
    document_url: str | None = Form(default=None),  # Universal URL parameter
    target_words: int | None = Form(default=None),
    output_format: str = Form(default="markdown"),
    user_prompt: str | None = Form(default=None)
):
    """Summarize an uploaded document, raw text, OR a document URL (Google Drive, Dropbox, OneDrive, etc.).

    Provide ONE of:
      - file (PDF, DOCX, TXT upload)
      - raw_text (pasted text string)
      - document_url (any accessible document URL: Google Drive, Dropbox, OneDrive, direct links, etc.)
      
    Priority: file > document_url > raw_text
    """
    # Count provided inputs
    inputs_provided = sum([
        file is not None,
        bool(document_url is not None and document_url.strip()),
        bool(raw_text is not None and raw_text.strip())
    ])
    
    if inputs_provided == 0:
        raise HTTPException(
            status_code=400,
            detail="Provide either a file, document URL, or raw text."
        )
    
    if inputs_provided > 1:
        raise HTTPException(
            status_code=400,
            detail="Provide only ONE input source (file, document URL, or raw text)."
        )
    
    # if file is None and (raw_text is None or not raw_text.strip()):
    #     raise HTTPException(status_code=400, detail="Provide either a file or non-empty raw_text.")

    logic = Mode5()
    # if target_words is not None and target_words <= 0:
    #     raise HTTPException(status_code=400, detail="target_words must be positive")
    
    
    # Validate prompt length
    if user_prompt:
        cleaned_prompt, was_truncated = validate_prompt_length(user_prompt, MAX_PROMPT_LENGTH)
        if was_truncated:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters"
            )
        user_prompt = cleaned_prompt
    
    # Priority 1: File upload
    if file is not None:
        allowed_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        }
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {file.content_type}"
            )
        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(file.filename)[-1]
            ) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save uploaded file: {e}"
            )
        
        try:
            result = await logic.process_document_file(
                tmp_path,
                target_words=target_words,
                output_format=output_format,
                user_prompt=user_prompt
            )
            return result
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    
    # Priority 2: Universal Document URL
    elif document_url is not None and document_url.strip():
        doc_url = document_url.strip()
        
        try:
            # Download from universal URL (Google Drive, Dropbox, OneDrive, direct links, etc.)
            temp_path, extension, filename = download_from_universal_url(doc_url)
            
            try:
                result = await logic.process_document_file(
                    temp_path,
                    target_words=target_words,
                    output_format=output_format,
                    user_prompt=user_prompt
                )
                # Add metadata about universal URL source
                result['meta']['source_type'] = 'document_url'
                result['meta']['original_filename'] = filename
                result['meta']['detected_extension'] = extension
                result['meta']['source_url'] = doc_url
                return result
            finally:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        
        except UniversalURLError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document from URL: {e}"
            )

    # Priority 3: Raw text input
    else:    
        try:
            result = await logic.process_raw_text(
                raw_text.strip(),
                source_name="pasted_text",
                target_words=target_words,
                output_format=output_format,
                user_prompt=user_prompt
            )
            return result
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process raw text: {e}"
            )
    
    