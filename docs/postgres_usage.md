# PostgreSQL Input Source — Usage Guide

## Overview

The PostgreSQL input adapter allows you to summarize content directly from PostgreSQL databases without exporting or copying data. The server securely connects using pre-configured read-only credentials.

**Key Features:**
- Fetch and summarize individual rows or ranges
- Optional context column for better summarization (e.g., include title with description)
- Three modes: single row, per-row, or aggregate summaries
- Secure server-side credential management

**Context Column Behavior:**
- **Single mode**: Context prepended to the single row's text
- **Per-row mode**: Each row gets its own context prepended (e.g., "Title 1: Description 1", "Title 2: Description 2")
- **Aggregate mode**: All rows combined with their contexts (e.g., "Title 1: Description 1... Title 2: Description 2...")

## Configuration

### Server Setup (Required)

Set the `POSTGRES_READONLY_DSN_TEMPLATE` in your environment or `config/settings.py`:

```python
# config/settings.py or environment variable
POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://readonly_user:password@db-host:5432/{db}"
```

**Important**: The `{db}` placeholder will be replaced with the client-provided database name. Never expose write credentials.

### Security Best Practices

1. **Use read-only database users** — Grant SELECT permission only
2. **Use strong, unique passwords** for database accounts
3. **Store credentials securely** — Use environment variables or secret managers (AWS Secrets Manager, Azure Key Vault, etc.)
4. **Set connection limits** on the database user to prevent abuse
5. **Monitor query logs** for unusual patterns
6. **Use SSL/TLS connections** in production (add `?sslmode=require` to DSN)

Example secure DSN:
```
postgresql://readonly_user:SECRET_PASSWORD@db.example.com:5432/{db}?sslmode=require
```

## API Usage

### Endpoint

```
POST /summarize-document
Content-Type: multipart/form-data
```

### Three Modes

#### 1. Single Row (Default)

Summarize one specific row by ID.

**Request:**
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=customer_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_value=INC_01" \
  -F "pg_text_column=description" \
  -F "target_words=200"
```

**With optional context column (e.g., title for better summarization):**
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=customer_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_value=INC_01" \
  -F "pg_text_column=description" \
  -F "pg_context_column=title" \
  -F "target_words=200"
```

**Response:**
```json
{
  "summary": "...",
  "meta": {
    "ingest": {
      "source_type": "postgres",
      "db": "customer_db",
      "table": "incidents",
      "id": 42
    }
  }
}
```

#### 2. Per-Row Mode

Summarize multiple rows individually (one summary per row).

**Request:**
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=customer_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_start=INC_01" \
  -F "pg_id_end=INC_10" \
  -F "pg_text_column=description" \
  -F "pg_mode=per_row" \
  -F "target_words=100"
```

**With context column (each row gets its title prepended):**
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=customer_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_start=INC_01" \
  -F "pg_id_end=INC_10" \
  -F "pg_text_column=description" \
  -F "pg_context_column=title" \
  -F "pg_mode=per_row" \
  -F "target_words=100"
```

**Response:**
```json
{
  "summaries": [
    {
      "id": 10,
      "result": {
        "summary": "...",
        "meta": {...}
      }
    },
    {
      "id": 11,
      "result": {
        "summary": "...",
        "meta": {...}
      }
    }
  ],
  "mode": "per_row",
  "rows_processed": 11
}
```

#### 3. Aggregate Mode

Combine multiple rows and produce one consolidated summary.

**Request:**
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=customer_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_start=INC_01" \
  -F "pg_id_end=INC_10" \
  -F "pg_text_column=description" \
  -F "pg_mode=aggregate" \
  -F "target_words=300"
```

**With context column (all rows combined with their titles):**
```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=customer_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=id" \
  -F "pg_id_start=INC_01" \
  -F "pg_id_end=INC_10" \
  -F "pg_text_column=description" \
  -F "pg_context_column=title" \
  -F "pg_mode=aggregate" \
  -F "target_words=300"
```

**Response:**
```json
{
  "summary": "...",
  "meta": {
    "ingest": {
      "source_type": "postgres",
      "db": "customer_db",
      "table": "incidents",
      "rows_covered": 11,
      "mode": "aggregate"
    }
  }
}
```

## Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `pg_db` | Yes | Database name | `customer_db` |
| `pg_table` | Yes | Table name (optionally schema-qualified) | `incidents` or `public.incidents` |
| `pg_id_column` | Yes | Column containing the row ID | `id` |
| `pg_text_column` | Yes | Column containing text to summarize | `description` |
| `pg_context_column` | No | Optional column for additional context (prepended to text) | `title` |
| `pg_id_value` | Single mode | Specific row ID | `INC_01` |
| `pg_id_start` | Range modes | Range start ID | `INC_01` |
| `pg_id_end` | Range modes | Range end ID | `20` |
| `pg_mode` | No | Mode: `single`, `per_row`, or `aggregate` (default: `per_row` for ranges) | `aggregate` |
| `target_words` | No | Target summary length in words | `200` |
| `output_format` | No | Output format: `markdown`, `plain`, or `both` (default: `markdown`) | `markdown` |

## Limits

| Limit | Default | Purpose |
|-------|---------|---------|
| Max rows per request | 100 | Prevent large queries |
| Max bytes per row | 200 KB | Prevent memory issues |
| Query timeout | 5 seconds | Cancel slow queries |
| Concurrent summaries | 3 | Protect LLM rate limits |

## Validation Rules

### Database Name
- Pattern: `[A-Za-z0-9_-]+`
- Examples: `my_db`, `prod-db`, `db2024`

### Table/Column Names
- Pattern: `[A-Za-z_][A-Za-z0-9_]*` (with optional schema: `schema.table`)
- Examples: `incidents`, `public.user_data`, `my_table_2024`
- **Rejected**: `123table` (starts with number), `table-name` (hyphen), `table;drop` (semicolon)

### ID Values
- Auto-detected as: integer, UUID, or text
- Examples: `42` (int), `550e8400-e29b-41d4-a716-446655440000` (UUID), `abc123` (text)

## Error Handling

| Status | Meaning | Example |
|--------|---------|---------|
| 400 | Bad input (validation failed) | Invalid table name, missing fields |
| 404 | Row not found | Single-mode query found no row |
| 502 | Database error | Auth failure, connection timeout |
| 500 | Processing error | Summarizer failure |

## Examples

### Use Case 1: Customer Support Tickets

**Scenario**: Summarize a specific support ticket

```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=support_db" \
  -F "pg_table=tickets" \
  -F "pg_id_column=ticket_id" \
  -F "pg_id_value=T-12345" \
  -F "pg_text_column=conversation" \
  -F "target_words=150"
```

### Use Case 2: Weekly Incident Report

**Scenario**: Aggregate all incidents from the past week

```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=ops_db" \
  -F "pg_table=incidents" \
  -F "pg_id_column=created_at" \
  -F "pg_id_start=2024-01-01" \
  -F "pg_id_end=2024-01-07" \
  -F "pg_text_column=details" \
  -F "pg_mode=aggregate" \
  -F "target_words=500"
```

### Use Case 3: Batch Processing

**Scenario**: Summarize each of 50 customer reviews individually

```bash
curl -X POST http://localhost:8000/summarize-document \
  -F "pg_db=reviews_db" \
  -F "pg_table=product_reviews" \
  -F "pg_id_column=review_id" \
  -F "pg_id_start=1" \
  -F "pg_id_end=50" \
  -F "pg_text_column=review_text" \
  -F "pg_mode=per_row" \
  -F "target_words=50"
```

## Troubleshooting

### Error: "POSTGRES_READONLY_DSN_TEMPLATE not configured"

**Solution**: Set the DSN template in `config/settings.py` or as an environment variable:

```bash
export POSTGRES_READONLY_DSN_TEMPLATE="postgresql://readonly:pass@host:5432/{db}"
```

### Error: "Invalid table name"

**Cause**: Table name contains disallowed characters (e.g., semicolon, space, special chars)

**Solution**: Use standard SQL identifiers (letters, numbers, underscores only)

### Error: "Authentication failed to Postgres database"

**Cause**: Incorrect credentials in DSN template or database doesn't allow connections

**Solution**: Verify credentials, check firewall rules, ensure database accepts connections

### Error: "No rows found"

**Cause**: The specified ID or range doesn't exist in the table

**Solution**: Verify the ID exists, check for typos

## Performance Tips

1. **Use specific ID values** when possible (faster than ranges)
2. **Limit range sizes** — stay under 100 rows for synchronous requests
3. **Use aggregate mode** for large ranges when you need one summary
4. **Index ID columns** in your database for faster queries
5. **Monitor query times** — if consistently slow, add database indexes

## Next Steps

- **Phase 2**: Background job queue for very large ranges (1000+ rows)
- **Phase 3**: Stored connection profiles (register DBs once, reference by ID)
- **Phase 4**: Column whitelisting per database for additional security

## Support

For issues or feature requests, see the project README or open a GitHub issue.
