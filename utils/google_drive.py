"""Google Drive public file downloader utility.

Handles downloading files from public Google Drive share links.
Supports both regular uploaded files (PDF, DOCX) and Google Workspace files (Docs, Sheets, Slides).
"""
import re
import gdown
import requests
import tempfile
import os
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class GoogleDriveError(Exception):
    """Custom exception for Google Drive download errors."""
    pass

def extract_file_id(url: str) -> Optional[str]:
    """Extract Google Drive file ID from various URL formats.
    
    Supported formats:
    - https://drive.google.com/file/d/{FILE_ID}/view
    - https://drive.google.com/open?id={FILE_ID}
    - https://docs.google.com/document/d/{FILE_ID}/edit
    - https://docs.google.com/spreadsheets/d/{FILE_ID}/edit
    - https://docs.google.com/presentation/d/{FILE_ID}/edit
    
    Args:
        url: Google Drive or Docs URL
        
    Returns:
        File ID string or None if not found
    """
    patterns = [
        r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'docs\.google\.com/document/d/([a-zA-Z0-9_-]+)',
        r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)',
        r'docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]{25,})$'  # Direct ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def detect_file_type(url: str) -> str:
    """Detect if URL is a Google Workspace file or regular uploaded file.
    
    Returns:
        'document' | 'spreadsheet' | 'presentation' | 'file'
    """
    if 'docs.google.com/document' in url:
        return 'document'
    elif 'docs.google.com/spreadsheets' in url:
        return 'spreadsheet'
    elif 'docs.google.com/presentation' in url:
        return 'presentation'
    else:
        return 'file'
    
def download_from_google_drive(url: str, max_size_mb: int = 10) -> Tuple[str, str, str]:
    """Download a file from Google Drive (public share link) using gdown.
    
    Args:
        url: Google Drive or Docs share URL
        max_size_mb: Maximum file size in MB (default 10MB)
        
    Returns:
        Tuple of (temp_file_path, extension, file_type)
        
    Raises:
        GoogleDriveError: If URL is invalid or download fails
    """
    # Extract file ID
    file_id = extract_file_id(url)
    if not file_id:
        raise GoogleDriveError(
            "Invalid Google Drive URL. Please provide a valid share link."
        )
    
    # Detect file type
    file_type = detect_file_type(url)
    
    logger.info(f"Detected file type: {file_type}, ID: {file_id}")
    
    # Build download URL - let gdown handle redirects
    download_url = f"https://drive.google.com/uc?id={file_id}"
    
    # Create temp file WITHOUT forcing extension
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='')
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        logger.info(f"Downloading from Google Drive using gdown: {file_id}")
        
        # Use gdown with fuzzy=True to handle various URL formats
        output = gdown.download(
            url=download_url,
            output=temp_path,
            quiet=False,
            fuzzy=True
        )
        
        if output is None:
            raise GoogleDriveError(
                "Failed to download file. Please ensure:\n"
                "1. The file is shared as 'Anyone with the link can view'\n"
                "2. The link is correct and accessible\n"
                "3. The file exists and hasn't been deleted"
            )
        
        # Check file size
        file_size = os.path.getsize(temp_path)
        size_mb = file_size / (1024 * 1024)
        
        if size_mb > max_size_mb:
            os.remove(temp_path)
            raise GoogleDriveError(
                f"File too large: {size_mb:.1f}MB exceeds {max_size_mb}MB limit"
            )
        
        logger.info(f"Successfully downloaded {size_mb:.1f}MB to {temp_path}")
        
        # Detect actual file extension from downloaded file
        extension = detect_extension_from_file(temp_path)
        
        # Rename file with correct extension
        if extension and extension != '':
            new_temp_path = temp_path + extension
            os.rename(temp_path, new_temp_path)
            temp_path = new_temp_path
            logger.info(f"Renamed to {temp_path} with extension {extension}")
        else:
            extension = '.bin'
        
        return temp_path, extension, file_type
        
    except Exception as e:
        # Clean up on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        error_msg = str(e)
        
        # Provide helpful error messages
        if "Cannot retrieve the public link" in error_msg:
            raise GoogleDriveError(
                "Cannot access the file. Please ensure it's shared as 'Anyone with the link can view'."
            )
        elif "Permission denied" in error_msg or "403" in error_msg:
            raise GoogleDriveError(
                "Access denied. The file must be shared publicly or with 'Anyone with the link'."
            )
        elif "404" in error_msg:
            raise GoogleDriveError(
                "File not found. Please check if the link is correct and the file still exists."
            )
        else:
            raise GoogleDriveError(
                f"Failed to download from Google Drive: {error_msg}"
            )


def detect_extension_from_file(file_path: str) -> str:
    """Detect file extension from actual file content using magic numbers."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
        
        # Check magic numbers (file signatures)
        if header.startswith(b'%PDF'):
            return '.pdf'
        elif header.startswith(b'PK\x03\x04'):
            # ZIP-based formats (DOCX, XLSX, etc.)
            # Read more to differentiate
            with open(file_path, 'rb') as f:
                content = f.read(1000)
                if b'word/' in content:
                    return '.docx'
                elif b'xl/' in content:
                    return '.xlsx'
                elif b'ppt/' in content:
                    return '.pptx'
                else:
                    return '.zip'
        elif header.startswith(b'\xd0\xcf\x11\xe0'):
            # Old Office formats (DOC, XLS, etc.)
            return '.doc'
        else:
            # Fallback to mimetypes
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                ext_map = {
                    'application/pdf': '.pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                    'text/plain': '.txt',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx'
                }
                return ext_map.get(mime_type, '.bin')
            
            return '.bin'
    except Exception as e:
        logger.warning(f"Could not detect file extension: {e}")
        return '.bin'


__all__ = ["download_from_google_drive", "GoogleDriveError"]
    
# def download_google_workspace_file(file_id: str, file_type: str, max_size_mb: int = 10) -> Tuple[str, str]:
#     """Download a Google Workspace file (Doc, Sheet, Slide) via export endpoint.
    
#     Args:
#         file_id: Google Drive file ID
#         file_type: 'document' | 'spreadsheet' | 'presentation'
#         max_size_mb: Maximum file size in MB
        
#     Returns:
#         Tuple of (temp_file_path, extension)
        
#     Raises:
#         GoogleDriveError: If download fails
#     """
#     # Map file type to export format and extension
#     export_configs = {
#         'document': ('pdf', '.pdf', 'https://docs.google.com/document/d/{}/export?format=pdf'),
#         'spreadsheet': ('xlsx', '.xlsx', 'https://docs.google.com/spreadsheets/d/{}/export?format=xlsx'),
#         'presentation': ('pdf', '.pdf', 'https://docs.google.com/presentation/d/{}/export?format=pdf')
#     }
    
#     if file_type not in export_configs:
#         raise GoogleDriveError(f"Unsupported Google Workspace file type: {file_type}")
    
#     export_format, extension, url_template = export_configs[file_type]
#     export_url = url_template.format(file_id)
    
#     try:
#         logger.info(f"Exporting Google {file_type} to {export_format}: {file_id}")
        
#         response = requests.get(export_url, stream=True, timeout=30)
#         response.raise_for_status()
        
#         # Check content length
#         content_length = response.headers.get('content-length')
#         if content_length:
#             size_mb = int(content_length) / (1024 * 1024)
#             if size_mb > max_size_mb:
#                 raise GoogleDriveError(
#                     f"File too large: {size_mb:.1f}MB exceeds {max_size_mb}MB limit"
#                 )
        
#         # Download to temp file
#         with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
#             downloaded_size = 0
#             for chunk in response.iter_content(chunk_size=8192):
#                 if chunk:
#                     tmp.write(chunk)
#                     downloaded_size += len(chunk)
                    
#                     # Check size during download
#                     if downloaded_size > max_size_mb * 1024 * 1024:
#                         tmp.close()
#                         os.unlink(tmp.name)
#                         raise GoogleDriveError(
#                             f"Download exceeded {max_size_mb}MB limit"
#                         )
            
#             temp_path = tmp.name
        
#         logger.info(f"Downloaded {downloaded_size / 1024:.1f}KB to {temp_path}")
#         return temp_path, extension
        
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Failed to export Google {file_type}: {e}")
#         raise GoogleDriveError(
#             f"Failed to export Google {file_type}. "
#             "Make sure the file is shared as 'Anyone with the link can view'."
#         )

# def download_regular_file(file_id: str, max_size_mb: int = 10) -> Tuple[str, str]:
#     """Download a regular file from Google Drive (PDF, DOCX, etc.).
    
#     Args:
#         file_id: Google Drive file ID
#         max_size_mb: Maximum file size in MB
        
#     Returns:
#         Tuple of (temp_file_path, extension)
        
#     Raises:
#         GoogleDriveError: If download fails
#     """
#     download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
#     try:
#         logger.info(f"Downloading regular file from Google Drive: {file_id}")
        
#         # Handle large file confirmation
#         session = requests.Session()
#         response = session.get(download_url, stream=True, timeout=30)
        
#         # Check for large file confirmation token
#         token = None
#         for key, value in response.cookies.items():
#             if key.startswith('download_warning'):
#                 token = value
#                 break
        
#         if token:
#             params = {'export': 'download', 'id': file_id, 'confirm': token}
#             response = session.get(download_url, params=params, stream=True, timeout=30)
        
#         response.raise_for_status()
        
#         # Check content length
#         content_length = response.headers.get('content-length')
#         if content_length:
#             size_mb = int(content_length) / (1024 * 1024)
#             if size_mb > max_size_mb:
#                 raise GoogleDriveError(
#                     f"File too large: {size_mb:.1f}MB exceeds {max_size_mb}MB limit"
#                 )
        
#         # Guess file extension
#         extension = '.bin'
#         content_type = response.headers.get('content-type', '')
#         content_disposition = response.headers.get('content-disposition', '')
        
#         # Extract from content-disposition header
#         if 'filename=' in content_disposition:
#             filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
#             if filename_match:
#                 filename = filename_match.group(1)
#                 _, ext = os.path.splitext(filename)
#                 if ext:
#                     extension = ext
        
#         # Fallback to content-type
#         if extension == '.bin':
#             content_type_map = {
#                 'application/pdf': '.pdf',
#                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
#                 'text/plain': '.txt'
#             }
#             extension = content_type_map.get(content_type, '.bin')
        
#         # Download to temp file
#         with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
#             downloaded_size = 0
#             for chunk in response.iter_content(chunk_size=8192):
#                 if chunk:
#                     tmp.write(chunk)
#                     downloaded_size += len(chunk)
                    
#                     if downloaded_size > max_size_mb * 1024 * 1024:
#                         tmp.close()
#                         os.unlink(tmp.name)
#                         raise GoogleDriveError(
#                             f"Download exceeded {max_size_mb}MB limit"
#                         )
            
#             temp_path = tmp.name
        
#         logger.info(f"Downloaded {downloaded_size / 1024:.1f}KB to {temp_path}")
#         return temp_path, extension
        
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Failed to download file from Google Drive: {e}")
#         raise GoogleDriveError(
#             f"Failed to download file. "
#             "Make sure the file is shared as 'Anyone with the link can view'."
#         )

# def download_from_google_drive(url: str, max_size_mb: int = 10) -> Tuple[str, str, str]:
#     """Download a file from Google Drive (public share link).
    
#     Handles both regular uploaded files and Google Workspace files.
    
#     Args:
#         url: Google Drive or Docs share URL
#         max_size_mb: Maximum file size in MB (default 10MB)
        
#     Returns:
#         Tuple of (temp_file_path, extension, file_type)
#         file_type is 'document' | 'spreadsheet' | 'presentation' | 'file'
        
#     Raises:
#         GoogleDriveError: If URL is invalid or download fails
#     """
#     # Extract file ID
#     file_id = extract_file_id(url)
#     if not file_id:
#         raise GoogleDriveError(
#             "Invalid Google Drive URL. Please provide a valid share link."
#         )
    
#     # Detect file type
#     file_type = detect_file_type(url)
    
#     logger.info(f"Detected file type: {file_type}, ID: {file_id}")
    
#     # Download based on type
#     if file_type in ['document', 'spreadsheet', 'presentation']:
#         temp_path, extension = download_google_workspace_file(file_id, file_type, max_size_mb)
#     else:
#         temp_path, extension = download_regular_file(file_id, max_size_mb)
    
#     return temp_path, extension, file_type


# __all__ = ["download_from_google_drive", "GoogleDriveError"]