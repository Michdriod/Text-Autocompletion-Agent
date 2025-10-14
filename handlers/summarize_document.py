from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from logic.mode_5 import Mode5
from config.settings import MAX_PROMPT_LENGTH
from utils.validator import validate_prompt_length
from utils.google_drive import download_from_google_drive, GoogleDriveError
import os
import tempfile
import shutil

router = APIRouter()

@router.post("/summarize-document")
async def summarize_document(
    file: UploadFile | None = File(default=None),
    raw_text: str | None = Form(default=None),
    google_drive_url: str | None = Form(default=None),
    target_words: int | None = Form(default=None),
    output_format: str = Form(default="markdown"),
    user_prompt: str | None = Form(default=None)
):
    """Summarize an uploaded document, raw text, OR a Google Drive public link.

    Provide ONE of:
      - file (PDF, DOCX, TXT upload)
      - raw_text (pasted text string)
      - google_drive_url (public Google Drive or Docs share link)
      
    Priority: file > google_drive_url > raw_text
    """
    # Count provided inputs
    inputs_provided = sum([
        file is not None,
        bool(google_drive_url is not None and google_drive_url.strip()),
        bool(raw_text is not None and raw_text.strip())
    ])
    
    if inputs_provided == 0:
        raise HTTPException(
            status_code=400,
            detail="Provide either a file, Google Drive URL, or raw text."
        )
    
    if inputs_provided > 1:
        raise HTTPException(
            status_code=400,
            detail="Provide only ONE input source (file, Google Drive URL, or raw text)."
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
    
    # Priority 2: Google Drive URL
    elif google_drive_url is not None and google_drive_url.strip():
        gdrive_url = google_drive_url.strip()
        
        try:
            # Download from Google Drive
            temp_path, extension, file_type = download_from_google_drive(gdrive_url, max_size_mb=10)
            
            # Validate file extension
            if extension not in ['.pdf', '.docx', '.txt', '.xlsx']:
                os.remove(temp_path)
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported file type from Google Drive: {extension}"
                )
            
            try:
                result = await logic.process_document_file(
                    temp_path,
                    target_words=target_words,
                    output_format=output_format,
                    user_prompt=user_prompt
                )
                # Add metadata about Google Drive source
                result['meta']['source_type'] = 'google_drive'
                result['meta']['google_drive_file_type'] = file_type
                return result
            finally:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        
        except GoogleDriveError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process Google Drive file: {e}"
            )

    # Raw text path
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
    
    