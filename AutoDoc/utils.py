"""Utility functions for AutoDoc."""

import os
import sys
import importlib.util
from typing import Dict, List, Any, Optional, Set


def find_python_files(directory: str, exclude_dirs: List[str] = None) -> List[str]:
    """
    Find all Python files in a directory and its subdirectories.
    
    Args:
        directory: Root directory to search
        exclude_dirs: Directories to exclude from the search
        
    Returns:
        List of paths to Python files
    """
    exclude_dirs = exclude_dirs or []
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    return python_files


def get_module_name(file_path: str, base_dir: str) -> str:
    """
    Get the importable module name from a file path.
    
    Args:
        file_path: Path to the Python file
        base_dir: Base directory of the project
        
    Returns:
        Importable module name
    """
    rel_path = os.path.relpath(file_path, base_dir)
    module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")
    return module_path


def is_valid_module(module_name: str) -> bool:
    """
    Check if a module name is valid and importable.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        True if the module is valid, False otherwise
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ValueError):
        return False


def count_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    This is a simple approximation, not exact.
    
    Args:
        text: The text to count tokens for
        
    Returns:
        Estimated token count
    """
    # A simple heuristic: about 4 characters per token for English text
    return len(text) // 4


def split_into_chunks(text: str, max_tokens: int = 8000) -> List[str]:
    """
    Split a long text into smaller chunks.
    
    Args:
        text: Text to split
        max_tokens: Maximum tokens per chunk
        
    Returns:
        List of text chunks
    """
    # Simple line-based chunking
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_tokens = count_tokens(line)
        
        if current_size + line_tokens > max_tokens and current_chunk:
            # Start a new chunk
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_size = line_tokens
        else:
            # Add to current chunk
            current_chunk.append(line)
            current_size += line_tokens
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    
    return chunks


def safe_mkdir(directory: str) -> None:
    """
    Safely create a directory if it doesn't exist.
    
    Args:
        directory: Path to the directory
    """
    os.makedirs(directory, exist_ok=True)
