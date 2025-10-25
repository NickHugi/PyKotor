"""INI generator for creating TSLPatcher-compatible changes.ini files from diffs.

This module provides functionality to convert diff results into TSLPatcher configuration files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.formats.twoda.twoda_data import TwoDA

if TYPE_CHECKING:
    from kotordiff.diff_objects import (
        CellDiff,
        ColumnDiff,
        DiffResult,
        FieldDiff,
        GFFDiffResult,
        HeaderDiff,
        RowDiff,
        StructDiff,
        TLKDiffResult,
        TLKEntryDiff,
        TwoDADiffResult,
    )


class INISection:
    """Represents a section in a changes.ini file."""

    def __init__(self, name: str):
        self.name = name
        self.items: dict[str, str | int | float] = {}

    def add_item(self, key: str, value: str | int | float):
        """Add an item to this section."""
        self.items[key] = value

    def to_ini_string(self) -> str:
        """Convert this section to INI format string."""
        lines = [f"[{self.name}]"]
        for key, value in self.items.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines)


class INIGenerator(ABC):
    """Abstract base class for INI generators."""

    @abstractmethod
    def generate_sections(self, diff_result: DiffResult[Any]) -> list[INISection]:
        """Generate INI sections from a diff result."""


class TwoDAINIGenerator(INIGenerator):
    """Generator for 2DA file modifications in changes.ini format."""

    def generate_sections(self, diff_result: DiffResult[Any]) -> list[INISection]:  # type: ignore[override]
        """Generate 2DA modification sections."""
        from kotordiff.diff_objects import TwoDADiffResult
        
        diff_result = cast("TwoDADiffResult", diff_result)
        sections: list[INISection] = []

        if not diff_result.is_different:
            return sections

        # Create main 2DA file section
        filename = Path(diff_result.left_identifier).name
        main_section = INISection(filename)

        modifier_index = 0

        # Process column additions/removals
        if diff_result.column_diffs:
            for col_diff in diff_result.column_diffs:
                section = self._generate_column_diff_section(
                    f"addcol_{col_diff.column_index}",
                    col_diff,
                )
                if section:
                    main_section.add_item(f"AddColumn{modifier_index}", section.name)
                    sections.append(section)
                    modifier_index += 1

        # Process row modifications
        if diff_result.row_diffs:
            for row_diff in diff_result.row_diffs:
                section = self._generate_row_diff_section(
                    f"row_{row_diff.row_index}",
                    row_diff,
                )
                if section:
                    action = self._determine_row_action(row_diff)
                    main_section.add_item(f"{action}{modifier_index}", section.name)
                    sections.append(section)
                    modifier_index += 1

        if main_section.items:
            sections.insert(0, main_section)

        return sections

    def _determine_row_action(self, row_diff: RowDiff) -> str:
        """Determine the appropriate action for a row diff."""
        from kotordiff.diff_objects import DiffType

        if row_diff.diff_type == DiffType.ADDED:
            return "AddRow"
        elif row_diff.diff_type == DiffType.MODIFIED:
            return "ChangeRow"
        return "ChangeRow"  # Default

    def _generate_column_diff_section(
        self,
        identifier: str,
        col_diff: ColumnDiff,
    ) -> INISection | None:
        """Generate section for column differences."""
        from kotordiff.diff_objects import DiffType

        if col_diff.diff_type != DiffType.ADDED:
            return None

        section = INISection(identifier)
        section.add_item("ColumnLabel", col_diff.column_name or f"col_{col_diff.column_index}")
        section.add_item("DefaultValue", "****")

        return section

    def _generate_row_diff_section(
        self,
        identifier: str,
        row_diff: RowDiff,
    ) -> INISection | None:
        """Generate section for row differences."""
        from kotordiff.diff_objects import DiffType

        section = INISection(identifier)

        # Add row index/label
        section.add_item("RowIndex", row_diff.row_index)

        # Process cell differences
        if row_diff.cell_diffs:
            for cell_diff in row_diff.cell_diffs:
                if cell_diff.diff_type in (DiffType.MODIFIED, DiffType.ADDED):
                    if cell_diff.column_name and cell_diff.right_value is not None:
                        section.add_item(cell_diff.column_name, cell_diff.right_value)

        return section if len(section.items) > 1 else None


class GFFINIGenerator(INIGenerator):
    """Generator for GFF file modifications in changes.ini format."""

    def generate_sections(self, diff_result: DiffResult[Any]) -> list[INISection]:  # type: ignore[override]
        """Generate GFF modification sections."""
        from kotordiff.diff_objects import GFFDiffResult
        
        diff_result = cast("GFFDiffResult", diff_result)
        sections: list[INISection] = []

        if not diff_result.is_different:
            return sections

        # Create main GFF file section
        filename = Path(diff_result.left_identifier).name
        main_section = INISection(filename)

        modifier_index = 0

        # Process field differences
        if diff_result.field_diffs:
            for field_diff in diff_result.field_diffs:
                if field_diff.right_value is not None:
                    # Simple field modification
                    field_path = field_diff.field_path.replace("/", "\\")
                    value_str = self._format_field_value(field_diff.right_value)
                    main_section.add_item(field_path, value_str)

        # Process struct differences (adding new fields)
        if diff_result.struct_diffs:
            for struct_diff in diff_result.struct_diffs:
                section = self._generate_struct_diff_section(
                    f"addstruct_{modifier_index}",
                    struct_diff,
                )
                if section:
                    main_section.add_item(f"AddField{modifier_index}", section.name)
                    sections.append(section)
                    modifier_index += 1

        if main_section.items:
            sections.insert(0, main_section)

        return sections

    def _format_field_value(self, value: Any) -> str:
        """Format a field value for INI output."""
        if isinstance(value, (Vector3, Vector4)):
            components = [value.x, value.y, value.z]
            if isinstance(value, Vector4):
                components.append(value.w)
            return "|".join(str(c) for c in components)
        elif isinstance(value, ResRef):
            return str(value)
        elif isinstance(value, LocalizedString):
            # For now, just return the stringref
            return str(value.stringref)
        elif isinstance(value, bool):
            return "1" if value else "0"
        return str(value)

    def _generate_struct_diff_section(
        self,
        identifier: str,
        struct_diff: StructDiff,
    ) -> INISection | None:
        """Generate section for struct differences."""
        from kotordiff.diff_objects import DiffType

        if struct_diff.diff_type != DiffType.ADDED:
            return None

        section = INISection(identifier)
        section.add_item("FieldType", "Struct")
        section.add_item("Path", struct_diff.struct_path.replace("/", "\\"))
        section.add_item("Label", Path(struct_diff.struct_path).name)

        # Add field modifications within the struct
        if struct_diff.field_diffs:
            field_index = 0
            for field_diff in struct_diff.field_diffs:
                if field_diff.diff_type == DiffType.ADDED:
                    subsection_name = f"{identifier}_field_{field_index}"
                    section.add_item(f"AddField{field_index}", subsection_name)
                    field_index += 1

        return section


class TLKINIGenerator(INIGenerator):
    """Generator for TLK file modifications in changes.ini format."""

    def generate_sections(self, diff_result: DiffResult[Any]) -> list[INISection]:  # type: ignore[override]
        """Generate TLK modification sections."""
        from kotordiff.diff_objects import TLKDiffResult
        
        diff_result = cast("TLKDiffResult", diff_result)
        sections: list[INISection] = []

        if not diff_result.is_different or not diff_result.entry_diffs:
            return sections

        # Create main TLK section
        main_section = INISection("TLKList")

        # Group entries into append vs replace
        append_entries: list[TLKEntryDiff] = []
        replace_entries: list[TLKEntryDiff] = []

        from kotordiff.diff_objects import DiffType

        for entry_diff in diff_result.entry_diffs:
            if entry_diff.diff_type == DiffType.ADDED:
                append_entries.append(entry_diff)
            elif entry_diff.diff_type == DiffType.MODIFIED:
                replace_entries.append(entry_diff)

        # Create sections for modifications
        token_id = 0

        if append_entries:
            # Use append.tlk
            tlk_section = INISection("append.tlk")
            for entry_diff in append_entries:
                tlk_section.add_item(str(token_id), str(entry_diff.entry_id))
                main_section.add_item(f"StrRef{token_id}", str(entry_diff.entry_id))
                token_id += 1
            sections.append(tlk_section)

        if replace_entries:
            # Use replace.tlk
            tlk_section = INISection("replace.tlk")
            for entry_diff in replace_entries:
                tlk_section.add_item(str(entry_diff.entry_id), str(token_id))
                main_section.add_item(f"StrRef{token_id}", str(entry_diff.entry_id))
                token_id += 1
            sections.append(tlk_section)

        if main_section.items:
            sections.insert(0, main_section)

        return sections


class SSFINIGenerator(INIGenerator):
    """Generator for SSF file modifications in changes.ini format."""

    def generate_sections(self, diff_result: DiffResult[Any]) -> list[INISection]:
        """Generate SSF modification sections."""
        sections: list[INISection] = []

        if not diff_result.is_different:
            return sections

        # Create main SSF section
        filename = Path(diff_result.left_identifier).name
        main_section = INISection("SSFList")
        main_section.add_item("File0", filename)

        # Create file section
        file_section = INISection(filename)

        # Add sound mappings (this would need actual SSF diff data)
        # Placeholder implementation
        sections.append(main_section)
        sections.append(file_section)

        return sections


class ChangesINIWriter:
    """Writes a complete changes.ini file from multiple diff results."""

    def __init__(self):
        self.generators: dict[str, INIGenerator] = {
            "2da": TwoDAINIGenerator(),
            "gff": GFFINIGenerator(),
            "tlk": TLKINIGenerator(),
            "ssf": SSFINIGenerator(),
        }
        self.config = ConfigParser()
        # Preserve case sensitivity
        self.config.optionxform = lambda option: option  # type: ignore[assignment, method-assign]

    def add_diff_result(self, diff_result: DiffResult[Any], resource_type: str):
        """Add a diff result to be included in the INI."""
        generator = self._get_generator(resource_type)
        if not generator:
            return

        sections = generator.generate_sections(diff_result)

        for section in sections:
            if section.name not in self.config:
                self.config.add_section(section.name)

            for key, value in section.items.items():
                self.config.set(section.name, key, str(value))

    def _get_generator(self, resource_type: str) -> INIGenerator | None:
        """Get the appropriate generator for a resource type."""
        resource_type_lower = resource_type.lower()

        # Map various resource types to generators
        if resource_type_lower in ("2da", "twoda"):
            return self.generators["2da"]
        elif resource_type_lower in ("gff", "utc", "uti", "utp", "ute", "utm", "utd", "utw", "dlg", "are", "git", "ifo", "gui"):
            return self.generators["gff"]
        elif resource_type_lower == "tlk":
            return self.generators["tlk"]
        elif resource_type_lower == "ssf":
            return self.generators["ssf"]

        return None

    def write_to_file(self, output_path: Path):
        """Write the changes.ini file to disk."""
        with output_path.open("w", encoding="utf-8") as f:
            self.config.write(f, space_around_delimiters=False)

    def write_to_string(self) -> str:
        """Return the changes.ini content as a string."""
        from io import StringIO

        output = StringIO()
        self.config.write(output, space_around_delimiters=False)
        return output.getvalue()

