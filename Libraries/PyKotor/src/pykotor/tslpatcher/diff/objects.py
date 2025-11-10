#!/usr/bin/env python3
"""Structured diff objects for KotorDiff that separate diff logic from output formatting."""

from __future__ import annotations

import traceback

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pykotor.resource.formats import gff, tlk, twoda

if TYPE_CHECKING:
    from utility.common.geometry import Vector3, Vector4
    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import ResRef
    from pykotor.resource.formats import lip
    from pykotor.resource.formats.gff.gff_data import GFFList, GFFStruct

T = TypeVar("T")


class DiffType(Enum):
    """Types of differences that can be detected."""

    IDENTICAL = "identical"
    MODIFIED = "modified"
    ADDED = "added"
    REMOVED = "removed"
    ERROR = "error"


class DiffFormat(Enum):
    """Supported diff output formats."""

    DEFAULT = "default"  # KotorDiff's native format
    UNIFIED = "unified"  # Standard unified diff format
    CONTEXT = "context"  # Context diff format
    SIDE_BY_SIDE = "side_by_side"  # Side-by-side comparison


@dataclass
class DiffResult(Generic[T]):
    """Base result of a diff operation."""

    diff_type: DiffType
    left_identifier: str
    right_identifier: str
    left_value: T | None = None
    right_value: T | None = None
    error_message: str | None = None
    details: dict[str, Any] | None = None

    @property
    def is_different(self) -> bool:
        """Check if the items are different."""
        return self.diff_type not in (DiffType.IDENTICAL,)

    @property
    def has_error(self) -> bool:
        """Check if there was an error during comparison."""
        return self.diff_type == DiffType.ERROR


@dataclass
class ResourceDiffResult(DiffResult[bytes]):
    """Result of comparing two resources."""

    resource_type: str | None = None
    left_size: int | None = None
    right_size: int | None = None

    def __post_init__(self):
        """Calculate sizes if not provided."""
        if self.left_size is None and self.left_value is not None:
            self.left_size = len(self.left_value)
        if self.right_size is None and self.right_value is not None:
            self.right_size = len(self.right_value)


@dataclass
class GFFDiffResult(DiffResult[Any]):
    """Result of comparing two GFF files."""

    field_diffs: list[FieldDiff] | None = None
    struct_diffs: list[StructDiff] | None = None


@dataclass
class FieldDiff:
    """Difference in a GFF field."""

    field_path: str
    diff_type: DiffType
    left_value: int | float | str | ResRef | LocalizedString | Vector3 | Vector4 | GFFStruct | GFFList | bytes | None = None
    right_value: int | float | str | ResRef | LocalizedString | Vector3 | Vector4 | GFFStruct | GFFList | bytes | None = None
    field_type: str | None = None


@dataclass
class StructDiff:
    """Difference in a GFF struct."""

    struct_path: str
    diff_type: DiffType
    field_diffs: list[FieldDiff] | None = None


@dataclass
class TwoDADiffResult(DiffResult[Any]):
    """Result of comparing two 2DA files."""

    header_diffs: list[HeaderDiff] | None = None
    row_diffs: list[RowDiff] | None = None
    column_diffs: list[ColumnDiff] | None = None


@dataclass
class HeaderDiff:
    """Difference in 2DA headers."""

    column_index: int
    diff_type: DiffType
    left_header: str | None = None
    right_header: str | None = None


@dataclass
class RowDiff:
    """Difference in a 2DA row."""

    row_index: int
    diff_type: DiffType
    cell_diffs: list[CellDiff] | None = None


@dataclass
class CellDiff:
    """Difference in a 2DA cell."""

    row_index: int
    column_index: int
    column_name: str | None
    diff_type: DiffType
    left_value: str | None = None
    right_value: str | None = None


@dataclass
class ColumnDiff:
    """Difference in a 2DA column."""

    column_index: int
    column_name: str | None
    diff_type: DiffType


@dataclass
class TLKDiffResult(DiffResult[Any]):
    """Result of comparing two TLK files."""

    entry_diffs: list[TLKEntryDiff] | None = None


@dataclass
class LIPDiffResult(DiffResult[Any]):
    """Result of comparing two LIP files."""

    entry_diffs: list[LIPEntryDiff] | None = None


@dataclass
class LIPEntryDiff:
    """Difference in a LIP entry."""

    entry_id: int
    diff_type: DiffType
    left_time: float | None = None
    right_time: float | None = None
    left_shape: lip.LIPShape | None = None
    right_shape: lip.LIPShape | None = None


@dataclass
class TLKEntryDiff:
    """Difference in a TLK entry."""

    entry_id: int
    diff_type: DiffType
    left_text: str | None = None
    right_text: str | None = None
    left_voiceover: str | None = None
    right_voiceover: str | None = None


class DiffComparator(ABC, Generic[T]):
    """Abstract base class for diff comparators."""

    @abstractmethod
    def compare(self, left: T, right: T, left_id: str, right_id: str) -> DiffResult[T]:
        """Compare two objects and return a structured diff result."""


class BytesDiffComparator(DiffComparator[bytes]):
    """Comparator for raw bytes data."""

    def compare(self, left: bytes, right: bytes, left_id: str, right_id: str) -> ResourceDiffResult:
        """Compare two byte arrays."""
        if left == right:
            return ResourceDiffResult(
                diff_type=DiffType.IDENTICAL,
                left_identifier=left_id,
                right_identifier=right_id,
                left_value=left,
                right_value=right,
            )
        return ResourceDiffResult(
            diff_type=DiffType.MODIFIED,
            left_identifier=left_id,
            right_identifier=right_id,
            left_value=left,
            right_value=right,
        )


class GFFDiffComparator(DiffComparator[Any]):
    """Comparator for GFF files using the existing compare mixin."""

    def compare(self, left: Any, right: Any, left_id: str, right_id: str) -> GFFDiffResult:
        """Compare two GFF objects."""
        try:
            # Use the existing compare method but capture the differences
            field_diffs: list[FieldDiff] = []
            struct_diffs: list[StructDiff] = []

            def diff_callback(message: str, *args, **kwargs):
                """Capture diff information instead of just logging."""
                # Parse the message to extract structured diff info
                # This is a simplified version - in practice, we'd need to
                # modify the GFF compare method to provide structured callbacks

            is_same = left.compare(right, diff_callback)

            diff_type = DiffType.IDENTICAL if is_same else DiffType.MODIFIED

            return GFFDiffResult(
                diff_type=diff_type,
                left_identifier=left_id,
                right_identifier=right_id,
                left_value=left,
                right_value=right,
                field_diffs=field_diffs if field_diffs else None,
                struct_diffs=struct_diffs if struct_diffs else None,
            )
        except Exception as e:  # noqa: BLE001
            print("Full traceback:")
            for line in traceback.format_exc().splitlines():
                print(f"  {line}")
            return GFFDiffResult(
                diff_type=DiffType.ERROR,
                left_identifier=left_id,
                right_identifier=right_id,
                error_message=str(e),
            )


class TwoDADiffComparator(DiffComparator[Any]):
    """Comparator for 2DA files using the existing compare mixin."""

    def compare(
        self,
        left: Any,
        right: Any,
        left_id: str,
        right_id: str,
    ) -> TwoDADiffResult:
        """Compare two 2DA objects."""
        try:
            # Use existing compare method but capture differences
            header_diffs: list[HeaderDiff] = []
            row_diffs: list[RowDiff] = []
            column_diffs: list[ColumnDiff] = []

            def diff_callback(message: str, *args, **kwargs):
                """Capture diff information."""
                # Parse and structure the diff information

            is_same = left.compare(right, diff_callback)

            diff_type = DiffType.IDENTICAL if is_same else DiffType.MODIFIED

            return TwoDADiffResult(
                diff_type=diff_type,
                left_identifier=left_id,
                right_identifier=right_id,
                left_value=left,
                right_value=right,
                header_diffs=header_diffs if header_diffs else None,
                row_diffs=row_diffs if row_diffs else None,
                column_diffs=column_diffs if column_diffs else None,
            )
        except Exception as e:  # noqa: BLE001
            print("Full traceback:")
            for line in traceback.format_exc().splitlines():
                print(f"  {line}")
            return TwoDADiffResult(
                diff_type=DiffType.ERROR,
                left_identifier=left_id,
                right_identifier=right_id,
                error_message=str(e),
            )


class TLKDiffComparator(DiffComparator[Any]):
    """Comparator for TLK files using the existing compare mixin."""

    def compare(self, left: Any, right: Any, left_id: str, right_id: str) -> TLKDiffResult:
        """Compare two TLK objects."""
        try:
            entry_diffs: list[TLKEntryDiff] = []

            def diff_callback(message: str, *args, **kwargs):
                """Capture diff information."""
                # Parse and structure the diff information

            is_same = left.compare(right, diff_callback)

            diff_type = DiffType.IDENTICAL if is_same else DiffType.MODIFIED

            return TLKDiffResult(
                diff_type=diff_type,
                left_identifier=left_id,
                right_identifier=right_id,
                left_value=left,
                right_value=right,
                entry_diffs=entry_diffs if entry_diffs else None,
            )
        except Exception as e:  # noqa: BLE001
            print("Full traceback:")
            for line in traceback.format_exc().splitlines():
                print(f"  {line}")
            return TLKDiffResult(
                diff_type=DiffType.ERROR,
                left_identifier=left_id,
                right_identifier=right_id,
                error_message=str(e),
            )


class LIPDiffComparator(DiffComparator[Any]):
    """Comparator for LIP files using the existing compare mixin."""

    def compare(
        self,
        left: Any,
        right: Any,
        left_id: str,
        right_id: str,
    ) -> LIPDiffResult:
        """Compare two LIP objects."""
        try:
            entry_diffs: list[LIPEntryDiff] = []

            def diff_callback(message: str, *args, **kwargs):
                """Capture diff information."""
                # Parse and structure the diff information

            is_same = left.compare(right, diff_callback)

            diff_type = DiffType.IDENTICAL if is_same else DiffType.MODIFIED

            return LIPDiffResult(
                diff_type=diff_type,
                left_identifier=left_id,
                right_identifier=right_id,
                left_value=left,
                right_value=right,
                entry_diffs=entry_diffs if entry_diffs else None,
            )
        except Exception as e:  # noqa: BLE001
            print("Full traceback:")
            for line in traceback.format_exc().splitlines():
                print(f"  {line}")
            return LIPDiffResult(
                diff_type=DiffType.ERROR,
                left_identifier=left_id,
                right_identifier=right_id,
                error_message=str(e),
            )


class DiffEngine:
    """Main diff engine that coordinates comparisons and returns structured results."""

    def __init__(self):
        self.comparators: dict[DiffResourceType, DiffComparator[Any]] = {
            DiffResourceType.GFF: GFFDiffComparator(),
            DiffResourceType.TWO_DA: TwoDADiffComparator(),
            DiffResourceType.TLK: TLKDiffComparator(),
            DiffResourceType.LIP: LIPDiffComparator(),
            DiffResourceType.BYTES: BytesDiffComparator(),
        }
        # Import structured engine lazily to avoid circular imports
        self._structured_engine = None

    @property
    def structured_engine(self):
        """Lazy load structured engine."""
        if self._structured_engine is None:
            from pykotor.tslpatcher.diff.structured import StructuredDiffEngine  # noqa: PLC0415

            self._structured_engine = StructuredDiffEngine()
        return self._structured_engine

    def compare_resources(
        self,
        left_data: bytes,
        right_data: bytes,
        left_id: str,
        right_id: str,
        resource_type: DiffResourceType,
    ) -> DiffResult[Any]:
        """Compare two resources and return structured diff results."""
        # Handle missing data
        if left_data is None and right_data is not None:
            return ResourceDiffResult(
                diff_type=DiffType.ADDED,
                left_identifier=left_id,
                right_identifier=right_id,
                right_value=right_data,
                resource_type=resource_type,
            )
        if left_data is not None and right_data is None:
            return ResourceDiffResult(
                diff_type=DiffType.REMOVED,
                left_identifier=left_id,
                right_identifier=right_id,
                left_value=left_data,
                resource_type=resource_type,
            )
        if left_data is None and right_data is None:
            return ResourceDiffResult(
                diff_type=DiffType.IDENTICAL,
                left_identifier=left_id,
                right_identifier=right_id,
                resource_type=resource_type,
            )

        # Get the appropriate comparator
        comparator = self.comparators.get(resource_type, self.comparators[DiffResourceType.BYTES])

        # For format-specific comparisons, we need to parse the data first
        if resource_type in ("gff", "2da", "tlk") and resource_type != "bytes":
            try:
                # Import here to avoid circular imports
                left_parsed: Any
                right_parsed: Any

                if resource_type == "gff":
                    left_parsed = gff.read_gff(left_data)
                    right_parsed = gff.read_gff(right_data)
                elif resource_type == "2da":
                    left_parsed = twoda.read_2da(left_data)
                    right_parsed = twoda.read_2da(right_data)
                elif resource_type == "tlk":
                    left_parsed = tlk.read_tlk(left_data)
                    right_parsed = tlk.read_tlk(right_data)
                else:
                    # Fallback to bytes comparison
                    return comparator.compare(left_data, right_data, left_id, right_id)

                return comparator.compare(left_parsed, right_parsed, left_id, right_id)

            except Exception as e:  # noqa: BLE001
                print("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    print(f"  {line}")
                return DiffResult(
                    diff_type=DiffType.ERROR,
                    left_identifier=left_id,
                    right_identifier=right_id,
                    error_message=f"Failed to parse {resource_type}: {e}",
                )

        # Fallback to bytes comparison
        return comparator.compare(left_data, right_data, left_id, right_id)


class DiffResourceType(Enum):
    GFF = "gff"
    TWO_DA = "2da"
    TLK = "tlk"
    LIP = "lip"
    BYTES = "bytes"
