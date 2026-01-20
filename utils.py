"""Utility functions for file management and helpers"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Remove invalid characters from filename
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    # Truncate if too long (leave room for path)
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename.strip()


def create_directory(path: str) -> bool:
    """
    Create directory if it doesn't exist
    
    Args:
        path: Directory path to create
        
    Returns:
        True if successful, False otherwise
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def get_file_extension(url: str, default: str = ".png") -> str:
    """
    Extract file extension from URL
    
    Args:
        url: Image URL
        default: Default extension if not found
        
    Returns:
        File extension including dot
    """
    # Try to get extension from URL path
    match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
    if match:
        ext = match.group(1).lower()
        # Common image extensions
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']:
            return f".{ext}"
    return default


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes into human readable string
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO"):
    """
    Setup logging configuration
    
    Args:
        log_file: Path to log file (optional)
        log_level: Logging level
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
