#!/usr/bin/env python3
"""Output formatters for different diff formats.

This module provides formatters that convert structured DiffResult objects
into various human-readable output formats (unified, context, side-by-side, etc.).
"""
from __future__ import annotations

import difflib
import traceback

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

from pykotor.tslpatcher.diff.objects import DiffFormat, DiffType, GFFDiffResult, ResourceDiffResult, TLKDiffResult, TwoDADiffResult

if TYPE_CHECKING:
    from pykotor.tslpatcher.diff.objects import DiffResult


class DiffFormatter(ABC):
    """Abstract base class for diff formatters."""

    def __init__(self, output_func: Callable[[str], None] | None = None):
        """Initialize formatter with optional output function.

        Args:
            output_func: Function to call for output (default: print)
        """
        self.output_func: Callable[[str], None] = output_func or print

    @abstractmethod
    def format_diff(self, diff_result: DiffResult[Any]) -> str:
        """Format a diff result into a string."""

    def output_diff(self, diff_result: DiffResult[Any]) -> None:
        """Output a formatted diff result."""
        formatted = self.format_diff(diff_result)
        if formatted:
            self.output_func(formatted)


class DefaultFormatter(DiffFormatter):
    """Default formatter that maintains existing KotorDiff behavior."""

    def format_diff(self, diff_result: DiffResult[Any]) -> str:  # noqa: PLR0911
        """Format using the default style."""
        if diff_result.has_error:
            return f"[Error] {diff_result.error_message}"

        if diff_result.diff_type == DiffType.IDENTICAL:
            return ""  # No output for identical files

        if diff_result.diff_type == DiffType.ADDED:
            return f"Resource added: '{diff_result.right_identifier}'"

        if diff_result.diff_type == DiffType.REMOVED:
            return f"Resource removed: '{diff_result.left_identifier}'"

        # Handle specific diff types
        if isinstance(diff_result, ResourceDiffResult):
            return self._format_resource_diff(diff_result)
        if isinstance(diff_result, GFFDiffResult):
            return self._format_gff_diff(diff_result)
        if isinstance(diff_result, TwoDADiffResult):
            return self._format_2da_diff(diff_result)
        if isinstance(diff_result, TLKDiffResult):
            return self._format_tlk_diff(diff_result)

        return f"'{diff_result.left_identifier}' differs from '{diff_result.right_identifier}'"

    def _format_resource_diff(self, diff_result: ResourceDiffResult) -> str:
        """Format a resource diff."""
        size_info = ""
        if diff_result.left_size is not None and diff_result.right_size is not None:
            size_info = f" (sizes: {diff_result.left_size} vs {diff_result.right_size})"

        resource_type = f" [{diff_result.resource_type}]" if diff_result.resource_type else ""

        return f"'{diff_result.left_identifier}'{resource_type} differs from '{diff_result.right_identifier}'{size_info}"

    def _format_gff_diff(self, diff_result: GFFDiffResult) -> str:
        """Format a GFF diff."""
        base_msg = f"GFF '{diff_result.left_identifier}' differs from '{diff_result.right_identifier}'"

        if diff_result.field_diffs:
            field_count = len(diff_result.field_diffs)
            base_msg += f" ({field_count} field differences)"

        return base_msg

    def _format_2da_diff(self, diff_result: TwoDADiffResult) -> str:
        """Format a 2DA diff."""
        base_msg = f"2DA '{diff_result.left_identifier}' differs from '{diff_result.right_identifier}'"

        diff_counts = []
        if diff_result.header_diffs:
            diff_counts.append(f"{len(diff_result.header_diffs)} header")
        if diff_result.row_diffs:
            diff_counts.append(f"{len(diff_result.row_diffs)} row")
        if diff_result.column_diffs:
            diff_counts.append(f"{len(diff_result.column_diffs)} column")

        if diff_counts:
            base_msg += f" ({', '.join(diff_counts)} differences)"

        return base_msg

    def _format_tlk_diff(self, diff_result: TLKDiffResult) -> str:
        """Format a TLK diff."""
        base_msg = f"TLK '{diff_result.left_identifier}' differs from '{diff_result.right_identifier}'"

        if diff_result.entry_diffs:
            entry_count = len(diff_result.entry_diffs)
            base_msg += f" ({entry_count} entry differences)"

        return base_msg


class UnifiedFormatter(DiffFormatter):
    """Unified diff formatter (similar to `diff -u`)."""

    def format_diff(self, diff_result: DiffResult[Any]) -> str:
        """Format using unified diff style."""
        if diff_result.has_error:
            return f"diff: {diff_result.error_message}"

        if diff_result.diff_type == DiffType.IDENTICAL:
            return ""  # No output for identical files in unified diff

        if diff_result.diff_type == DiffType.ADDED:
            return f"--- /dev/null\n+++ {diff_result.right_identifier}"

        if diff_result.diff_type == DiffType.REMOVED:
            return f"--- {diff_result.left_identifier}\n+++ /dev/null"

        # For modified files, try to create a meaningful unified diff
        header = f"--- {diff_result.left_identifier}\n+++ {diff_result.right_identifier}"

        # Handle text-like content
        if isinstance(diff_result, ResourceDiffResult) and diff_result.resource_type in ("txt", "nss"):
            try:
                if diff_result.left_value is not None and diff_result.right_value is not None:
                    left_lines = diff_result.left_value.decode("utf-8", errors="ignore").splitlines(keepends=True)
                    right_lines = diff_result.right_value.decode("utf-8", errors="ignore").splitlines(keepends=True)
                else:
                    left_lines = []
                    right_lines = []

                diff_lines = list(difflib.unified_diff(
                    left_lines,
                    right_lines,
                    fromfile=diff_result.left_identifier,
                    tofile=diff_result.right_identifier,
                    lineterm="",
                ))

                return "\n".join(diff_lines)
            except Exception as e:  # noqa: BLE001
                print(f"Error formatting unified diff: {e.__class__.__name__}: {e}")
                print("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    print(f"  {line}")

        # For binary or structured files, just show the header
        return header + "\nBinary files differ"


class ContextFormatter(DiffFormatter):
    """Context diff formatter (similar to `diff -c`)."""

    def format_diff(self, diff_result: DiffResult[Any]) -> str:
        """Format using context diff style."""
        if diff_result.has_error:
            return f"diff: {diff_result.error_message}"

        if diff_result.diff_type == DiffType.IDENTICAL:
            return ""

        if diff_result.diff_type == DiffType.ADDED:
            return f"*** /dev/null\n--- {diff_result.right_identifier}"

        if diff_result.diff_type == DiffType.REMOVED:
            return f"*** {diff_result.left_identifier}\n--- /dev/null"

        # For modified files
        header = f"*** {diff_result.left_identifier}\n--- {diff_result.right_identifier}"

        # Handle text-like content
        if isinstance(diff_result, ResourceDiffResult) and diff_result.resource_type in ("txt", "nss"):
            try:
                if diff_result.left_value is not None and diff_result.right_value is not None:
                    left_lines = diff_result.left_value.decode("utf-8", errors="ignore").splitlines(keepends=True)
                    right_lines = diff_result.right_value.decode("utf-8", errors="ignore").splitlines(keepends=True)
                else:
                    left_lines = []
                    right_lines = []

                diff_lines = list(difflib.context_diff(
                    left_lines,
                    right_lines,
                    fromfile=diff_result.left_identifier,
                    tofile=diff_result.right_identifier,
                    lineterm="",
                ))

                return "\n".join(diff_lines)
            except Exception as e:  # noqa: BLE001
                print(f"Error formatting context diff: {e.__class__.__name__}: {e}")
                print("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    print(f"  {line}")

        return header + "\nBinary files differ"


class SideBySideFormatter(DiffFormatter):
    """Side-by-side diff formatter."""

    def __init__(
        self,
        width: int = 80,
        output_func: Callable[[str], None] | None = None,
    ):
        """Initialize with custom width and output function.

        Args:
            width: Total width for side-by-side display
            output_func: Function to call for output (default: print)
        """
        super().__init__(output_func)
        self.width: int = width
        self.half_width: int = width // 2 - 2

    def format_diff(self, diff_result: DiffResult[Any]) -> str:
        """Format using side-by-side style."""
        if diff_result.has_error:
            return f"Error: {diff_result.error_message}"

        if diff_result.diff_type == DiffType.IDENTICAL:
            return ""  # No output for identical files

        if diff_result.diff_type == DiffType.ADDED:
            return f"{'(none)':<{self.half_width}} | {diff_result.right_identifier:>{self.half_width}}"

        if diff_result.diff_type == DiffType.REMOVED:
            return f"{diff_result.left_identifier:<{self.half_width}} | {'(none)':>{self.half_width}}"

        # For modified files, show a simple side-by-side comparison
        left_name = diff_result.left_identifier[:self.half_width-3] + "..." if len(diff_result.left_identifier) > self.half_width else diff_result.left_identifier
        right_name = diff_result.right_identifier[:self.half_width-3] + "..." if len(diff_result.right_identifier) > self.half_width else diff_result.right_identifier

        return f"{left_name:<{self.half_width}} | {right_name:>{self.half_width}}"


class FormatterFactory:
    """Factory for creating diff formatters."""

    @staticmethod
    def create_formatter(
        format_type: DiffFormat,
        output_func: Callable[[str], None] | None = None,
        **kwargs,
    ) -> DiffFormatter:
        """Create a formatter of the specified type.

        Args:
            format_type: Type of formatter to create
            output_func: Function to call for output (default: print)
            **kwargs: Additional formatter-specific arguments

        Returns:
            Configured DiffFormatter instance
        """
        if format_type == DiffFormat.DEFAULT:
            return DefaultFormatter(output_func)
        if format_type == DiffFormat.UNIFIED:
            return UnifiedFormatter(output_func)
        if format_type == DiffFormat.CONTEXT:
            return ContextFormatter(output_func)
        if format_type == DiffFormat.SIDE_BY_SIDE:
            width = kwargs.get("width", 80)
            return SideBySideFormatter(width, output_func)
        error_msg = f"Unknown diff format: {format_type}"
        raise ValueError(error_msg)

