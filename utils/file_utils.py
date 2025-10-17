"""File utility functions for detecting file types and handling file operations."""

import os
import logging
from typing import Optional
import zipfile

logger = logging.getLogger(__name__)

def detect_extension_from_file(file_path: str) -> str:
    """Detect file extension by reading file headers/magic bytes.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Detected file extension (e.g., '.pdf', '.docx', '.txt')
        
    Raises:
        ValueError: If file type cannot be determined or is unsupported
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            # Read first 512 bytes to check file signatures
            header = f.read(512)
            
        if not header:
            raise ValueError("File appears to be empty")
        
        # Check file signatures (magic bytes)
        
        # PDF files start with %PDF
        if header.startswith(b'%PDF'):
            return '.pdf'
        
        # DOCX files are ZIP archives with specific structure
        if header.startswith(b'PK\x03\x04'):
            # This is a ZIP file, check if it's DOCX
            # DOCX files contain specific files in the ZIP
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    # Check for DOCX-specific files
                    if any('word/document.xml' in f for f in file_list):
                        return '.docx'
                    # Could be other Office formats, but we'll default to .docx for now
                    elif any(f.startswith('word/') for f in file_list):
                        return '.docx'
            except Exception as e:
                logger.warning(f"Could not analyze ZIP structure: {e}")
                # Assume it's DOCX if it's a ZIP file and we can't determine otherwise
                return '.docx'
        
        # DOC files (older Word format) start with specific signatures
        if (header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1') or  # OLE2 signature
            header.startswith(b'\xdb\xa5-\x00\x00\x00')):  # DOC signature
            return '.doc'
        
        # TXT files - check if content is mostly text
        if _is_text_file(header):
            return '.txt'
        
        # If we can't determine from magic bytes, try to guess from content
        logger.warning(f"Could not determine file type from magic bytes, analyzing content...")
        
        # Read more of the file to analyze
        with open(file_path, 'rb') as f:
            larger_sample = f.read(4096)  # Read first 4KB
        
        # Check if it's likely a text file
        if _is_text_file(larger_sample):
            return '.txt'
        
        # If all else fails, check the original filename if available
        # This is a fallback and not very reliable
        base_name = os.path.basename(file_path)
        if '.' in base_name:
            ext = os.path.splitext(base_name)[1].lower()
            if ext in ['.pdf', '.docx', '.doc', '.txt']:
                logger.warning(f"Using filename extension as fallback: {ext}")
                return ext
        
        # Unable to determine file type
        raise ValueError(f"Unable to determine file type. Supported formats: PDF, DOCX, DOC, TXT")
        
    except Exception as e:
        logger.error(f"Error detecting file type for {file_path}: {e}")
        raise ValueError(f"Error analyzing file: {e}")

def _is_text_file(data: bytes) -> bool:
    """Check if binary data appears to be text content.
    
    Args:
        data: Binary data to analyze
        
    Returns:
        True if data appears to be text, False otherwise
    """
    if not data:
        return False
    
    # Check for null bytes (common in binary files)
    if b'\x00' in data:
        return False
    
    try:
        # Try to decode as UTF-8
        text = data.decode('utf-8')
        
        # Check if most characters are printable
        printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
        total_chars = len(text)
        
        if total_chars == 0:
            return False
        
        # If more than 90% of characters are printable, consider it text
        printable_ratio = printable_chars / total_chars
        return printable_ratio > 0.9
        
    except UnicodeDecodeError:
        # Try other common encodings
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                text = data.decode(encoding)
                printable_chars = sum(1 for c in text if ord(c) < 128 and (c.isprintable() or c.isspace()))
                total_chars = len(text)
                
                if total_chars > 0:
                    printable_ratio = printable_chars / total_chars
                    if printable_ratio > 0.8:  # Lower threshold for other encodings
                        return True
            except UnicodeDecodeError:
                continue
        
        return False

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    if not os.path.exists(file_path):
        return 0.0
    
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

def is_supported_file_type(file_path: str) -> bool:
    """Check if file type is supported.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file type is supported, False otherwise
    """
    try:
        extension = detect_extension_from_file(file_path)
        return extension in ['.pdf', '.docx', '.doc', '.txt']
    except Exception:
        return False

def cleanup_temp_file(file_path: str) -> None:
    """Safely delete a temporary file.
    
    Args:
        file_path: Path to the file to delete
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Could not clean up temporary file {file_path}: {e}")