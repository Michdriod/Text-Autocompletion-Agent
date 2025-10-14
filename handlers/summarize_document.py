from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from logic.mode_5 import Mode5
from config.settings import MAX_PROMPT_LENGTH
from utils.validator import validate_prompt_length
import os
import tempfile
import shutil

router = APIRouter()

@router.post("/summarize-document")
async def summarize_document(
    file: UploadFile | None = File(default=None),
    raw_text: str | None = Form(default=None),
    target_words: int | None = Form(default=None),
    output_format: str = Form(default="markdown"),
    user_prompt: str | None = Form(default=None)
):
    """Summarize an uploaded document OR directly pasted raw text.

    Provide either:
      - file (PDF, DOCX, TXT)
      - raw_text (string)
    If both are provided, file takes precedence.
    """
    if file is None and (raw_text is None or not raw_text.strip()):
        raise HTTPException(status_code=400, detail="Provide either a file or non-empty raw_text.")

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
    

    # If file provided, process as before
    if file is not None:
        allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
        try:
            result = await logic.process_document_file(tmp_path, target_words=target_words, output_format=output_format, user_prompt=user_prompt)
            return result
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    else:
        # Raw text path
        try:
            result = await logic.process_raw_text(raw_text.strip(), source_name="pasted_text", target_words=target_words, output_format=output_format, user_prompt=user_prompt)
            return result
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process raw text: {e}")
    
    