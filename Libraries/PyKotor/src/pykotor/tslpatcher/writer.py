"""Expert-level TSLPatcher INI serialization that generates exact, compliant changes.ini files.

This module provides precise TSLPatcher INI format generation based on analysis of:
- TSLPatcher test cases and expected output formats
- TSLPatcher reader implementation for parsing logic
- Exact section ordering and naming conventions
- Proper handling of all modifier types and their parameters
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFStruct
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    Memory2DAModifierGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    RowValue2DAMemory,
    RowValueConstant,
    RowValueHigh,
    RowValueTLKMemory,
    TargetType,
)

if TYPE_CHECKING:
    from pykotor.tslpatcher.memory import TokenUsage
    from pykotor.tslpatcher.mods.gff import ModificationsGFF
    from pykotor.tslpatcher.mods.install import InstallFile  # noqa: F401
    from pykotor.tslpatcher.mods.ncs import ModificationsNCS
    from pykotor.tslpatcher.mods.nss import ModificationsNSS
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.twoda import Modifications2DA
    from utility.system.path import Path

# ---------------------------------------------------------------------------
# INI Escaping Utilities
# ---------------------------------------------------------------------------


def escape_ini_value(value: str) -> str:
    r"""Escape a string value for INI format.

    TSLPatcher INI files require special character escaping:
    - Backslashes: \\
    - Newlines: \\n (note: double backslash for INI parsing)
    - Carriage returns: \\r
    - Tabs: \\t

    Args:
        value: Raw string value to escape

    Returns:
        Escaped string safe for INI format
    """
    if not isinstance(value, str):
        return str(value)

    # Escape backslashes first (must be done before other escapes that add backslashes)
    value = value.replace("\\", "\\\\")

    # Escape newlines and carriage returns (common in dialog text)
    value = value.replace("\r\n", "\\n")  # Windows line endings
    value = value.replace("\n", "\\n")  # Unix line endings
    value = value.replace("\r", "\\r")  # Mac line endings

    # Escape tabs
    value = value.replace("\t", "\\t")

    return value


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ModificationsByType:
    """Typed collection of modifications grouped by format type."""

    tlk: list[ModificationsTLK]  # List[ModificationsTLK]
    install: list[InstallFile]  # List[InstallFile]
    twoda: list[Modifications2DA]  # List[Modifications2DA]
    gff: list[ModificationsGFF]  # List[ModificationsGFF]
    ssf: list[ModificationsSSF]  # List[ModificationsSSF]
    ncs: list[ModificationsNCS]  # List[ModificationsNCS]
    nss: list[ModificationsNSS]  # List[ModificationsNSS]

    @classmethod
    def create_empty(cls) -> ModificationsByType:
        """Create an empty ModificationsByType instance."""
        return cls(twoda=[], gff=[], tlk=[], ssf=[], ncs=[], nss=[], install=[])


@dataclass
class IniGenerationConfig:
    """Configuration for INI generation (changes.ini) for both 2-way and 3-way diffs."""

    generate_ini: bool = True
    ini: Path | None = None


# Logging helpers


class TSLPatcherINISerializer:
    """Serializes PatcherModifications objects to exact TSLPatcher INI format."""

    @staticmethod
    def _format_ini_value(value: str | int | object) -> str:
        """Format an INI file value, wrapping in double quotes if it contains a single quote.

        Args:
            value: The value to format (will be converted to string)

        Returns:
            Formatted value, wrapped in double quotes if it contains a single quote
        """
        value_str = str(value)
        if "'" in value_str:
            return f'"{value_str}"'
        return value_str

    def serialize(
        self,
        modifications_by_type: ModificationsByType,
        *,
        include_header: bool = True,
        include_settings: bool = False,
    ) -> str:
        """Generate complete INI content from modifications.

        Args:
            modifications_by_type: ModificationsByType from __main__.py
            include_header: Whether to include comment header (default: True)
            include_settings: Whether to include [Settings] section (default: False)
        """
        print("TSLPatcherINISerializer.serialize() started")
        print(
            f"Serializing {len(modifications_by_type.twoda)} 2DA, {len(modifications_by_type.gff)} GFF, "
            f"{len(modifications_by_type.tlk)} TLK, {len(modifications_by_type.ssf)} SSF, "
            f"{len(modifications_by_type.ncs)} NCS, "
            f"{len(modifications_by_type.install)} install files"
        )

        lines: list[str] = []

        # Add header comment
        if include_header:
            print("Adding INI header")
            lines.extend(self._generate_header())

        # Add [Settings] section if requested
        if include_settings:
            print("Adding [Settings] section")
            lines.extend(self._generate_settings())

        # Order matters per TSLPatcher convention:
        # [TLKList], [InstallList], [2DAList], [GFFList], [CompileList], [SSFList]
        print("Serializing TLK list...")
        lines.extend(self._serialize_tlk_list(modifications_by_type.tlk))

        print("Serializing Install list...")
        lines.extend(self._serialize_install_list(modifications_by_type.install))

        print("Serializing 2DA list...")
        lines.extend(self._serialize_2da_list(modifications_by_type.twoda))

        print("Serializing GFF list...")
        lines.extend(self._serialize_gff_list(modifications_by_type.gff))

        print("Serializing SSF list...")
        lines.extend(self._serialize_ssf_list(modifications_by_type.ssf))

        print("Serializing HACKList (NCS)...")
        lines.extend(self._serialize_hack_list(modifications_by_type.ncs))

        print(f"Serialization complete: {len(lines)} total lines")
        return "\n".join(lines)

    def _generate_header(self) -> list[str]:
        """Generate INI file header comment."""
        today = datetime.now(tz=timezone.utc).strftime("%m/%d/%Y")
        return [
            "; ============================================================================",
            f";  TSLPatcher Modifications File — Generated by HoloPatcher ({today})",
            "; ============================================================================",
            ";",
            ";  Crafted by: th3w1zard1 (Boden Crouch) with love for the KOTOR community",
            ";",
            ";  This file is part of the PyKotor ecosystem — an exhaustive modding for",
            ";  Knights of the Old Republic development, built to be cross-platform,",
            ";  reproducible, and future-proof.",
            ";",
            ";  Core Ecosystem Components:",
            ";    • PyKotor: Python library for reading/writing KOTOR formats",
            ";    • HoloPatcher: Cross-platform TSLPatcher alternative",
            ";    • HolocronToolset: Complete modding suite for KotOR I & II",
            ";    • KotorDiff: Advanced diff engine for patch generation",
            ";        https://github.com/th3w1zard1/PyKotor",
            ";    • KOTORModSync: Multi-mod installer with conflict resolution",
            ";        https://github.com/th3w1zard1/KOTORModSync",
            ";    • HoloLSP: The first ever Language Server Protocol for KotOR",
            ";        https://github.com/th3w1zard1/HoloLSP",
            ";    • HoloPatcher.NET: .NET implementation of HoloPatcher",
            ";        https://github.com/th3w1zard1/HoloPatcher.NET",
            ";",
            ";  https://www.bolabaden.org  - Self-Hosted Infrastructure and Initiatives",
            ";",
            ";  Developer Initiatives — bolabaden Organization:",
            ";    • bolabaden-site: Main website + frontend",
            ";        https://github.com/bolabaden/bolabaden-site",
            ";    • bolabaden-infra: Kubernetes backbone for bolabaden.org",
            ";        https://github.com/bolabaden/bolabaden-infra",
            ";    • ai-researchwizard: AI-powered research assistant",
            ";        https://github.com/bolabaden/ai-researchwizard",
            "; ----------------------------------------------------------------------------",
            ";",
            ";  FORMATTING NOTES:",
            ";    • This file is TSLPatcher-compliant and machine-generated.",
            ";    • You may add blank lines between sections (for readability).",
            ";    • You may add comment lines starting with semicolon.",
            ";    • Do NOT add blank lines or comments inside a section (between keys).",
            "; ============================================================================",
            "",
        ]

    def _generate_settings(self) -> list[str]:
        """Generate default [Settings] section."""
        return [
            "[Settings]",
            "LogLevel=3",
            "",
        ]

    def _serialize_2da_list(
        self,
        modifications: list[Modifications2DA],
    ) -> list[str]:
        """Serialize [2DAList] section."""
        if not modifications:
            print("No 2DA modifications to serialize")
            return []

        print(f"Serializing {len(modifications)} 2DA files")

        lines: list[str] = []
        lines.append("[2DAList]")

        for idx, mod_2da in enumerate(modifications):
            print(f"Adding 2DA table {idx}: {mod_2da.sourcefile} ({len(mod_2da.modifiers)} modifiers)")
            lines.append(f"Table{idx}={self._format_ini_value(mod_2da.sourcefile)}")
        lines.append("")

        # Generate each 2DA file's sections
        for mod_2da in modifications:
            lines.extend(self._serialize_2da_file(mod_2da))

        return lines

    def _serialize_2da_file(
        self,
        mod_2da: Modifications2DA,
    ) -> list[str]:
        """Serialize a single 2DA file's modifications."""
        lines: list[str] = []
        lines.append(f"[{mod_2da.sourcefile}]")

        # List all modifiers
        modifier_idx = 0
        for modifier in mod_2da.modifiers:
            if isinstance(modifier, ChangeRow2DA):
                section_name = modifier.identifier or f"{mod_2da.sourcefile}_changerow_{modifier_idx}"
                lines.append(f"ChangeRow{modifier_idx}={self._format_ini_value(section_name)}")
                modifier_idx += 1
            elif isinstance(modifier, AddRow2DA):
                section_name = modifier.identifier or f"{mod_2da.sourcefile}_addrow_{modifier_idx}"
                lines.append(f"AddRow{modifier_idx}={self._format_ini_value(section_name)}")
                modifier_idx += 1
            elif isinstance(modifier, AddColumn2DA):
                section_name = modifier.identifier or f"{mod_2da.sourcefile}_addcol_{modifier_idx}"
                lines.append(f"AddColumn{modifier_idx}={self._format_ini_value(section_name)}")
                modifier_idx += 1
        lines.append("")

        # Generate detailed sections for each modifier
        for modifier in mod_2da.modifiers:
            if isinstance(modifier, (ChangeRow2DA, AddRow2DA, AddColumn2DA)):
                lines.extend(self._serialize_2da_modifier(modifier))

        return lines

    def _serialize_2da_modifier(  # noqa: C901, PLR0912
        self,
        modifier: ChangeRow2DA | AddRow2DA | AddColumn2DA,
    ) -> list[str]:
        """Serialize a single 2DA modifier section with exact TSLPatcher format."""
        lines: list[str] = []
        section_name = modifier.identifier

        if isinstance(modifier, ChangeRow2DA):
            lines.append(f"[{section_name}]")

            # Target specification (exactly as TSLPatcher expects)
            if modifier.target.target_type == TargetType.ROW_INDEX:
                lines.append(f"RowIndex={self._format_ini_value(str(modifier.target.value))}")
            elif modifier.target.target_type == TargetType.ROW_LABEL:
                lines.append(f"RowLabel={self._format_ini_value(modifier.target.value)}")
            elif modifier.target.target_type == TargetType.LABEL_COLUMN:
                lines.append(f"LabelIndex={self._format_ini_value(str(modifier.target.value))}")

            # Cell modifications (preserve exact column names and values)
            for col, row_value in modifier.cells.items():
                cell_val = self._serialize_row_value(row_value)
                lines.append(f"{col}={self._format_ini_value(cell_val)}")

            # Store 2DA memory assignments (if any)
            if hasattr(modifier, "store_2da") and modifier.store_2da:
                for token_id, row_value in modifier.store_2da.items():
                    store_val = self._serialize_row_value(row_value)
                    lines.append(f"2DAMEMORY{token_id}={self._format_ini_value(store_val)}")

            # Store TLK memory assignments (if any)
            if hasattr(modifier, "store_tlk") and modifier.store_tlk:
                for token_id, row_value in modifier.store_tlk.items():
                    store_val = self._serialize_row_value(row_value)
                    lines.append(f"StrRef{token_id}={self._format_ini_value(store_val)}")

            lines.append("")

        elif isinstance(modifier, AddRow2DA):
            lines.append(f"[{section_name}]")

            # Exclusive column (prevents duplicate values)
            if modifier.exclusive_column:
                lines.append(f"ExclusiveColumn={self._format_ini_value(modifier.exclusive_column)}")

            # Row label (if specified)
            if modifier.row_label:
                lines.append(f"RowLabel={self._format_ini_value(modifier.row_label)}")

            # Cell values
            for col, row_value in modifier.cells.items():
                cell_val = self._serialize_row_value(row_value)
                lines.append(f"{col}={self._format_ini_value(cell_val)}")

            # Store 2DA memory assignments (if any)
            if hasattr(modifier, "store_2da") and modifier.store_2da:
                for token_id, row_value in modifier.store_2da.items():
                    store_val = self._serialize_row_value(row_value)
                    lines.append(f"2DAMEMORY{token_id}={self._format_ini_value(store_val)}")

            # Store TLK memory assignments (if any)
            if hasattr(modifier, "store_tlk") and modifier.store_tlk:
                for token_id, row_value in modifier.store_tlk.items():
                    store_val = self._serialize_row_value(row_value)
                    lines.append(f"StrRef{token_id}={self._format_ini_value(store_val)}")

            lines.append("")

        elif isinstance(modifier, AddColumn2DA):
            lines.append(f"[{section_name}]")
            lines.append(f"ColumnLabel={self._format_ini_value(modifier.header)}")
            default_val = modifier.default if modifier.default else "****"
            lines.append(f"DefaultValue={self._format_ini_value(default_val)}")

            # Index-based inserts (I0=value, I1=value, etc.)
            for row_idx, row_value in modifier.index_insert.items():
                idx_val = self._serialize_row_value(row_value)
                lines.append(f"I{row_idx}={self._format_ini_value(idx_val)}")

            # Label-based inserts (Llabel=value)
            for row_label, row_value in modifier.label_insert.items():
                label_val = self._serialize_row_value(row_value)
                lines.append(f"L{row_label}={self._format_ini_value(label_val)}")

            # Store 2DA memory assignments (if any)
            if hasattr(modifier, "store_2da") and modifier.store_2da:
                for token_id, store_val in modifier.store_2da.items():
                    lines.append(f"2DAMEMORY{token_id}={self._format_ini_value(store_val)}")

            lines.append("")

        return lines

    def _serialize_token_usage(self, token_usage: TokenUsage) -> str:
        """Serialize a TokenUsage to its TSLPatcher string representation.

        CRITICAL: This writes the TOKEN REFERENCE (e.g., 'StrRef5'), NOT the resolved value.

        Args:
            token_usage: TokenUsage object (TokenUsageTLK, TokenUsage2DA, or NoTokenUsage)

        Returns:
            Token reference string for INI
        """
        if isinstance(token_usage, TokenUsageTLK):
            return f"StrRef{token_usage.token_id}"
        if isinstance(token_usage, TokenUsage2DA):
            return f"2DAMEMORY{token_usage.token_id}"
        if isinstance(token_usage, NoTokenUsage):
            return token_usage.stored
        # Fallback - shouldn't happen
        return str(token_usage)

    def _serialize_row_value(self, row_value: Any) -> str:
        """Serialize a RowValue to its TSLPatcher string representation."""
        # Handle different RowValue types exactly as TSLPatcher expects
        if isinstance(row_value, RowValue2DAMemory):
            return f"2DAMEMORY{row_value.token_id}"
        if isinstance(row_value, RowValueTLKMemory):
            return f"StrRef{row_value.token_id}"
        if isinstance(row_value, RowValueConstant):
            return str(row_value.string)
        if isinstance(row_value, RowValueHigh):
            return f"High({row_value.column})" if row_value.column else "High()"
        # Fallback for other RowValue types (RowValueRowIndex, RowValueRowLabel, RowValueRowCell)
        if hasattr(row_value, "value") and callable(row_value.value):
            return str(row_value.value(None, None, None))  # type: ignore[arg-type]
        return str(row_value)

    def _serialize_gff_list(
        self,
        modifications: list[ModificationsGFF],
    ) -> list[str]:
        """Serialize [GFFList] section with exact TSLPatcher format."""
        if not modifications:
            print("No GFF modifications to serialize")
            return []

        print(f"Serializing {len(modifications)} GFF files")

        lines: list[str] = []
        lines.append("[GFFList]")

        for idx, mod_gff in enumerate(modifications):
            # Use Replace# or File# based on replace_file flag
            prefix = "Replace" if getattr(mod_gff, "replace_file", False) else "File"
            print(f"Adding GFF file {idx}: {prefix}{idx}={mod_gff.sourcefile} ({len(mod_gff.modifiers)} modifiers)")
            lines.append(f"{prefix}{idx}={self._format_ini_value(mod_gff.sourcefile)}")
        lines.append("")

        # Generate each GFF file's sections
        for mod_gff in modifications:
            lines.extend(self._serialize_gff_file(mod_gff))

        return lines

    def _serialize_gff_file(
        self,
        mod_gff: ModificationsGFF,
    ) -> list[str]:
        """Serialize a single GFF file's modifications with exact TSLPatcher format."""
        lines: list[str] = []
        lines.append(f"[{mod_gff.sourcefile}]")

        # Add TSLPatcher exclamation-point variables if present
        if hasattr(mod_gff, "replace_file"):
            lines.append(f"!ReplaceFile={'1' if mod_gff.replace_file else '0'}")
        if hasattr(mod_gff, "destination") and mod_gff.destination != "Override":
            lines.append(f"!Destination={self._format_ini_value(mod_gff.destination)}")
        if hasattr(mod_gff, "saveas") and mod_gff.saveas != mod_gff.sourcefile:
            lines.append(f"!Filename={self._format_ini_value(mod_gff.saveas)}")

        # Collect AddField indices first
        addfield_modifiers = []

        # Process modifiers in order
        for gff_modifier in mod_gff.modifiers:
            if isinstance(gff_modifier, ModifyFieldGFF):
                # Direct field modification: Path=Value (use backslashes per TSLPatcher)
                path_str = str(gff_modifier.path).replace("/", "\\")
                value_str = self._serialize_field_value(gff_modifier.value)
                lines.append(f"{path_str}={self._format_ini_value(value_str)}")

            elif isinstance(gff_modifier, Memory2DAModifierGFF):
                # Memory assignment: 2DAMEMORY#=!FieldPath or 2DAMEMORY#=2DAMEMORY#
                if gff_modifier.src_token_id is None:
                    # 2DAMEMORY#=!FieldPath
                    path_str = str(gff_modifier.path).replace("/", "\\")
                    lines.append(f"2DAMEMORY{gff_modifier.dest_token_id}=!FieldPath")
                    # Note: The path is stored but not written in the main section
                    # It's inferred from the field being modified
                else:
                    # 2DAMEMORY#=2DAMEMORY#
                    lines.append(f"2DAMEMORY{gff_modifier.dest_token_id}=2DAMEMORY{gff_modifier.src_token_id}")

            elif isinstance(gff_modifier, (AddFieldGFF, AddStructToListGFF)):
                addfield_modifiers.append(gff_modifier)

        # Add AddField# references
        for idx, gff_modifier in enumerate(addfield_modifiers):
            section_name = gff_modifier.identifier or f"addfield_{idx}"
            lines.append(f"AddField{idx}={self._format_ini_value(section_name)}")

        lines.append("")

        # Generate AddField subsections after the main file section
        for idx, gff_modifier in enumerate(addfield_modifiers):
            section_name = gff_modifier.identifier or f"addfield_{idx}"
            lines.extend(self._serialize_addfield_section(gff_modifier, section_name))

        return lines

    def _serialize_addfield_section(  # noqa: C901, PLR0912
        self,
        gff_modifier: AddFieldGFF | AddStructToListGFF,
        section_name: str,
    ) -> list[str]:
        """Serialize an AddField or AddStructToListGFF subsection with exact TSLPatcher format."""
        lines: list[str] = []
        lines.append(f"[{section_name}]")

        # Determine if this is AddStructToListGFF or AddFieldGFF
        is_add_struct_to_list = isinstance(gff_modifier, AddStructToListGFF)

        # FieldType - AddStructToListGFF is always Struct type
        if is_add_struct_to_list:
            field_type_name = "Struct"
        elif isinstance(gff_modifier, AddFieldGFF):
            field_type_name = self._get_gff_field_type_name(gff_modifier.field_type)
        else:
            field_type_name = "Struct"  # Default fallback
        lines.append(f"FieldType={self._format_ini_value(field_type_name)}")

        # Label - AddStructToListGFF doesn't have label, use empty string
        label = getattr(gff_modifier, "label", "")
        lines.append(f"Label={self._format_ini_value(label)}")

        # Path (use backslashes)
        path_str = str(gff_modifier.path).replace("/", "\\")
        lines.append(f"Path={self._format_ini_value(path_str)}")

        # Add field value based on type
        if is_add_struct_to_list:
            # AddStructToListGFF always has TypeId
            if isinstance(gff_modifier.value, FieldValueConstant) and isinstance(gff_modifier.value.stored, GFFStruct):
                lines.append(f"TypeId={self._format_ini_value(str(gff_modifier.value.stored.struct_id))}")

            # Handle index_to_token for AddStructToListGFF
            if hasattr(gff_modifier, "index_to_token") and gff_modifier.index_to_token is not None:
                lines.append(f"2DAMEMORY{gff_modifier.index_to_token}=listindex")
        elif hasattr(gff_modifier, "field_type"):
            if gff_modifier.field_type == GFFFieldType.Struct:
                # For Struct, we need TypeId instead of Value
                if isinstance(gff_modifier.value, FieldValueConstant) and isinstance(gff_modifier.value.stored, GFFStruct):
                    lines.append(f"TypeId={self._format_ini_value(str(gff_modifier.value.stored.struct_id))}")
            elif gff_modifier.field_type in (GFFFieldType.List,):
                # Lists don't need a Value
                pass
            elif gff_modifier.field_type == GFFFieldType.LocalizedString:
                # LocalizedString uses StrRef and lang# keys
                self._serialize_localized_string_value(gff_modifier.value, lines)
            else:
                # Regular value
                value_str = self._serialize_field_value(gff_modifier.value)
                if value_str:  # Only add Value= if there's an actual value
                    lines.append(f"Value={self._format_ini_value(value_str)}")

        # Process nested modifiers (if any) - includes Memory2DAModifierGFF
        if hasattr(gff_modifier, "modifiers") and gff_modifier.modifiers:
            # Count AddField modifiers and Memory2DAModifierGFF separately
            addfield_count = 0
            for nested_mod in gff_modifier.modifiers:
                if isinstance(nested_mod, Memory2DAModifierGFF):
                    # Memory assignment in nested context
                    if nested_mod.src_token_id is None:
                        # 2DAMEMORY#=!FieldPath
                        lines.append(f"2DAMEMORY{nested_mod.dest_token_id}=!FieldPath")
                    else:
                        # 2DAMEMORY#=2DAMEMORY#
                        lines.append(f"2DAMEMORY{nested_mod.dest_token_id}=2DAMEMORY{nested_mod.src_token_id}")
                elif isinstance(nested_mod, (AddFieldGFF, AddStructToListGFF)):
                    nested_section = nested_mod.identifier or f"{section_name}_nested_{addfield_count}"
                    lines.append(f"AddField{addfield_count}={self._format_ini_value(nested_section)}")
                    addfield_count += 1

        lines.append("")

        # Recursively generate nested AddField/AddStructToListGFF sections
        if hasattr(gff_modifier, "modifiers") and gff_modifier.modifiers:
            for nested_idx, nested_mod in enumerate(gff_modifier.modifiers):
                if isinstance(nested_mod, (AddFieldGFF, AddStructToListGFF)):
                    nested_section = nested_mod.identifier or f"{section_name}_nested_{nested_idx}"
                    lines.extend(self._serialize_addfield_section(nested_mod, nested_section))

        return lines

    def _serialize_localized_string_value(
        self,
        field_value: Any,
        lines: list[str],
    ) -> None:
        """Serialize LocalizedString field value to TSLPatcher format."""
        # Extract the actual LocalizedString from FieldValue wrapper
        loc_string: LocalizedString | None = None
        if hasattr(field_value, "stored"):
            loc_string = field_value.stored
        elif isinstance(field_value, LocalizedString):
            loc_string = field_value

        if loc_string and isinstance(loc_string, LocalizedString):
            # Add StrRef - handle both LocalizedStringDelta with token and regular LocalizedString
            if isinstance(loc_string, LocalizedStringDelta) and loc_string.stringref is not None:
                # LocalizedStringDelta can have a FieldValue token reference
                strref_value = self._serialize_field_value(loc_string.stringref)
                lines.append(f"StrRef={self._format_ini_value(strref_value)}")
            elif hasattr(loc_string, "stringref"):
                # Regular LocalizedString with numeric stringref
                lines.append(f"StrRef={self._format_ini_value(str(loc_string.stringref))}")

            # Add lang# entries (escape text for INI format)
            for lang, gender, text in loc_string:
                substring_id = LocalizedString.substring_id(lang, gender)
                escaped_text = escape_ini_value(text)
                lines.append(f"lang{substring_id}={self._format_ini_value(escaped_text)}")

    def _get_gff_field_type_name(self, field_type: Any) -> str:
        """Convert GFFFieldType enum to TSLPatcher field type name."""
        # Mapping based on TSLPatcher reader implementation
        type_mapping = {
            GFFFieldType.UInt8: "Byte",
            GFFFieldType.Int8: "Char",
            GFFFieldType.UInt16: "Word",
            GFFFieldType.Int16: "Short",
            GFFFieldType.UInt32: "DWORD",
            GFFFieldType.Int32: "Int",
            GFFFieldType.Int64: "Int64",
            GFFFieldType.Single: "Float",
            GFFFieldType.Double: "Double",
            GFFFieldType.String: "ExoString",
            GFFFieldType.ResRef: "ResRef",
            GFFFieldType.LocalizedString: "ExoLocString",
            GFFFieldType.Vector3: "Position",
            GFFFieldType.Vector4: "Orientation",
            GFFFieldType.Struct: "Struct",
            GFFFieldType.List: "List",
        }
        return type_mapping.get(field_type, str(field_type.value))

    def _serialize_field_value(self, field_value: Any) -> str:
        """Serialize a FieldValue to its TSLPatcher string representation."""
        # CRITICAL: Write token REFERENCES, not resolved values
        if isinstance(field_value, FieldValue2DAMemory):
            # 2DAMEMORY tokens reference 2DA row values stored in memory
            return f"2DAMEMORY{field_value.token_id}"
        if isinstance(field_value, FieldValueTLKMemory):
            return f"StrRef{field_value.token_id}"
        if isinstance(field_value, FieldValueConstant):
            return self._format_gff_value(field_value.stored)
        # Fallback for other FieldValue types
        if hasattr(field_value, "value") and callable(field_value.value):
            return self._format_gff_value(field_value.value(None, None))  # type: ignore[arg-type]
        return self._format_gff_value(field_value)

    def _format_gff_value(  # noqa: PLR0911
        self,
        value: Any,
    ) -> str:
        """Format a GFF field value for INI output with exact TSLPatcher format."""
        if isinstance(value, (Vector3, Vector4)):
            # TSLPatcher expects comma-separated values with specific precision
            if isinstance(value, Vector4):
                return f"{value.x:.6f},{value.y:.6f},{value.z:.6f},{value.w:.6f}"
            return f"{value.x:.6f},{value.y:.6f},{value.z:.6f}"
        if isinstance(value, LocalizedString):
            return str(value.stringref)
        if isinstance(value, ResRef):
            return str(value)
        if isinstance(value, str):
            # Escape string values for INI format
            return escape_ini_value(value)
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            # Format numbers exactly as TSLPatcher expects
            if isinstance(value, float):
                return f"{value:.6f}".rstrip("0").rstrip(".")
            return str(value)
        if value is None:
            return ""
        return str(value)

    def _serialize_tlk_list(
        self,
        modifications: list[ModificationsTLK],
    ) -> list[str]:
        """Serialize [TLKList] section."""
        if not modifications:
            print("No TLK modifications to serialize")
            return []

        print(f"Serializing {len(modifications)} TLK modification sets")

        lines: list[str] = []
        mod_tlk: ModificationsTLK = modifications[0]  # Should only be one TLK modification
        assert isinstance(mod_tlk, ModificationsTLK), "mod_tlk should be a ModificationsTLK"

        print(f"TLK has {len(mod_tlk.modifiers)} modifiers")

        lines.append("[TLKList]")

        # Determine file types needed
        has_replacements: bool = any(m.is_replacement for m in mod_tlk.modifiers)
        has_appends: bool = any(not m.is_replacement for m in mod_tlk.modifiers)

        print(f"TLK has {sum(1 for m in mod_tlk.modifiers if m.is_replacement)} replacements, {sum(1 for m in mod_tlk.modifiers if not m.is_replacement)} appends")

        # Modern TSLPatcher syntax for appends: Use StrRef token mappings ONLY
        # For replacements: Still use ReplaceFile# syntax
        if has_replacements:
            lines.append("ReplaceFile0=replace.tlk")
            print("Added ReplaceFile0=replace.tlk")

        # StrRef token mappings for appends: StrRef{original_strref}={token_id}
        # These tell TSLPatcher which token each original StrRef maps to
        if has_appends:
            append_modifiers = [m for m in mod_tlk.modifiers if not m.is_replacement]
            strref_count = len(append_modifiers)
            print(f"Adding {strref_count} StrRef token mappings for appends")

            # Add each StrRef mapping with helpful comment
            for tlk_modifier in append_modifiers:
                # Truncate text for comment (max 60 chars)
                text_preview = (tlk_modifier.text or "")[:60]
                # Escape special characters for INI comment
                text_preview = text_preview.replace("\n", "\\n").replace("\r", "\\r")

                # Build comment with text and sound (if present)
                comment_parts: list[str] = []
                if text_preview:
                    comment_parts.append(f'"{text_preview}"')
                if tlk_modifier.sound:
                    comment_parts.append(f"sound={tlk_modifier.sound}")

                comment = " | ".join(comment_parts) if comment_parts else "(empty entry)"

                # Add the line with comment
                token_id_str = str(tlk_modifier.token_id)
                lines.append(f"StrRef{tlk_modifier.mod_index}={self._format_ini_value(token_id_str)}  ; {comment}")

        lines.append("")

        # Generate replace.tlk section (only for replacements)
        if has_replacements:
            replace_count = sum(1 for m in mod_tlk.modifiers if m.is_replacement)
            print(f"Generating [replace.tlk] section with {replace_count} entries")
            lines.append("[replace.tlk]")
            lines.extend([f"{tlk_modifier.token_id}={tlk_modifier.mod_index}" for tlk_modifier in mod_tlk.modifiers if tlk_modifier.is_replacement])
            lines.append("")

        return lines

    def _serialize_ssf_list(
        self,
        modifications: list[ModificationsSSF],
    ) -> list[str]:
        """Serialize [SSFList] section."""
        if not modifications:
            print("No SSF modifications to serialize")
            return []

        print(f"Serializing {len(modifications)} SSF files")

        lines: list[str] = []
        lines.append("[SSFList]")

        for idx, mod_ssf in enumerate(modifications):
            prefix = "Replace" if mod_ssf.replace_file else "File"
            print(f"Adding SSF file {idx}: {prefix}{idx}={mod_ssf.sourcefile} ({len(mod_ssf.modifiers)} modifiers)")
            lines.append(f"{prefix}{idx}={self._format_ini_value(mod_ssf.sourcefile)}")
        lines.append("")

        # Generate each SSF file's sections
        for mod_ssf in modifications:
            lines.extend(self._serialize_ssf_file(mod_ssf))

        return lines

    def _serialize_ssf_file(
        self,
        mod_ssf: ModificationsSSF,
    ) -> list[str]:
        """Serialize a single SSF file's modifications."""
        lines: list[str] = []
        lines.append(f"[{mod_ssf.sourcefile}]")

        # TSLPatcher SSF sound name mappings
        SOUND_NAMES = {
            SSFSound.BATTLE_CRY_1: "Battlecry 1",
            SSFSound.BATTLE_CRY_2: "Battlecry 2",
            SSFSound.BATTLE_CRY_3: "Battlecry 3",
            SSFSound.BATTLE_CRY_4: "Battlecry 4",
            SSFSound.BATTLE_CRY_5: "Battlecry 5",
            SSFSound.BATTLE_CRY_6: "Battlecry 6",
            SSFSound.SELECT_1: "Selected 1",
            SSFSound.SELECT_2: "Selected 2",
            SSFSound.SELECT_3: "Selected 3",
            SSFSound.ATTACK_GRUNT_1: "Attack 1",
            SSFSound.ATTACK_GRUNT_2: "Attack 2",
            SSFSound.ATTACK_GRUNT_3: "Attack 3",
            SSFSound.PAIN_GRUNT_1: "Pain 1",
            SSFSound.PAIN_GRUNT_2: "Pain 2",
            SSFSound.LOW_HEALTH: "Low health",
            SSFSound.DEAD: "Death",
            SSFSound.CRITICAL_HIT: "Critical hit",
            SSFSound.TARGET_IMMUNE: "Target immune",
            SSFSound.LAY_MINE: "Place mine",
            SSFSound.DISARM_MINE: "Disarm mine",
            SSFSound.BEGIN_STEALTH: "Stealth on",
            SSFSound.BEGIN_SEARCH: "Search",
            SSFSound.BEGIN_UNLOCK: "Pick lock start",
            SSFSound.UNLOCK_FAILED: "Pick lock fail",
            SSFSound.UNLOCK_SUCCESS: "Pick lock done",
            SSFSound.SEPARATED_FROM_PARTY: "Leave party",
            SSFSound.REJOINED_PARTY: "Rejoin party",
            SSFSound.POISONED: "Poisoned",
        }

        for ssf_modifier in mod_ssf.modifiers:
            sound_name = SOUND_NAMES.get(ssf_modifier.sound, f"Sound{ssf_modifier.sound.value}")
            # CRITICAL: Write token REFERENCE, not resolved value
            value = self._serialize_token_usage(ssf_modifier.stringref)
            lines.append(f"{sound_name}={self._format_ini_value(str(value))}")

        lines.append("")
        return lines

    def _serialize_hack_list(
        self,
        modifications: list,  # list[ModificationsNCS]
    ) -> list[str]:
        """Serialize [HACKList] section for NCS binary patches."""
        if not modifications:
            print("No NCS modifications to serialize")
            return []

        print(f"Serializing {len(modifications)} NCS files for HACKList")

        lines: list[str] = []
        lines.append("[HACKList]")

        for idx, mod_ncs in enumerate(modifications):
            prefix = "Replace" if mod_ncs.replace_file else "File"
            print(f"Adding NCS file {idx}: {prefix}{idx}={mod_ncs.sourcefile} ({len(mod_ncs.modifiers)} 'hacks')")
            lines.append(f"{prefix}{idx}={self._format_ini_value(mod_ncs.sourcefile)}")
        lines.append("")

        # Generate each NCS file's sections
        for mod_ncs in modifications:
            lines.extend(self._serialize_ncs_file(mod_ncs))

        return lines

    def _serialize_ncs_file(
        self,
        mod_ncs: ModificationsNCS,
    ) -> list[str]:
        """Serialize a single NCS file's hack modifications."""
        lines: list[str] = []
        lines.append(f"[{mod_ncs.sourcefile}]")

        # Serialize each hack entry
        from pykotor.tslpatcher.mods.ncs import NCSTokenType  # noqa: PLC0415

        for modifier in mod_ncs.modifiers:
            offset = modifier.offset
            token_id_or_value = modifier.token_id_or_value
            token_type = modifier.token_type

            if token_type in (NCSTokenType.STRREF, NCSTokenType.STRREF32):
                # StrRef token reference
                lines.append(f"Hack{offset:08X}={self._format_ini_value(f'StrRef{token_id_or_value}')}")
            elif token_type in (NCSTokenType.MEMORY_2DA, NCSTokenType.MEMORY_2DA32):
                # 2DAMEMORY token reference
                lines.append(f"Hack{offset:08X}={self._format_ini_value(f'2DAMEMORY{token_id_or_value}')}")
            else:
                # Direct value (uint8, uint16, uint32)
                lines.append(f"Hack{offset:08X}={self._format_ini_value(str(token_id_or_value))}")

        lines.append("")
        return lines

    def _serialize_install_list(
        self,
        install_files: list[InstallFile],
    ) -> list[str]:
        """Serialize [InstallList] section with exact TSLPatcher format.

        Args:
            install_files: List of InstallFile objects to serialize
        """
        if not install_files:
            print("No install files to serialize")
            return []

        # Group InstallFile objects by destination folder
        folders_dict: dict[str, list[InstallFile]] = {}
        for install_file in install_files:
            dest = install_file.destination if install_file.destination != "." else "Override"
            if dest not in folders_dict:
                folders_dict[dest] = []
            folders_dict[dest].append(install_file)

        total_files = len(install_files)
        print(f"Serializing InstallList with {len(folders_dict)} folders, {total_files} total files")

        lines: list[str] = []
        lines.append("[InstallList]")

        # List all folder entries (using install_folder# format per TSLPatcher convention)
        sorted_destinations = sorted(folders_dict.keys())
        for i, dest in enumerate(sorted_destinations):
            files_in_folder = folders_dict[dest]
            print(f"Install folder {i}: {dest} ({len(files_in_folder)} files)")
            lines.append(f"install_folder{i}={self._format_ini_value(dest)}")
        lines.append("")

        # Generate folder sections with file lists
        for i, dest in enumerate(sorted_destinations):
            files_in_folder = folders_dict[dest]
            section_name = f"install_folder{i}"

            print(f"Generating section [{section_name}] for {dest} with {len(files_in_folder)} files")

            # Add comment for readability
            lines.append(f"; {dest} :")
            lines.append(f"[{section_name}]")

            # Sort files by filename for consistent output
            def get_filename(install_file: InstallFile) -> str:
                return install_file.saveas or install_file.sourcefile
            sorted_files = sorted(files_in_folder, key=get_filename)

            # List files - use Replace# if replace_file is True, otherwise File#
            for j, install_file in enumerate(sorted_files):
                filename = get_filename(install_file)
                if install_file.replace_file:
                    file_line = f"Replace{j}={self._format_ini_value(filename)}"
                    print(f"  Replace{j}={filename}")
                else:
                    file_line = f"File{j}={self._format_ini_value(filename)}"
                    print(f"  File{j}={filename}")
                lines.append(file_line)

            if len(files_in_folder) > 5:
                print(f"  ... and {len(files_in_folder) - 5} more files")

            lines.append("")

        return lines
