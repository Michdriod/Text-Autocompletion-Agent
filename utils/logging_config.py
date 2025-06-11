# Logging configuration for the Multi-Mode Text Enrichment System
# Provides structured logging with different levels and formatters

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from config import get_config

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    config = get_config()
    
    # Use config values if not provided
    log_level = log_level or config.log_level.value
    
    # Create logger
    logger = logging.getLogger("text_enrichment")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=config.log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger

def get_logger(name: str = "text_enrichment") -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

# Request logging middleware
class RequestLoggingMiddleware:
    """Middleware to log HTTP requests and responses."""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Log request
            method = scope["method"]
            path = scope["path"]
            query_string = scope.get("query_string", b"").decode()
            
            self.logger.info(f"Request: {method} {path}?{query_string}")
            
            # Wrap send to log response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    self.logger.info(f"Response: {status_code} for {method} {path}")
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# Performance logging decorator
import time
import functools

def log_performance(logger_name: str = "performance"):
    """Decorator to log function execution time."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func.__name__} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func.__name__} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
