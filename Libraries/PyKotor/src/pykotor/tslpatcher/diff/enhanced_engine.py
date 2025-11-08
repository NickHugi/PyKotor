#!/usr/bin/env python3
"""Enhanced diff engine with formatting support.

This module provides an enhanced diff engine that combines structured
comparison with configurable output formatting.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from pykotor.resource.formats import gff
from pykotor.tslpatcher.diff.formatters import DiffFormat, FormatterFactory
from pykotor.tslpatcher.diff.objects import DiffEngine as StructuredDiffEngine, DiffResourceType

if TYPE_CHECKING:
    from pykotor.tslpatcher.diff.engine import ComparableResource
    from pykotor.tslpatcher.diff.formatters import DiffFormatter


class EnhancedDiffEngine:
    """Enhanced diff engine that returns structured diff results with formatted output."""

    def __init__(
        self,
        diff_format: DiffFormat = DiffFormat.DEFAULT,
        output_func: Callable[[str], None] | None = None,
    ):
        """Initialize with format and output function.

        Args:
            diff_format: Format to use for diff output
            output_func: Function to call for output (default: print)
        """
        self.structured_engine: StructuredDiffEngine = StructuredDiffEngine()
        self.formatter: DiffFormatter = FormatterFactory.create_formatter(diff_format, output_func)

    def compare_resources(
        self,
        res_a: ComparableResource,
        res_b: ComparableResource,
    ) -> bool:
        """Compare two resources and output formatted results.

        Args:
            res_a: First resource to compare
            res_b: Second resource to compare

        Returns:
            True if resources are identical, False otherwise
        """
        # Determine the resource type for structured comparison
        resource_type = self._get_resource_type(res_a.ext)

        # Use structured diff engine
        diff_result = self.structured_engine.compare_resources(
            res_a.data,
            res_b.data,
            res_a.identifier,
            res_b.identifier,
            resource_type,
        )

        # Format and output the result
        self.formatter.output_diff(diff_result)

        # Return whether they're identical
        return not diff_result.is_different

    def _get_resource_type(self, ext: str) -> DiffResourceType:
        """Map file extension to resource type.

        Args:
            ext: File extension (without dot)

        Returns:
            Resource type string for the structured diff engine
        """
        gff_extensions = gff.GFFContent.get_extensions()

        if ext in gff_extensions:
            return DiffResourceType.GFF
        if ext == "2da":
            return DiffResourceType.TWO_DA
        if ext == "tlk":
            return DiffResourceType.TLK
        if ext == "lip":
            return DiffResourceType.LIP
        return DiffResourceType.BYTES
