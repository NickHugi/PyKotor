"""Diff analyzers that convert raw diffs into TSLPatcher modification structures.

This module provides analyzers that examine differences between game files
and generate appropriate TSLPatcher modification objects.
"""

from __future__ import annotations

import traceback

from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import TYPE_CHECKING, Any

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource
from pykotor.extract.installation import Installation
from pykotor.extract.twoda import K1Columns2DA, K2Columns2DA
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf.ssf_auto import read_ssf
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.resource.formats.tlk.tlk_auto import read_tlk
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    ModificationsGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.ncs import ModificationsNCS, ModifyNCS, NCSTokenType
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK, ModifyTLK
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    Modifications2DA,
    RowValueConstant,
    RowValueRowIndex,
    RowValueTLKMemory,
    Target,
    TargetType,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pykotor.resource.formats.tlk.tlk_data import TLKEntry
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.tslpatcher.mods.template import PatcherModifications


def _parse_numeric_row_label(label: str | None) -> int | None:
    """Convert a 2DA row label to an int when possible."""
    if not label:
        return None
    stripped = label.strip()
    if not stripped:
        return None
    if stripped[0] in "+-":
        sign = stripped[0]
        digits = stripped[1:]
        if digits.isdigit():
            return int(sign + digits)
        return None
    if stripped.isdigit():
        return int(stripped)
    return None


def _resolve_row_index_value(fallback_index: int, *labels: str | None) -> int:
    """Prefer numeric row labels over positional indices for ChangeRow targets."""
    for label in labels:
        numeric = _parse_numeric_row_label(label)
        if numeric is not None:
            return numeric
    return fallback_index


class DiffAnalyzer(ABC):
    """Abstract base class for diff analyzers."""

    @abstractmethod
    def analyze(
        self,
        left_data: bytes,
        right_data: bytes,
        identifier: str,
    ) -> PatcherModifications | tuple[PatcherModifications, dict[int, int]] | None:
        """Analyze differences and return a PatcherModifications object.

        TLK analyzers may return a tuple of (ModificationsTLK, strref_mappings).
        All other analyzers return PatcherModifications | None.
        """


class TwoDADiffAnalyzer(DiffAnalyzer):
    """Analyzer for 2DA file differences."""

    def analyze(
        self,
        left_data: bytes,
        right_data: bytes,
        identifier: str,
    ) -> Modifications2DA | None:
        """Analyze 2DA differences and create modification object."""
        try:
            left_2da = read_2da(left_data)
            right_2da = read_2da(right_data)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to parse 2DA files: identifier={identifier}, error={e}")
            traceback.print_exc()
            return None

        # Extract just the filename from the identifier (may contain full path like "install/modules/file.2da")
        filename: str = PurePath(identifier).name
        modifications = Modifications2DA(filename)

        # Detect column differences
        self._analyze_columns(left_2da, right_2da, modifications, identifier)

        # Detect row differences
        self._analyze_rows(left_2da, right_2da, modifications, identifier)

        if modifications.modifiers:
            print(f"2DA modifications: identifier={identifier}, modifier_count={len(modifications.modifiers)}")

        return modifications if modifications.modifiers else None

    def _analyze_columns(
        self,
        left_2da: TwoDA,
        right_2da: TwoDA,
        modifications: Modifications2DA,
        identifier: str,
    ):
        """Analyze column differences."""
        left_headers = set(left_2da.get_headers())
        right_headers = set(right_2da.get_headers())

        # Detect added columns
        added_columns = right_headers - left_headers

        for col_idx, col_name in enumerate(sorted(added_columns)):
            # Determine default value
            column_data = right_2da.get_column(col_name)
            default_value = self._determine_default_value(column_data)

            # Create AddColumn2DA modifier with index-based identifier
            add_column_id = f"{modifications.sourcefile}_{col_name}_addcol_{col_idx}"
            add_column = AddColumn2DA(
                identifier=add_column_id,
                header=col_name,
                default=default_value,
                index_insert={},
                label_insert={},
                store_2da={},
            )

            # Populate specific cell values if they differ from default
            row_height = right_2da.get_height()
            for row_idx in range(row_height):
                cell_value = right_2da.get_cell(row_idx, col_name)
                is_different = cell_value != default_value
                if is_different:
                    add_column.index_insert[row_idx] = RowValueConstant(cell_value)

            modifications.modifiers.append(add_column)

    def _analyze_rows(
        self,
        left_2da: TwoDA,
        right_2da: TwoDA,
        modifications: Modifications2DA,
        identifier: str,
    ):
        """Analyze row differences."""
        left_height = left_2da.get_height()
        right_height = right_2da.get_height()

        # Common headers
        common_headers = [h for h in left_2da.get_headers() if h in right_2da.get_headers()]

        # Check existing rows for modifications
        min_height = min(left_height, right_height)
        change_row_counter = 0
        for row_idx in range(min_height):
            changed_cells = {}

            for header in common_headers:
                left_value = left_2da.get_cell(row_idx, header)
                right_value = right_2da.get_cell(row_idx, header)
                values_differ = left_value != right_value

                if values_differ:
                    changed_cells[header] = RowValueConstant(right_value)

            if changed_cells:
                # Use simple index-based identifier
                change_row_id = f"{modifications.sourcefile}_changerow_{change_row_counter}"
                change_row_counter += 1

                left_label: str | None = None
                right_label: str | None = None
                try:
                    left_label = left_2da.get_label(row_idx)
                except Exception:  # noqa: BLE001
                    left_label = None
                try:
                    right_label = right_2da.get_label(row_idx)
                except Exception:  # noqa: BLE001
                    right_label = None

                target_row_index = _resolve_row_index_value(row_idx, right_label, left_label)

                change_row = ChangeRow2DA(
                    identifier=change_row_id,
                    target=Target(TargetType.ROW_INDEX, target_row_index),
                    cells=changed_cells,
                )
                modifications.modifiers.append(change_row)

        # Check for added rows
        has_new_rows = right_height > left_height
        if has_new_rows:
            for add_row_counter, row_idx in enumerate(range(left_height, right_height)):
                cells = {}
                row_label = right_2da.get_label(row_idx)

                for header in right_2da.get_headers():
                    cell_value = right_2da.get_cell(row_idx, header)
                    has_value = bool(cell_value)
                    if has_value:  # Only include non-empty cells
                        cells[header] = RowValueConstant(cell_value)

                # Use simple index-based identifier
                add_row_id = f"{modifications.sourcefile}_addrow_{add_row_counter}"

                add_row = AddRow2DA(
                    identifier=add_row_id,
                    exclusive_column=None,
                    row_label=row_label,
                    cells=cells,
                )
                modifications.modifiers.append(add_row)

    def _determine_default_value(self, column_data: list[str]) -> str:
        """Determine the most appropriate default value for a column."""
        if not column_data:
            return "****"

        # Count occurrences
        value_counts: dict[str, int] = {}
        for value in column_data:
            value_counts[value] = value_counts.get(value, 0) + 1

        # Return most common value, preferring "****" if it's common
        star_count = value_counts.get("****", 0)
        quarter_threshold = len(column_data) // 4
        has_stars = "****" in value_counts
        is_common_star = has_stars and star_count > quarter_threshold
        if is_common_star:
            return "****"

        # Find the most common value
        if value_counts:
            most_common = max(value_counts.items(), key=lambda x: x[1])
            most_common_value = most_common[0]
            most_common_count = most_common[1]

            # Only use most common value as default if it appears in more than half the rows
            # Otherwise use "****" to avoid excessive defaults
            half_threshold = len(column_data) / 2
            if most_common_count > half_threshold:
                return most_common_value

            # If empty string is most common, use it
            if most_common_value == "" and most_common_count > quarter_threshold:
                return ""

            # Otherwise default to "****" to minimize default pollution
            return "****"

        return "****"


class GFFDiffAnalyzer(DiffAnalyzer):
    """Analyzer for GFF file differences."""

    def analyze(
        self,
        left_data: bytes,
        right_data: bytes,
        identifier: str,
    ) -> ModificationsGFF | None:
        """Analyze GFF differences and create modification object."""
        try:
            left_gff = read_gff(left_data)
            right_gff = read_gff(right_data)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to parse GFF files: identifier={identifier}, error={e}")
            traceback.print_exc()
            return None

        # Extract just the filename from the identifier (may contain full path like "install/modules/file.utc")
        filename: str = PurePath(identifier).name
        modifications = ModificationsGFF(filename, replace=False, modifiers=[])

        # Analyze struct differences recursively
        root_path = PurePath()
        self._analyze_struct(
            left_gff.root,
            right_gff.root,
            root_path,
            modifications,
        )

        if modifications.modifiers:
            print(f"GFF modifications: identifier={identifier}, modifier_count={len(modifications.modifiers)}")

        return modifications if modifications.modifiers else None

    def _analyze_struct(
        self,
        left_struct: GFFStruct,
        right_struct: GFFStruct,
        path: PurePath,
        modifications: ModificationsGFF,
    ):
        """Recursively analyze struct differences."""
        # Get all fields
        left_fields = {label for label, _, _ in left_struct}
        right_fields = {label for label, _, _ in right_struct}

        # Common fields - check for modifications
        common_fields = left_fields & right_fields
        for field_label in common_fields:
            field_path = path / field_label
            self._analyze_field(
                left_struct,
                right_struct,
                field_label,
                field_path,
                modifications,
            )

        # Added fields
        added_fields = right_fields - left_fields
        for field_label in added_fields:
            field_path = path / field_label
            self._create_add_field(
                right_struct,
                field_label,
                field_path,
                modifications,
            )

    def _analyze_field(
        self,
        left_struct: GFFStruct,
        right_struct: GFFStruct,
        field_label: str,
        field_path: PurePath,
        modifications: ModificationsGFF,
    ):
        """Analyze a specific field for differences."""
        # Use exists() to check field presence, then get field info properly
        left_exists = left_struct.exists(field_label)
        if not left_exists:
            return
        right_exists = right_struct.exists(field_label)
        if not right_exists:
            return

        # Access the field objects directly from _fields to get field type
        left_field = left_struct._fields[field_label]
        right_field = right_struct._fields[field_label]

        # Get field types by calling the field_type() method
        left_field_type = left_field.field_type()
        right_field_type = right_field.field_type()

        types_differ = left_field_type != right_field_type
        if types_differ:
            # Type changed - treat as modification
            self._create_modify_field(
                right_struct,
                field_label,
                field_path,
                modifications,
            )
            return

        # Compare values based on type
        is_struct_type = left_field_type == GFFFieldType.Struct
        if is_struct_type:
            # Recursively analyze nested struct
            left_nested = left_struct.get_struct(field_label)
            right_nested = right_struct.get_struct(field_label)
            self._analyze_struct(left_nested, right_nested, field_path, modifications)

        elif left_field_type == GFFFieldType.List:
            # Analyze list differences
            left_list = left_struct.get_list(field_label)
            right_list = right_struct.get_list(field_label)
            self._analyze_list(left_list, right_list, field_path, modifications)

        # Scalar value comparison
        else:
            values_equal = self._values_equal(
                left_field_type,
                right_field_type,
                left_struct,
                right_struct,
                field_label,
            )
            if not values_equal:
                self._create_modify_field(
                    right_struct,
                    field_label,
                    field_path,
                    modifications,
                )

    def _analyze_list(
        self,
        left_list: GFFList,
        right_list: GFFList,
        path: PurePath,
        modifications: ModificationsGFF,
    ):
        """Analyze list differences."""
        left_size = len(left_list)
        right_size = len(right_list)

        # Check common elements for modifications
        min_size = min(left_size, right_size)
        for idx in range(min_size):
            item_path = path / str(idx)
            left_item = left_list.at(idx)
            right_item = right_list.at(idx)
            left_item_exists = left_item is not None
            if not left_item_exists:
                continue
            right_item_exists = right_item is not None
            if not right_item_exists:
                continue
            if left_item is not None and right_item is not None:
                self._analyze_struct(left_item, right_item, item_path, modifications)

        # Handle added list elements
        has_new_items = right_size > left_size
        if has_new_items:
            for idx in range(left_size, right_size):
                right_item = right_list.at(idx)
                right_item_exists = right_item is not None
                if not right_item_exists:
                    continue

                # Create AddStructToListGFF for each new list entry
                # Generate unique identifier for this list addition
                sourcefile_normalized = modifications.sourcefile.replace(".", "_")
                path_name = path.name
                section_name = f"gff_{sourcefile_normalized}_{path_name}_{idx}_0"

                # Create a FieldValueConstant that wraps the GFFStruct
                value = FieldValueConstant(right_item)

                # Create the AddStructToListGFF modifier
                add_struct = AddStructToListGFF(
                    identifier=section_name,
                    value=value,
                    path=str(path),
                    index_to_token=None,
                    modifiers=[],
                )

                # Recursively add all fields from the new struct
                if right_item is not None:
                    self._add_all_struct_fields(right_item, add_struct, PurePath())

                modifications.modifiers.append(add_struct)

    def _add_all_struct_fields(
        self,
        struct: GFFStruct,
        parent_modifier: AddStructToListGFF | AddFieldGFF,
        base_path: PurePath,
    ):
        """Recursively add all fields from a struct as AddFieldGFF modifiers."""
        # Iterate over struct fields (returns tuples of (label, field_type, value))
        parent_id = parent_modifier.identifier
        for field_info in struct:
            field_label, field_type, field_value = field_info
            field_path = base_path / field_label if base_path.name else PurePath(field_label)

            # Generate unique section name for this field
            section_name = f"{parent_id}_{field_label}_0".replace("\\", "_").replace("/", "_")

            # Create AddFieldGFF for this field
            is_struct_type = field_type == GFFFieldType.Struct
            if is_struct_type:
                # For structs, create AddFieldGFF with nested modifiers
                value_constant = FieldValueConstant(field_value)
                add_field = AddFieldGFF(
                    identifier=section_name,
                    value=value_constant,
                    field_type=field_type,
                    label=field_label,
                    path=str(field_path),
                    modifiers=[],
                )

                # Recursively add nested fields
                is_gff_struct = isinstance(field_value, GFFStruct)
                if is_gff_struct:
                    self._add_all_struct_fields(field_value, add_field, PurePath())

                parent_modifier.modifiers.append(add_field)

            elif field_type == GFFFieldType.List:
                # For lists, create AddFieldGFF
                value_constant = FieldValueConstant(field_value)
                add_field = AddFieldGFF(
                    identifier=section_name,
                    value=value_constant,
                    field_type=field_type,
                    label=field_label,
                    path=str(field_path),
                    modifiers=[],
                )

                # Add nested structs from the list
                is_gff_list = isinstance(field_value, GFFList)
                if is_gff_list:
                    for list_idx in range(len(field_value)):
                        list_item = field_value.at(list_idx)
                        is_list_item_struct = isinstance(list_item, GFFStruct)
                        if is_list_item_struct:
                            list_section_name = f"{section_name}_{list_idx}_0"
                            list_value = FieldValueConstant(list_item)

                            add_list_struct = AddStructToListGFF(
                                identifier=list_section_name,
                                value=list_value,
                                path="",
                                index_to_token=None,
                                modifiers=[],
                            )

                            # Recursively add all fields from the list item
                            self._add_all_struct_fields(list_item, add_list_struct, PurePath())
                            add_field.modifiers.append(add_list_struct)

                parent_modifier.modifiers.append(add_field)

            else:
                # For simple fields, just create AddFieldGFF with the value
                value_constant = FieldValueConstant(field_value)
                add_field = AddFieldGFF(
                    identifier=section_name,
                    value=value_constant,
                    field_type=field_type,
                    label=field_label,
                    path=str(field_path),
                    modifiers=[],
                )
                parent_modifier.modifiers.append(add_field)

    def _create_modify_field(
        self,
        struct: GFFStruct,
        field_label: str,
        field_path: PurePath,
        modifications: ModificationsGFF,
    ):
        """Create a ModifyFieldGFF modifier."""
        field_exists = struct.exists(field_label)
        if not field_exists:
            return

        # Access the field object directly from _fields
        field = struct._fields[field_label]
        field_type = field.field_type()
        value = self._get_field_value(struct, field_label, field_type)

        path_str = str(field_path).replace("/", "\\")
        modify_field = ModifyFieldGFF(
            path=path_str,
            value=FieldValueConstant(value),
        )
        modifications.modifiers.append(modify_field)

    def _create_add_field(
        self,
        struct: GFFStruct,
        field_label: str,
        field_path: PurePath,
        modifications: ModificationsGFF,
    ):
        """Create an AddFieldGFF modifier."""
        field_exists = struct.exists(field_label)
        if not field_exists:
            return

        # Access the field object directly from _fields
        field = struct._fields[field_label]
        field_type = field.field_type()
        value = self._get_field_value(struct, field_label, field_type)

        # Determine parent path
        has_parent: bool = bool(field_path.parent.parts)
        parent_path = str(field_path.parent).replace("/", "\\") if has_parent else ""

        sourcefile_normalized = modifications.sourcefile.replace(".", "_")
        add_field_id = f"{sourcefile_normalized}_add_{field_label}"
        add_field = AddFieldGFF(
            identifier=add_field_id,
            label=field_label,
            field_type=field_type,
            value=FieldValueConstant(value),
            path=parent_path,
        )
        modifications.modifiers.append(add_field)

    def _get_field_value(
        self,
        struct: GFFStruct,
        field_label: str,
        field_type: GFFFieldType,
    ) -> Any:
        """Get the value of a field based on its type."""
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
        has_getter = getter is not None
        if has_getter:
            return getter(field_label) if getter is not None else None

        return None

    GFF_FLOAT_TOLERANCE = 1e-6

    def _values_equal(
        self,
        left_field_type: GFFFieldType,
        right_field_type: GFFFieldType,
        left_struct: GFFStruct,
        right_struct: GFFStruct,
        field_label: str,
    ) -> bool:
        """Check if two field values are equal."""
        left_value = self._get_field_value(left_struct, field_label, left_field_type)
        right_value = self._get_field_value(right_struct, field_label, right_field_type)

        # Special handling for floats
        is_float_comparison = isinstance(left_value, float) and isinstance(right_value, float)
        if is_float_comparison:
            diff = abs(left_value - right_value)
            return diff < self.GFF_FLOAT_TOLERANCE

        return left_value == right_value


class TLKDiffAnalyzer(DiffAnalyzer):
    """Analyzer for TLK file differences.

    Per TSLPatcher design, ALL TLK changes (modifications and new entries) are appended.
    References to modified StrRefs are updated via tokens in GFF/2DA/SSF files.
    """

    def analyze(
        self,
        left_data: bytes,
        right_data: bytes,
        identifier: str,
    ) -> tuple[ModificationsTLK, dict[int, int]] | None:
        """Analyze TLK differences and create modification object.

        Both modified and new entries are appended.

        Returns:
            Tuple of (ModificationsTLK, strref_mappings) or None if no modifications.
            strref_mappings maps old StrRef -> token_id for reference analysis.
        """
        try:
            left_tlk = read_tlk(left_data)
            right_tlk = read_tlk(right_data)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to parse TLK files: identifier={identifier}, error={e}")
            traceback.print_exc()
            return None

        left_size = len(left_tlk)
        right_size = len(right_tlk)

        # Extract the actual TLK filename from the identifier (e.g., "swkotor\dialog.tlk" -> "dialog.tlk")
        # This is needed for StrRef reference finding
        tlk_filename: str = PurePath(identifier).name

        # Use "append.tlk" as the sourcefile per TSLPatcher convention (this is the OUTPUT file)
        # But store the actual TLK filename for reference finding
        modifications = ModificationsTLK(filename="append.tlk", replace=False, modifiers=[])
        modifications.saveas = tlk_filename  # This is the actual TLK file being patched (dialog.tlk)

        # StrRef mappings will be returned separately for storage in TLKModificationWithSource
        strref_mappings: dict[int, int] = {}  # old_strref -> token_id

        token_id = 0

        # Process modified entries - these get appended and old refs must be updated
        min_size = min(left_size, right_size)
        for idx in range(min_size):
            left_entry: TLKEntry | None = left_tlk.get(idx)
            right_entry: TLKEntry | None = right_tlk.get(idx)
            left_entry_exists = left_entry is not None
            if not left_entry_exists:
                continue
            right_entry_exists = right_entry is not None
            if not right_entry_exists:
                continue

            # Type narrowing - at this point both entries are guaranteed to be TLKEntry
            if left_entry is None or right_entry is None:
                continue

            text_differs = left_entry.text != right_entry.text
            voiceover_differs = left_entry.voiceover != right_entry.voiceover
            entry_modified = text_differs or voiceover_differs
            if entry_modified:
                # Append the modified entry as a new entry
                modify = ModifyTLK(token_id, is_replacement=False)
                modify.mod_index = idx  # Store the original TLK index for reference tracking
                modify.text = right_entry.text
                modify.sound = right_entry.voiceover
                modifications.modifiers.append(modify)

                # Track that old StrRef idx should map to token_id
                strref_mappings[idx] = token_id
                token_id += 1

        # Process new entries (appends)
        has_new_entries = right_size > left_size
        if has_new_entries:
            for idx in range(left_size, right_size):
                right_entry = right_tlk.get(idx)
                right_entry_exists = right_entry is not None
                if not right_entry_exists:
                    continue

                # Type narrowing
                if right_entry is None:
                    continue

                # Append: token_id is the memory token
                modify = ModifyTLK(token_id, is_replacement=False)
                modify.mod_index = idx  # Store the original TLK index for reference
                modify.text = right_entry.text
                modify.sound = right_entry.voiceover
                modifications.modifiers.append(modify)

                # Track mapping for new entries too (though they may not have refs in vanilla)
                strref_mappings[idx] = token_id
                token_id += 1

        # Note: strref_mappings are NOT stored on ModificationsTLK
        # They will be returned as a tuple with the modifications object
        # This keeps ModificationsTLK clean for reader/patcher code

        if modifications.modifiers:
            print(f"TLK modifications: identifier={identifier}, modifier_count={len(modifications.modifiers)}, strref_count={len(strref_mappings)}")
            # Return tuple: (modifications, strref_mappings)
            # The caller will extract both and store in TLKModificationWithSource
            return (modifications, strref_mappings)
        return None


class SSFDiffAnalyzer(DiffAnalyzer):
    """Analyzer for SSF file differences."""

    def analyze(
        self,
        left_data: bytes,
        right_data: bytes,
        identifier: str,
    ) -> ModificationsSSF | None:
        """Analyze SSF differences and create modification object."""
        try:
            left_ssf = read_ssf(left_data)
            right_ssf = read_ssf(right_data)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to parse SSF files: identifier={identifier}, error={e.__class__.__name__}: {e}")
            traceback.print_exc()
            return None

        # Extract just the filename from the identifier (may contain full path like "install/modules/file.ssf")
        filename: str = PurePath(identifier).name
        modifications = ModificationsSSF(filename, replace=False, modifiers=[])

        # Check all SSF sounds
        for sound in SSFSound:
            left_value = left_ssf.get(sound)
            right_value = right_ssf.get(sound)
            values_differ = left_value != right_value

            if values_differ:
                right_value_exists = right_value is not None
                if not right_value_exists:
                    continue

                modify = ModifySSF(sound, NoTokenUsage(str(right_value)))
                modifications.modifiers.append(modify)

        if modifications.modifiers:
            print(f"SSF modifications: identifier={identifier}, modifier_count={len(modifications.modifiers)}")

        return modifications if modifications.modifiers else None


class DiffAnalyzerFactory:
    """Factory for creating appropriate diff analyzers."""

    @staticmethod
    def get_analyzer(resource_type: str) -> DiffAnalyzer | None:
        """Get the appropriate analyzer for a resource type."""
        resource_type_lower = resource_type.lower()

        is_twoda = resource_type_lower in ("2da", "twoda")
        if is_twoda:
            return TwoDADiffAnalyzer()

        is_gff = resource_type_lower in ("gff", "utc", "uti", "utp", "ute", "utm", "utd", "utw", "dlg", "are", "git", "ifo", "gui", "jrl", "fac")
        if is_gff:
            return GFFDiffAnalyzer()

        is_tlk = resource_type_lower == "tlk"
        if is_tlk:
            return TLKDiffAnalyzer()

        is_ssf = resource_type_lower == "ssf"
        if is_ssf:
            return SSFDiffAnalyzer()

        return None


# Standalone functions for StrRef reference analysis
def _find_strref_in_gff_struct(
    gff_struct: GFFStruct,
    target_strref: int,
    current_path: PurePath,
) -> list[PurePath]:
    """Recursively find all LocalizedString fields with the target StrRef.

    Args:
        gff_struct: GFFStruct to search
        target_strref: StrRef to find
        current_path: Current path in the GFF structure

    Returns:
        List of paths to fields containing the target StrRef
    """
    locations: list[PurePath] = []

    for label, field_type, value in gff_struct:
        field_path = current_path / label

        is_locstring = field_type == GFFFieldType.LocalizedString
        is_locstring_value = isinstance(value, LocalizedString)
        if is_locstring and is_locstring_value:
            matches_target = value.stringref == target_strref
            if matches_target:
                locations.append(field_path)

        is_struct = field_type == GFFFieldType.Struct
        is_struct_value = isinstance(value, GFFStruct)
        if is_struct and is_struct_value:
            nested_locations = _find_strref_in_gff_struct(value, target_strref, field_path)
            locations.extend(nested_locations)

        is_list = field_type == GFFFieldType.List
        is_list_value = isinstance(value, GFFList)
        if is_list and is_list_value:
            for idx, item in enumerate(value):
                is_item_struct = isinstance(item, GFFStruct)
                if is_item_struct:
                    item_path = field_path / str(idx)
                    item_locations = _find_strref_in_gff_struct(item, target_strref, item_path)
                    locations.extend(item_locations)

    return locations


def _extract_ncs_consti_offsets(  # noqa: C901, PLR0912
    ncs_data: bytes,
    target_value: int,
) -> list[int]:
    """Extract byte offsets of all CONSTI instructions with a specific value from NCS bytecode.

    Args:
        ncs_data: Raw NCS file bytes
        target_value: The integer value to search for in CONSTI instructions

    Returns:
        List of byte offsets where the 4-byte CONSTI value starts (offset+2 from instruction start)
    """
    offsets: list[int] = []
    try:
        with BinaryReader.from_auto(ncs_data) as reader:
            # Skip NCS header (13 bytes)
            signature = reader.read_string(4)
            is_valid_signature = signature == "NCS "
            if not is_valid_signature:
                return offsets
            version = reader.read_string(4)
            is_valid_version = version == "V1.0"
            if not is_valid_version:
                return offsets
            magic_byte = reader.read_uint8()
            is_valid_magic = magic_byte == 0x42  # noqa: PLR2004
            if not is_valid_magic:
                return offsets
            total_size = reader.read_uint32(big=True)

            # Read instructions and track offsets
            while reader.position() < total_size and reader.remaining() > 0:
                opcode = reader.read_uint8()
                qualifier = reader.read_uint8()

                # Check if this is CONSTI (opcode=0x04, qualifier=0x03)
                is_consti = opcode == 0x04 and qualifier == 0x03  # noqa: PLR2004
                if is_consti:
                    value_offset = reader.position()
                    const_value = reader.read_int32(big=True)
                    matches_target = const_value == target_value
                    if matches_target:
                        offsets.append(value_offset)
                # Skip to next instruction based on opcode/qualifier
                elif opcode == 0x04:  # CONSTx  # noqa: PLR2004
                    is_constf = qualifier == 0x04  # noqa: PLR2004
                    if is_constf:
                        reader.skip(4)
                    else:
                        is_consts = qualifier == 0x05  # noqa: PLR2004
                        if is_consts:
                            str_len = reader.read_uint16(big=True)
                            reader.skip(str_len)
                        else:
                            is_consto = qualifier == 0x06  # noqa: PLR2004
                            if is_consto:
                                reader.skip(4)
                elif opcode in (0x01, 0x03, 0x26, 0x27):  # CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP
                    reader.skip(6)
                elif opcode == 0x2C:  # STORE_STATE  # noqa: PLR2004
                    reader.skip(8)
                elif opcode in (0x1B, 0x1D, 0x1E, 0x1F, 0x23, 0x24, 0x25, 0x28, 0x29):  # MOVSP, jumps, inc/dec
                    reader.skip(4)
                elif opcode == 0x05:  # ACTION  # noqa: PLR2004
                    reader.skip(3)
                elif opcode == 0x21:  # DESTRUCT  # noqa: PLR2004
                    reader.skip(6)
                elif opcode == 0x0B and qualifier == 0x24:  # EQUALTT  # noqa: PLR2004
                    reader.skip(2)
                elif opcode == 0x0C and qualifier == 0x24:  # NEQUALTT  # noqa: PLR2004
                    reader.skip(2)
                    # Other instructions have no additional data

    except Exception as e:  # noqa: BLE001, S110
        # If anything fails, return what we found so far
        exception_type = e.__class__.__name__
        offsets_so_far = len(offsets)
        print(f"NCS processing failed: target_value={target_value}, exception_type={exception_type}, error={e}, offsets_so_far={offsets_so_far}")

    return offsets


def analyze_tlk_strref_references(  # noqa: PLR0913
    tlk_modifications: tuple[ModificationsTLK, dict[int, int]],  # noqa: ARG001
    strref_mappings: dict[int, int],
    installation_or_folder_path: Path,
    gff_modifications: list[ModificationsGFF],
    twoda_modifications: list[Modifications2DA],
    ssf_modifications: list[ModificationsSSF],
    ncs_modifications: list,  # list[ModificationsNCS]
) -> None:
    """Analyze StrRef references and create patches to update them to new tokens.

    Searches the ENTIRE installation/folder for all files that reference the modified StrRefs,
    not just files in the diff. Creates patches to update those references to use StrRef tokens.

    Args:
        tlk_modifications: ModificationsTLK object
        strref_mappings: Dictionary mapping old StrRef -> token_id for reference analysis
        installation_or_folder_path: Path to KOTOR installation or folder to search
        gff_modifications: List to append GFF modifications to
        twoda_modifications: List to append 2DA modifications to
        ssf_modifications: List to append SSF modifications to
        ncs_modifications: List to append NCS modifications to
    """
    if not strref_mappings:
        print(f"No StrRef mappings provided: installation_path={installation_or_folder_path}")
        return
    print(f"Analyzing StrRef references: {len(strref_mappings)} mappings")

    try:
        # Check if this is an installation or just a folder
        is_installation = False
        installation = None
        try:
            installation = Installation(installation_or_folder_path)
            is_installation = True
            game = installation.game()
        except Exception:  # noqa: BLE001
            # Not an installation, treat as folder
            is_installation = False
            print(f"Treating as folder, attempting game detection: path={installation_or_folder_path}")
            # Try to detect game from folder structure (look for chitin.key or swkotor.exe)
            chitin_key = installation_or_folder_path / "chitin.key"
            swkotor_exe = installation_or_folder_path / "swkotor.exe"
            swkotor2_exe = installation_or_folder_path / "swkotor2.exe"

            chitin_exists = chitin_key.is_file()
            swkotor_exists = swkotor_exe.is_file()
            swkotor2_exists = swkotor2_exe.is_file()
            print(
                f"Game detection files: chitin_exists={chitin_exists}, swkotor_exists={swkotor_exists}, swkotor2_exists={swkotor2_exists}, path={installation_or_folder_path}"
            )  # noqa: E501

            if swkotor2_exists:
                game = Game.K2
                print(f"Detected K2 from swkotor2.exe: game={game}, path={installation_or_folder_path}")
            elif swkotor_exists or chitin_exists:
                game = Game.K1
                print(f"Detected K1 from files: game={game}, swkotor_exists={swkotor_exists}, chitin_exists={chitin_exists}, path={installation_or_folder_path}")
            else:
                print(
                    f"Could not detect game type: path={installation_or_folder_path}, chitin_exists={chitin_exists}, swkotor_exists={swkotor_exists}, swkotor2_exists={swkotor2_exists}"  # noqa: E501
                )  # noqa: E501
                print(f"Assuming K2 by default: path={installation_or_folder_path}")
                game = Game.K2

        # Get the relevant 2DA column definitions
        is_k1 = game.is_k1()
        is_k2 = game.is_k2()
        print(f"Determining game-specific 2DA columns: game={game}, is_k1={is_k1}, is_k2={is_k2}")
        if is_k1:
            relevant_2da_filenames = K1Columns2DA.StrRefs.as_dict()
            print(f"Using K1 2DA definitions: game={game}, num_2da_files={len(relevant_2da_filenames)}")
        elif is_k2:
            relevant_2da_filenames = K2Columns2DA.StrRefs.as_dict()
            print(f"Using K2 2DA definitions: game={game}, num_2da_files={len(relevant_2da_filenames)}")
        else:
            print(f"Unknown game type, cannot proceed: game={game}, path={installation_or_folder_path}")
            return

        search_type = "installation" if is_installation else "folder"
        twoda_count = len(relevant_2da_filenames)
        print(f"Searching for StrRef references: search_type={search_type}, path={installation_or_folder_path}, game={game}, twoda_file_count={twoda_count}")

    except Exception as e:  # noqa: BLE001
        print(f"Failed to initialize StrRef analysis: {e.__class__.__name__}: {e}")
        print("Full traceback:")
        for line in traceback.format_exc().splitlines():
            print(f"  {line}")
        return

    # For each modified/new StrRef, find all references in the ENTIRE installation/folder
    for old_strref, token_id in strref_mappings.items():
        print(f"Analyzing StrRef {old_strref} -> token {token_id}")

        try:
            found_resources: set[FileResource] = set()

            if is_installation and installation:
                # Use the comprehensive search method
                from pykotor.tools.reference_cache import find_tlk_entry_references  # noqa: PLC0415

                found_resources = find_tlk_entry_references(installation, old_strref, logger=None)
            else:
                # Search all relevant files in folder
                all_files = list(installation_or_folder_path.rglob("*"))

                found_resources = set()
                for file_path in all_files:
                    if not file_path.is_file():
                        continue

                    restype: ResourceType | None = ResourceType.from_extension(file_path.suffix)
                    if not restype or not restype.is_valid():
                        continue

                    file_res: FileResource = FileResource(
                        resname=file_path.stem,
                        restype=restype,
                        size=file_path.stat().st_size,
                        offset=0,
                        filepath=file_path,
                    )

                    # Check based on file type
                    try:
                        if restype is ResourceType.TwoDA and file_path.name.lower() in relevant_2da_filenames:
                            twoda_obj = read_2da(BinaryReader.load_file(file_path))
                            columns_with_strrefs = relevant_2da_filenames[file_path.name.lower()]

                            for row_idx in range(twoda_obj.get_height()):
                                for column_name in columns_with_strrefs:
                                    if column_name == ">>##HEADER##<<":
                                        continue
                                    cell = twoda_obj.get_cell(row_idx, column_name)
                                    if cell and cell.strip().isdigit() and int(cell.strip()) == old_strref:
                                        found_resources.add(file_res)
                                        break

                        elif restype is ResourceType.SSF:
                            ssf_obj = read_ssf(BinaryReader.load_file(file_path))
                            for sound in SSFSound:
                                if ssf_obj.get(sound) == old_strref:
                                    found_resources.add(file_res)
                                    break

                        elif restype is ResourceType.NCS:
                            # Just check if it contains the StrRef, actual offset extraction happens later
                            ncs_data = BinaryReader.load_file(file_path)
                            if _extract_ncs_consti_offsets(ncs_data, old_strref):
                                found_resources.add(file_res)

                        else:
                            # Try as GFF
                            gff_obj = read_gff(BinaryReader.load_file(file_path))
                            if _find_strref_in_gff_struct(gff_obj.root, old_strref, PurePath()):
                                found_resources.add(file_res)
                    except Exception as e:  # noqa: BLE001
                        print(f"Failed to process file {file_path}: {e.__class__.__name__}: {e}")
                        print("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            print(f"  {line}")
                        continue

            if not found_resources:
                continue

            print(f"  Found {len(found_resources)} references")

            # Process each resource that references this StrRef
            for idx, resource in enumerate(found_resources, 1):
                filename = resource.filename().lower()
                restype = resource.restype()

                print(f"  [{idx}/{len(found_resources)}] Patching {filename} (StrRef {old_strref} → StrRef{token_id})")

                # Handle 2DA files
                if filename in relevant_2da_filenames and restype is ResourceType.TwoDA:
                    try:
                        twoda_obj = read_2da(resource.data())
                        columns_with_strrefs = relevant_2da_filenames[filename]

                        # Find all cells containing this StrRef
                        for row_idx in range(twoda_obj.get_height()):
                            for column_name in columns_with_strrefs:
                                if column_name == ">>##HEADER##<<":
                                    # Special case: header row contains strrefs - skip as we can't patch headers
                                    continue

                                try:
                                    cell_value = twoda_obj.get_cell(row_idx, column_name)
                                    if cell_value and cell_value.strip().isdigit() and int(cell_value.strip()) == old_strref:
                                        # Found a match - create a ChangeRow2DA modification
                                        print(f"Found StrRef {old_strref} in {filename} row {row_idx}, column {column_name}")

                                        # Check if we already have a modification for this file
                                        existing_mod = next((m for m in twoda_modifications if m.sourcefile == filename), None)
                                        if existing_mod is None:
                                            existing_mod = Modifications2DA(filename)
                                            twoda_modifications.append(existing_mod)

                                        try:
                                            row_label = twoda_obj.get_label(row_idx)
                                        except Exception:  # noqa: BLE001
                                            row_label = None
                                        target_row_index = _resolve_row_index_value(row_idx, row_label)

                                        # Create ChangeRow2DA with 2DAMEMORY token
                                        change_row = ChangeRow2DA(
                                            identifier=f"strref_update_{row_idx}_{column_name}",
                                            target=Target(TargetType.ROW_INDEX, target_row_index),
                                            cells={column_name: RowValueTLKMemory(token_id)},
                                        )
                                        existing_mod.modifiers.append(change_row)

                                except Exception:  # noqa: BLE001
                                    print("Full traceback:")
                                    for line in traceback.format_exc().splitlines():
                                        print(f"  {line}")
                                    continue

                    except Exception as e:  # noqa: BLE001
                        print(f"Failed to process 2DA {filename}: {e.__class__.__name__}: {e}")
                        print("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            print(f"  {line}")

                # Handle SSF files
                elif restype is ResourceType.SSF:
                    try:
                        ssf_obj = read_ssf(resource.data())

                        # Check all SSF sounds for this StrRef
                        modified_sounds: list[SSFSound] = []
                        for sound in SSFSound:
                            sound_strref = ssf_obj.get(sound)
                            if sound_strref == old_strref:
                                modified_sounds.append(sound)

                        if modified_sounds:
                            print(f"Found {len(modified_sounds)} SSF sounds with StrRef {old_strref} in {filename}")

                            # Check if we already have a modification for this file
                            existing_ssf_mod = next((m for m in ssf_modifications if m.sourcefile == filename), None)
                            if existing_ssf_mod is None:
                                existing_ssf_mod = ModificationsSSF(filename, replace=False, modifiers=[])
                                ssf_modifications.append(existing_ssf_mod)

                            # Create ModifySSF for each sound
                            for sound in modified_sounds:
                                modify_ssf = ModifySSF(sound, TokenUsageTLK(token_id))
                                existing_ssf_mod.modifiers.append(modify_ssf)
                                print(f"Created SSF patch for {filename} sound {sound.name}: StrRef {old_strref} -> StrRef{token_id}")

                    except Exception as e:  # noqa: BLE001
                        print(f"Failed to process SSF {filename}: {e.__class__.__name__}: {e}")
                        print("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            print(f"  {line}")

                # Handle NCS files (compiled scripts)
                elif restype is ResourceType.NCS:
                    try:
                        ncs_data = resource.data()
                        consti_offsets = _extract_ncs_consti_offsets(ncs_data, old_strref)

                        if consti_offsets:
                            print(f"Found {len(consti_offsets)} CONSTI instructions with StrRef {old_strref} in {filename}")

                            # Check if we already have a modification for this file
                            existing_ncs_mod = next((m for m in ncs_modifications if m.sourcefile == filename), None)
                            if existing_ncs_mod is None:
                                existing_ncs_mod = ModificationsNCS(filename, replace=False, modifiers=[])
                                ncs_modifications.append(existing_ncs_mod)

                            # Create HACKList entries for each offset
                            for offset in consti_offsets:
                                # Create ModifyNCS with STRREF32 type (32-bit signed int for CONSTI instructions)
                                # This writes 32-bit int from memory.memory_str[token_id]
                                modify_ncs = ModifyNCS(
                                    token_type=NCSTokenType.STRREF32,
                                    offset=offset,
                                    token_id_or_value=token_id,
                                )
                                existing_ncs_mod.modifiers.append(modify_ncs)

                    except Exception as e:  # noqa: BLE001
                        print(f"Failed to process NCS {filename}: {e.__class__.__name__}: {e}")
                        print("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            print(f"  {line}")

                # Handle GFF files
                else:
                    try:
                        gff_obj = read_gff(resource.data())

                        # Search recursively for LocalizedString fields with this StrRef
                        strref_locations = _find_strref_in_gff_struct(gff_obj.root, old_strref, PurePath())

                        if strref_locations:
                            # Check if we already have a modification for this file
                            existing_gff_mod = next((m for m in gff_modifications if m.sourcefile == filename), None)
                            if existing_gff_mod is None:
                                existing_gff_mod = ModificationsGFF(filename, replace=False, modifiers=[])
                                gff_modifications.append(existing_gff_mod)

                            # Create ModifyFieldGFF for each location
                            for field_path in strref_locations:
                                # Create LocalizedStringDelta with token
                                locstring_delta = LocalizedStringDelta(FieldValueTLKMemory(token_id))

                                modify_field = ModifyFieldGFF(
                                    path=str(field_path).replace("/", "\\"),
                                    value=FieldValueConstant(locstring_delta),
                                )
                                existing_gff_mod.modifiers.append(modify_field)

                    except Exception as e:  # noqa: BLE001
                        print(f"Failed to process GFF {filename}: {e.__class__.__name__}: {e}")
                        print("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            print(f"  {line}")

        except Exception as e:  # noqa: BLE001
            print(f"Failed to analyze StrRef {old_strref}: {e.__class__.__name__}: {e}")
            print("Full traceback:")
            for line in traceback.format_exc().splitlines():
                print(f"  {line}")
            continue


def analyze_2da_memory_references(  # noqa: PLR0913, C901
    twoda_modifications: list[Modifications2DA],
    installation_or_folder_path: Path,
    gff_modifications: list[ModificationsGFF],
) -> None:
    """Analyze 2DA memory references and create patches to update them to new tokens.

    Searches the ENTIRE installation/folder for all GFF files that reference modified 2DA rows,
    and creates patches to update those references to use 2DAMEMORY tokens.

    Args:
        twoda_modifications: List of 2DA modifications with assigned token IDs
        installation_or_folder_path: Path to KOTOR installation or folder to search
        gff_modifications: List to append GFF modifications to
    """
    if not twoda_modifications:
        mods_count = 0
        print(f"No 2DA modifications to analyze: mods_count={mods_count}, installation_path={installation_or_folder_path}")
        return

    print(f"Analyzing 2DA memory references: {len(twoda_modifications)} 2DA files modified")

    # Import the mapping here to avoid circular imports
    from pykotor.tools.reference_cache import GFF_FIELD_TO_2DA_MAPPING  # noqa: PLC0415

    # Build reverse mapping: 2da_filename -> list of field names that reference it
    twoda_to_fields: dict[str, list[str]] = {}
    for field_name, twoda_filename in GFF_FIELD_TO_2DA_MAPPING.items():
        twoda_filename_lower = str(twoda_filename.resname).lower()
        if twoda_filename_lower not in twoda_to_fields:
            twoda_to_fields[twoda_filename_lower] = []
        twoda_to_fields[twoda_filename_lower].append(field_name)

    # Build mapping of (2da_filename, row_index) -> token_id from modifications
    row_to_token: dict[tuple[str, int], int] = {}

    for mod_2da in twoda_modifications:
        twoda_filename = str(mod_2da.sourcefile).lower()

        # Process each modifier to extract row indices and token IDs
        for modifier in mod_2da.modifiers:
            if isinstance(modifier, AddRow2DA) and modifier.store_2da:
                # AddRow rows have unknown indices until patch-time; we cannot create static mappings for RowIndex storage.
                for token_id, _row_value in modifier.store_2da.items():
                    if isinstance(_row_value, RowValueRowIndex):
                        print(f"Skipping AddRow2DA mapping for 2DAMEMORY token {token_id}: row index is determined at install time")
                        continue
                    if isinstance(_row_value, RowValueConstant):
                        try:
                            row_idx = int(_row_value.string)
                        except (ValueError, AttributeError) as e:  # noqa: PERF203
                            print(f"Failed to map {twoda_filename} row {_row_value.string} -> 2DAMEMORY{token_id}: {e.__class__.__name__}: {e}")
                            traceback.print_exc()
                            continue
                        row_to_token[(twoda_filename, row_idx)] = token_id
                        print(f"Mapped {twoda_filename} row {row_idx} -> 2DAMEMORY{token_id}")

            elif isinstance(modifier, ChangeRow2DA) and modifier.target.target_type is TargetType.ROW_INDEX:
                # For ChangeRow, extract the target row index
                assert isinstance(modifier.target.value, int), "Target value was expected to be int if type is row index."
                row_idx = modifier.target.value
                if not isinstance(row_idx, int) or not modifier.store_2da:
                    continue

                # Check if we're storing this row's index in a token
                for token_id, _row_value in modifier.store_2da.items():
                    if not isinstance(_row_value, RowValueRowIndex):
                        continue
                    row_to_token[(twoda_filename, row_idx)] = token_id
                    print(f"Mapped {twoda_filename} row {row_idx} -> 2DAMEMORY{token_id}")

    if not row_to_token:
        mappings_count = 0
        print(f"No 2DA row->token mappings found: mappings_count={mappings_count}")
        return

    print(f"Found {len(row_to_token)} 2DA row->token mappings")

    # Search for GFF files that reference these 2DA rows
    try:
        # Check if this is an installation or just a folder
        is_installation = False
        installation = None
        try:
            installation = Installation(installation_or_folder_path)
            is_installation = True
        except Exception:  # noqa: BLE001
            is_installation = False
            print(f"Treating as folder for 2DA reference search: path={installation_or_folder_path}")

        # Collect all GFF files to search
        if is_installation and installation:
            # Search all resources in the installation (Installation implements __iter__)
            all_resources: list[FileResource] = [res for res in installation if res.restype() in GFFContent.get_restypes()]
        else:
            # Search all files in folder
            all_files: list[Path] = list(installation_or_folder_path.rglob("*"))
            all_resources = []

            for file_path in all_files:
                if not file_path.is_file():
                    continue

                restype: ResourceType = ResourceType.from_extension(file_path.suffix)
                if restype not in GFFContent.get_restypes():
                    continue

                file_res: FileResource = FileResource(
                    resname=file_path.stem,
                    restype=restype,
                    size=file_path.stat().st_size,
                    offset=0,
                    filepath=file_path,
                )
                all_resources.append(file_res)

        print(f"Searching {len(all_resources)} resources for 2DA references")

        # For each modified 2DA row, search for references
        for (twoda_filename, row_index), token_id in row_to_token.items():
            # Get field names that reference this 2DA
            if twoda_filename not in twoda_to_fields:
                print(f"No known field mappings for {twoda_filename}")
                continue

            field_names = twoda_to_fields[twoda_filename]
            print(f"Analyzing {twoda_filename} row {row_index} -> token {token_id} (fields: {', '.join(field_names)})")

            found_count = 0

            # Search each resource
            for resource in all_resources:
                try:
                    data = resource.data()
                    gff_obj = read_gff(data)

                    # Search for fields matching this 2DA reference
                    field_paths = _find_2da_ref_in_gff_struct(
                        gff_obj.root,
                        field_names,
                        row_index,
                        PurePath(),
                    )

                    if field_paths:
                        found_count += len(field_paths)
                        filename = resource.filename().lower()

                        # Check if we already have a modification for this file
                        existing_gff_mod = next((m for m in gff_modifications if m.sourcefile == filename), None)
                        if existing_gff_mod is None:
                            existing_gff_mod = ModificationsGFF(filename, replace=False, modifiers=[])
                            gff_modifications.append(existing_gff_mod)

                        # Create ModifyFieldGFF for each location
                        for field_path in field_paths:
                            modify_field = ModifyFieldGFF(
                                path=str(field_path).replace("/", "\\"),
                                value=FieldValue2DAMemory(token_id),
                            )
                            existing_gff_mod.modifiers.append(modify_field)
                            print(f"  [{filename}] {field_path} -> 2DAMEMORY{token_id}")

                except Exception:  # noqa: BLE001, S110
                    # Not a GFF file or failed to parse, skip
                    pass

            if found_count > 0:
                print(f"  Found {found_count} references total")

    except Exception as e:  # noqa: BLE001
        print(f"Failed to analyze 2DA memory references: {e.__class__.__name__}: {e}")
        print("Full traceback:")
        for line in traceback.format_exc().splitlines():
            print(f"  {line}")


def _find_2da_ref_in_gff_struct(
    gff_struct: GFFStruct,
    field_names: list[str],
    target_value: int,
    current_path: PurePath,
) -> list[PurePath]:
    """Recursively find all fields with specific names that have the target value.

    Args:
        gff_struct: GFFStruct to search
        field_names: List of field names to look for
        target_value: The integer value to match
        current_path: Current path in the GFF structure

    Returns:
        List of paths to fields containing the target value
    """
    locations: list[PurePath] = []

    for label, field_type, value in gff_struct:
        field_path = current_path / label

        # Check if this is one of the fields we're looking for and value matches
        if label in field_names and isinstance(value, int) and value == target_value:
            locations.append(field_path)

        # Recurse into nested structures
        if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
            nested_locations = _find_2da_ref_in_gff_struct(value, field_names, target_value, field_path)
            locations.extend(nested_locations)

        elif field_type == GFFFieldType.List and isinstance(value, GFFList):
            for idx, item in enumerate(value):
                if isinstance(item, GFFStruct):
                    item_path = field_path / str(idx)
                    item_locations = _find_2da_ref_in_gff_struct(item, field_names, target_value, item_path)
                    locations.extend(item_locations)

    return locations
