"""Unit tests for PostgreSQL input adapter.

Tests validation, query construction, error handling, and data processing
using mocked asyncpg connections.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from utils.postgres_input import (
    fetch_rows,
    fetch_single_row_text,
    _validate_db_name,
    _validate_identifier,
    _quote_identifier,
    _infer_id_type,
)


class TestValidation:
    """Test input validation functions."""
    
    def test_validate_db_name_valid(self):
        assert _validate_db_name("mydb") is True
        assert _validate_db_name("my_db") is True
        assert _validate_db_name("my-db") is True
        assert _validate_db_name("db123") is True
    
    def test_validate_db_name_invalid(self):
        assert _validate_db_name("my.db") is False
        assert _validate_db_name("my db") is False
        assert _validate_db_name("my;db") is False
        assert _validate_db_name("") is False
    
    def test_validate_identifier_valid(self):
        assert _validate_identifier("table_name") is True
        assert _validate_identifier("_table") is True
        assert _validate_identifier("Table123") is True
        assert _validate_identifier("schema.table") is True
        assert _validate_identifier("my_schema.my_table") is True
    
    def test_validate_identifier_invalid(self):
        assert _validate_identifier("123table") is False
        assert _validate_identifier("table-name") is False
        assert _validate_identifier("table name") is False
        assert _validate_identifier("table;drop") is False
        assert _validate_identifier("") is False
        assert _validate_identifier("schema..table") is False
    
    def test_quote_identifier(self):
        assert _quote_identifier("table") == '"table"'
        assert _quote_identifier("schema.table") == '"schema"."table"'
        assert _quote_identifier("my_table") == '"my_table"'
    
    def test_infer_id_type(self):
        assert _infer_id_type("123") == "int"
        assert _infer_id_type("0") == "int"
        assert _infer_id_type("550e8400-e29b-41d4-a716-446655440000") == "uuid"
        assert _infer_id_type("abc123") == "text"
        assert _infer_id_type("123abc") == "text"


@pytest.mark.asyncio
class TestFetchRows:
    """Test fetch_rows function with mocked asyncpg."""
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_fetch_single_row_success(self, mock_settings, mock_asyncpg):
        """Test successful single row fetch."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 42, "content": "Test content"}
        ]
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        
        rows = await fetch_rows(
            db_name="testdb",
            table="incidents",
            id_column="id",
            text_column="description",
            id_value="42"
        )
        
        assert len(rows) == 1
        assert rows[0]["id"] == 42
        assert rows[0]["text"] == "Test content"
        mock_conn.close.assert_called_once()
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_fetch_range_success(self, mock_settings, mock_asyncpg):
        """Test successful range query."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 10, "content": "Content 10"},
            {"id": 11, "content": "Content 11"},
            {"id": 12, "content": "Content 12"},
        ]
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        
        rows = await fetch_rows(
            db_name="testdb",
            table="incidents",
            id_column="id",
            text_column="description",
            id_start="10",
            id_end="12"
        )
        
        assert len(rows) == 3
        assert rows[0]["id"] == 10
        assert rows[2]["id"] == 12
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_invalid_db_name_raises(self, mock_settings, mock_asyncpg):
        """Test that invalid db_name raises ValueError."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        with pytest.raises(ValueError, match="Invalid db_name"):
            await fetch_rows(
                db_name="test;db",  # Invalid character
                table="incidents",
                id_column="id",
                text_column="description",
                id_value="42"
            )
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_invalid_table_raises(self, mock_settings, mock_asyncpg):
        """Test that invalid table name raises ValueError."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        with pytest.raises(ValueError, match="Invalid table"):
            await fetch_rows(
                db_name="testdb",
                table="incidents; DROP TABLE users; --",  # SQL injection attempt
                id_column="id",
                text_column="description",
                id_value="42"
            )
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_truncation_of_large_content(self, mock_settings, mock_asyncpg):
        """Test that large content is truncated to max_bytes."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        large_content = "A" * 300_000  # 300KB
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 42, "content": large_content}
        ]
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        
        rows = await fetch_rows(
            db_name="testdb",
            table="incidents",
            id_column="id",
            text_column="description",
            id_value="42",
            max_bytes=200_000
        )
        
        assert len(rows[0]["text"].encode("utf-8")) <= 200_000
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_bytea_column_decoded(self, mock_settings, mock_asyncpg):
        """Test that bytea columns are decoded to text."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 42, "content": b"Binary content"}
        ]
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        
        rows = await fetch_rows(
            db_name="testdb",
            table="incidents",
            id_column="id",
            text_column="description",
            id_value="42"
        )
        
        assert rows[0]["text"] == "Binary content"
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_missing_dsn_template_raises(self, mock_settings, mock_asyncpg):
        """Test that missing DSN template raises RuntimeError."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = None
        
        with pytest.raises(RuntimeError, match="not configured"):
            await fetch_rows(
                db_name="testdb",
                table="incidents",
                id_column="id",
                text_column="description",
                id_value="42"
            )
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_context_column_prepended(self, mock_settings, mock_asyncpg):
        """Test that context column is prepended to content when provided."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 1, "context": "Database Connection Timeout", "content": "Users are experiencing intermittent timeouts..."}
        ]
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        
        rows = await fetch_rows(
            db_name="testdb",
            table="incidents",
            id_column="id",
            text_column="description",
            context_column="title",
            id_value="1"
        )
        
        assert len(rows) == 1
        assert rows[0]["text"].startswith("Database Connection Timeout:")
        assert "Users are experiencing intermittent timeouts" in rows[0]["text"]
    
    @patch('utils.postgres_input.asyncpg')
    @patch('utils.postgres_input.settings')
    async def test_context_column_optional(self, mock_settings, mock_asyncpg):
        """Test that context column is optional and doesn't break when not provided."""
        mock_settings.POSTGRES_READONLY_DSN_TEMPLATE = "postgresql://user:pass@host:5432/{db}"
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 1, "content": "Users are experiencing intermittent timeouts..."}
        ]
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        
        rows = await fetch_rows(
            db_name="testdb",
            table="incidents",
            id_column="id",
            text_column="description",
            id_value="1"
            # No context_column parameter
        )
        
        assert len(rows) == 1
        assert rows[0]["text"] == "Users are experiencing intermittent timeouts..."


@pytest.mark.asyncio
class TestFetchSingleRowText:
    """Test fetch_single_row_text convenience wrapper."""
    
    @patch('utils.postgres_input.fetch_rows')
    async def test_success(self, mock_fetch_rows):
        """Test successful single row text fetch."""
        mock_fetch_rows.return_value = [{"id": 42, "text": "Test content"}]
        
        text = await fetch_single_row_text(
            db_name="testdb",
            table="incidents",
            id_column="id",
            id_value="42",
            text_column="description"
        )
        
        assert text == "Test content"
    
    @patch('utils.postgres_input.fetch_rows')
    async def test_not_found_raises(self, mock_fetch_rows):
        """Test that missing row raises ValueError."""
        mock_fetch_rows.return_value = []
        
        with pytest.raises(ValueError, match="No row found"):
            await fetch_single_row_text(
                db_name="testdb",
                table="incidents",
                id_column="id",
                id_value="999",
                text_column="description"
            )
    
    @patch('utils.postgres_input.fetch_rows')
    async def test_empty_content_raises(self, mock_fetch_rows):
        """Test that empty content raises ValueError."""
        mock_fetch_rows.return_value = [{"id": 42, "text": "   "}]
        
        with pytest.raises(ValueError, match="empty content"):
            await fetch_single_row_text(
                db_name="testdb",
                table="incidents",
                id_column="id",
                id_value="42",
                text_column="description"
            )
