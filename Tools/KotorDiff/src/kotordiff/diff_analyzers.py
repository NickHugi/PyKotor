"""Diff analyzers that convert raw diffs into TSLPatcher modification structures.

This module provides analyzers that examine differences between game files
and generate appropriate TSLPatcher modification objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import TYPE_CHECKING, Any

from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf.ssf_auto import read_ssf
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.resource.formats.tlk.tlk_auto import read_tlk
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.tslpatcher.memory import NoTokenUsage
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    AddStructToListGFF,
    FieldValueConstant,
    ModificationsGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK, ModifyTLK
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    Modifications2DA,
    RowValueConstant,
    Target,
    TargetType,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.tlk.tlk_data import TLKEntry
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.tslpatcher.mods.template import PatcherModifications


class DiffAnalyzer(ABC):
    """Abstract base class for diff analyzers."""

    @abstractmethod
    def analyze(
        self,
        left_data: bytes,
        right_data: bytes,
        identifier: str,
    ) -> PatcherModifications | None:
        """Analyze differences and return a PatcherModifications object."""


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
        except Exception:  # noqa: BLE001
            return None

        modifications = Modifications2DA(identifier)

        # Detect column differences
        self._analyze_columns(left_2da, right_2da, modifications)

        # Detect row differences
        self._analyze_rows(left_2da, right_2da, modifications)

        return modifications if modifications.modifiers else None

    def _analyze_columns(
        self,
        left_2da: TwoDA,
        right_2da: TwoDA,
        modifications: Modifications2DA,
    ):
        """Analyze column differences."""
        left_headers = set(left_2da.get_headers())
        right_headers = set(right_2da.get_headers())

        # Detect added columns
        added_columns = right_headers - left_headers
        for col_name in added_columns:
            _col_index = right_2da.get_headers().index(col_name)

            # Determine default value
            column_data = right_2da.get_column(col_name)
            default_value = self._determine_default_value(column_data)

            # Create AddColumn2DA modifier
            add_column = AddColumn2DA(
                identifier=f"add_col_{col_name}",
                header=col_name,
                default=default_value,
                index_insert={},
                label_insert={},
                store_2da={},
            )

            # Populate specific cell values if they differ from default
            for row_idx in range(right_2da.get_height()):
                cell_value = right_2da.get_cell(row_idx, col_name)
                if cell_value != default_value:
                    add_column.index_insert[row_idx] = RowValueConstant(cell_value)

            modifications.modifiers.append(add_column)

    def _analyze_rows(
        self,
        left_2da: TwoDA,
        right_2da: TwoDA,
        modifications: Modifications2DA,
    ):
        """Analyze row differences."""
        left_height = left_2da.get_height()
        right_height = right_2da.get_height()

        # Common headers
        common_headers = [
            h for h in left_2da.get_headers()
            if h in right_2da.get_headers()
        ]

        # Check existing rows for modifications
        for row_idx in range(min(left_height, right_height)):
            changed_cells = {}

            for header in common_headers:
                left_value = left_2da.get_cell(row_idx, header)
                right_value = right_2da.get_cell(row_idx, header)

                if left_value != right_value:
                    changed_cells[header] = RowValueConstant(right_value)

            if changed_cells:
                change_row = ChangeRow2DA(
                    identifier=f"change_row_{row_idx}",
                    target=Target(TargetType.ROW_INDEX, row_idx),
                    cells=changed_cells,
                )
                modifications.modifiers.append(change_row)

        # Check for added rows
        if right_height > left_height:
            for row_idx in range(left_height, right_height):
                cells = {}
                row_label = right_2da.get_label(row_idx)

                for header in right_2da.get_headers():
                    cell_value = right_2da.get_cell(row_idx, header)
                    if cell_value:  # Only include non-empty cells
                        cells[header] = RowValueConstant(cell_value)

                add_row = AddRow2DA(
                    identifier=f"add_row_{row_idx}",
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
        if "****" in value_counts and value_counts["****"] > len(column_data) // 4:
            return "****"

        # Return most common value
        return max(value_counts.items(), key=lambda x: x[1])[0] if value_counts else "****"


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
        except Exception:  # noqa: BLE001
            return None

        modifications = ModificationsGFF(identifier, replace=False, modifiers=[])

        # Analyze struct differences recursively
        self._analyze_struct(
            left_gff.root,
            right_gff.root,
            PurePath(),
            modifications,
        )

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
        left_field = left_struct.acquire(field_label, None)
        if not left_field:
            print(f"Field {field_label} not found in left struct: {left_struct}")
            return
        right_field = right_struct.acquire(field_label, None)
        if not right_field:
            print(f"Field {field_label} not found in right struct: {right_struct}")
            return

        if left_field.field_type != right_field.field_type:
            # Type changed - treat as modification
            self._create_modify_field(
                right_struct,
                field_label,
                field_path,
                modifications,
            )
            return

        # Compare values based on type
        if left_field.field_type == GFFFieldType.Struct:
            # Recursively analyze nested struct
            left_nested = left_struct.get_struct(field_label)
            right_nested = right_struct.get_struct(field_label)
            self._analyze_struct(left_nested, right_nested, field_path, modifications)

        elif left_field.field_type == GFFFieldType.List:
            # Analyze list differences
            left_list = left_struct.get_list(field_label)
            right_list = right_struct.get_list(field_label)
            self._analyze_list(left_list, right_list, field_path, modifications)

        # Scalar value comparison
        elif not self._values_equal(left_field, right_field, left_struct, right_struct, field_label):
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
        for idx in range(min(left_size, right_size)):
            item_path = path / str(idx)
            left_item = left_list.at(idx)
            right_item = right_list.at(idx)
            if not left_item:
                print(f"List item {idx} not found in left list: {left_list}")
                continue
            if not right_item:
                print(f"List item {idx} not found in right list: {right_list}")
                continue
            self._analyze_struct(left_item, right_item, item_path, modifications)

        # Handle added list elements
        if right_size > left_size:
            for idx in range(left_size, right_size):
                right_item = right_list.at(idx)
                if not right_item:
                    print(f"List item {idx} not found in right list during add: {right_list}")
                    continue

                # Create AddStructToListGFF for each new list entry
                # Generate unique identifier for this list addition
                section_name = f"gff_{modifications.sourcefile.replace('.', '_')}_{path.name}_{idx}_0"

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
                self._add_all_struct_fields(right_item, add_struct, PurePath())

                modifications.modifiers.append(add_struct)

    def _add_all_struct_fields(  # noqa: C901, PLR0912
        self,
        struct: GFFStruct,
        parent_modifier: AddStructToListGFF | AddFieldGFF,
        base_path: PurePath,
    ):
        """Recursively add all fields from a struct as AddFieldGFF modifiers."""
        # Iterate over struct fields (returns tuples of (label, field_type, value))
        for field_info in struct:
            field_label, field_type, field_value = field_info
            field_path = base_path / field_label if base_path.name else PurePath(field_label)

            # Generate unique section name for this field
            parent_id = parent_modifier.identifier
            section_name = f"{parent_id}_{field_label}_0".replace("\\", "_").replace("/", "_")

            # Create AddFieldGFF for this field
            if field_type == GFFFieldType.Struct:
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
                if isinstance(field_value, GFFStruct):
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
                if isinstance(field_value, GFFList):
                    for list_idx in range(len(field_value)):
                        list_item = field_value.at(list_idx)
                        if isinstance(list_item, GFFStruct):
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
        field = struct.acquire(field_label, None)
        if not field:
            print(f"Field {field_label} not found in struct: {struct}")
            return
        value = self._get_field_value(struct, field_label, field.field_type)

        modify_field = ModifyFieldGFF(
            path=str(field_path).replace("/", "\\"),
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
        field = struct.acquire(field_label, None)
        if not field:
            print(f"Field {field_label} not found in struct: {struct}")
            return
        value = self._get_field_value(struct, field_label, field.field_type)

        # Determine parent path
        parent_path = str(field_path.parent).replace("/", "\\") if field_path.parent.parts else ""

        add_field = AddFieldGFF(
            identifier=f"add_{field_label}",
            label=field_label,
            field_type=field.field_type,
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
        if getter:
            return getter(field_label)

        return None

    GFF_FLOAT_TOLERANCE = 1e-6

    def _values_equal(
        self,
        left_field: Any,
        right_field: Any,
        left_struct: GFFStruct,
        right_struct: GFFStruct,
        field_label: str,
    ) -> bool:
        """Check if two field values are equal."""
        left_value = self._get_field_value(left_struct, field_label, left_field.field_type)
        right_value = self._get_field_value(right_struct, field_label, right_field.field_type)

        # Special handling for floats
        if isinstance(left_value, float) and isinstance(right_value, float):
            return abs(left_value - right_value) < self.GFF_FLOAT_TOLERANCE

        return left_value == right_value


class TLKDiffAnalyzer(DiffAnalyzer):
    """Analyzer for TLK file differences."""

    def analyze(
        self,
        left_data: bytes,
        right_data: bytes,
        identifier: str,
    ) -> ModificationsTLK | None:
        """Analyze TLK differences and create modification object."""
        try:
            left_tlk = read_tlk(left_data)
            right_tlk = read_tlk(right_data)
        except Exception as e:  # noqa: BLE001
            print(f"Error reading TLK: {e}")
            return None

        # Use "append.tlk" as the filename per TSLPatcher convention
        modifications = ModificationsTLK(filename="append.tlk", replace=False, modifiers=[])

        left_size = len(left_tlk)
        right_size = len(right_tlk)

        token_id = 0

        # Check for modified entries
        for idx in range(min(left_size, right_size)):
            left_entry: TLKEntry | None = left_tlk.get(idx)
            right_entry: TLKEntry | None = right_tlk.get(idx)
            if left_entry is None:
                print(f"TLK entry {idx} not found in left TLK: {left_tlk}")
                continue
            if right_entry is None:
                print(f"TLK entry {idx} not found in right TLK: {right_tlk}")
                continue

            if left_entry.text != right_entry.text or left_entry.voiceover != right_entry.voiceover:
                # Replacement: token_id is the memory token, mod_index is the actual TLK string ID to replace
                modify = ModifyTLK(token_id, is_replacement=True)
                modify.mod_index = idx  # The actual TLK index to replace
                modify.text = right_entry.text
                modify.sound = right_entry.voiceover
                modifications.modifiers.append(modify)
                token_id += 1

        # Check for added entries (appends)
        if right_size > left_size:
            for idx in range(left_size, right_size):
                right_entry = right_tlk.get(idx)
                if right_entry is None:
                    print(f"TLK entry {idx} not found in right TLK: {right_tlk}")
                    continue
                # Append: token_id is the memory token, mod_index is the append.tlk index (0-based from start of appends)
                modify = ModifyTLK(token_id, is_replacement=False)
                modify.mod_index = idx  # Store the original TLK index for reference
                modify.text = right_entry.text
                modify.sound = right_entry.voiceover
                modifications.modifiers.append(modify)
                token_id += 1

        return modifications if modifications.modifiers else None


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
            print(f"Error reading SSF: {e}")
            return None

        modifications = ModificationsSSF(identifier, replace=False, modifiers=[])

        # Check all SSF sounds
        for sound in SSFSound:
            left_value = left_ssf.get(sound)
            right_value = right_ssf.get(sound)

            if left_value != right_value:
                if right_value is None:
                    print(f"SSF sound {sound} not found in right SSF: {right_ssf}")
                    continue
                modify = ModifySSF(sound, NoTokenUsage(str(right_value)))
                modifications.modifiers.append(modify)

        return modifications if modifications.modifiers else None


class DiffAnalyzerFactory:
    """Factory for creating appropriate diff analyzers."""

    @staticmethod
    def get_analyzer(resource_type: str) -> DiffAnalyzer | None:
        """Get the appropriate analyzer for a resource type."""
        resource_type_lower = resource_type.lower()

        if resource_type_lower in ("2da", "twoda"):
            return TwoDADiffAnalyzer()
        if resource_type_lower in ("gff", "utc", "uti", "utp", "ute", "utm", "utd", "utw", "dlg", "are", "git", "ifo", "gui", "jrl", "fac"):
            return GFFDiffAnalyzer()
        if resource_type_lower == "tlk":
            return TLKDiffAnalyzer()
        if resource_type_lower == "ssf":
            return SSFDiffAnalyzer()

        return None




