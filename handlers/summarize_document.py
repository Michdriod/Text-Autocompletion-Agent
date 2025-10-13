from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from logic.mode_5 import Mode5
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
    if target_words is not None and target_words <= 0:
        raise HTTPException(status_code=400, detail="target_words must be positive")

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
            result = await logic.process_document_file(tmp_path, target_words=target_words, output_format=output_format)
            return result
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    else:
        # Raw text path
        try:
            result = await logic.process_raw_text(raw_text.strip(), source_name="pasted_text", target_words=target_words, output_format=output_format)
            return result
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process raw text: {e}")