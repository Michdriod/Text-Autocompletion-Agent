# PostgreSQL Input Adapter — Implementation Plan (SIMPLIFIED)

## What are we building?

A new way for users to summarize content that lives in a PostgreSQL database — just like they can already upload files, paste text, or provide URLs.

### The big picture (analogy)

Think of your system like a restaurant kitchen:
- **Currently**: Customers can bring ingredients (file upload), hand you a recipe (raw text), or give you a grocery store address (URL) to fetch ingredients
- **What we're adding**: Customers can now give you a warehouse location (database name), aisle number (table name), and shelf position (row ID) — and you'll fetch the ingredients from there

The kitchen (your summarizer) doesn't change — we're just adding a new way to get ingredients into it.

---

## What the user will do (simple example)

**Scenario**: You have an "incidents" table in a Postgres database with columns like:
- `id` (incident number: 1, 2, 3, etc.)
- `description` (the text to summarize)
- `status`, `priority`, etc.

**Current system**: User must export the description text, copy-paste it, or upload as a file.

**New system**: User fills out a form:
```
Database name: customer_db
Table name: incidents
ID column: id
Text column: description
ID to summarize: 42
```

Your server fetches the description from row 42 and summarizes it automatically.

---

## Three ways to use it (modes)

### Mode 1: Single row (DEFAULT)
- **What**: Summarize one specific row
- **Example**: "Summarize incident #42"
- **User provides**: database, table, id_column, id_value (e.g., 42), text_column
- **Result**: One summary

### Mode 2: Per-row (for ranges)
- **What**: Summarize multiple rows individually
- **Example**: "Summarize incidents #10 through #20, give me one summary per incident"
- **User provides**: database, table, id_column, id_start (10), id_end (20), text_column
- **Result**: List of summaries (one for each row)

### Mode 3: Aggregate (combine then summarize)
- **What**: Fetch multiple rows, combine their text, then summarize everything together
- **Example**: "Summarize all incidents #10 through #20 as one overall summary"
- **User provides**: same as Mode 2, but set mode='aggregate'
- **Result**: One combined summary

---

## How it works behind the scenes (step-by-step)

### Step 1: User sends request to your API
```
POST /summarize-document
Form fields:
  pg_db = "customer_db"
  pg_table = "incidents"
  pg_id_column = "id"
  pg_id_value = "42"
  pg_text_column = "description"
  target_words = 200
```

### Step 2: Your server validates inputs
- Check that table/column names contain only safe characters (letters, numbers, underscore)
- No weird characters that could break SQL (no quotes, semicolons, etc.)
- **Why**: Protect against SQL injection attacks

### Step 3: Your server builds a safe database connection
- **Important**: The USER does NOT send database passwords
- **Instead**: Your server has a pre-configured connection stored in settings
- Template looks like: `postgresql://readonly_user:secret_password@db-host:5432/{database_name}`
- Server substitutes `{database_name}` with the validated `pg_db` value

### Step 4: Server fetches the data safely
```sql
-- Your server runs this query (simplified):
SELECT "description" AS content 
FROM "incidents" 
WHERE "id" = $1  -- $1 is a placeholder for the safe parameter
LIMIT 1
```
- The `$1` is replaced with the user's id_value (42) **safely** by the database driver
- This prevents SQL injection

### Step 5: Server passes text to your existing summarizer
- Takes the fetched text (e.g., "Customer reported network outage on...")
- Calls `Mode5.process_raw_text(content, target_words=200, ...)`
- This is the **same** code path as when someone pastes text

### Step 6: Return summary to user
- Same response format as your existing summarizer
- Added metadata shows it came from postgres:
```json
{
  "summary": "...",
  "meta": {
    "source_type": "postgres",
    "table": "incidents",
    "id": 42
  }
}
```

---

## Security (keeping your database safe)

### What could go wrong (and how we prevent it)

**Problem 1**: User tries to inject malicious SQL
```
Bad input: pg_table = "incidents; DROP TABLE users; --"
```
**Prevention**: Strict validation — only allow letters, numbers, underscore in table names. Reject anything else.

**Problem 2**: User sends their own database password
**Prevention**: Server NEVER accepts passwords from users. All credentials are stored server-side only.

**Problem 3**: Query runs forever and crashes the server
**Prevention**: Set a 5-second timeout. If query takes longer, cancel it.

**Problem 4**: Someone requests 1 million rows
**Prevention**: Hard limit of 100 rows maximum per request.

**Problem 5**: Passwords leak into logs
**Prevention**: Never log the connection string or user data — only counts like "fetched 5 rows, 2.3KB"

---

## What files will change

### 1. New file: `utils/postgres_adapter.py`
**Purpose**: Contains the safe database fetching logic
**Main function**: `fetch_rows(db_name, table, id_column, text_column, id_value=None, id_start=None, id_end=None)`
- Validates all inputs
- Connects to database safely
- Fetches rows
- Returns list of `{id: X, text: "..."}` objects

### 2. Updated: `handlers/summarize_document.py`
**Changes**: Add new form fields and wire to the adapter
**New parameters**:
- `pg_db` — database name
- `pg_table` — table name
- `pg_id_column` — which column has the ID
- `pg_id_value` — single ID (for mode 1)
- `pg_id_start`, `pg_id_end` — range (for modes 2 & 3)
- `pg_text_column` — which column has the text
- `pg_mode` — "single", "per_row", or "aggregate"

### 3. Updated: `config/settings.py`
**Changes**: Add database connection template
```python
POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://readonly:pass@host:5432/{db}"
```

### 4. Updated: `requirements.txt`
**Changes**: Add `asyncpg==0.27.0` (the Postgres driver library)

---

## Limits and defaults (preventing abuse)

| Setting | Default | Why |
|---------|---------|-----|
| Max rows per request | 100 | Prevent huge queries that slow down DB |
| Max size per row | 200 KB | Prevent loading giant text blobs into memory |
| Query timeout | 5 seconds | Cancel slow queries automatically |
| Allowed db_name chars | Letters, digits, `_`, `-` | Prevent SQL injection |
| Allowed table/column chars | Letters, digits, `_`, and `schema.table` format | Safe identifiers only |

---

## Example usage (concrete)

### Example 1: Summarize one incident
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=prod_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_value=42" \
  -F "pg_text_column=description" \
  -F "target_words=150"
```

**What happens**:
1. Server validates inputs ✓
2. Connects to database using pre-configured credentials ✓
3. Runs: `SELECT description FROM incidents WHERE id = 42 LIMIT 1` ✓
4. Gets text: "Network outage reported by customer..."
5. Summarizes to 150 words ✓
6. Returns summary ✓

### Example 2: Summarize a range (per-row)
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=prod_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_start=10" \
  -F "pg_id_end=15" \
  -F "pg_text_column=description" \
  -F "pg_mode=per_row" \
  -F "target_words=100"
```

**What happens**:
1. Server fetches rows 10-15 (6 rows) ✓
2. Summarizes EACH row separately (6 summaries) ✓
3. Returns:
```json
{
  "summaries": [
    {"id": 10, "summary": "..."},
    {"id": 11, "summary": "..."},
    ...
  ]
}
```

### Example 3: Summarize a range (aggregate)
```bash
# Same as Example 2, but change pg_mode to "aggregate"
```

**What happens**:
1. Server fetches rows 10-15 ✓
2. Combines all text together ✓
3. Summarizes the COMBINED text as ONE summary ✓
4. Returns one consolidated summary covering all 6 incidents

---

## Testing plan (how we verify it works)

### Unit tests (test individual pieces)
1. **Test validation**: Pass bad table names → should reject
2. **Test SQL building**: Verify queries use parameters correctly
3. **Test truncation**: Fetch huge text → should truncate to 200KB
4. **Test errors**: Database connection fails → should return clean error

### Integration tests (test end-to-end)
1. Mock database responses
2. Send request with postgres fields
3. Verify summarizer is called with correct text
4. Verify response has correct metadata

---

## What you need to decide before we code

### Decisions needed:
1. ✓ **Config key name**: Use `POSTGRES_READONLY_DSN_TEMPLATE` (confirmed)
2. ✓ **Database name characters**: Allow letters, digits, underscore, hyphen (confirmed)
3. ✓ **Defaults**: max_rows=100, max_bytes=200KB, timeout=5s (confirmed)
4. ✓ **Default mode for ranges**: Use `per_row` (confirmed)
5. ✓ **Parameter names**: Use `pg_db`, `pg_table`, `pg_id_column`, etc. (confirmed)

### Ready to implement?
If this plan makes sense, I will:
1. Write `utils/postgres_adapter.py` with safe fetching logic
2. Update `handlers/summarize_document.py` to accept postgres fields
3. Add `asyncpg` to `requirements.txt`
4. Create basic unit tests
5. Run tests and fix any issues

---

## Visual flow diagram

```
User Request
    ↓
[Validate inputs]
    ↓
[Build safe DB connection using server credentials]
    ↓
[Fetch row(s) with parameterized query]
    ↓
[Truncate if needed]
    ↓
Mode decision:
    ├─ Single → [Summarize 1 text] → Return 1 summary
    ├─ Per-row → [Summarize each] → Return list of summaries  
    └─ Aggregate → [Combine texts] → [Summarize combined] → Return 1 summary
```

---

## Common questions answered

**Q: Why not let users send their own database passwords?**  
A: Security risk. If passwords are intercepted or logged, your database is compromised. Server-side credentials are safer.

**Q: What if my table has a weird name like "my-table" or "My Table"?**  
A: Our validator only allows safe characters. If you need special names, you'll need to use standard naming (snake_case: `my_table`).

**Q: Can I fetch from multiple tables at once?**  
A: Not in Phase 1. Keep it simple: one table per request.

**Q: What if I want to fetch 1000 rows?**  
A: Current limit is 100 for safety. For larger batches, we'll add a background job system in Phase 2.

**Q: Will this slow down my database?**  
A: We use read-only credentials, timeouts, and row limits to minimize impact. Monitor your DB after deployment.

---

**Next step**: Tell me if this version makes sense, and I'll implement the code!

Decisions confirmed
-------------------
- Config key: `POSTGRES_READONLY_DSN_TEMPLATE` (server-side template containing credentials and host, with a `{db}` placeholder). Alternatively, separate env vars (host/user/pass) may be used and `database=db_name` passed to the driver.
- db_name allowed characters: letters, digits, underscore, hyphen. Validator: `^[A-Za-z0-9_-]+$`.
- Default limits:
  - `max_rows` for synchronous (non-job) requests: 100
  - `max_bytes` per row: 200_000 bytes (200 KB)
  - `statement_timeout`: 5 seconds
- `pg_mode` exposed to clients with allowed values `single`, `per_row`, `aggregate`.
  - If `id_value` present → mode `single` (client need not provide pg_mode)
  - If `id_start`/`id_end` present and pg_mode omitted → default `per_row` (as requested)

High-level components
---------------------
1. Configuration
   - `config/settings.py` must include `POSTGRES_READONLY_DSN_TEMPLATE` (or equivalent env vars). Template example: `postgresql://readonly_user:password@db-host:5432/{db}`.

2. Adapter module (utils)
   - New module: `utils/postgres_adapter.py` (or similar) with a small, focused API for server-side fetches.
   - Public function(s) (async):
     - `fetch_rows(db_name, table, id_column, text_column, id_value=None, id_start=None, id_end=None, limit=100, max_bytes=200000, timeout_seconds=5) -> List[Dict[id, text]]`
     - Optionally a wrapper `fetch_single_row_text(...)` that convenience-returns the single content string or raises if not found.

   Responsibilities:
   - Validate inputs (db_name, table, id_column, text_column) with strict regexes.
   - Build DSN safely from server template (only substitute `{db}` with validated db_name) OR connect via explicit host/user/pass env vars with `database=db_name` argument.
   - Quote identifiers safely for SQL (split `schema.table` into parts and double-quote each part).
   - Use `asyncpg` (or the chosen Postgres driver) to connect with a short timeout.
   - Set `statement_timeout` at connection-level (SET LOCAL) for query safety.
   - Use a parameterized query for any user-provided value (IDs). Never interpolate values.
   - Fetch at most `limit` rows (where `limit` is validated and capped by server-wide maximum).
   - Per-row handling: coerce bytes to UTF-8 text safely, truncate to `max_bytes`, and return list items `{ 'id': <id>, 'text': <string> }`.
   - Error mapping: raise `ValueError` for invalid inputs and `RuntimeError` for DB errors. Avoid leaking DB internals in exception messages.

3. Handler changes (`handlers/summarize_document.py`)
   - Replace/extend the existing postgres-related form fields as follows (example minimal set):
     - `pg_db` (db_name)
     - `pg_table`
     - `pg_id_column`
     - `pg_id_value` (optional, single id)
     - `pg_id_start` and `pg_id_end` (optional range)
     - `pg_text_column`
     - `pg_mode` (optional, choices: `single`, `per_row`, `aggregate`)
   - Input detection and validation logic:
     - If `pg_db` + `pg_table` + `pg_id_column` + `pg_text_column` are provided then consider Postgres path.
     - If `pg_id_value` present → single (ignore `pg_id_start`/`pg_id_end`).
     - Else if `pg_id_start`/`pg_id_end` present → treat as range.
     - Validate `pg_mode` if provided. If missing and range present, default to `per_row` (per your choice).
   - Calling adapter and integration:
     - Call `fetch_rows(...)` with appropriate arguments and `limit` set to server `max_rows`.
     - If `single` mode: expect exactly one row (or 404), extract `text` and call `Mode5.process_raw_text(text, source_name=..., target_words=..., output_format=..., user_prompt=...)`. Return the result with added metadata under `meta.ingest` describing db/table/id/text_column.
     - If `per_row` mode: iterate rows (best done with concurrency limit to avoid flooding the LLM provider and DB). For each row call `Mode5.process_raw_text` and collect results. Return a JSON structure `{ "summaries": [{"id": ..., "result": <mode5_result>}, ...] }`. Include per-row error entries if processing failed for a row.
     - If `aggregate` mode: concatenate the row texts (or, if combined size exceeds threshold, do hierarchical chunking: chunk -> summarize chunks -> merge summaries), then call `Mode5.process_raw_text` once and return consolidated summary with meta including `rows_covered`.

4. Concurrency & resource controls
   - In `per_row` mode, limit concurrent summarization tasks (e.g., semaphore concurrency = 3 or configurable) to protect the LLM and DB.
   - For synchronous requests, cap `limit` to `max_rows` (100). If client asks for more rows, return 400 requesting job-mode processing.
   - Provide guidance to use a job queue for very large ranges (Phase 2)

5. Validation rules
   - `db_name` validator: `^[A-Za-z0-9_-]+$`
   - `table` / `id_column` / `text_column` validator: `^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$` (supports optional `schema.table`).
   - `id_value` inference: if digits only -> integer; if UUID-like -> uuid; else treat as text. Validate conversion too.
   - `limit` must be positive and ≤ server hard cap (100 by default).

6. Error handling & HTTP mapping
   - `400 Bad Request` for validation errors, missing required postgres fields, or range too large for sync.
   - `404 Not Found` for single id missing row (or return 200 with empty summary if you prefer — but 404 is clearer).
   - `502 Bad Gateway` / `504 Gateway Timeout` for DB connectivity, auth failure, or statement timeout.
   - `500 Internal Server Error` for unexpected summarization failures.
   - In `per_row` mode, return per-row error details rather than failing the whole request.

7. Observability and logging
   - Log only steward-level metadata (counts, sizes in bytes, durations), never credentials or full content.
   - Emit metrics: rows_fetched, bytes_fetched, summarization_time_per_row, errors.
   - Add debug logs that can be enabled in staging to display query text and parameter shapes (still mask db credentials).

8. Tests
   - Unit tests for `utils/postgres_adapter` using `pytest` + `pytest-asyncio` and mocking `asyncpg`:
     - valid single row fetch returns expected text; test bytea decode and truncation
     - invalid identifier patterns raise `ValueError`
     - id parsing (int/uuid/text) validation and errors
     - DB errors map to `RuntimeError`
   - Handler tests:
     - Mock `fetch_rows` and `Mode5.process_raw_text` to assert handler returns expected shapes for `single`, `per_row`, and `aggregate` modes.
     - Test per-row error handling.

9. Rollout plan
   - Phase 1: implement adapter + handler changes for `single` and `per_row` (capped) and `aggregate` for small ranges. Require feature flag in staging.
   - Phase 2: add job queue (Redis + RQ/Celery or background worker) for large ranges and bulk. Add pooling per db profile if load requires it.
   - Phase 3: add admin UI to register read-only DB profiles and optional allowlisting of tables/columns per profile.

10. Security checklist
   - Use read-only DB user.
   - Do not accept client-sent connection strings.
   - Mask credentials in logs.
   - Rate-limit the endpoint. Consider requiring authentication (token) and RBAC for DB access.
   - Use parameterized queries and strict identifier validation.

11. Example request/response flows (conceptual)

Single row (default):
- Request fields: `pg_db`, `pg_table`, `pg_id_column`, `pg_id_value`, `pg_text_column`, `target_words` (optional)
- Server: fetch single row, call `Mode5.process_raw_text`, return `result` (same structure as existing summarizer responses) with added `meta.ingest` showing `source_type: 'postgres'` and db/table/id info.

Per-row (range):
- Request fields: `pg_db`, `pg_table`, `pg_id_column`, `pg_id_start`, `pg_id_end`, `pg_text_column`, `pg_mode='per_row'`, `target_words` (optional)
- Server: fetch up to `max_rows` rows, summarize each row individually, return `{"summaries": [{"id": <id>, "result": <mode5_result>}, ...]}` with per-row meta.

Aggregate (range):
- Request fields: same as per-row but `pg_mode='aggregate'`
- Server: fetch up to `max_rows` rows, combine texts (or do chunked hierarchical summarize), call `Mode5.process_raw_text` once, return consolidated summary and meta (including `rows_covered`).

12. Things to confirm before coding
- Handler parameter names to use in the function signature (`pg_db` vs `pg_database`, `pg_id_start` / `pg_id_end` naming).
- Whether `per_row` or `aggregate` should be the default for ranges (we will use `per_row` as requested).
- Exact server caps: confirm final `max_rows`, `max_bytes`, and `statement_timeout` values (defaults are 100, 200KB, 5s).

13. Next steps (after approval)
- I will implement the adapter in `utils/postgres_adapter.py` and add `asyncpg` to `requirements.txt`.
- Update `handlers/summarize_document.py` signature to accept `pg_db`, `pg_id_start`, `pg_id_end`, and `pg_mode` and wire to adapter.
- Add unit tests for the adapter (mocking asyncpg) and handler tests (mocking adapter + Mode5).
- Run tests, fix issues, iterate until green.

---

If you approve this plan I will produce the exact set of file patches (adapter + handler signature update + requirements change + tests stubs). If you want any minor changes to validators, naming, or defaults, tell me now and I will incorporate them into the patches.