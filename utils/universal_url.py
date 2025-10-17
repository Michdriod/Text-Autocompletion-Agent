"""Universal URL handler for downloading documents from any accessible URL.

Supports:
- Google Drive (existing functionality)
- Any accessible URL serving PDF, DOCX, TXT files
- Cloud storage (Dropbox, OneDrive, Box, etc.)
- Direct file URLs from any server
- CDN-hosted documents
- Any publicly accessible document URL
"""

import os
import re
import tempfile
import logging
from typing import Optional, Tuple
import requests
from urllib.parse import urlparse, parse_qs

from .google_drive import download_from_google_drive, GoogleDriveError
from .file_utils import detect_extension_from_file

logger = logging.getLogger(__name__)

class UniversalURLError(Exception):
    """Exception raised for URL download errors."""
    pass

class UniversalURLHandler:
    """Handles downloading documents from any accessible URL."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Supported file extensions
        self.supported_extensions = {'.pdf', '.docx', '.txt', '.doc'}
        
        # Known cloud storage optimizations (for better handling)
        self.cloud_optimizations = {
            'dropbox': {
                'patterns': ['dropbox.com'],
                'transforms': [
                    (r'\?dl=0', '?dl=1'),
                    (r'&dl=0', '&dl=1')
                ]
            },
            'onedrive': {
                'patterns': ['onedrive.live.com', '1drv.ms'],
                'transforms': [
                    (r'$', '?download=1')  # Add download parameter
                ]
            },
            'sharepoint': {
                'patterns': ['sharepoint.com'],
                'transforms': [
                    (r'\?e=', '?download=1&e=')
                ]
            },
            'box': {
                'patterns': ['box.com'],
                'transforms': []
            }
        }

    def detect_url_type(self, url: str) -> str:
        """Detect the type of URL and return appropriate handler type.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Handler type: 'google_drive' or 'accessible_url'
        """
        url_lower = url.lower()
        
        # Google Drive URLs (use existing specialized handler)
        if any(pattern in url_lower for pattern in ['drive.google.com', 'docs.google.com']):
            return 'google_drive'
        
        # Everything else - try as accessible URL
        return 'accessible_url'

    def optimize_cloud_url(self, url: str) -> str:
        """Optimize cloud storage URLs for direct download when possible.
        
        Args:
            url: Original URL
            
        Returns:
            Optimized URL (or original if no optimization available)
        """
        url_lower = url.lower()
        
        # Apply known optimizations
        for service, config in self.cloud_optimizations.items():
            if any(pattern in url_lower for pattern in config['patterns']):
                optimized_url = url
                for pattern, replacement in config['transforms']:
                    optimized_url = re.sub(pattern, replacement, optimized_url)

                # Additional SharePoint handling: enforce download=1 if absent
                if service == 'sharepoint':
                    if 'download=1' not in optimized_url:
                        if '?' in optimized_url:
                            optimized_url += '&download=1'
                        else:
                            optimized_url += '?download=1'
                
                if optimized_url != url:
                    logger.info(f"Optimized {service} URL: {url} -> {optimized_url}")
                    return optimized_url
        
        return url

    def is_likely_document_url(self, url: str, content_type: str = None, content_length: str = None) -> bool:
        """Check if URL is likely to be a document based on various indicators.
        
        Args:
            url: The URL to check
            content_type: HTTP Content-Type header (if available)
            content_length: HTTP Content-Length header (if available)
            
        Returns:
            True if likely a document, False otherwise
        """
        url_lower = url.lower()
        
        # Check URL extension
        parsed = urlparse(url_lower)
        path = parsed.path.split('?')[0]  # Remove query params
        
        if any(path.endswith(ext) for ext in self.supported_extensions):
            return True
        
        # Check Content-Type if available
        if content_type:
            content_type_lower = content_type.lower()
            document_types = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain',
                'application/octet-stream'  # Sometimes used for binary files
            ]
            if any(doc_type in content_type_lower for doc_type in document_types):
                return True
        
        # Check for known cloud storage patterns (likely to be files)
        cloud_indicators = [
            'dropbox.com/s/',
            'dropbox.com/scl/',
            'onedrive.live.com',
            '1drv.ms',
            'sharepoint.com',
            'box.com',
            'icloud.com',
            'amazonaws.com',
            'storage.googleapis.com',
            'cdn.',
            'files.',
            'documents.',
            'attachments.'
        ]
        
        if any(indicator in url_lower for indicator in cloud_indicators):
            return True
        
        # Check file size (if very large, likely a document)
        if content_length:
            try:
                size_bytes = int(content_length)
                # Files between 1KB and 10MB are likely documents
                if 1024 <= size_bytes <= 10 * 1024 * 1024:
                    return True
            except ValueError:
                pass
        
        return False

    def download_accessible_url(self, url: str) -> Tuple[str, str, str]:
        """Download a file from any accessible URL.
        
        Args:
            url: Any accessible file URL
            
        Returns:
            Tuple of (file_path, detected_extension, original_filename)
            
        Raises:
            UniversalURLError: If download fails or file is unsupported
        """
        try:
            # First, optimize the URL if it's from a known cloud service
            download_url = self.optimize_cloud_url(url)
            
            logger.info(f"Attempting to download from: {download_url}")
            
            # Make HEAD request first to check headers without downloading
            try:
                head_response = self.session.head(download_url, timeout=10, allow_redirects=True)
                head_response.raise_for_status()
                
                content_type = head_response.headers.get('content-type', '')
                content_length = head_response.headers.get('content-length')
                
                logger.info(f"HEAD response - Content-Type: {content_type}, Content-Length: {content_length}")
                
                # Check if it looks like a document
                if not self.is_likely_document_url(download_url, content_type, content_length):
                    logger.warning(f"URL doesn't appear to be a document: {download_url}")
                    # Continue anyway - might still be a valid document
                
                # Check file size
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > 10:
                        raise UniversalURLError(f"File too large: {size_mb:.1f}MB (max 10MB)")
                
            except requests.RequestException as e:
                logger.warning(f"HEAD request failed, trying direct download: {e}")
                # Continue with GET request - some servers don't support HEAD
            
            # Make GET request to download the file
            response = self.session.get(download_url, stream=True, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Get final headers after redirects
            content_type = response.headers.get('content-type', '').lower()
            content_length = response.headers.get('content-length')
            
            logger.info(f"Download started - Content-Type: {content_type}, Content-Length: {content_length}")

            # SharePoint auth-wall / HTML page detection
            if 'sharepoint.com' in download_url.lower():
                if 'text/html' in content_type:
                    # Peek at a small portion of the content to look for auth markers
                    try:
                        preview_bytes = next(response.iter_content(chunk_size=2048))
                        preview_text = preview_bytes.decode('utf-8', errors='ignore')
                        auth_indicators = ['Sign in', 'login', 'auth', 'Access Denied', 'SharePoint']
                        if any(ind.lower() in preview_text.lower() for ind in auth_indicators):
                            raise UniversalURLError(
                                "SharePoint link appears to require authentication or is not a direct file. "
                                "Ensure the file is shared publicly (Anyone with the link) and try again."
                            )
                    except StopIteration:
                        raise UniversalURLError(
                            "Received empty HTML response from SharePoint. Ensure the link is a direct document link."
                        )
            
            # Extract filename from URL or headers
            filename = self._extract_filename(download_url, response.headers)
            
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp')
            
            try:
                # Download file in chunks with size monitoring
                with os.fdopen(temp_fd, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Check size limit during download
                            if downloaded > 10 * 1024 * 1024:  # 10MB
                                raise UniversalURLError("File too large (>10MB)")
                
                # Detect actual file type from content
                detected_extension = detect_extension_from_file(temp_path)
                
                # Validate file type
                if detected_extension not in self.supported_extensions:
                    raise UniversalURLError(
                        f"Unsupported file type: {detected_extension}. "
                        f"Supported: {', '.join(sorted(self.supported_extensions))}"
                    )
                
                # Check if file has actual content
                file_size = os.path.getsize(temp_path)
                if file_size < 100:  # Less than 100 bytes is suspicious
                    raise UniversalURLError("Downloaded file appears to be empty or invalid")
                
                # Rename file with correct extension
                final_path = temp_path.replace('.tmp', detected_extension)
                os.rename(temp_path, final_path)
                
                logger.info(f"Successfully downloaded: {filename} ({detected_extension}, {file_size} bytes)")
                return final_path, detected_extension, filename
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
                
        except requests.RequestException as e:
            logger.error(f"Request failed for URL {url}: {e}")
            
            # Provide more specific error messages
            if "403" in str(e):
                raise UniversalURLError("Access denied. The file may be private or require authentication.")
            elif "404" in str(e):
                raise UniversalURLError("File not found. Please check the URL.")
            elif "timeout" in str(e).lower():
                raise UniversalURLError("Download timeout. The server may be slow or unresponsive.")
            else:
                raise UniversalURLError(f"Failed to download file: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            raise UniversalURLError(f"Download error: {e}")

    def _extract_filename(self, url: str, headers: dict) -> str:
        """Extract filename from URL or response headers.
        
        Args:
            url: Original URL
            headers: Response headers
            
        Returns:
            Extracted filename
        """
        # Try Content-Disposition header first
        content_disposition = headers.get('content-disposition', '')
        if content_disposition:
            # Parse filename from header
            filename_match = re.search(r'filename[*]?=(?:"([^"]+)"|([^;]+))', content_disposition)
            if filename_match:
                filename = filename_match.group(1) or filename_match.group(2)
                return filename.strip()
        
        # Extract from URL path
        parsed = urlparse(url)
        path = parsed.path
        
        # Remove query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        # Get filename from path
        filename = os.path.basename(path)
        
        # Clean up the filename
        if filename:
            # Remove URL encoding
            filename = filename.replace('%20', ' ')
            
            # If filename has extension, use it
            if any(filename.lower().endswith(ext) for ext in self.supported_extensions):
                return filename
        
        # Fallback: try to extract from URL components
        path_parts = [part for part in path.split('/') if part]
        for part in reversed(path_parts):
            if any(ext in part.lower() for ext in self.supported_extensions):
                return part
        
        # Last resort: generate filename based on URL
        domain = parsed.netloc.replace('www.', '')
        return f"document_from_{domain}.pdf"

    def download_from_url(self, url: str) -> Tuple[str, str, str]:
        """Main method to download a document from any accessible URL.
        
        Args:
            url: Any document URL (Google Drive, cloud storage, direct link, etc.)
            
        Returns:
            Tuple of (file_path, detected_extension, original_filename)
            
        Raises:
            UniversalURLError: If URL is inaccessible or download fails
        """
        # Basic URL validation
        if not url or not url.strip():
            raise UniversalURLError("URL cannot be empty")
        
        url = url.strip()
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        url_type = self.detect_url_type(url)
        
        logger.info(f"Processing URL: {url} (detected type: {url_type})")
        
        if url_type == 'google_drive':
            try:
                # Use existing Google Drive handler for better reliability
                return download_from_google_drive(url)
            except GoogleDriveError as e:
                logger.warning(f"Google Drive handler failed: {e}, trying generic approach")
                # Fallback to generic handler
                return self.download_accessible_url(url)
        
        else:
            # Try to download from any accessible URL
            return self.download_accessible_url(url)


# Convenience functions for backward compatibility
def download_from_universal_url(url: str) -> Tuple[str, str, str]:
    """Download a document from any accessible URL.
    
    Args:
        url: Any document URL
        
    Returns:
        Tuple of (file_path, detected_extension, original_filename)
    """
    handler = UniversalURLHandler()
    return handler.download_from_url(url)


def detect_url_type(url: str) -> str:
    """Detect the type of URL.
    
    Args:
        url: URL to analyze
        
    Returns:
        URL type: 'google_drive' or 'accessible_url'
    """
    handler = UniversalURLHandler()
    return handler.detect_url_type(url)