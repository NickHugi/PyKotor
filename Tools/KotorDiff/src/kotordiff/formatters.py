#!/usr/bin/env python3
"""Output formatters for different diff formats.

DEPRECATED: This module has been migrated to pykotor.tslpatcher.diff.formatters
Import from there instead for shared library usage.

This file is kept for backwards compatibility with existing kotordiff code.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kotordiff.logger import diff_output, separator
from pykotor.tslpatcher.diff.formatters import (
    ContextFormatter as _ContextFormatter,
    DefaultFormatter as _DefaultFormatter,
    DiffFormatter as _DiffFormatter,
    SideBySideFormatter as _SideBySideFormatter,
    UnifiedFormatter as _UnifiedFormatter,
)
from pykotor.tslpatcher.diff.objects import DiffFormat

if TYPE_CHECKING:
    from pykotor.tslpatcher.diff.objects import DiffResult


# Re-export base classes with kotordiff-specific output handling
class DiffFormatter(_DiffFormatter):
    """Wrapper for shared DiffFormatter with kotordiff logger integration."""

    def __init__(self):
        """Initialize with kotordiff logger functions."""
        super().__init__(output_func=diff_output)


class DefaultFormatter(_DefaultFormatter):
    """Default formatter with kotordiff logger integration."""

    def __init__(self):
        """Initialize with kotordiff logger functions."""
        super().__init__(output_func=diff_output)

    def output_diff(self, diff_result: DiffResult[Any]) -> None:
        """Output with separator support from kotordiff logger."""
        formatted = self.format_diff(diff_result)
        if not formatted:
            return
        if diff_result.is_different:
            separator(formatted)
        else:
            diff_output(formatted)


class UnifiedFormatter(_UnifiedFormatter):
    """Unified formatter with kotordiff logger integration."""

    def __init__(self):
        """Initialize with kotordiff logger functions."""
        super().__init__(output_func=diff_output)


class ContextFormatter(_ContextFormatter):
    """Context formatter with kotordiff logger integration."""

    def __init__(self):
        """Initialize with kotordiff logger functions."""
        super().__init__(output_func=diff_output)


class SideBySideFormatter(_SideBySideFormatter):
    """Side-by-side formatter with kotordiff logger integration."""

    def __init__(self, width: int = 80):
        """Initialize with width and kotordiff logger functions."""
        super().__init__(width, output_func=diff_output)


class FormatterFactory:
    """Factory for creating diff formatters with kotordiff logger integration."""

    @staticmethod
    def create_formatter(format_type: DiffFormat, **kwargs) -> DiffFormatter:
        """Create a formatter of the specified type."""
        if format_type == DiffFormat.DEFAULT:
            return DefaultFormatter()
        if format_type == DiffFormat.UNIFIED:
            return UnifiedFormatter()
        if format_type == DiffFormat.CONTEXT:
            return ContextFormatter()
        if format_type == DiffFormat.SIDE_BY_SIDE:
            width = kwargs.get("width", 80)
            return SideBySideFormatter(width)
        error_msg = f"Unknown diff format: {format_type}"
        raise ValueError(error_msg)
