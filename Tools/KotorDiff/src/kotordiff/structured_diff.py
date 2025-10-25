"""Structured diff engine that generates detailed diff results for INI generation.

This module provides comprehensive diffing capabilities that produce structured
results suitable for converting to TSLPatcher modifications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf.ssf_auto import read_ssf
from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.formats.tlk.tlk_auto import read_tlk
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA

from kotordiff.diff_objects import (
    CellDiff,
    ColumnDiff,
    DiffType,
    FieldDiff,
    GFFDiffResult,
    HeaderDiff,
    RowDiff,
    StructDiff,
    TLKDiffResult,
    TLKEntryDiff,
    TwoDADiffResult,
)

if TYPE_CHECKING:
    pass


class StructuredDiffEngine:
    """Engine for generating structured, detailed diff results."""

    def compare_2da(
        self,
        left_data: bytes,
        right_data: bytes,
        left_id: str,
        right_id: str,
    ) -> TwoDADiffResult:
        """Compare two 2DA files and return structured diff."""
        try:
            left_2da = read_2da(left_data)
            right_2da = read_2da(right_data)
        except Exception as e:
            return TwoDADiffResult(
                diff_type=DiffType.ERROR,
                left_identifier=left_id,
                right_identifier=right_id,
                error_message=str(e),
            )

        # Check for differences
        header_diffs = self._compare_2da_headers(left_2da, right_2da)
        column_diffs = self._compare_2da_columns(left_2da, right_2da)
        row_diffs = self._compare_2da_rows(left_2da, right_2da)

        # Determine overall diff type
        if not header_diffs and not column_diffs and not row_diffs:
            diff_type = DiffType.IDENTICAL
        else:
            diff_type = DiffType.MODIFIED

        return TwoDADiffResult(
            diff_type=diff_type,
            left_identifier=left_id,
            right_identifier=right_id,
            left_value=left_data,
            right_value=right_data,
            header_diffs=header_diffs,
            row_diffs=row_diffs,
            column_diffs=column_diffs,
        )

    def _compare_2da_headers(
        self,
        left_2da: TwoDA,
        right_2da: TwoDA,
    ) -> list[HeaderDiff]:
        """Compare 2DA headers."""
        header_diffs: list[HeaderDiff] = []

        left_headers = left_2da.get_headers()
        right_headers = right_2da.get_headers()

        max_len = max(len(left_headers), len(right_headers))

        for idx in range(max_len):
            left_header = left_headers[idx] if idx < len(left_headers) else None
            right_header = right_headers[idx] if idx < len(right_headers) else None

            if left_header != right_header:
                if left_header is None:
                    diff_type = DiffType.ADDED
                elif right_header is None:
                    diff_type = DiffType.REMOVED
                else:
                    diff_type = DiffType.MODIFIED

                header_diffs.append(
                    HeaderDiff(
                        column_index=idx,
                        diff_type=diff_type,
                        left_header=left_header,
                        right_header=right_header,
                    )
                )

        return header_diffs

    def _compare_2da_columns(
        self,
        left_2da: TwoDA,
        right_2da: TwoDA,
    ) -> list[ColumnDiff]:
        """Compare 2DA columns."""
        column_diffs: list[ColumnDiff] = []

        left_headers = set(left_2da.get_headers())
        right_headers = set(right_2da.get_headers())

        # Added columns
        added_columns = right_headers - left_headers
        for col_name in added_columns:
            col_index = right_2da.get_headers().index(col_name)
            column_diffs.append(
                ColumnDiff(
                    column_index=col_index,
                    column_name=col_name,
                    diff_type=DiffType.ADDED,
                )
            )

        # Removed columns
        removed_columns = left_headers - right_headers
        for col_name in removed_columns:
            col_index = left_2da.get_headers().index(col_name)
            column_diffs.append(
                ColumnDiff(
                    column_index=col_index,
                    column_name=col_name,
                    diff_type=DiffType.REMOVED,
                )
            )

        return column_diffs

    def _compare_2da_rows(
        self,
        left_2da: TwoDA,
        right_2da: TwoDA,
    ) -> list[RowDiff]:
        """Compare 2DA rows."""
        row_diffs: list[RowDiff] = []

        left_height = left_2da.get_height()
        right_height = right_2da.get_height()

        common_headers = [
            h for h in left_2da.get_headers()
            if h in right_2da.get_headers()
        ]

        # Check existing rows
        for row_idx in range(min(left_height, right_height)):
            cell_diffs = []

            for col_idx, header in enumerate(common_headers):
                left_value = left_2da.get_cell(row_idx, header)
                right_value = right_2da.get_cell(row_idx, header)

                if left_value != right_value:
                    cell_diffs.append(
                        CellDiff(
                            row_index=row_idx,
                            column_index=col_idx,
                            column_name=header,
                            diff_type=DiffType.MODIFIED,
                            left_value=left_value,
                            right_value=right_value,
                        )
                    )

            if cell_diffs:
                row_diffs.append(
                    RowDiff(
                        row_index=row_idx,
                        diff_type=DiffType.MODIFIED,
                        cell_diffs=cell_diffs,
                    )
                )

        # Added rows
        if right_height > left_height:
            for row_idx in range(left_height, right_height):
                cell_diffs = []

                for col_idx, header in enumerate(right_2da.get_headers()):
                    cell_value = right_2da.get_cell(row_idx, header)
                    cell_diffs.append(
                        CellDiff(
                            row_index=row_idx,
                            column_index=col_idx,
                            column_name=header,
                            diff_type=DiffType.ADDED,
                            left_value=None,
                            right_value=cell_value,
                        )
                    )

                row_diffs.append(
                    RowDiff(
                        row_index=row_idx,
                        diff_type=DiffType.ADDED,
                        cell_diffs=cell_diffs,
                    )
                )

        # Removed rows
        if left_height > right_height:
            for row_idx in range(right_height, left_height):
                row_diffs.append(
                    RowDiff(
                        row_index=row_idx,
                        diff_type=DiffType.REMOVED,
                        cell_diffs=[],
                    )
                )

        return row_diffs

    def compare_gff(
        self,
        left_data: bytes,
        right_data: bytes,
        left_id: str,
        right_id: str,
    ) -> GFFDiffResult:
        """Compare two GFF files and return structured diff."""
        try:
            left_gff = read_gff(left_data)
            right_gff = read_gff(right_data)
        except Exception as e:
            return GFFDiffResult(
                diff_type=DiffType.ERROR,
                left_identifier=left_id,
                right_identifier=right_id,
                error_message=str(e),
            )

        field_diffs, struct_diffs = self._compare_gff_structs(
            left_gff.root,
            right_gff.root,
            "",
        )

        # Determine overall diff type
        if not field_diffs and not struct_diffs:
            diff_type = DiffType.IDENTICAL
        else:
            diff_type = DiffType.MODIFIED

        return GFFDiffResult(
            diff_type=diff_type,
            left_identifier=left_id,
            right_identifier=right_id,
            left_value=left_data,
            right_value=right_data,
            field_diffs=field_diffs,
            struct_diffs=struct_diffs,
        )

    def _compare_gff_structs(
        self,
        left_struct: GFFStruct,
        right_struct: GFFStruct,
        path: str,
    ) -> tuple[list[FieldDiff], list[StructDiff]]:
        """Recursively compare GFF structs."""
        field_diffs: list[FieldDiff] = []
        struct_diffs: list[StructDiff] = []

        # Get all field labels from structs
        left_fields: set[str] = set()
        right_fields: set[str] = set()
        
        for field_data in left_struct:
            if isinstance(field_data, tuple) and len(field_data) >= 1:
                left_fields.add(field_data[0])
        
        for field_data in right_struct:
            if isinstance(field_data, tuple) and len(field_data) >= 1:
                right_fields.add(field_data[0])

        # Common fields - check for modifications
        common_fields = left_fields & right_fields
        for field_label in common_fields:
            field_path = f"{path}/{field_label}" if path else field_label
            field_diff = self._compare_gff_field(
                left_struct,
                right_struct,
                field_label,
                field_path,
            )
            if field_diff:
                if isinstance(field_diff, tuple):
                    # Nested struct diffs
                    nested_field_diffs, nested_struct_diffs = field_diff
                    field_diffs.extend(nested_field_diffs)
                    struct_diffs.extend(nested_struct_diffs)
                else:
                    field_diffs.append(field_diff)

        # Added fields
        added_fields = right_fields - left_fields
        for field_label in added_fields:
            field_path = f"{path}/{field_label}" if path else field_label
            try:
                field = right_struct.acquire(field_label, None)
                if field is None:
                    continue

                field_diffs.append(
                    FieldDiff(
                        field_path=field_path,
                        diff_type=DiffType.ADDED,
                        left_value=None,
                        right_value=self._get_gff_field_value(right_struct, field_label, field.field_type),
                        field_type=field.field_type.name,
                    )
                )
            except (ValueError, KeyError):
                continue

        # Removed fields
        removed_fields = left_fields - right_fields
        for field_label in removed_fields:
            field_path = f"{path}/{field_label}" if path else field_label
            try:
                field = left_struct.acquire(field_label, None)
                if field is None:
                    continue

                field_diffs.append(
                    FieldDiff(
                        field_path=field_path,
                        diff_type=DiffType.REMOVED,
                        left_value=self._get_gff_field_value(left_struct, field_label, field.field_type),
                        right_value=None,
                        field_type=field.field_type.name,
                    )
                )
            except (ValueError, KeyError):
                continue

        return field_diffs, struct_diffs

    def _compare_gff_field(
        self,
        left_struct: GFFStruct,
        right_struct: GFFStruct,
        field_label: str,
        field_path: str,
    ) -> FieldDiff | tuple[list[FieldDiff], list[StructDiff]] | None:
        """Compare a specific GFF field."""
        try:
            left_field = left_struct.acquire(field_label, None)
            right_field = right_struct.acquire(field_label, None)
        except (ValueError, KeyError):
            return None
            
        if left_field is None or right_field is None:
            return None

        if left_field.field_type != right_field.field_type:
            # Type changed
            return FieldDiff(
                field_path=field_path,
                diff_type=DiffType.MODIFIED,
                left_value=str(left_field.field_type),
                right_value=str(right_field.field_type),
                field_type="TYPE_CHANGE",
            )

        # Handle nested structures
        if left_field.field_type == GFFFieldType.Struct:
            left_nested = left_struct.get_struct(field_label)
            right_nested = right_struct.get_struct(field_label)
            return self._compare_gff_structs(left_nested, right_nested, field_path)

        elif left_field.field_type == GFFFieldType.List:
            # List comparison is complex, simplified here
            left_list = left_struct.get_list(field_label)
            right_list = right_struct.get_list(field_label)

            if left_list.size != right_list.size:
                return FieldDiff(
                    field_path=field_path,
                    diff_type=DiffType.MODIFIED,
                    left_value=f"List[{left_list.size}]",
                    right_value=f"List[{right_list.size}]",
                    field_type="List",
                )

        # Scalar comparison
        left_value = self._get_gff_field_value(left_struct, field_label, left_field.field_type)
        right_value = self._get_gff_field_value(right_struct, field_label, right_field.field_type)

        if not self._gff_values_equal(left_value, right_value):
            return FieldDiff(
                field_path=field_path,
                diff_type=DiffType.MODIFIED,
                left_value=left_value,
                right_value=right_value,
                field_type=left_field.field_type.name,
            )

        return None

    def _get_gff_field_value(
        self,
        struct: GFFStruct,
        field_label: str,
        field_type: GFFFieldType,
    ) -> Any:
        """Get GFF field value."""
        type_getters = {
            GFFFieldType.UInt8: struct.get_uint8,
            GFFFieldType.Int8: struct.get_int8,
            GFFFieldType.UInt16: struct.get_uint16,
            GFFFieldType.Int16: struct.get_int16,
            GFFFieldType.UInt32: struct.get_uint32,
            GFFFieldType.Int32: struct.get_int32,
            GFFFieldType.UInt64: struct.get_uint64,
            GFFFieldType.Int64: struct.get_int64,
            GFFFieldType.Single: struct.get_single,
            GFFFieldType.Double: struct.get_double,
            GFFFieldType.String: struct.get_string,
            GFFFieldType.ResRef: struct.get_resref,
            GFFFieldType.LocalizedString: struct.get_locstring,
            GFFFieldType.Vector3: struct.get_vector3,
            GFFFieldType.Vector4: struct.get_vector4,
        }

        getter = type_getters.get(field_type)
        return getter(field_label) if getter else None

    def _gff_values_equal(self, left: Any, right: Any) -> bool:
        """Check if two GFF values are equal."""
        if isinstance(left, float) and isinstance(right, float):
            return abs(left - right) < 1e-6
        return left == right

    def compare_tlk(
        self,
        left_data: bytes,
        right_data: bytes,
        left_id: str,
        right_id: str,
    ) -> TLKDiffResult:
        """Compare two TLK files and return structured diff."""
        try:
            left_tlk = read_tlk(left_data)
            right_tlk = read_tlk(right_data)
        except Exception as e:
            return TLKDiffResult(
                diff_type=DiffType.ERROR,
                left_identifier=left_id,
                right_identifier=right_id,
                error_message=str(e),
            )

        entry_diffs: list[TLKEntryDiff] = []

        left_size = len(left_tlk)
        right_size = len(right_tlk)

        # Compare existing entries
        for idx in range(min(left_size, right_size)):
            left_entry = left_tlk.get(idx)
            right_entry = right_tlk.get(idx)

            if left_entry is None or right_entry is None:
                continue

            if (left_entry.text != right_entry.text or
                str(left_entry.voiceover) != str(right_entry.voiceover)):
                entry_diffs.append(
                    TLKEntryDiff(
                        entry_id=idx,
                        diff_type=DiffType.MODIFIED,
                        left_text=left_entry.text,
                        right_text=right_entry.text,
                        left_voiceover=str(left_entry.voiceover),
                        right_voiceover=str(right_entry.voiceover),
                    )
                )

        # Added entries
        if right_size > left_size:
            for idx in range(left_size, right_size):
                right_entry = right_tlk.get(idx)
                if right_entry is None:
                    continue
                entry_diffs.append(
                    TLKEntryDiff(
                        entry_id=idx,
                        diff_type=DiffType.ADDED,
                        left_text=None,
                        right_text=right_entry.text,
                        left_voiceover=None,
                        right_voiceover=str(right_entry.voiceover),
                    )
                )

        # Removed entries
        if left_size > right_size:
            for idx in range(right_size, left_size):
                left_entry = left_tlk.get(idx)
                if left_entry is None:
                    continue
                entry_diffs.append(
                    TLKEntryDiff(
                        entry_id=idx,
                        diff_type=DiffType.REMOVED,
                        left_text=left_entry.text,
                        right_text=None,
                        left_voiceover=str(left_entry.voiceover),
                        right_voiceover=None,
                    )
                )

        # Determine overall diff type
        diff_type = DiffType.IDENTICAL if not entry_diffs else DiffType.MODIFIED

        return TLKDiffResult(
            diff_type=diff_type,
            left_identifier=left_id,
            right_identifier=right_id,
            left_value=left_data,
            right_value=right_data,
            entry_diffs=entry_diffs,
        )

