"""Agnostic system utilities for cross-platform compatibility."""

from __future__ import annotations


def askdirectory(title: str = "Select Directory") -> str:
    """Ask user to select a directory using console input.
    
    Args:
    ----
        title: The title for the dialog window
        
    Returns:
    -------
        str: The selected directory path, or empty string if cancelled
    """
    result = input(f"{title}: ").strip()
    return result


def askopenfilename(title: str = "Select File") -> str:
    """Ask user to select a file using console input.
    
    Args:
    ----
        title: The title for the dialog window
        
    Returns:
    -------
        str: The selected file path, or empty string if cancelled
    """
    result = input(f"{title}: ").strip()
    return result