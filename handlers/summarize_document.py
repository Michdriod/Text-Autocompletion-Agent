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
    # Postgres source fields (optional): provide db_name + table + columns + id/range
    pg_db: str | None = Form(default=None),
    pg_table: str | None = Form(default=None),
    pg_id_column: str | None = Form(default=None),
    pg_id_value: str | None = Form(default=None),  # Single ID
    pg_id_start: str | None = Form(default=None),  # Range start
    pg_id_end: str | None = Form(default=None),  # Range end
    pg_text_column: str | None = Form(default=None),
    pg_context_column: str | None = Form(default=None),  # Optional: e.g., title for better context
    pg_mode: str | None = Form(default=None),  # "single", "per_row", "aggregate"
    target_words: int | None = Form(default=None),
    output_format: str = Form(default="markdown"),
    user_prompt: str | None = Form(default=None)
):
    """Summarize an uploaded document, raw text, document URL, OR PostgreSQL content.

    Provide ONE of:
      - file (PDF, DOCX, TXT upload)
      - raw_text (pasted text string)
      - document_url (any accessible document URL: Google Drive, Dropbox, OneDrive, direct links, etc.)
      - postgres (pg_db + pg_table + pg_id_column + pg_text_column + id/range)
      
    Priority: file > document_url > postgres > raw_text
    """
    # Count provided inputs
    postgres_provided = all([
        pg_db is not None and pg_db.strip(),
        pg_table is not None and pg_table.strip(),
        pg_id_column is not None and pg_id_column.strip(),
        pg_text_column is not None and pg_text_column.strip(),
    ]) and (
        (pg_id_value is not None and pg_id_value.strip()) or
        (pg_id_start is not None and pg_id_start.strip()) or
        (pg_id_end is not None and pg_id_end.strip())
    )

    inputs_provided = sum([
        file is not None,
        bool(document_url is not None and document_url.strip()),
        bool(raw_text is not None and raw_text.strip()),
        bool(postgres_provided),
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

    # Priority 3: Postgres source
    elif postgres_provided:
        import asyncio
        from utils.postgres_input import fetch_rows
        
        # Determine mode
        if pg_id_value and pg_id_value.strip():
            mode = "single"
        else:
            # Range query
            mode = pg_mode.strip().lower() if pg_mode and pg_mode.strip() else "per_row"
        
        # Validate mode
        if mode not in ("single", "per_row", "aggregate"):
            raise HTTPException(status_code=400, detail=f"Invalid pg_mode: {mode}. Must be 'single', 'per_row', or 'aggregate'")
        
        try:
            rows = await fetch_rows(
                db_name=pg_db.strip(),
                table=pg_table.strip(),
                id_column=pg_id_column.strip(),
                text_column=pg_text_column.strip(),
                id_value=pg_id_value.strip() if pg_id_value and pg_id_value.strip() else None,
                id_start=pg_id_start.strip() if pg_id_start and pg_id_start.strip() else None,
                id_end=pg_id_end.strip() if pg_id_end and pg_id_end.strip() else None,
                context_column=pg_context_column.strip() if pg_context_column and pg_context_column.strip() else None,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except RuntimeError as rexc:
            raise HTTPException(status_code=502, detail=str(rexc))
        except Exception as e:
            logger.exception("Unexpected error fetching from Postgres")
            raise HTTPException(status_code=500, detail="Failed to fetch from Postgres")
        
        if not rows:
            raise HTTPException(status_code=404, detail="No rows found for the provided criteria")
        
        # Mode: single
        if mode == "single":
            try:
                result = await logic.process_raw_text(
                    rows[0]["text"],
                    source_name=f"postgres:{pg_table.strip()}:{pg_id_column.strip()}={rows[0]['id']}",
                    target_words=target_words,
                    output_format=output_format,
                    user_prompt=user_prompt
                )
                result.setdefault('meta', {}).setdefault('ingest', {})
                result['meta']['ingest'].update({
                    'source_type': 'postgres',
                    'db': pg_db.strip(),
                    'table': pg_table.strip(),
                    'id_column': pg_id_column.strip(),
                    'id': rows[0]['id'],
                    'text_column': pg_text_column.strip(),
                })
                return result
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception as e:
                logger.exception("Failed to process Postgres text")
                raise HTTPException(status_code=500, detail="Failed to summarize content")
        
        # Mode: per_row
        elif mode == "per_row":
            summaries = []
            sem = asyncio.Semaphore(3)  # Limit concurrency to 3
            
            async def summarize_one(row):
                async with sem:
                    try:
                        result = await logic.process_raw_text(
                            row["text"],
                            source_name=f"postgres:{pg_table.strip()}:{pg_id_column.strip()}={row['id']}",
                            target_words=target_words,
                            output_format=output_format,
                            user_prompt=user_prompt
                        )
                        result.setdefault('meta', {}).setdefault('ingest', {})
                        result['meta']['ingest'].update({
                            'source_type': 'postgres',
                            'db': pg_db.strip(),
                            'table': pg_table.strip(),
                            'id': row['id'],
                        })
                        return {"id": row["id"], "result": result}
                    except Exception as e:
                        logger.warning(f"Failed to summarize row {row['id']}: {e}")
                        return {"id": row["id"], "error": str(e)}
            
            summaries = await asyncio.gather(*[summarize_one(r) for r in rows])
            return {"summaries": summaries, "mode": "per_row", "rows_processed": len(rows)}
        
        # Mode: aggregate
        else:  # mode == "aggregate"
            combined = "\n\n".join([r["text"] for r in rows if r["text"]])
            try:
                result = await logic.process_raw_text(
                    combined,
                    source_name=f"postgres:{pg_table.strip()}:aggregate",
                    target_words=target_words,
                    output_format=output_format,
                    user_prompt=user_prompt
                )
                result.setdefault('meta', {}).setdefault('ingest', {})
                result['meta']['ingest'].update({
                    'source_type': 'postgres',
                    'db': pg_db.strip(),
                    'table': pg_table.strip(),
                    'rows_covered': len(rows),
                    'mode': 'aggregate',
                })
                return result
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception as e:
                logger.exception("Failed to process aggregated Postgres content")
                raise HTTPException(status_code=500, detail="Failed to summarize content")

    # Priority 4: Raw text input
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
    
    