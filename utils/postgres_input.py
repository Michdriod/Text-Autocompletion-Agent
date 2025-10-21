"""PostgreSQL input adapter for Text-Autocompletion-Agent.

Production-quality adapter that safely fetches text content from PostgreSQL databases
for summarization. Supports single-row, per-row (range), and aggregate modes.

Key features:
  - Server-side credentials only (no client-sent passwords)
  - Strict identifier validation (prevents SQL injection)
  - Parameterized queries for all user values
  - Statement timeout enforcement
  - Row and byte limits for safety
  - Clean error mapping without leaking internals

Security model:
  - Server holds POSTGRES_READONLY_DSN_TEMPLATE in config
  - Clients provide only: db_name, table, id_column, text_column, id values
  - All identifiers validated with strict regex before query construction
  - All values passed as parameters (never interpolated)
"""

from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional

try:
    import asyncpg  # type: ignore
except ImportError:  # pragma: no cover
    asyncpg = None  # type: ignore

from config import settings

logger = logging.getLogger(__name__)

# Validation patterns
DB_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

# Default limits
DEFAULT_MAX_ROWS = 100
DEFAULT_MAX_BYTES = 200_000  # 200 KB per row
DEFAULT_TIMEOUT = 5  # seconds


def _validate_db_name(name: str) -> bool:
    """Validate database name: letters, digits, underscore, hyphen only."""
    return bool(DB_NAME_RE.fullmatch(name))


def _validate_identifier(name: str) -> bool:
    """Validate table/column identifier: allow schema.table format.
    
    Pattern: letter/underscore start, then alphanumeric/underscore.
    Supports optional schema qualification: schema.table
    """
    return bool(IDENT_RE.fullmatch(name))


def _quote_identifier(ident: str) -> str:
    """Quote SQL identifier safely for interpolation.
    
    Splits schema.table and quotes each part separately.
    """
    parts = ident.split(".")
    return ".".join(f'"{p}"' for p in parts)


def _infer_id_type(value: str) -> str:
    """Infer ID type from string value: int, uuid, or text."""
    if value.isdigit():
        return "int"
    if UUID_RE.fullmatch(value):
        return "uuid"
    return "text"


def _build_dsn(db_name: str) -> str:
    """Build DSN from server template by substituting db_name.
    
    Expects settings.POSTGRES_READONLY_DSN_TEMPLATE like:
      postgresql://readonly:pass@host:5432/{db}
    """
    template = getattr(settings, "POSTGRES_READONLY_DSN_TEMPLATE", None)
    if not template:
        raise RuntimeError(
            "POSTGRES_READONLY_DSN_TEMPLATE not configured in settings. "
            "Set it to a connection string with {db} placeholder."
        )
    try:
        return template.format(db=db_name)
    except KeyError:
        raise RuntimeError("DSN template must contain {db} placeholder")


async def fetch_rows(
    db_name: str,
    table: str,
    id_column: str,
    text_column: str,
    id_value: Optional[str] = None,
    id_start: Optional[str] = None,
    id_end: Optional[str] = None,
    context_column: Optional[str] = None,
    limit: int = DEFAULT_MAX_ROWS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_seconds: int = DEFAULT_TIMEOUT,
) -> List[Dict[str, Any]]:
    """Fetch rows from Postgres table with safe query construction.
    
    Args:
        db_name: Database name (validated, substituted into server DSN template)
        table: Table name, optionally schema-qualified (validated)
        id_column: ID column name (validated)
        text_column: Text column name (validated)
        id_value: Single ID value (for single-row fetch)
        id_start: Range start ID (for range queries)
        id_end: Range end ID (for range queries)
        context_column: Optional column for additional context (e.g., title) to prepend to text
        limit: Max rows to fetch (capped at DEFAULT_MAX_ROWS)
        max_bytes: Max bytes per row text (truncation limit)
        timeout_seconds: Connection and statement timeout
    
    Returns:
        List of dicts: [{'id': <value>, 'text': <string>}, ...]
        If context_column is provided, text will be: "<context>: <text_content>"
    
    Raises:
        ValueError: Invalid inputs, missing row, empty content
        RuntimeError: DB connectivity or query errors
    """
    if asyncpg is None:
        raise RuntimeError("asyncpg not installed. Install with: pip install asyncpg")
    
    # Input validation
    if not db_name or not db_name.strip():
        raise ValueError("db_name is required")
    if not _validate_db_name(db_name.strip()):
        raise ValueError(f"Invalid db_name: {db_name}")
    
    for name, value in [("table", table), ("id_column", id_column), ("text_column", text_column)]:
        if not value or not value.strip():
            raise ValueError(f"{name} is required")
        if not _validate_identifier(value.strip()):
            raise ValueError(f"Invalid {name}: {value}")
    
    # Validate context_column if provided (optional)
    if context_column and context_column.strip():
        if not _validate_identifier(context_column.strip()):
            raise ValueError(f"Invalid context_column: {context_column}")
    
    # Enforce limit cap
    if limit <= 0 or limit > DEFAULT_MAX_ROWS:
        raise ValueError(f"limit must be between 1 and {DEFAULT_MAX_ROWS}")
    
    # Quote identifiers safely
    table_q = _quote_identifier(table.strip())
    id_col_q = _quote_identifier(id_column.strip())
    text_col_q = _quote_identifier(text_column.strip())
    context_col_q = _quote_identifier(context_column.strip()) if (context_column and context_column.strip()) else None
    
    # Build WHERE clause and parameters
    where_clause = ""
    params: List[Any] = []
    
    if id_value is not None and id_value.strip():
        where_clause = f"WHERE {id_col_q} = $1"
        id_type = _infer_id_type(id_value.strip())
        if id_type == "int":
            try:
                params = [int(id_value.strip())]
            except ValueError:
                raise ValueError(f"id_value '{id_value}' is not a valid integer")
        else:
            params = [id_value.strip()]
    elif id_start is not None or id_end is not None:
        if id_start and id_end:
            where_clause = f"WHERE {id_col_q} BETWEEN $1 AND $2"
            params = [id_start.strip(), id_end.strip()]
        elif id_start:
            where_clause = f"WHERE {id_col_q} >= $1"
            params = [id_start.strip()]
        elif id_end:
            where_clause = f"WHERE {id_col_q} <= $1"
            params = [id_end.strip()]
    
    # Build final query with optional context column
    if context_col_q:
        # If context column provided, concatenate it with text: "context: text"
        select_clause = f"SELECT {id_col_q} AS id, {context_col_q} AS context, {text_col_q} AS content"
    else:
        select_clause = f"SELECT {id_col_q} AS id, {text_col_q} AS content"
    
    query = f"{select_clause} FROM {table_q} {where_clause} ORDER BY {id_col_q} LIMIT {int(limit)}"
    
    # Build DSN
    dsn = _build_dsn(db_name.strip())
    
    conn: Optional[asyncpg.Connection] = None
    try:
        # Connect with timeout
        conn = await asyncpg.connect(dsn=dsn, timeout=timeout_seconds)
        
        # Set statement timeout (best effort)
        try:
            await conn.execute(f"SET LOCAL statement_timeout = {int(timeout_seconds * 1000)}")
        except Exception:
            pass  # Not all postgres versions support this
        
        # Execute query
        rows = await conn.fetch(query, *params) if params else await conn.fetch(query)
        
        # Process rows
        results: List[Dict[str, Any]] = []
        for row in rows:
            raw_content = row["content"]
            
            # Handle context column if present
            context_text = ""
            if context_col_q and "context" in row:
                raw_context = row["context"]
                if isinstance(raw_context, (bytes, bytearray)):
                    try:
                        raw_context = raw_context.decode("utf-8", errors="replace")
                    except Exception:
                        raw_context = raw_context.decode("latin1", errors="replace")
                context_text = "" if raw_context is None else str(raw_context).strip()
            
            # Handle bytea columns for main content
            if isinstance(raw_content, (bytes, bytearray)):
                try:
                    raw_content = raw_content.decode("utf-8", errors="replace")
                except Exception:
                    raw_content = raw_content.decode("latin1", errors="replace")
            
            # Coerce to string
            content_text = "" if raw_content is None else str(raw_content)
            
            # Combine context and content if context exists
            if context_text:
                text = f"{context_text}: {content_text}"
            else:
                text = content_text
            
            # Truncate if needed
            encoded = text.encode("utf-8")
            if len(encoded) > max_bytes:
                logger.info(
                    "Row truncated",
                    extra={"table": table, "id": row["id"], "original_bytes": len(encoded), "max_bytes": max_bytes}
                )
                text = encoded[:max_bytes].decode("utf-8", errors="ignore")
            
            results.append({"id": row["id"], "text": text})
        
        return results
    
    except ValueError:
        raise
    except asyncpg.InvalidAuthorizationSpecificationError:
        logger.debug("Postgres auth failure", exc_info=True)
        raise RuntimeError("Authentication failed to Postgres database")
    except (asyncpg.PostgresError, OSError) as exc:
        logger.debug("Postgres error", exc_info=True)
        raise RuntimeError(f"Database error: {type(exc).__name__}")
    except Exception as exc:
        logger.exception("Unexpected error fetching from Postgres")
        raise RuntimeError("Unexpected database error")
    finally:
        if conn:
            try:
                await conn.close()
            except Exception:
                pass


async def fetch_single_row_text(
    db_name: str,
    table: str,
    id_column: str,
    id_value: str,
    text_column: str,
    context_column: Optional[str] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT,
) -> str:
    """Convenience wrapper for single-row text fetch.
    
    Raises ValueError if row not found or content empty.
    """
    rows = await fetch_rows(
        db_name=db_name,
        table=table,
        id_column=id_column,
        text_column=text_column,
        id_value=id_value,
        context_column=context_column,
        limit=1,
        timeout_seconds=timeout_seconds,
    )
    
    if not rows:
        raise ValueError(f"No row found with {id_column}={id_value}")
    
    text = rows[0]["text"]
    if not text or not text.strip():
        raise ValueError(f"Row {id_column}={id_value} has empty content")
    
    return text