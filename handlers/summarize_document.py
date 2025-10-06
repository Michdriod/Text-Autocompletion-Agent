from fastapi import APIRouter, UploadFile, File, HTTPException
from logic.mode_5 import Mode5
import os
import tempfile
import shutil

router = APIRouter()

@router.post("/summarize-document")
async def summarize_document(file: UploadFile = File(...)):
    """Accepts a document file (PDF, DOCX, TXT) and returns a summary and metadata."""
    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")
    # Save to a temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    try:
        logic = Mode5()
        result = await logic.process_document_file(tmp_path)
        return result
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass