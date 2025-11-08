"""Expert-level TSLPatcher INI serialization that generates exact, compliant changes.ini files.

This module provides precise TSLPatcher INI format generation based on analysis of:
- TSLPatcher test cases and expected output formats
- TSLPatcher reader implementation for parsing logic
- Exact section ordering and naming conventions
- Proper handling of all modifier types and their parameters
"""

from __future__ import annotations

import os
import traceback

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable, Iterable

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import FileResource
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import detect_gff, read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.lip.lip_auto import read_lip, write_lip
from pykotor.resource.formats.ssf.ssf_auto import read_ssf, write_ssf
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.resource.formats.tlk.tlk_auto import read_tlk, write_tlk
from pykotor.resource.formats.tlk.tlk_data import TLK  # noqa: PLC0415
from pykotor.resource.formats.twoda.twoda_auto import read_2da, write_2da
from pykotor.resource.type import ResourceType
from pykotor.tools.reference_cache import GFF_FIELD_TO_2DA_MAPPING, StrRefReferenceCache
from pykotor.tslpatcher.diff.resolution import TLKModificationWithSource  # noqa: PLC0415
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.gff import (  # noqa: PLC0415
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    Memory2DAModifierGFF,
    ModificationsGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.ncs import ModificationsNCS  # ModifyNCS, NCSTokenType temporarily unused - NCS disabled  # noqa: PLC0415
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK  # noqa: PLC0415
from pykotor.tslpatcher.mods.twoda import (  # noqa: PLC0415
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    Modifications2DA,
    Modify2DA,  # noqa: F401
    RowValue2DAMemory,
    RowValueConstant,
    RowValueHigh,
    RowValueRowCell,
    RowValueRowIndex,
    RowValueRowLabel,
    RowValueTLKMemory,
    Target,
    TargetType,
)
from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource
    from pykotor.tools.reference_cache import StrRefReferenceCache, StrRefSearchResult, TwoDAMemoryReferenceCache
    from pykotor.tslpatcher.memory import TokenUsage
    from pykotor.tslpatcher.mods.install import InstallFile
    from pykotor.tslpatcher.mods.nss import ModificationsNSS
    from pykotor.tslpatcher.mods.template import PatcherModifications
    from pykotor.tslpatcher.mods.tlk import ModifyTLK
    from pykotor.tslpatcher.mods.twoda import RowValue

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
        value_str: str = str(value)
        if "'" in value_str:
            return f'"{value_str}"'
        return value_str

    def serialize(
        self,
        modifications_by_type: ModificationsByType,
        *,
        include_header: bool = True,
        include_settings: bool = False,
        verbose: bool = True,
    ) -> str:
        """Generate complete INI content from modifications.

        Args:
            modifications_by_type: ModificationsByType from __main__.py
            include_header: Whether to include comment header (default: True)
            include_settings: Whether to include [Settings] section (default: False)
            verbose: Whether to print detailed per-file logging (default: True)
        """
        if verbose:
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
            if verbose:
                print("Adding INI header")
            lines.extend(self._generate_header())

        # Add [Settings] section if requested
        if include_settings:
            if verbose:
                print("Adding [Settings] section")
            lines.extend(self._generate_settings())

        # Order matters per TSLPatcher convention:
        # [TLKList], [InstallList], [2DAList], [GFFList], [CompileList], [SSFList]
        if verbose:
            print("Serializing TLK list...")
        lines.extend(self._serialize_tlk_list(modifications_by_type.tlk, verbose=verbose))

        if verbose:
            print("Serializing Install list...")
        lines.extend(self._serialize_install_list(modifications_by_type.install, verbose=verbose))

        if verbose:
            print("Serializing 2DA list...")
        lines.extend(self._serialize_2da_list(modifications_by_type.twoda, verbose=verbose))

        if verbose:
            print("Serializing GFF list...")
        lines.extend(self._serialize_gff_list(modifications_by_type.gff, verbose=verbose))

        if verbose:
            print("Serializing SSF list...")
        lines.extend(self._serialize_ssf_list(modifications_by_type.ssf, verbose=verbose))

        if verbose:
            print("Serializing HACKList (NCS)...")
        lines.extend(self._serialize_hack_list(modifications_by_type.ncs, verbose=verbose))

        if verbose:
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
        *,
        verbose: bool = True,
    ) -> list[str]:
        """Serialize [2DAList] section."""
        if not modifications:
            if verbose:
                print("No 2DA modifications to serialize")
            return []

        if verbose:
            print(f"Serializing {len(modifications)} 2DA files")

        lines: list[str] = []
        lines.append("[2DAList]")

        for idx, mod_2da in enumerate(modifications):
            if verbose:
                print(f"Adding 2DA table {idx}: {mod_2da.sourcefile} ({len(mod_2da.modifiers)} modifiers)")
            # Section name references must match section headers exactly (no quotes) - section headers are written as [{sourcefile}]
            lines.append(f"Table{idx}={mod_2da.sourcefile}")
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
        modifier_idx: int = 0
        for modifier in mod_2da.modifiers:
            if isinstance(modifier, ChangeRow2DA):
                section_name = modifier.identifier or f"{mod_2da.sourcefile}_changerow_{modifier_idx}"
                # Section name references must match section headers exactly (no quotes)
                lines.append(f"ChangeRow{modifier_idx}={section_name}")
                modifier_idx += 1
            elif isinstance(modifier, AddRow2DA):
                section_name = modifier.identifier or f"{mod_2da.sourcefile}_addrow_{modifier_idx}"
                # Section name references must match section headers exactly (no quotes)
                lines.append(f"AddRow{modifier_idx}={section_name}")
                modifier_idx += 1
            elif isinstance(modifier, AddColumn2DA):
                section_name = modifier.identifier or f"{mod_2da.sourcefile}_addcol_{modifier_idx}"
                # Section name references must match section headers exactly (no quotes)
                lines.append(f"AddColumn{modifier_idx}={section_name}")
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
        section_name: str = modifier.identifier

        if isinstance(modifier, ChangeRow2DA):
            lines.append(f"[{section_name}]")

            # Target specification (exactly as TSLPatcher expects)
            if modifier.target.target_type == TargetType.ROW_INDEX:
                assert modifier.target.value is not None, "modifier.target.value is None"
                assert isinstance(modifier.target.value, int), f"modifier.target.value is not int or RowValueRowIndex, but is {modifier.target.value.__class__.__name__}"
                lines.append(f"RowIndex={self._format_ini_value(str(modifier.target.value))}")
            elif modifier.target.target_type == TargetType.ROW_LABEL:
                assert modifier.target.value is not None, "modifier.target.value is None"
                assert isinstance(modifier.target.value, str), f"modifier.target.value is not str, but is {modifier.target.value.__class__.__name__}"
                lines.append(f"RowLabel={self._format_ini_value(modifier.target.value)}")
            elif modifier.target.target_type == TargetType.LABEL_COLUMN:
                assert modifier.target.value is not None, "modifier.target.value is None"
                assert isinstance(modifier.target.value, int), f"modifier.target.value is not int, but is {modifier.target.value.__class__.__name__}"
                lines.append(f"LabelIndex={self._format_ini_value(str(modifier.target.value))}")

            # Cell modifications (preserve exact column names and values)
            for col, row_value in modifier.cells.items():
                cell_val = self._serialize_row_value(row_value)
                lines.append(f"{col}={self._format_ini_value(cell_val)}")

            # Store 2DA memory assignments
            for token_id, row_value in modifier.store_2da.items():
                store_value = self._serialize_store_row_value(row_value)
                lines.append(f"2DAMEMORY{token_id}={self._format_ini_value(store_value)}")

            # Store TLK memory assignments
            for token_id, row_value in modifier.store_tlk.items():
                store_value = self._serialize_store_row_value(row_value)
                lines.append(f"StrRef{token_id}={self._format_ini_value(store_value)}")

            lines.append("")

        elif isinstance(modifier, AddRow2DA):
            lines.append(f"[{section_name}]")

            # Exclusive column (prevents duplicate values)
            if modifier.exclusive_column:
                assert modifier.exclusive_column is not None, "modifier.exclusive_column is None"
                assert isinstance(modifier.exclusive_column, str), f"modifier.exclusive_column is not str, but is {modifier.exclusive_column.__class__.__name__}"
                lines.append(f"ExclusiveColumn={self._format_ini_value(modifier.exclusive_column)}")

            # Row label (if specified)
            if modifier.row_label:
                assert modifier.row_label is not None, "modifier.row_label is None"
                assert isinstance(modifier.row_label, str), f"modifier.row_label is not str, but is {modifier.row_label.__class__.__name__}"
                lines.append(f"RowLabel={self._format_ini_value(modifier.row_label)}")

            # Cell values
            for col, row_value in modifier.cells.items():
                cell_val = self._serialize_row_value(row_value)
                lines.append(f"{col}={self._format_ini_value(cell_val)}")

            # Store 2DA memory assignments (if any and not empty)
            for token_id, row_value in modifier.store_2da.items():
                store_value = self._serialize_store_row_value(row_value)
                lines.append(f"2DAMEMORY{token_id}={self._format_ini_value(store_value)}")

            # Store TLK memory assignments (if any and not empty)
            for token_id, row_value in modifier.store_tlk.items():
                store_value = self._serialize_store_row_value(row_value)
                lines.append(f"StrRef{token_id}={self._format_ini_value(store_value)}")

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

            # Store 2DA memory assignments (if any and not empty)
            for token_id, store_val in modifier.store_2da.items():
                assert store_val is not None, "store_val is None"
                assert isinstance(store_val, str), f"store_val is not str, but is {store_val.__class__.__name__}"
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
        # RowValueRowIndex, RowValueRowLabel, RowValueRowCell should not appear in INI serialization
        # They are runtime-only types used during patch application
        msg = f"Cannot serialize runtime-only RowValue type: {type(row_value).__name__}"
        raise TypeError(msg)

    def _serialize_store_row_value(self, row_value: RowValue) -> str:
        """Serialize a RowValue used for 2DAMEMORY/TLK storage assignments."""
        if isinstance(row_value, RowValueRowIndex):
            return "RowIndex"
        if isinstance(row_value, RowValueRowLabel):
            return "RowLabel"
        if isinstance(row_value, RowValueRowCell):
            return row_value.column
        if isinstance(row_value, RowValue2DAMemory):
            return f"2DAMEMORY{row_value.token_id}"
        if isinstance(row_value, RowValueTLKMemory):
            return f"StrRef{row_value.token_id}"
        if isinstance(row_value, RowValueHigh):
            return f"High({row_value.column})" if row_value.column else "High()"
        if isinstance(row_value, RowValueConstant):
            return row_value.string
        msg = f"Unsupported RowValue type for memory storage serialization: {row_value.__class__.__name__}"
        raise TypeError(msg)

    def _serialize_gff_list(
        self,
        modifications: list[ModificationsGFF],
        *,
        verbose: bool = True,
    ) -> list[str]:
        """Serialize [GFFList] section with exact TSLPatcher format."""
        if not modifications:
            if verbose:
                print("No GFF modifications to serialize")
            return []

        if verbose:
            print(f"Serializing {len(modifications)} GFF files")

        lines: list[str] = []
        lines.append("[GFFList]")

        for idx, mod_gff in enumerate(modifications):
            # Use Replace# or File# based on replace_file flag - ModificationsGFF always has replace_file
            assert isinstance(mod_gff, ModificationsGFF), f"Expected ModificationsGFF, got {type(mod_gff).__name__}"
            prefix = "Replace" if mod_gff.replace_file else "File"
            if verbose:
                print(f"Adding GFF file {idx}: {prefix}{idx}={mod_gff.sourcefile} ({len(mod_gff.modifiers)} modifiers)")
            # Section name references must match section headers exactly (no quotes) - section headers are written as [{sourcefile}]
            lines.append(f"{prefix}{idx}={mod_gff.sourcefile}")
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

        # Add TSLPatcher exclamation-point variables - ModificationsGFF always has these attributes
        assert isinstance(mod_gff, ModificationsGFF), f"mod_gff must be ModificationsGFF, got {type(mod_gff).__name__}"
        lines.append(f"!ReplaceFile={'1' if mod_gff.replace_file else '0'}")
        if mod_gff.destination != "Override":
            lines.append(f"!Destination={self._format_ini_value(mod_gff.destination)}")
        if mod_gff.saveas != mod_gff.sourcefile:
            lines.append(f"!Filename={self._format_ini_value(mod_gff.saveas)}")

        # Collect AddField indices first
        addfield_modifiers = []

        # Process modifiers in order
        for gff_modifier in mod_gff.modifiers:
            if isinstance(gff_modifier, ModifyFieldGFF):
                # Direct field modification: Path=Value (use backslashes per TSLPatcher)
                path_str = str(gff_modifier.path).replace("/", "\\")

                # Check if this is a LocalizedString field (wrapped in FieldValueConstant containing LocalizedStringDelta)
                value = gff_modifier.value
                is_localized_string = False
                loc_string_delta: LocalizedStringDelta | None = None
                if isinstance(value, FieldValueConstant):
                    stored = value.stored
                    if isinstance(stored, LocalizedStringDelta):
                        is_localized_string = True
                        loc_string_delta = stored

                if not is_localized_string or loc_string_delta is None:
                    value_str = self._serialize_field_value(gff_modifier.value)
                    lines.append(f"{path_str}={self._format_ini_value(value_str)}")
                else:
                    # For LocalizedString fields with LocalizedStringDelta, serialize inline using subsection reference
                    # Generate a unique section name based on the path
                    sanitized_path = path_str.replace("\\", "_").replace("[", "_").replace("]", "_")
                    section_name = f"{mod_gff.sourcefile}_{sanitized_path}"
                    lines.append(f"{path_str}=<{section_name}>")
                    # Store for serialization after main section
                    if not hasattr(self, "_pending_localized_string_subsections"):
                        self._pending_localized_string_subsections = []
                    self._pending_localized_string_subsections.append((section_name, loc_string_delta))

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
            # Section name references must match section headers exactly (no quotes)
            lines.append(f"AddField{idx}={section_name}")

        lines.append("")

        # Generate AddField subsections after the main file section
        for idx, gff_modifier in enumerate(addfield_modifiers):
            section_name = gff_modifier.identifier or f"addfield_{idx}"
            lines.extend(self._serialize_addfield_section(gff_modifier, section_name))

        # Generate LocalizedString subsections (for inline LocalizedStringDelta fields)
        if hasattr(self, "_pending_localized_string_subsections") and self._pending_localized_string_subsections:
            for section_name, loc_string_delta in self._pending_localized_string_subsections:
                lines.append("")
                lines.append(f"[{section_name}]")
                # Serialize the LocalizedStringDelta
                # Add StrRef - handle FieldValueTLKMemory token reference
                assert loc_string_delta is not None
                if loc_string_delta.stringref is not None:
                    strref_value = self._serialize_field_value(loc_string_delta.stringref)
                    lines.append(f"StrRef={self._format_ini_value(strref_value)}")

                # Add lang# entries (escape text for INI format)
                for lang, gender, text in loc_string_delta:
                    substring_id = LocalizedString.substring_id(lang, gender)
                    escaped_text = escape_ini_value(text)
                    lines.append(f"lang{substring_id}={self._format_ini_value(escaped_text)}")

            # Clear the pending subsections list
            self._pending_localized_string_subsections.clear()

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
            label = ""  # AddStructToListGFF doesn't have label
        elif isinstance(gff_modifier, AddFieldGFF):
            field_type_name = self._get_gff_field_type_name(gff_modifier.field_type)
            label = gff_modifier.label
        else:
            msg = f"gff_modifier must be AddStructToListGFF or AddFieldGFF, got {type(gff_modifier).__name__}"
            raise TypeError(msg)

        lines.append(f"FieldType={self._format_ini_value(field_type_name)}")
        lines.append(f"Label={self._format_ini_value(label)}")

        # Path (use backslashes) - only write if non-empty (Path is optional)
        path_str = str(gff_modifier.path).replace("/", "\\")
        if path_str:
            lines.append(f"Path={self._format_ini_value(path_str)}")

        # Add field value based on type
        if is_add_struct_to_list:
            assert isinstance(gff_modifier, AddStructToListGFF), f"Expected AddStructToListGFF, got {type(gff_modifier).__name__}"
            # AddStructToListGFF always has TypeId
            if isinstance(gff_modifier.value, FieldValueConstant) and isinstance(gff_modifier.value.stored, GFFStruct):
                lines.append(f"TypeId={self._format_ini_value(str(gff_modifier.value.stored.struct_id))}")

            # Handle index_to_token for AddStructToListGFF (always present, may be None)
            if gff_modifier.index_to_token is not None:
                lines.append(f"2DAMEMORY{gff_modifier.index_to_token}=listindex")
        elif isinstance(gff_modifier, AddFieldGFF):
            # AddFieldGFF always has field_type attribute
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
                # Regular value - always write Value= even if empty (reader expects it)
                value_str = self._serialize_field_value(gff_modifier.value)
                lines.append(f"Value={self._format_ini_value(value_str)}")

        # Process nested modifiers - both AddFieldGFF and AddStructToListGFF have modifiers attribute
        assert isinstance(gff_modifier, (AddFieldGFF, AddStructToListGFF)), f"Expected AddFieldGFF or AddStructToListGFF, got {type(gff_modifier).__name__}"
        if gff_modifier.modifiers:
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
                    # Section name references must match section headers exactly (no quotes)
                    lines.append(f"AddField{addfield_count}={nested_section}")
                    addfield_count += 1

        lines.append("")

        # Recursively generate nested AddField/AddStructToListGFF sections
        if gff_modifier.modifiers:
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
        if isinstance(field_value, FieldValueConstant):
            loc_string = field_value.stored
        elif isinstance(field_value, LocalizedString):
            loc_string = field_value

        if not isinstance(loc_string, LocalizedString):
            msg = f"Expected LocalizedString but got {type(loc_string).__name__}: {loc_string}"
            print(msg)
            raise TypeError(msg)

        # Add StrRef - handle both LocalizedStringDelta with token and regular LocalizedString
        if isinstance(loc_string, LocalizedStringDelta):
            # LocalizedStringDelta can have a FieldValue token reference or be None
            if loc_string.stringref is not None:
                strref_value = self._serialize_field_value(loc_string.stringref)
                lines.append(f"StrRef={self._format_ini_value(strref_value)}")
        else:
            # Regular LocalizedString always has numeric stringref
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
        # Should never reach here - all FieldValue types should be handled above
        msg = f"Unexpected FieldValue type: {type(field_value).__name__}"
        raise TypeError(msg)

    def _format_gff_value(  # noqa: PLR0911
        self,
        value: Any,
    ) -> str:
        """Format a GFF field value for INI output with exact TSLPatcher format."""
        if isinstance(value, (Vector3, Vector4)):
            # TSLPatcher expects pipe-separated values with specific precision
            if isinstance(value, Vector4):
                return f"{value.x:.6f}|{value.y:.6f}|{value.z:.6f}|{value.w:.6f}"
            return f"{value.x:.6f}|{value.y:.6f}|{value.z:.6f}"
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
        *,
        verbose: bool = True,
    ) -> list[str]:
        """Serialize [TLKList] section."""
        if not modifications:
            if verbose:
                print("No TLK modifications to serialize")
            return []

        if verbose:
            print(f"Serializing {len(modifications)} TLK modification sets")

        lines: list[str] = []
        mod_tlk: ModificationsTLK = modifications[0]  # Should only be one TLK modification
        assert isinstance(mod_tlk, ModificationsTLK), "mod_tlk should be a ModificationsTLK"

        if verbose:
            print(f"TLK has {len(mod_tlk.modifiers)} modifiers")

        lines.append("[TLKList]")

        # Determine file types needed
        has_replacements: bool = any(m.is_replacement for m in mod_tlk.modifiers)
        has_appends: bool = any(not m.is_replacement for m in mod_tlk.modifiers)

        if verbose:
            print(f"TLK has {sum(1 for m in mod_tlk.modifiers if m.is_replacement)} replacements, {sum(1 for m in mod_tlk.modifiers if not m.is_replacement)} appends")

        # Modern TSLPatcher syntax for appends: Use StrRef token mappings ONLY
        # For replacements: Still use ReplaceFile# syntax
        if has_replacements:
            lines.append("ReplaceFile0=replace.tlk")
            if verbose:
                print("Added ReplaceFile0=replace.tlk")

        # StrRef token mappings for appends: StrRef{original_strref}={token_id}
        # These tell TSLPatcher which token each original StrRef maps to
        if has_appends:
            append_modifiers = [m for m in mod_tlk.modifiers if not m.is_replacement]
            strref_count = len(append_modifiers)
            if verbose:
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
        *,
        verbose: bool = True,
    ) -> list[str]:
        """Serialize [SSFList] section."""
        if not modifications:
            if verbose:
                print("No SSF modifications to serialize")
            return []

        if verbose:
            print(f"Serializing {len(modifications)} SSF files")

        lines: list[str] = []
        lines.append("[SSFList]")

        for idx, mod_ssf in enumerate(modifications):
            prefix = "Replace" if mod_ssf.replace_file else "File"
            if verbose:
                print(f"Adding SSF file {idx}: {prefix}{idx}={mod_ssf.sourcefile} ({len(mod_ssf.modifiers)} modifiers)")
            # Section name references must match section headers exactly (no quotes) - section headers are written as [{sourcefile}]
            lines.append(f"{prefix}{idx}={mod_ssf.sourcefile}")
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
            # TSLPatcher allows spaces in keys (e.g., "Battlecry 1", "Selected 1")
            lines.append(f"{sound_name}={self._format_ini_value(str(value))}")

        lines.append("")
        return lines

    def _serialize_hack_list(
        self,
        modifications: list,  # list[ModificationsNCS]
        *,
        verbose: bool = True,
    ) -> list[str]:
        """Serialize [HACKList] section for NCS binary patches."""
        if not modifications:
            if verbose:
                print("No NCS modifications to serialize")
            return []

        if verbose:
            print(f"Serializing {len(modifications)} NCS files for HACKList")

        lines: list[str] = []
        lines.append("[HACKList]")

        for idx, mod_ncs in enumerate(modifications):
            prefix = "Replace" if mod_ncs.replace_file else "File"
            if verbose:
                print(f"Adding NCS file {idx}: {prefix}{idx}={mod_ncs.sourcefile} ({len(mod_ncs.modifiers)} 'hacks')")
            # Section name references must match section headers exactly (no quotes) - section headers are written as [{sourcefile}]
            lines.append(f"{prefix}{idx}={mod_ncs.sourcefile}")
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
        *,
        verbose: bool = True,
    ) -> list[str]:
        """Serialize [InstallList] section with exact TSLPatcher format.

        Args:
            install_files: List of InstallFile objects to serialize
            verbose: Whether to print detailed logging
        """
        if not install_files:
            if verbose:
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
        if verbose:
            print(f"Serializing InstallList with {len(folders_dict)} folders, {total_files} total files")

        lines: list[str] = []
        lines.append("[InstallList]")

        # List all folder entries (using install_folder# format per TSLPatcher convention)
        sorted_destinations = sorted(folders_dict.keys())
        for i, dest in enumerate(sorted_destinations):
            files_in_folder = folders_dict[dest]
            if verbose:
                print(f"Install folder {i}: {dest} ({len(files_in_folder)} files)")
            lines.append(f"install_folder{i}={self._format_ini_value(dest)}")
        lines.append("")

        # Generate folder sections with file lists
        for i, dest in enumerate(sorted_destinations):
            files_in_folder = folders_dict[dest]
            section_name = f"install_folder{i}"

            if verbose:
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
                    if verbose:
                        print(f"  Replace{j}={filename}")
                else:
                    file_line = f"File{j}={self._format_ini_value(filename)}"
                    if verbose:
                        print(f"  File{j}={filename}")
                lines.append(file_line)

            if len(files_in_folder) > 5 and verbose:
                print(f"  ... and {len(files_in_folder) - 5} more files")

            lines.append("")

        return lines


# Logging helpers
# Log level: 0 = normal, 1 = verbose, 2 = debug
_log_level = 2 if os.environ.get("KOTORDIFF_DEBUG") else (1 if os.environ.get("KOTORDIFF_VERBOSE") else 0)


def _log_debug(msg: str) -> None:
    """Log debug message if debug level is enabled."""
    if _log_level >= 2:
        print(f"[DEBUG] {msg}")


def _log_verbose(msg: str) -> None:
    """Log verbose message if verbose level is enabled."""
    if _log_level >= 1:
        print(f"[VERBOSE] {msg}")


# Global cache dictionary to persist StrRef caches across all method calls
# Key: installation path (Path), Value: StrRefReferenceCache instance
_global_strref_caches: dict[Path, StrRefReferenceCache] = {}


@dataclass
class TwoDALinkTarget:
    row_index: int
    token_id: int
    row_label: str | None = None


@dataclass
class PendingStrRefReference:
    """Temporarily stored StrRef reference that will be applied when the file is diffed.

    Attributes:
        filename: The resource filename (e.g., "p_vima_ssf.ssf")
        source_path: The installation or path where this StrRef was found
        old_strref: The original StrRef value
        token_id: The TLKMEMORY token ID to use
        location_type: Type of location (2da, ssf, gff, ncs)
        location_data: Location-specific data (row_index/column_name for 2DA, sound for SSF, field_path for GFF, byte_offset for NCS)
    """

    filename: str
    source_path: Installation | Path
    old_strref: int
    token_id: int
    location_type: str  # "2da", "ssf", "gff", "ncs"
    location_data: dict[str, Any]


@dataclass
class Pending2DARowReference:
    """Temporarily stored 2DA row reference that will be applied when the GFF file is diffed.

    Attributes:
        gff_filename: The GFF resource filename (e.g., "item.uti")
        source_path: The installation or path where this 2DA row reference was found
        twoda_filename: The 2DA filename (e.g., "appearance.2da")
        row_index: The 2DA row index being referenced
        token_id: The 2DAMEMORY token ID to use
        field_paths: List of GFF field paths that reference this row
    """

    gff_filename: str
    source_path: Installation | Path
    twoda_filename: str
    row_index: int
    token_id: int
    field_paths: list[str]


class IncrementalTSLPatchDataWriter:
    """Writes tslpatchdata files and INI sections incrementally during diff."""

    def __init__(
        self,
        tslpatchdata_path: Path,
        ini_filename: str,
        base_data_path: Path | None = None,
        modded_data_path: Path | None = None,
        strref_cache: StrRefReferenceCache | None = None,
        twoda_caches: dict[int, CaseInsensitiveDict[TwoDAMemoryReferenceCache]] | None = None,
        log_func: Callable[[str], None] | None = None,
    ):
        """Initialize incremental writer.

        Args:
            tslpatchdata_path: Path to tslpatchdata folder
            ini_filename: Name of INI file to generate
            base_data_path: Optional base path for reading vanilla/original files
            modded_data_path: Optional path for reading modded files (for AddRow2DA linking)
            strref_cache: Optional StrRef reference cache for TLK linking
                (built from installation that has StrRefs that others don't)
            twoda_caches: Optional nested dict of 2DA caches
                Structure: {installation_index: CaseInsensitiveDict[TwoDAMemoryReferenceCache]}
                Keys are case-insensitive 2DA filenames (e.g., "appearance.2da", "APPEARANCE.2DA")
                Each cache should be built from the installation that has entries
                for that specific 2DA filename that others don't.
            log_func: Optional logging function

        Note: For n-way diffs, caches should be built from whichever installation has
        entries (2DA rows, StrRef entries, GFF fields, SSF entries, etc.) that others don't.
        There should be a separate cache for each unique (installation_index, 2da_filename) pair.
        """
        self.tslpatchdata_path: Path = tslpatchdata_path
        self.ini_path: Path = tslpatchdata_path / ini_filename
        self.base_data_path: Path | None = base_data_path
        self.modded_data_path: Path | None = modded_data_path
        self.strref_cache: StrRefReferenceCache | None = strref_cache
        # Convert regular dicts to CaseInsensitiveDict if needed
        self.twoda_caches: dict[int, CaseInsensitiveDict[TwoDAMemoryReferenceCache]] = {}
        if twoda_caches:
            for install_idx, filename_to_cache in twoda_caches.items():
                if isinstance(filename_to_cache, CaseInsensitiveDict):
                    self.twoda_caches[install_idx] = filename_to_cache
                    continue
                # Convert regular dict to CaseInsensitiveDict
                self.twoda_caches[install_idx] = CaseInsensitiveDict(filename_to_cache)
        self.log_func: Callable[[str], None] = log_func or print

        # Metadata storage for TLK modifications (strref_mappings, source installations)
        # Key: id(ModificationsTLK object), Value: dict with strref_mappings and source_installations
        self._tlk_metadata: dict[int, dict[str, Any]] = {}

        # Create tslpatchdata directory
        self.tslpatchdata_path.mkdir(parents=True, exist_ok=True)

        # Track what we've written
        self.written_sections: set[str] = set()
        self.install_folders: dict[str, list[str]] = {}

        # Track modifications for final InstallList generation
        self.all_modifications: ModificationsByType = self._create_empty_modifications()

        # Track insertion positions for each section (for real-time appending)
        self.section_markers: dict[str, str] = {
            "tlk": "[TLKList]",
            "install": "[InstallList]",
            "2da": "[2DAList]",
            "gff": "[GFFList]",
            "ncs": "[CompileList]",
            "ssf": "[SSFList]",
        }

        # Track folder numbers for InstallList
        self.folder_numbers: dict[str, int] = {}
        self.next_folder_number: int = 0

        # Initialize INI file with all headers
        self._initialize_ini()

        _log_debug(f"Incremental writer initialized at: {self.tslpatchdata_path}")

        # Track global 2DAMEMORY token allocation
        self._next_2da_token_id: int = 0

        # Track TLK modifications with their source paths for intelligent cache building
        # Key: source_index (0=first/vanilla, 1=second/modded, 2=third, etc.)
        # Value: list of TLKModificationWithSource objects from that source
        self.tlk_mods_by_source: dict[int, list[TLKModificationWithSource]] = {}

        # Track pending StrRef references that will be applied when files are diffed
        # Key: filename (lowercase) -> list of PendingStrRefReference
        self._pending_strref_references: dict[str, list[PendingStrRefReference]] = {}

        # Track pending 2DA row references that will be applied when GFF files are diffed
        # Key: gff_filename (lowercase) -> list of Pending2DARowReference
        self._pending_2da_row_references: dict[str, list[Pending2DARowReference]] = {}

        # Performance optimization: batch INI writes to reduce overhead
        self._pending_ini_writes: set[str] = set()  # Track sections that need to be written
        self._batch_writes: bool = True  # Flag to enable/disable write batching
        self._writes_since_last_flush: int = 0
        self._write_batch_size: int = 50  # Write every N modifications

    def register_tlk_modification_with_source(
        self,
        tlk_mod: ModificationsTLK,
        source_path: Path | Installation,  # Installation or Path
        source_index: int,
    ) -> None:
        """Register a TLK modification with its source path for cache building.

        Args:
            tlk_mod: The TLK modification object
            source_path: The installation or folder path this TLK came from
            source_index: Index of the source (0=first/vanilla, 1=second/modded, etc.)
        """
        is_installation: bool = isinstance(source_path, Installation)

        wrapped = TLKModificationWithSource(
            modification=tlk_mod,
            source_path=source_path,
            source_index=source_index,
            is_installation=is_installation,
        )

        if source_index not in self.tlk_mods_by_source:
            self.tlk_mods_by_source[source_index] = []

        self.tlk_mods_by_source[source_index].append(wrapped)
        _log_debug(f"Registered TLK mod from source {source_index}: {tlk_mod.sourcefile} ({len(getattr(tlk_mod, 'strref_mappings', {}))} StrRefs)")

    @staticmethod
    def _format_path_with_source_prefix(path_str: str, source: Installation | Path) -> str:
        """Format a relative path with the source folder/installation name as a prefix.

        This ensures paths in log messages clearly indicate which installation they come from.

        Args:
            path_str: The relative path string (e.g., "data/2da.bif/planetary.2da")
            source: The Installation or Path object where the resource was found

        Returns:
            Formatted path with source prefix (e.g., "swkotor/data/2da.bif/planetary.2da")
        """
        if isinstance(source, Installation):
            installation_path = source.path()
            source_folder = installation_path.name if installation_path else "unknown"
        elif isinstance(source, Path):
            source_folder = source.name if source else "unknown"
        else:
            source_folder = "unknown"
        return f"{source_folder}/{path_str}"

    @staticmethod
    def _create_empty_modifications() -> ModificationsByType:
        """Create empty modifications collection."""
        from pykotor.tslpatcher.writer import ModificationsByType  # noqa: PLC0415

        return ModificationsByType.create_empty()

    def _initialize_ini(self) -> None:
        """Initialize INI file with header, [Settings], and all List section headers."""
        header_lines = self._generate_custom_header()
        settings_lines = self._generate_settings()

        # Write all section headers in TSLPatcher-compliant order
        section_headers = [
            "",
            "[TLKList]",
            "",
            "",
            "[InstallList]",
            "",
            "",
            "[2DAList]",
            "",
            "",
            "[GFFList]",
            "",
            "",
            "[CompileList]",
            "",
            "",
            "[SSFList]",
            "",
        ]

        content = "\n".join([*header_lines, "", *settings_lines, *section_headers])
        self.ini_path.write_text(content, encoding="utf-8")
        _log_debug(f"Initialized INI with all section headers at: {self.ini_path}")

    def _generate_custom_header(self) -> list[str]:
        """Generate custom INI file header with PyKotor branding."""
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
            ";",
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
        """Generate default [Settings] section with all required TSLPatcher keys."""
        return [
            "[Settings]",
            "FileExists=1",
            "WindowCaption=Mod Installer",
            "ConfirmMessage=Install this mod?",
            "LogLevel=3",
            "InstallerMode=1",
            "BackupFiles=1",
            "PlaintextLog=0",
            "LookupGameFolder=0",
            "LookupGameNumber=1",
            "SaveProcessedScripts=0",
            "",
        ]

    def write_modification(
        self,
        modification: PatcherModifications,
        source_data: bytes | None = None,
        source_path: Installation | Path | None = None,
        modded_source_path: Installation | Path | None = None,
    ) -> None:
        """Write a modification's resource file and INI section immediately.

        Args:
            modification: The modification object to write
            source_data: Optional source data (vanilla version for patching)
            source_path: Optional source installation or path where this file comes from
        """
        # Check for and apply pending StrRef references before writing
        filename_lower = modification.sourcefile.lower()
        self._apply_pending_strref_references(filename_lower, modification, source_data, source_path)

        # Check for and apply pending 2DA row references before writing (for GFF files)
        if isinstance(modification, ModificationsGFF):
            self._apply_pending_2da_row_references(filename_lower, modification, source_data, source_path)

        # Determine modification type and dispatch
        if isinstance(modification, Modifications2DA):
            self._write_2da_modification(modification, source_data, source_path, modded_source_path)
        elif isinstance(modification, ModificationsGFF):
            self._write_gff_modification(modification, source_data)
        elif isinstance(modification, ModificationsTLK):
            self._write_tlk_modification(modification)
        elif isinstance(modification, ModificationsSSF):
            self._write_ssf_modification(modification, source_data)
        elif isinstance(modification, ModificationsNCS):
            self._write_ncs_modification(modification, source_data)
        else:
            _log_debug(f"Unknown modification type: {type(modification).__name__}")

    def _write_2da_modification(
        self,
        mod_2da: Modifications2DA,
        source_data: bytes | None,
        source_path: Installation | Path | None = None,
        modded_source_path: Installation | Path | None = None,
    ) -> None:
        """Write 2DA resource file and INI section."""
        filename: str = mod_2da.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written 2DA: {filename}")
            return

        change_row_targets, add_row_targets = self._prepare_twoda_tokens(mod_2da)

        # Write resource file (base vanilla 2DA that will be patched)
        if source_data:
            output_path: Path = self.tslpatchdata_path / filename
            try:
                twoda_obj = read_2da(source_data)
                write_2da(twoda_obj, output_path, ResourceType.TwoDA)
                _log_verbose(f"Wrote 2DA file: {filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to write 2DA {filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return

        # Add to install folders
        self._add_to_install_folder("Override", filename)

        # Write INI section
        self._write_to_ini([mod_2da], "2da")
        self.written_sections.add(filename)

        # Track in all_modifications (only if not already added)
        if mod_2da not in self.all_modifications.twoda:
            self.all_modifications.twoda.append(mod_2da)

        # Create linking patches for modified rows using BATCH PROCESSING
        # Use source_path from write_modification parameter, or try to infer from base_data_path
        if source_path is None:
            if hasattr(mod_2da, "source_path"):
                source_path = Path(mod_2da.sourcefile)
            elif self.base_data_path:
                source_path = Path(self.base_data_path, mod_2da.sourcefile)

        # BATCH PROCESSING: Process all 2DA row modifications together
        if change_row_targets and source_path and isinstance(source_path, Installation):
            # Group by 2DA filename for batch processing
            twoda_to_targets: dict[str, list[TwoDALinkTarget]] = {}
            for target in change_row_targets:
                if filename not in twoda_to_targets:
                    twoda_to_targets[filename] = []
                twoda_to_targets[filename].append(target)

            # Process each 2DA file's rows in batch
            for twoda_file, targets in twoda_to_targets.items():
                self.log_func(f"\n=== Batch Finding References for {len(targets)} rows in {twoda_file} ===")
                self._find_and_patch_2da_rows_batch(source_path, twoda_file, targets)
        elif change_row_targets and source_path:
            # Fallback: process individually for Path-based sources
            for target in change_row_targets:
                self.log_func(f"\n=== Finding References for 2DA Row: {filename} row {target.row_index} -> Token {target.token_id} ===")
                self._find_and_patch_single_2da_row(source_path, filename, target.row_index, target.token_id)

        # Process each new row ONE AT A TIME (label-based lookup is harder to batch)
        # For AddRow2DA, scan the MODDED source (where the new row exists)
        scan_source = modded_source_path if modded_source_path else source_path
        if add_row_targets and scan_source:
            for target in add_row_targets:
                self.log_func(f"\n=== Finding References for New 2DA Row: {filename} label '{target.row_label}' -> Token {target.token_id} ===")
                if not modded_source_path:
                    self.log_func("[Warning] No modded_source_path provided, using vanilla source (may not find new row references)")
                # For new rows, we need the row_label since index is unknown
                if target.row_label:
                    self._find_and_patch_single_2da_row_by_label(scan_source, filename, target.row_label, target.token_id)

    def _prepare_twoda_tokens(self, mod_2da: Modifications2DA) -> tuple[list[TwoDALinkTarget], list[TwoDALinkTarget]]:
        """Prepare 2DAMEMORY tokens for 2DA row modifications.

        Handles both ChangeRow2DA and AddRow2DA:
        - ChangeRow2DA: Modifies existing rows, creates linking patches for vanilla references
        - AddRow2DA: Adds new rows, creates linking patches for modded references

        Returns:
            (change_row_targets, add_row_targets) - Two lists of link targets for different caches
        """
        from pykotor.tslpatcher.mods.twoda import AddRow2DA, ChangeRow2DA, RowValueRowIndex, TargetType

        change_row_targets: list[TwoDALinkTarget] = []
        add_row_targets: list[TwoDALinkTarget] = []

        for modifier in mod_2da.modifiers:
            # Handle ChangeRow2DA - existing rows being modified
            if isinstance(modifier, ChangeRow2DA):
                # Reserve any existing tokens in store_2da
                if modifier.store_2da:
                    self._reserve_existing_twoda_tokens(modifier.store_2da.keys())

                # Extract row index - only handle ROW_INDEX targets
                if modifier.target.target_type != TargetType.ROW_INDEX:
                    continue
                if not isinstance(modifier.target.value, int):
                    continue

                row_index: int = modifier.target.value

                # If no store_2da, allocate a token and store RowIndex
                if not modifier.store_2da:
                    token_id: int = self._allocate_2da_token()
                    modifier.store_2da = {token_id: RowValueRowIndex()}
                    change_row_targets.append(TwoDALinkTarget(row_index=row_index, token_id=token_id, row_label=None))
                    continue

                # Process existing store_2da tokens
                for token_id, row_value in list(modifier.store_2da.items()):
                    if not isinstance(row_value, RowValueRowIndex):
                        continue
                    # Token stores the row index - use this for linking
                    change_row_targets.append(TwoDALinkTarget(row_index=row_index, token_id=token_id, row_label=None))

            # Handle AddRow2DA - new rows being added
            elif isinstance(modifier, AddRow2DA):
                # If no store_2da, allocate a token and store RowIndex
                if not modifier.store_2da:
                    token_id = self._allocate_2da_token()
                    modifier.store_2da = {token_id: RowValueRowIndex()}
                    self.log_func(f"[DEBUG] Created 2DAMEMORY token {token_id} for AddRow2DA with label '{modifier.row_label}'")
                    add_row_targets.append(
                        TwoDALinkTarget(
                            row_index=-1,  # Unknown until patch time
                            token_id=token_id,
                            row_label=modifier.row_label,
                        )
                    )
                    continue

                self._reserve_existing_twoda_tokens(modifier.store_2da.keys())

                # For AddRow2DA, we can't know the final row index until patch time
                # But we CAN create linking patches for the modded installation
                # The row_label is our best identifier for the "new" row
                for token_id, row_value in list(modifier.store_2da.items()):
                    if not isinstance(row_value, RowValueRowIndex):
                        continue
                    # Use row_label as the identifier (since index is unknown)
                    # We'll need to find references by matching the row_label in the modded 2DA
                    add_row_targets.append(
                        TwoDALinkTarget(
                            row_index=-1,  # Unknown until patch time
                            token_id=token_id,
                            row_label=modifier.row_label,
                        )
                    )

        return change_row_targets, add_row_targets

    def _reserve_existing_twoda_tokens(self, token_ids: Iterable[int]) -> None:
        for token_id in token_ids:
            if token_id >= self._next_2da_token_id:
                self._next_2da_token_id = token_id + 1

    def _allocate_2da_token(self) -> int:
        """Allocate a new 2DAMEMORY token ID."""
        token_id: int = self._next_2da_token_id
        self._next_2da_token_id += 1
        return token_id

    def _replace_cells_with_2damemory_tokens(self) -> None:
        """Replace cell values with 2DAMEMORY token references when values match stored tokens.

        After all 2DA modifications are created, this method:
        1. Processes modifiers in order, tracking which tokens are stored at each point
        2. Replaces RowValueConstant values that match stored values with RowValue2DAMemory references
        3. Only replaces with tokens that have been stored in previous modifiers (ensures proper ordering)

        This ensures that when we store 2DAMEMORY0=RowIndex, any cell values that equal that row index
        will be written as `column=2DAMEMORY0` instead of `column=80`.
        """
        from pykotor.tslpatcher.mods.twoda import (
            AddRow2DA,
            ChangeRow2DA,
            RowValue2DAMemory,
            RowValueConstant,
            RowValueRowIndex,
            TargetType,
        )

        # Track which tokens are available at each point (tokens that have been stored)
        # Format: {stored_value: token_id} - only includes tokens that have been stored so far
        available_tokens: dict[str, int] = {}

        replacements_made: int = 0

        # Process modifiers in order to ensure tokens are stored before being used
        for mod_2da in self.all_modifications.twoda:
            for modifier in mod_2da.modifiers:
                if not isinstance(modifier, (ChangeRow2DA, AddRow2DA)):
                    continue

                # First, process store_2da entries to add tokens to available_tokens
                for token_id, row_value in modifier.store_2da.items():
                    stored_value: str | None = None

                    if isinstance(row_value, RowValueRowIndex):
                        # For RowIndex, the stored value is the row index as a string
                        if isinstance(modifier, AddRow2DA):
                            # For AddRow2DA with RowValueRowIndex, the row index isn't known until runtime
                            # So we can't match it statically - skip this token for matching
                            continue
                        if (
                            isinstance(modifier, ChangeRow2DA)
                            and modifier.target.target_type == TargetType.ROW_INDEX
                            and isinstance(modifier.target.value, int)
                        ):
                            stored_value = str(modifier.target.value)
                    elif isinstance(row_value, RowValueConstant):
                        # For constant values, the stored value is the string itself
                        stored_value = row_value.string
                    elif isinstance(row_value, RowValueRowLabel):
                        # For RowLabel, we can match if we have the row label
                        # For ChangeRow2DA, we can get it from target
                        # For AddRow2DA, we can get it from modifier.row_label
                        if isinstance(modifier, ChangeRow2DA):
                            if (
                                modifier.target.target_type == TargetType.ROW_LABEL
                                and isinstance(modifier.target.value, str)
                            ):
                                stored_value = modifier.target.value
                        elif isinstance(modifier, AddRow2DA) and modifier.row_label:
                            stored_value = modifier.row_label
                    elif isinstance(row_value, RowValueRowCell):
                        # For RowCell, we can match if we can determine the cell value
                        # This is more complex - we'd need to read the 2DA file to get the cell value
                        # For now, skip RowCell matching as it requires runtime evaluation
                        continue
                    # Note: We handle RowIndex (for ChangeRow2DA only), RowLabel, and Constant values for matching.

                    if (
                        stored_value is not None
                        # Only add if this token hasn't been stored yet, or if this token ID is lower
                        # (prefer lower token IDs when multiple tokens store the same value)
                        and (
                            stored_value not in available_tokens
                            or token_id < available_tokens[stored_value]
                        )
                    ):
                        available_tokens[stored_value] = token_id

                # Now check cell values and replace with available tokens
                # Only replace with tokens that have been stored in previous modifiers
                for column_name, cell_value in list(modifier.cells.items()):
                    if isinstance(cell_value, RowValueConstant):
                        cell_string = cell_value.string
                        if cell_string in available_tokens:
                            token_id = available_tokens[cell_string]
                            # Replace with 2DAMEMORY token reference
                            modifier.cells[column_name] = RowValue2DAMemory(token_id)
                            replacements_made += 1
                            self.log_func(f"  Replaced {mod_2da.sourcefile} {modifier.identifier} {column_name}={cell_string} with 2DAMEMORY{token_id}")

        if replacements_made > 0:
            self.log_func(f"  Replaced {replacements_made} cell value(s) with 2DAMEMORY token references")

    @staticmethod
    def _gff_has_twoda_token(
        mod_gff: ModificationsGFF,
        path: str,
        token_id: int,
    ) -> bool:
        for modifier in mod_gff.modifiers:
            if not isinstance(modifier, ModifyFieldGFF):
                continue

            existing_path: str = str(modifier.path).replace("/", "\\")
            if existing_path.lower() != path.lower():
                continue

            if isinstance(modifier.value, FieldValue2DAMemory) and modifier.value.token_id == token_id:
                return True

        return False

    def _allocate_listindex_tokens_for_gff(
        self,
        mod_gff: ModificationsGFF,
    ) -> None:
        """Allocate 2DAMEMORY tokens for ListIndex in AddStructToListGFF entries when needed.

        This scans all AddStructToListGFF modifiers and allocates index_to_token
        if any nested fields reference 2DA rows (indicating cross-references might be needed).

        Args:
            mod_gff: The GFF modifications to process
        """
        from pykotor.tslpatcher.mods.gff import AddStructToListGFF, FieldValue2DAMemory

        def _needs_listindex_token(modifier: AddStructToListGFF) -> bool:
            """Check if an AddStructToListGFF needs a ListIndex token."""
            # If already has a token, skip
            if modifier.index_to_token is not None:
                return False

            # Check if any nested modifiers use 2DAMEMORY (indicates 2DA row references)
            def _has_2da_references(mod: Any) -> bool:
                if isinstance(mod, ModifyFieldGFF):
                    # Check if field value uses 2DAMEMORY
                    return isinstance(mod.value, FieldValue2DAMemory)
                if isinstance(mod, AddFieldGFF):
                    # Check if field value uses 2DAMEMORY
                    if isinstance(mod.value, FieldValue2DAMemory):
                        return True
                    # Recursively check nested modifiers
                    return bool(mod.modifiers and any(_has_2da_references(nested) for nested in mod.modifiers))
                if isinstance(mod, AddStructToListGFF):
                    # Recursively check nested modifiers
                    return bool(mod.modifiers and any(_has_2da_references(nested) for nested in mod.modifiers))
                return False

            return _has_2da_references(modifier)

        def _allocate_tokens_recursive(modifier: Any) -> None:
            """Recursively allocate tokens for AddStructToListGFF entries."""
            if isinstance(modifier, AddStructToListGFF):
                if _needs_listindex_token(modifier):
                    token_id = self._allocate_2da_token()
                    modifier.index_to_token = token_id
                    self.log_func(f"    Allocated 2DAMEMORY{token_id}=ListIndex for AddStructToListGFF [{modifier.identifier}]")

                # Process nested modifiers
                for nested in modifier.modifiers:
                    _allocate_tokens_recursive(nested)
            elif isinstance(modifier, AddFieldGFF):
                # Process nested modifiers
                for nested in modifier.modifiers:
                    _allocate_tokens_recursive(nested)

        # Process all modifiers in the GFF modification
        for modifier in mod_gff.modifiers:
            _allocate_tokens_recursive(modifier)

    def _write_gff_modification(
        self,
        mod_gff: ModificationsGFF,
        source_data: bytes | None,
    ) -> None:
        """Write GFF resource file and INI section."""
        filename: str = mod_gff.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written GFF: {filename}")
            return

        # Allocate ListIndex tokens before writing
        self._allocate_listindex_tokens_for_gff(mod_gff)

        # Get destination for INI tracking
        destination: str = getattr(mod_gff, "destination", "Override")

        # Get actual filename (might be different from sourcefile)
        actual_filename: str = getattr(mod_gff, "saveas", mod_gff.sourcefile)

        # CRITICAL: ALL files go directly in tslpatchdata root, NOT in subdirectories
        # The destination field tells TSLPatcher where to install them at runtime
        output_path: Path = self.tslpatchdata_path / actual_filename

        # Write resource file (base vanilla GFF that will be patched)
        if source_data:
            try:
                gff_obj = read_gff(source_data)
                ext = PurePath(actual_filename).suffix.lstrip(".").lower()
                restype: ResourceType | None = ResourceType.from_extension(ext)

                # If from_extension fails, try to determine from filename
                if restype is None or not restype.is_valid():
                    # Try mapping common GFF extensions
                    gff_extension_map: dict[str, ResourceType] = {
                        "are": ResourceType.ARE,
                        "dlg": ResourceType.DLG,
                        "fac": ResourceType.FAC,
                        "gff": ResourceType.GFF,
                        "git": ResourceType.GIT,
                        "gui": ResourceType.GUI,
                        "ifo": ResourceType.IFO,
                        "jrl": ResourceType.JRL,
                        "utc": ResourceType.UTC,
                        "utd": ResourceType.UTD,
                        "ute": ResourceType.UTE,
                        "uti": ResourceType.UTI,
                        "utm": ResourceType.UTM,
                        "utp": ResourceType.UTP,
                        "utw": ResourceType.UTW,
                    }
                    restype = gff_extension_map.get(ext)

                if restype is None or not restype.is_valid():
                    msg = f"Could not determine valid ResourceType for GFF file {actual_filename} (extension: {ext})"
                    self.log_func(msg)
                    return

                # Determine the desired output file format (GFF, GFF_XML, or GFF_JSON)
                file_format: ResourceType = detect_gff(source_data)
                if file_format not in {ResourceType.GFF, ResourceType.GFF_XML, ResourceType.GFF_JSON}:
                    file_format = ResourceType.GFF

                write_gff(gff_obj, output_path, file_format)
                _log_verbose(f"Wrote GFF file: {actual_filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to write GFF {actual_filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return

        # Add to install folders
        self._add_to_install_folder(destination, actual_filename)

        # Write INI section
        self._write_to_ini([mod_gff], "gff")
        self.written_sections.add(filename)

        # Track in all_modifications (only if not already added)
        if mod_gff not in self.all_modifications.gff:
            self.all_modifications.gff.append(mod_gff)

    def _write_tlk_modification(
        self,
        mod_tlk: ModificationsTLK,
    ) -> None:
        """Write TLK modification and create linking patches.

        This is where we use the StrRef cache to find all files that need
        linking patches for the modified TLK entries.
        """
        filename: str = mod_tlk.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written TLK: {filename}")
            return

        # Generate append.tlk file
        appends: list[ModifyTLK] = [m for m in mod_tlk.modifiers if not m.is_replacement]

        if appends:
            _log_debug(f"Creating append.tlk with {len(appends)} entries")
            append_tlk: TLK = TLK()
            append_tlk.resize(len(appends))

            sorted_appends: list[ModifyTLK] = sorted(appends, key=lambda m: m.token_id)

            for append_idx, modifier in enumerate(sorted_appends):
                text: str = modifier.text if modifier.text else ""
                sound_str: str = str(modifier.sound) if modifier.sound else ""
                append_tlk.replace(append_idx, text, sound_str)

            append_path: Path = self.tslpatchdata_path / "append.tlk"
            write_tlk(append_tlk, append_path, ResourceType.TLK)
            _log_verbose(f"Wrote append.tlk with {len(appends)} entries")

        # Add to install folders
        self._add_to_install_folder(".", "append.tlk")

        # Find StrRef references and create linking patches using BATCH PROCESSING
        # Get strref_mappings and source installations from the metadata dict
        tlk_metadata: dict[str, Any] | None = self._tlk_metadata.get(id(mod_tlk))
        strref_mappings: dict[int, int] = {}
        source_installations: list[Installation | Path] = []

        if tlk_metadata:
            strref_mappings = tlk_metadata.get("strref_mappings", {})
            source_installations = tlk_metadata.get("source_installations", [])

        if not strref_mappings:
            # Write INI section
            self._write_to_ini([mod_tlk], "tlk")
            self.written_sections.add(filename)

            # Track in all_modifications (only if not already added)
            if mod_tlk not in self.all_modifications.tlk:
                self.all_modifications.tlk.append(mod_tlk)
            return

        # If no installations from metadata, try fallback
        if not source_installations and self.base_data_path:
            source_installations.append(self.base_data_path)

        # For diff entries, search BOTH installations for references
        # References to the old StrRef might exist in either installation
        if source_installations:
            # BATCH PROCESSING: Collect all StrRefs to process
            strrefs_to_search: dict[Installation | Path, list[tuple[int, int]]] = {}

            # First pass: determine which StrRefs to search in which installations
            for old_strref, new_token_id in strref_mappings.items():
                # Find the modifier entry that corresponds to this StrRef
                modifier_entry: ModifyTLK | None = None
                for modifier in mod_tlk.modifiers:
                    if modifier.mod_index == old_strref:
                        modifier_entry = modifier
                        break

                # Check if StrRef exists in both installations (diff) or just one (unique)
                exists_in_path1: bool = False
                exists_in_path2: bool = False
                path1_text: str = ""
                path1_sound: str = ""
                path2_text: str = ""
                path2_sound: str = ""
                new_text: str = ""

                # Check first source installation (path1)
                if source_installations and len(source_installations) > 0 and isinstance(source_installations[0], Installation):
                    try:
                        talktable = source_installations[0].talktable()
                        path1_text = talktable.string(old_strref)
                        path1_sound = str(talktable.sound(old_strref))
                        # Empty string means the entry doesn't exist or is invalid
                        exists_in_path1 = bool(path1_text) or bool(path1_sound)
                    except Exception:  # noqa: BLE001
                        exists_in_path1 = False

                # Check second source installation (path2) if it exists
                if source_installations and len(source_installations) > 1 and isinstance(source_installations[1], Installation):
                    try:
                        talktable = source_installations[1].talktable()
                        path2_text = talktable.string(old_strref)
                        path2_sound = str(talktable.sound(old_strref))
                        # Empty string means the entry doesn't exist or is invalid
                        exists_in_path2 = bool(path2_text) or bool(path2_sound)
                    except Exception:  # noqa: BLE001
                        exists_in_path2 = False

                # Get new entry from modifier
                if modifier_entry:
                    new_text = modifier_entry.text if modifier_entry.text else ""

                # Log the diff
                self.log_func(f"\n=== Finding References for StrRef {old_strref} -> Token {new_token_id} ===")

                # Determine which installations to search based on where the entry exists
                # References are ALWAYS relevant to the installation they're found in
                # Each installation must be searched separately, and references found
                # in one installation should only patch files from that same installation
                installations_to_search: list[Installation | Path] = []

                # If exists in both paths, show diff format and search both separately
                if exists_in_path1 and exists_in_path2:
                    self.log_func(f"  Diff: StrRef {old_strref}")
                    path1_name = source_installations[0].path() if isinstance(source_installations[0], Installation) else str(source_installations[0])
                    path2_name = source_installations[1].path() if isinstance(source_installations[1], Installation) else str(source_installations[1])
                    self.log_func(f"    Path 1 ({path1_name}): {path1_text[:100]}{'...' if len(path1_text) > 100 else ''}")
                    self.log_func(f"    Path 2 ({path2_name}): {path2_text[:100]}{'...' if len(path2_text) > 100 else ''}")
                    # Search both paths separately - references found in each will only
                    # be linked to files from that same installation
                    installations_to_search = source_installations
                # If exists only in path1, show unique to path1
                elif exists_in_path1:
                    path1_name = source_installations[0].path() if isinstance(source_installations[0], Installation) else str(source_installations[0])
                    self.log_func(f"  Unique to Path 1 ({path1_name}): {path1_text[:100]}{'...' if len(path1_text) > 100 else ''}")
                    # Search only path1 - references will only link to path1 files
                    installations_to_search = [source_installations[0]]
                # If exists only in path2, show unique to path2
                elif exists_in_path2:
                    path2_name = source_installations[1].path() if isinstance(source_installations[1], Installation) else str(source_installations[1])
                    self.log_func(f"  Unique to Path 2 ({path2_name}): {path2_text[:100]}{'...' if len(path2_text) > 100 else ''}")
                    # Search only path2 - references will only link to path2 files
                    installations_to_search = [source_installations[1]]
                # If doesn't exist in either but has new text from modifier, it's a new entry
                elif new_text:
                    self.log_func(f"  New entry: {new_text[:100]}{'...' if len(new_text) > 100 else ''}")
                    # Don't search for references to new entries that don't exist yet
                    installations_to_search = []

                # Collect StrRefs to search per installation
                for source in installations_to_search:
                    if source not in strrefs_to_search:
                        strrefs_to_search[source] = []
                    strrefs_to_search[source].append((old_strref, new_token_id))

            # Second pass: Batch process all StrRefs per installation
            from pykotor.tools.reference_cache import (  # noqa: PLC0415
                GFFRefLocation,
                # NCSRefLocation,  # FIXME: TEMPORARILY DISABLED - NCS scanning
                SSFRefLocation,
                TwoDARefLocation,
                find_all_strref_references,
            )

            # Use global cache to persist across all method calls
            global _global_strref_caches  # noqa: PLW0602

            for source, strref_token_pairs in strrefs_to_search.items():
                if not isinstance(source, Installation):
                    # Path-based sources - fall back to individual processing
                    for old_strref, new_token_id in strref_token_pairs:
                        self._find_and_patch_single_strref(source, old_strref, new_token_id)
                    continue

                # Extract just the StrRefs for batch lookup
                strrefs_to_find = [strref for strref, _ in strref_token_pairs]

                installation_name = source.path()
                self.log_func(f"\n=== Batch Finding References for {len(strrefs_to_find)} StrRefs in {installation_name} ===")

                # Get the existing cache for this installation, or None if it's the first time
                cache = _global_strref_caches.get(source.path())

                # Batch find all StrRef references. The function will build the cache if not provided.
                batch_results, used_cache = find_all_strref_references(
                    source,
                    strrefs_to_find,
                    cache=cache,
                    logger=self.log_func,
                )

                # Store the (potentially newly built) cache for the next iteration
                if source.path() not in _global_strref_caches:
                    _global_strref_caches[source.path()] = used_cache

                # Process results for each StrRef
                for old_strref, new_token_id in strref_token_pairs:
                    if old_strref not in batch_results:
                        continue

                    search_results = batch_results[old_strref]

                    # Filter out resources from rims folder (game doesn't use them)
                    filtered_results = []
                    for search_result in search_results:
                        resource = search_result.resource
                        filepath = resource.filepath()
                        # Check if path contains "rims" folder (case-insensitive)
                        path_parts = [part.lower() for part in filepath.parts]
                        if "rims" not in path_parts:
                            filtered_results.append(search_result)

                    search_results = filtered_results
                    self.log_func(f"Found {len(search_results)} resource(s) referencing StrRef {old_strref}")

                    # Group results by resource identifier (resname.restype)
                    grouped_results: dict[str, list[StrRefSearchResult]] = {}
                    for search_result in search_results:
                        resource = search_result.resource
                        resource_id = resource.filename().lower()

                        if resource_id not in grouped_results:
                            grouped_results[resource_id] = []
                        grouped_results[resource_id].append(search_result)

                    # For each unique resource, pick the highest priority instance
                    # CRITICAL: All results in results_group come from the same installation (source)
                    # References are ALWAYS relevant to the installation they're found in
                    # We prioritize within a single installation only - never cross-installation
                    prioritized_results: list[StrRefSearchResult] = []
                    for resource_id, results_group in grouped_results.items():
                        if len(results_group) == 1:
                            prioritized_results.append(results_group[0])
                            continue
                        # Multiple instances within the SAME installation - pick highest priority
                        # All instances are from the same source installation, so prioritization
                        # is safe (Override > Modules > Chitin within that installation)
                        if isinstance(source, Installation):
                            installation_source = source  # Type narrowing
                            best_result: StrRefSearchResult = min(results_group, key=lambda r: self._get_resource_priority(r.resource, installation_source))
                            best_priority = self._get_resource_priority(best_result.resource, installation_source)
                            priority_names = ["Override", "Modules (.mod)", "Modules (.rim)", "Chitin BIFs"]
                            installation_path = installation_source.path()
                            self.log_func(f"  Multiple instances of {resource_id} found in {installation_path}, using {priority_names[best_priority]} version")
                        else:
                            # For Path sources, just use first result (priority not applicable)
                            best_result = results_group[0]
                        prioritized_results.append(best_result)

                    # Store references temporarily instead of creating patches IMMEDIATELY
                    # They will be applied when the file is actually diffed
                    for search_result in prioritized_results:
                        resource = search_result.resource
                        locations = search_result.locations  # Typed location objects!
                        resource_filename = resource.filename()

                        try:
                            filename = resource_filename.lower()
                            resource_identifier = resource.identifier()

                            # Get relative path for logging (using path_ident for BIF/capsule resources)
                            try:
                                path_ident = resource.path_ident()
                                relative_path = path_ident.relative_to(source.path())
                                rel_path_str = relative_path.as_posix()
                            except ValueError:
                                rel_path_str = str(resource.path_ident())

                            resname_ext = f"{resource_identifier.resname}.{resource_identifier.restype.extension}"
                            # Format path with installation folder prefix for clarity
                            formatted_path = self._format_path_with_source_prefix(rel_path_str, source)
                            self.log_func(f"  Resource: {formatted_path} ({resname_ext})")

                            # Store references temporarily instead of creating patches immediately
                            # Process each location based on its type - NO STRING PARSING!
                            for location in locations:
                                if isinstance(location, TwoDARefLocation):
                                    # Store 2DA reference for later
                                    self._store_pending_strref_reference(
                                        filename,
                                        source,
                                        old_strref,
                                        new_token_id,
                                        "2da",
                                        {"row_index": location.row_index, "column_name": location.column_name, "resource_path": rel_path_str},
                                    )
                                elif isinstance(location, SSFRefLocation):
                                    # Store SSF reference for later
                                    self._store_pending_strref_reference(
                                        filename,
                                        source,
                                        old_strref,
                                        new_token_id,
                                        "ssf",
                                        {"sound": location.sound},
                                    )
                                elif isinstance(location, GFFRefLocation):
                                    # Store GFF reference for later
                                    self._store_pending_strref_reference(
                                        filename,
                                        source,
                                        old_strref,
                                        new_token_id,
                                        "gff",
                                        {"field_path": location.field_path},
                                    )
                                # FIXME: TEMPORARILY DISABLED - NCS reference finding will be revisited later
                                # elif isinstance(location, NCSRefLocation):
                                #     # Store NCS reference for later
                                #     self._store_pending_strref_reference(
                                #         filename,
                                #         source,
                                #         old_strref,
                                #         new_token_id,
                                #         "ncs",
                                #         {"byte_offset": location.byte_offset},
                                #     )
                        except Exception as e:  # noqa: BLE001
                            _log_debug(f"Error processing StrRef reference: {e.__class__.__name__}: {e}")
                            import traceback

                            traceback.print_exc()
        else:
            self.log_func(f"[Warning] No source installations for TLK {mod_tlk.saveas}, cannot find StrRef references")

        # Write INI section
        self._write_to_ini([mod_tlk], "tlk")
        self.written_sections.add(filename)

        # Track in all_modifications (only if not already added)
        if mod_tlk not in self.all_modifications.tlk:
            self.all_modifications.tlk.append(mod_tlk)

    @staticmethod
    def _get_resource_priority(resource: FileResource, installation: Installation) -> int:
        """Get resource priority based on KOTOR resolution order.

        Returns priority (lower = higher priority):
        0 = Override (highest)
        1 = Modules (.mod)
        2 = Modules (.rim/_s.rim/_dlg.erf)
        3 = Chitin BIFs (lowest)
        """
        filepath = resource.filepath()
        parent_names_lower = [parent.name.lower() for parent in filepath.parents]

        if "override" in parent_names_lower:
            return 0
        if "modules" in parent_names_lower:
            name_lower = filepath.name.lower()
            if name_lower.endswith(".mod"):
                return 1
            return 2  # .rim/_s.rim/_dlg.erf
        if "data" in parent_names_lower or filepath.suffix.lower() == ".bif":
            return 3
        # Files directly in installation root treated as Override priority
        if filepath.parent == installation.path():
            return 0
        # Default to lowest priority if unknown
        return 3

    def _find_and_patch_single_strref(
        self,
        source: Installation | Path,
        strref: int,
        token_id: int,
    ) -> None:
        """Find ALL references to a SINGLE StrRef and create linking patches IMMEDIATELY.

        Only uses the highest priority resource when multiple instances exist,
        following KOTOR resource resolution order: Override > Modules > Chitin

        Args:
            source: Installation or Path where the StrRef came from
            strref: The single StrRef ID to find references for
            token_id: The token ID to use in linking patches
        """
        # If it's an Installation, use the dedicated function from talktable.py
        if isinstance(source, Installation):
            from pykotor.tools.reference_cache import (  # noqa: PLC0415
                GFFRefLocation,
                SSFRefLocation,
                TwoDARefLocation,
                find_strref_references,
            )

            self.log_func(f"Searching Installation for StrRef {strref}...")
            try:
                # Use the new function that returns COMPLETE typed location data
                search_results = find_strref_references(source, strref, logger=self.log_func)

                # Filter out resources from rims folder (game doesn't use them)
                filtered_results = []
                for search_result in search_results:
                    resource = search_result.resource
                    filepath = resource.filepath()
                    # Check if path contains "rims" folder (case-insensitive)
                    path_parts = [part.lower() for part in filepath.parts]
                    if "rims" not in path_parts:
                        filtered_results.append(search_result)

                search_results = filtered_results
                self.log_func(f"Found {len(search_results)} resource(s) referencing StrRef {strref}")

                grouped_results: dict[str, list[StrRefSearchResult]] = {}
                for search_result in search_results:
                    resource = search_result.resource
                    resource_id = resource.filename().lower()

                    if resource_id not in grouped_results:
                        grouped_results[resource_id] = []
                    grouped_results[resource_id].append(search_result)

                # For each unique resource, pick the highest priority instance
                prioritized_results: list[StrRefSearchResult] = []
                for resource_id, results_group in grouped_results.items():
                    if len(results_group) == 1:
                        prioritized_results.append(results_group[0])
                    else:
                        # Multiple instances - pick highest priority (lowest priority number)
                        best_result: StrRefSearchResult = min(results_group, key=lambda r: self._get_resource_priority(r.resource, source))
                        best_priority = self._get_resource_priority(best_result.resource, source)
                        priority_names = ["Override", "Modules (.mod)", "Modules (.rim)", "Chitin BIFs"]
                        self.log_func(f"  Multiple instances of {resource_id} found, using {priority_names[best_priority]} version")
                        prioritized_results.append(best_result)

                # Store references temporarily instead of creating patches IMMEDIATELY
                # They will be applied when the file is actually diffed
                for search_result in prioritized_results:
                    resource = search_result.resource
                    locations = search_result.locations  # Typed location objects!
                    resource_filename = resource.filename()

                    try:
                        filename = resource_filename.lower()
                        resource_identifier = resource.identifier()

                        # Get relative path for logging (using path_ident for BIF/capsule resources)
                        try:
                            path_ident = resource.path_ident()
                            relative_path = path_ident.relative_to(source.path())
                            rel_path_str = relative_path.as_posix()
                        except ValueError:
                            rel_path_str = str(resource.path_ident())

                        resname_ext = f"{resource_identifier.resname}.{resource_identifier.restype.extension}"
                        # Format path with installation folder prefix for clarity
                        formatted_path = self._format_path_with_source_prefix(rel_path_str, source)
                        self.log_func(f"  Resource: {formatted_path} ({resname_ext})")

                        # Store references temporarily instead of creating patches immediately
                        # Process each location based on its type - NO STRING PARSING!
                        for location in locations:
                            if isinstance(location, TwoDARefLocation):
                                # Store 2DA reference for later
                                self._store_pending_strref_reference(
                                    filename,
                                    source,
                                    strref,
                                    token_id,
                                    "2da",
                                    {"row_index": location.row_index, "column_name": location.column_name, "resource_path": rel_path_str},
                                )
                            elif isinstance(location, SSFRefLocation):
                                # Store SSF reference for later
                                self._store_pending_strref_reference(
                                    filename,
                                    source,
                                    strref,
                                    token_id,
                                    "ssf",
                                    {"sound": location.sound},
                                )
                            elif isinstance(location, GFFRefLocation):
                                # Store GFF reference for later
                                self._store_pending_strref_reference(
                                    filename,
                                    source,
                                    strref,
                                    token_id,
                                    "gff",
                                    {"field_path": location.field_path},
                                )
                            # FIXME: TEMPORARILY DISABLED - NCS reference finding will be revisited later
                            # elif isinstance(location, NCSRefLocation):
                            #     # Store NCS reference for later
                            #     self._store_pending_strref_reference(
                            #         filename,
                            #         source,
                            #         strref,
                            #         token_id,
                            #         "ncs",
                            #         {"byte_offset": location.byte_offset},
                            #     )

                    except Exception as e:
                        self.log_func(f"[Warning] Error processing resource {resource_filename}: {e.__class__.__name__}: {e}")
                        self.log_func(traceback.format_exc())

            except Exception as e:
                self.log_func(f"[Error] Failed to search Installation: {e.__class__.__name__}: {e}")
                self.log_func(traceback.format_exc())

        elif isinstance(source, Path):
            # Path-based scanning is not supported with typed location objects
            # Only Installation-based scanning returns proper typed location data
            self.log_func(f"[Warning] Path-based StrRef searching not supported (only Installation): {source}")

    def _find_and_patch_2da_rows_batch(
        self,
        source: Installation,
        twoda_filename: str,
        targets: list[TwoDALinkTarget],
    ) -> None:
        """Find ALL references to multiple 2DA rows and create linking patches using batch processing.

        Args:
            source: Installation where the 2DA came from
            twoda_filename: Name of the 2DA file (e.g., "soundset.2da")
            targets: List of 2DA row targets to find references for
        """
        from pykotor.tools.reference_cache import TwoDAMemoryReferenceCache  # noqa: PLC0415

        # Build or use cache for batch processing
        cache = TwoDAMemoryReferenceCache(source.game())

        # Scan all GFF resources to build cache (only once)
        self.log_func(f"Building 2DA reference cache for {twoda_filename}...")
        resource_count = 0
        for resource in source:
            try:
                restype = resource.restype()
                if restype not in GFFContent.get_restypes():
                    continue

                data = resource.data()
                cache.scan_resource(resource, data)
                resource_count += 1
            except Exception:  # noqa: BLE001, S110, S112
                continue

        self.log_func(f"Cache built: scanned {resource_count} GFF resources")

        # Get the 2DA identifier for field mapping
        twoda_resname: str = twoda_filename.lower().replace(".2da", "")

        # Find which GFF fields reference this 2DA file
        reverse_mapping: dict[str, list[str]] = {}  # 2da_name -> [field_names]
        for field_name, resource_id in GFF_FIELD_TO_2DA_MAPPING.items():
            if resource_id.resname.lower() == twoda_resname:
                if twoda_resname not in reverse_mapping:
                    reverse_mapping[twoda_resname] = []
                reverse_mapping[twoda_resname].append(field_name)

        if twoda_resname not in reverse_mapping:
            self.log_func(f"  No known GFF fields reference {twoda_filename}")
            return

        field_names = reverse_mapping[twoda_resname]
        self.log_func(f"  Looking for fields: {', '.join(field_names)}")

        # Process each target using the cache
        for target in targets:
            row_index = target.row_index
            token_id = target.token_id

            # Get references from cache
            cache_results = cache.get_references(twoda_filename, row_index)

            self.log_func(f"Found {len(cache_results)} file(s) referencing {twoda_filename} row {row_index}")

            # Convert cache results to pending references
            for identifier, field_paths in cache_results:
                try:
                    # Find the resource
                    found_resource: FileResource | None = None
                    for res in source:
                        if res.identifier() == identifier:
                            found_resource = res
                            break

                    if found_resource is None:
                        continue

                    filename = f"{identifier.resname}.{identifier.restype.extension}".lower()

                    # Store reference temporarily instead of creating patches immediately
                    self._store_pending_2da_row_reference(
                        filename,
                        source,
                        twoda_filename,
                        row_index,
                        token_id,
                        field_paths,
                    )
                except Exception as e:  # noqa: BLE001
                    _log_debug(f"Error processing 2DA row reference: {e.__class__.__name__}: {e}")

    def _find_and_patch_single_2da_row(
        self,
        source: Installation | Path,
        twoda_filename: str,
        row_index: int,
        token_id: int,
    ) -> None:
        """Find ALL references to a SINGLE 2DA row and create linking patches IMMEDIATELY.

        Args:
            source: Installation or Path where the 2DA came from
            twoda_filename: Name of the 2DA file (e.g., "soundset.2da")
            row_index: The row index to find references for
            token_id: The 2DAMEMORY token ID to use in linking patches
        """
        # Get the 2DA identifier for field mapping
        twoda_resname = twoda_filename.lower().replace(".2da", "")

        # Find which GFF fields reference this 2DA file
        reverse_mapping: dict[str, list[str]] = {}  # 2da_name -> [field_names]
        for field_name, resource_id in GFF_FIELD_TO_2DA_MAPPING.items():
            if resource_id.resname.lower() == twoda_resname:
                if twoda_resname not in reverse_mapping:
                    reverse_mapping[twoda_resname] = []
                reverse_mapping[twoda_resname].append(field_name)

        if twoda_resname not in reverse_mapping:
            self.log_func(f"  No known GFF fields reference {twoda_filename}")
            return

        field_names = reverse_mapping[twoda_resname]
        self.log_func(f"  Looking for fields: {', '.join(field_names)}")

        # If Installation, scan all GFF files
        if isinstance(source, Installation):
            self.log_func(f"Searching Installation for references to {twoda_filename} row {row_index}...")
            found_count = 0

            for resource in source:
                try:
                    restype = resource.restype()
                    if restype not in GFFContent.get_restypes():
                        continue

                    data = resource.data()
                    filename = resource.filename().lower()

                    # Find field paths in this GFF that reference our row index
                    field_paths = self._find_2da_row_in_gff(data, field_names, row_index)
                    if field_paths:
                        # Store reference temporarily instead of creating patches immediately
                        self._store_pending_2da_row_reference(
                            filename,
                            source,
                            twoda_filename,
                            row_index,
                            token_id,
                            field_paths,
                        )
                        found_count += 1

                except Exception as e:
                    _log_debug(f"Error scanning resource for 2DA refs: {e.__class__.__name__}: {e}")

            self.log_func(f"Found {found_count} file(s) referencing {twoda_filename} row {row_index}")

        # If Path, scan directory/file
        elif isinstance(source, Path):
            self.log_func(f"Searching Path for references to {twoda_filename} row {row_index}...")
            found_count = 0

            if source.is_dir():
                for file_path in source.rglob("*"):
                    if file_path.is_file():
                        try:
                            restype = ResourceType.from_extension(file_path.suffix)
                            if restype not in GFFContent.get_restypes():
                                continue

                            data = file_path.read_bytes()
                            filename = file_path.name.lower()

                            field_paths = self._find_2da_row_in_gff(data, field_names, row_index)
                            if field_paths:
                                # Store reference temporarily instead of creating patches immediately
                                self._store_pending_2da_row_reference(
                                    filename,
                                    source,
                                    twoda_filename,
                                    row_index,
                                    token_id,
                                    field_paths,
                                )
                                found_count += 1

                        except Exception as e:
                            _log_debug(f"Error scanning file for 2DA refs: {e.__class__.__name__}: {e}")

            elif source.is_file():
                try:
                    restype = ResourceType.from_extension(source.suffix)
                    if restype in GFFContent.get_restypes():
                        data = source.read_bytes()
                        filename = source.name.lower()

                        field_paths = self._find_2da_row_in_gff(data, field_names, row_index)
                        if field_paths:
                            # Store reference temporarily instead of creating patches immediately
                            self._store_pending_2da_row_reference(
                                filename,
                                source,
                                twoda_filename,
                                row_index,
                                token_id,
                                field_paths,
                            )
                            found_count += 1
                except Exception as e:
                    self.log_func(f"[Warning] Error scanning file: {e.__class__.__name__}: {e}")

            self.log_func(f"Found {found_count} file(s) referencing {twoda_filename} row {row_index}")

    def _find_and_patch_single_2da_row_by_label(
        self,
        source: Installation | Path,
        twoda_filename: str,
        row_label: str,
        token_id: int,
    ) -> None:
        """Find references to a 2DA row by its label (for AddRow2DA)."""
        # For new rows (AddRow2DA), we need to first look up the row index in the source
        # by finding the row with the matching label
        self.log_func(f"  Looking up row index for label '{row_label}' in {twoda_filename}...")

        # Try to load the 2DA and find the row index
        row_index: int | None = None
        if isinstance(source, Installation):
            resource = source.resource(twoda_filename.replace(".2da", ""), ResourceType.TwoDA)
            if resource and resource.data:
                try:
                    twoda = read_2da(resource.data)
                    for idx in range(twoda.get_height()):
                        if twoda.get_row_label(idx) == row_label:
                            row_index = idx
                            break
                except Exception as e:
                    _log_debug(f"Error reading 2DA for label lookup: {e.__class__.__name__}: {e}")
        elif isinstance(source, Path):
            twoda_path = source / twoda_filename if source.is_dir() else source
            if twoda_path.exists():
                try:
                    data = twoda_path.read_bytes()
                    twoda = read_2da(data)
                    for idx in range(twoda.get_height()):
                        if twoda.get_row_label(idx) == row_label:
                            row_index = idx
                            break
                except Exception as e:
                    _log_debug(f"Error reading 2DA for label lookup: {e.__class__.__name__}: {e}")

        if row_index is None:
            self.log_func(f"  Could not find row with label '{row_label}' in {twoda_filename}")
            return

        self.log_func(f"  Found row index {row_index} for label '{row_label}'")
        # Now use the standard row index lookup
        self._find_and_patch_single_2da_row(source, twoda_filename, row_index, token_id)

    def _find_2da_row_in_gff(
        self,
        data: bytes,
        field_names: list[str],
        row_index: int,
    ) -> list[str]:
        """Find GFF field paths that reference a specific 2DA row index."""
        field_paths: list[str] = []
        try:
            gff = read_gff(data)
            self._scan_gff_for_2da_row(gff.root, field_names, row_index, "", field_paths)
        except Exception as e:
            _log_debug(f"Error reading GFF for 2DA row search: {e.__class__.__name__}: {e}")
        return field_paths

    def _scan_gff_for_2da_row(
        self,
        struct: GFFStruct,
        field_names: list[str],
        row_index: int,
        path_prefix: str,
        field_paths: list[str],
    ) -> None:
        """Recursively scan GFF for fields that reference a specific 2DA row."""
        for field_label, field_type, field_value in struct:
            field_path = f"{path_prefix}.{field_label}" if path_prefix else field_label

            try:
                # Check if this field name matches one we're looking for
                if field_label in field_names and isinstance(field_value, int) and field_value == row_index:
                    field_paths.append(field_path)

                # Recurse into structs and lists
                if field_type == GFFFieldType.Struct:
                    assert isinstance(field_value, GFFStruct), f"Expected GFFStruct, got {type(field_value).__name__}"
                    self._scan_gff_for_2da_row(field_value, field_names, row_index, field_path, field_paths)
                elif field_type == GFFFieldType.List:
                    assert isinstance(field_value, GFFList), f"Expected GFFList, got {type(field_value).__name__}"
                    for idx, list_struct in enumerate(field_value):
                        assert isinstance(list_struct, GFFStruct), f"Expected GFFStruct, got {type(list_struct).__name__}"
                        list_path = f"{field_path}[{idx}]"
                        self._scan_gff_for_2da_row(list_struct, field_names, row_index, list_path, field_paths)

            except Exception as e:
                _log_debug(f"Error scanning GFF field for 2DA row: {e.__class__.__name__}: {e}")

    def _create_immediate_gff_2da_patches(
        self,
        gff_filename: str,
        field_paths: list[str],
        token_id: int,
    ) -> None:
        """Create GFF patches that replace 2DA row references with 2DAMEMORY tokens.

        DEPRECATED: This method is kept for backward compatibility but should not be used.
        Use _create_gff_2da_patch instead, which properly handles deferred application.
        """
        # Redirect to the new method (without modification parameter for backward compatibility)
        self._create_gff_2da_patch(gff_filename, field_paths, token_id, None)

    def _find_strref_locations_in_2da(
        self,
        data: bytes,
        strref: int,
    ) -> list[str]:
        """Find specific cell locations in a 2DA file that contain the StrRef."""
        locations = []
        try:
            twoda = read_2da(data)
            self.log_func(f"    [DEBUG] Scanning 2DA: {twoda.get_height()} rows, {len(twoda.get_labels())} columns")
            for row_idx in range(twoda.get_height()):
                for col_label in twoda.get_labels():
                    try:
                        cell_value = twoda.get_cell(row_idx, col_label)
                        if cell_value and cell_value.strip().isdigit() and int(cell_value) == strref:
                            self.log_func(f"    [DEBUG] Found match: row {row_idx}, column '{col_label}', value='{cell_value}', strref={strref}")
                            locations.append(f"row_{row_idx}.{col_label}")
                    except Exception as e:
                        self.log_func(f"    [DEBUG] Error scanning 2DA cell [{row_idx}][{col_label}]: {e.__class__.__name__}: {e}")
            self.log_func(f"    [DEBUG] _find_strref_locations_in_2da found {len(locations)} locations for StrRef {strref}")
        except Exception as e:
            self.log_func(f"    [DEBUG] Error reading 2DA: {e.__class__.__name__}: {e}")
            self.log_func(traceback.format_exc())
        return locations

    def _find_strref_locations_in_ssf(
        self,
        data: bytes,
        strref: int,
    ) -> list[str]:
        """Find specific sound slots in an SSF file that contain the StrRef."""
        locations = []
        try:
            ssf = read_ssf(data)
            for sound in SSFSound:
                sound_strref = ssf.get(sound)
                if sound_strref == strref:
                    locations.append(f"sound_{sound.name}")
        except Exception as e:
            _log_debug(f"Error reading SSF: {e.__class__.__name__}: {e}")
        return locations

    def _find_strref_locations_in_gff(
        self,
        data: bytes,
        strref: int,
    ) -> list[str]:
        """Find specific field paths in a GFF file that contain the StrRef."""
        locations: list[str] = []
        try:
            gff = read_gff(data)
            self._scan_gff_for_single_strref(gff.root, strref, "", locations)
        except Exception as e:
            _log_debug(f"Error reading GFF: {e.__class__.__name__}: {e}")
        return locations

    def _find_strref_offsets_in_ncs(
        self,
        resource: FileResource,
        strref: int,
    ) -> list[int]:
        """Find byte offsets of all CONSTI instructions in an NCS file that contain the StrRef.

        Returns list of byte offsets where the 4-byte integer value starts
        (i.e., offset + 2 from instruction start).

        FIXME: TEMPORARILY DISABLED - Will revisit NCS scanning later.
        """
        # FIXME: TEMPORARILY DISABLED - NCS scanning will be revisited later
        return []
        # from pykotor.common.stream import BinaryReader
        #
        # offsets: list[int] = []
        # try:
        #     ncs_data = resource.data()
        #     with BinaryReader.from_auto(ncs_data) as reader:
        #         # Skip NCS header (13 bytes)
        #         if reader.read_string(4) != "NCS ":
        #             return offsets
        #         if reader.read_string(4) != "V1.0":
        #             return offsets
        #         magic_byte = reader.read_uint8()
        #         if magic_byte != 0x42:  # noqa: PLR2004
        #             return offsets
        #         total_size = reader.read_uint32(big=True)
        #
        #         # Now read instructions and track offsets
        #         while reader.position() < total_size and reader.remaining() > 0:
        #             opcode = reader.read_uint8()
        #             qualifier = reader.read_uint8()
        #
        #             # Check if this is CONSTI (opcode=0x04, qualifier=0x03)
        #             if opcode == 0x04 and qualifier == 0x03:  # CONSTI  # noqa: PLR2004
        #                 value_offset = reader.position()  # Current position is where the 4-byte value starts
        #                 const_value = reader.read_int32(big=True)
        #                 if const_value == strref:
        #                     offsets.append(value_offset)
        #             # Skip to next instruction based on opcode/qualifier
        #             elif opcode == 0x04:  # CONSTx  # noqa: PLR2004
        #                 if qualifier == 0x04:  # CONSTF  # noqa: PLR2004
        #                     reader.skip(4)
        #                 elif qualifier == 0x05:  # CONSTS  # noqa: PLR2004
        #                     str_len = reader.read_uint16(big=True)
        #                     reader.skip(str_len)
        #                 elif qualifier == 0x06:  # CONSTO  # noqa: PLR2004
        #                     reader.skip(4)
        #             elif opcode in (0x01, 0x03, 0x26, 0x27):  # CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP
        #                 reader.skip(6)
        #             elif opcode == 0x2C:  # STORE_STATE  # noqa: PLR2004
        #                 reader.skip(8)
        #             elif opcode in (0x1B, 0x1D, 0x1E, 0x1F, 0x23, 0x24, 0x25, 0x28, 0x29):  # MOVSP, jumps, inc/dec
        #                 reader.skip(4)
        #             elif opcode == 0x05:  # ACTION  # noqa: PLR2004
        #                 reader.skip(3)
        #             elif opcode == 0x21:  # DESTRUCT  # noqa: PLR2004
        #                 reader.skip(6)
        #             elif opcode == 0x0B and qualifier == 0x24:  # EQUALTT  # noqa: PLR2004
        #                 reader.skip(2)
        #             elif opcode == 0x0C and qualifier == 0x24:  # NEQUALTT  # noqa: PLR2004
        #                 reader.skip(2)
        #             # Other instructions have no additional data
        # except Exception as e:  # noqa: BLE001
        #     _log_debug(f"Error reading NCS for StrRef offsets: {e.__class__.__name__}: {e}")
        # return offsets

    def _scan_gff_for_single_strref(
        self,
        struct: GFFStruct,
        strref: int,
        path_prefix: str,
        locations: list[str],
    ) -> None:
        """Recursively scan GFF struct for a single StrRef."""
        field_label: str
        field_type: GFFFieldType
        field_value: int | str | ResRef | Vector3 | Vector4 | LocalizedString | GFFStruct | GFFList | bytes | float
        for field_label, field_type, field_value in struct:
            field_path = f"{path_prefix}.{field_label}" if path_prefix else field_label

            try:
                # LocalizedString fields
                if field_type == GFFFieldType.LocalizedString and isinstance(field_value, LocalizedString) and field_value.stringref == strref:
                    locations.append(field_path)
            except Exception as e:
                _log_debug(f"Error scanning GFF field {field_path}: {e.__class__.__name__}: {e}")

    # REMOVED: _scan_resource_for_strrefs and _scan_gff_struct_for_strrefs
    # These were batch/multi-strref scanners, no longer used
    # Now using single-strref variants: _find_strref_locations_in_*

    def _store_pending_strref_reference(
        self,
        filename: str,
        source_path: Installation | Path,
        old_strref: int,
        token_id: int,
        location_type: str,
        location_data: dict[str, Any],
    ) -> None:
        """Store a StrRef reference temporarily until the file is diffed.

        Args:
            filename: Resource filename (lowercase)
            source_path: Installation or Path where the StrRef was found
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            location_type: Type of location ("2da", "ssf", "gff", "ncs")
            location_data: Location-specific data
        """
        if filename not in self._pending_strref_references:
            self._pending_strref_references[filename] = []

        pending_ref = PendingStrRefReference(
            filename=filename,
            source_path=source_path,
            old_strref=old_strref,
            token_id=token_id,
            location_type=location_type,
            location_data=location_data,
        )
        self._pending_strref_references[filename].append(pending_ref)
        self.log_func(f"    Stored pending StrRef reference: {filename} ({location_type}) -> Token {token_id}")

    def _apply_pending_strref_references(
        self,
        filename: str,
        modification: PatcherModifications,
        source_data: bytes | None,
        source_path: Installation | Path | None = None,
    ) -> None:
        """Check and apply pending StrRef references for a file being diffed.

        Only applies references if:
        - The file matches the pending reference filename
        - AND it comes from the same path as where the StrRef was found
        - AND the StrRef still exists at the expected location in the source data

        References are only relevant to the path they're from.

        Args:
            filename: The filename being diffed (lowercase)
            modification: The modification object being written
            source_data: Optional source data to verify StrRef still exists
            source_path: Optional path where this file is coming from
        """
        if filename not in self._pending_strref_references:
            return

        pending_refs = self._pending_strref_references[filename]
        if not pending_refs:
            return

        applied_refs: list[PendingStrRefReference] = []
        for pending_ref in pending_refs:
            # Only apply references if they come from the same path
            # References are only relevant to the path they're from
            should_apply = False

            if source_path is None:
                # If source_path is None, we can't verify the path match, so don't apply
                continue

            # Check if paths match exactly
            if isinstance(pending_ref.source_path, Installation) and isinstance(source_path, Installation):
                should_apply = pending_ref.source_path.path() == source_path.path()
            elif isinstance(pending_ref.source_path, Path) and isinstance(source_path, Path):
                should_apply = pending_ref.source_path == source_path
            else:
                should_apply = False

            # Also verify the StrRef still exists at the expected location in the source data
            if should_apply and source_data is not None:
                should_apply = self._verify_strref_location(source_data, pending_ref)

            if not should_apply:
                continue

            # Apply the reference to the modification object being written
            if pending_ref.location_type == "2da":
                self._create_immediate_2da_strref_patch_single(
                    filename,
                    pending_ref.old_strref,
                    pending_ref.token_id,
                    pending_ref.location_data["row_index"],
                    pending_ref.location_data["column_name"],
                    pending_ref.location_data.get("resource_path"),
                    modification,  # Pass the modification object being written
                )
            elif pending_ref.location_type == "ssf":
                self._create_immediate_ssf_strref_patch_single(
                    filename,
                    pending_ref.old_strref,
                    pending_ref.token_id,
                    pending_ref.location_data["sound"],
                    modification,  # Pass the modification object being written
                )
            elif pending_ref.location_type == "gff":
                self._create_immediate_gff_strref_patch_single(
                    filename,
                    pending_ref.old_strref,
                    pending_ref.token_id,
                    pending_ref.location_data["field_path"],
                    modification,  # Pass the modification object being written
                )
            # FIXME: TEMPORARILY DISABLED - NCS reference finding will be revisited later
            # elif pending_ref.location_type == "ncs":
            #     self._create_immediate_ncs_strref_patch_single(
            #         filename,
            #         pending_ref.old_strref,
            #         pending_ref.token_id,
            #         pending_ref.location_data["byte_offset"],
            #         modification,  # Pass the modification object being written
            #     )
            applied_refs.append(pending_ref)

        # Remove applied references
        for applied_ref in applied_refs:
            pending_refs.remove(applied_ref)
        if not pending_refs:
            del self._pending_strref_references[filename]

    def _verify_strref_location(
        self,
        data: bytes,
        pending_ref: PendingStrRefReference,
    ) -> bool:
        """Verify that a StrRef still exists at the expected location in the data.

        Args:
            data: The file data to check
            pending_ref: The pending StrRef reference

        Returns:
            True if the StrRef exists at the expected location, False otherwise
        """
        try:
            if pending_ref.location_type == "2da":
                twoda = read_2da(data)
                row_index = pending_ref.location_data["row_index"]
                column_name = pending_ref.location_data["column_name"]
                cell_value = twoda.get_cell(row_index, column_name)
                if cell_value and cell_value.strip().isdigit():
                    return int(cell_value.strip()) == pending_ref.old_strref
                return False

            if pending_ref.location_type == "ssf":
                ssf = read_ssf(data)
                sound = pending_ref.location_data["sound"]
                return ssf.get(sound) == pending_ref.old_strref

            if pending_ref.location_type == "gff":
                gff_obj = read_gff(data)
                field_path = pending_ref.location_data["field_path"]
                # Navigate to the field path and check if it has the StrRef
                return self._check_gff_field_strref(gff_obj.root, field_path, pending_ref.old_strref)

            # FIXME: TEMPORARILY DISABLED - NCS reference finding will be revisited later
            # if pending_ref.location_type == "ncs":
            #     # For NCS, check if the byte offset still contains the StrRef
            #     from pykotor.common.stream import BinaryReader
            #
            #     with BinaryReader.from_auto(data) as reader:
            #         reader.seek(pending_ref.location_data["byte_offset"])
            #         value = reader.read_int32(big=True)
            #         return value == pending_ref.old_strref

        except Exception as e:  # noqa: BLE001
            _log_debug(f"Error verifying StrRef location: {e.__class__.__name__}: {e}")
            return False

        return False

    def _check_gff_field_strref(
        self,
        struct: GFFStruct,
        field_path: str,
        strref: int,
    ) -> bool:
        """Check if a GFF field at the given path contains the StrRef.

        Args:
            struct: The GFF struct to search
            field_path: The field path (e.g., "FirstName", "ItemList[0].LocalizedName")
            strref: The StrRef value to check for

        Returns:
            True if the field contains the StrRef, False otherwise
        """
        from pykotor.common.language import LocalizedString
        from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFList

        # Parse field path (handle array indices)
        parts = field_path.split(".")
        current = struct

        for i, part in enumerate(parts):
            if "[" in part and "]" in part:
                # Array access like "ItemList[0]"
                field_label = part[: part.index("[")]
                index = int(part[part.index("[") + 1 : part.index("]")])
                # Get the field from current struct
                for field_label_check, field_type, field_value in current:
                    if field_label_check == field_label and field_type == GFFFieldType.List and isinstance(field_value, GFFList):
                        if index < len(field_value):
                            current = field_value[index]
                            break
                        return False
                else:
                    return False
            # Regular field access
            if i == len(parts) - 1:
                # Last part - check if it has the StrRef
                for field_label_check, field_type, field_value in current:
                    if field_label_check == part:
                        if field_type == GFFFieldType.LocalizedString and isinstance(field_value, LocalizedString):
                            return field_value.stringref == strref
                        return False
                return False

            # Not the last part - navigate deeper
            for field_label_check, field_type, field_value in current:
                if field_label_check == part:
                    if field_type == GFFFieldType.Struct and isinstance(field_value, GFFStruct):
                        current = field_value
                        break
                    return False
            else:
                return False

        return False

    def _store_pending_2da_row_reference(
        self,
        gff_filename: str,
        source_path: Installation | Path,
        twoda_filename: str,
        row_index: int,
        token_id: int,
        field_paths: list[str],
    ) -> None:
        """Store a 2DA row reference temporarily until the GFF file is diffed.

        Args:
            gff_filename: GFF resource filename (lowercase)
            source_path: Installation or Path where the 2DA row reference was found
            twoda_filename: The 2DA filename (e.g., "appearance.2da")
            row_index: The 2DA row index being referenced
            token_id: The 2DAMEMORY token ID to use
            field_paths: List of GFF field paths that reference this row
        """
        if gff_filename not in self._pending_2da_row_references:
            self._pending_2da_row_references[gff_filename] = []

        pending_ref = Pending2DARowReference(
            gff_filename=gff_filename,
            source_path=source_path,
            twoda_filename=twoda_filename,
            row_index=row_index,
            token_id=token_id,
            field_paths=field_paths,
        )
        self._pending_2da_row_references[gff_filename].append(pending_ref)
        self.log_func(f"    Stored pending 2DA row reference: {gff_filename} -> {twoda_filename} row {row_index} = 2DAMEMORY{token_id} ({len(field_paths)} field(s))")

    def _apply_pending_2da_row_references(
        self,
        gff_filename: str,
        modification: PatcherModifications,
        source_data: bytes | None,
        source_path: Installation | Path | None = None,
    ) -> None:
        """Check and apply pending 2DA row references for a GFF file being diffed.

        Only applies references if:
        - The GFF file matches the pending reference filename
        - AND it comes from the same path as where the 2DA row reference was found
        - AND the 2DA row still exists at the expected location in the source data

        References are only relevant to the path they're from.

        Args:
            gff_filename: The GFF filename being diffed (lowercase)
            modification: The GFF modification object being written
            source_data: Optional source data to verify 2DA row still exists
            source_path: Optional path where this file is coming from
        """
        if gff_filename not in self._pending_2da_row_references:
            return

        pending_refs = self._pending_2da_row_references[gff_filename]
        if not pending_refs:
            return

        applied_refs: list[Pending2DARowReference] = []
        for pending_ref in pending_refs:
            # Only apply references if they come from the same path
            # References are only relevant to the path they're from
            should_apply = False

            if source_path is None:
                # If source_path is None, we can't verify the path match, so don't apply
                continue

            # Check if paths match exactly
            if isinstance(pending_ref.source_path, Installation) and isinstance(source_path, Installation):
                should_apply = pending_ref.source_path.path() == source_path.path()
            elif isinstance(pending_ref.source_path, Path) and isinstance(source_path, Path):
                should_apply = pending_ref.source_path == source_path
            else:
                should_apply = False

            # Also verify the 2DA row still exists at the expected location in the source data
            if should_apply and source_data is not None:
                should_apply = self._verify_2da_row_location(source_data, pending_ref)

            if not should_apply:
                continue

            # Apply the reference to the modification object being written
            self._create_gff_2da_patch(
                gff_filename,
                pending_ref.field_paths,
                pending_ref.token_id,
                modification,  # Pass the modification object being written
            )
            applied_refs.append(pending_ref)

        # Remove applied references
        for applied_ref in applied_refs:
            pending_refs.remove(applied_ref)
        if not pending_refs:
            del self._pending_2da_row_references[gff_filename]

    def _verify_2da_row_location(
        self,
        data: bytes,
        pending_ref: Pending2DARowReference,
    ) -> bool:
        """Verify that a 2DA row reference still exists at the expected locations in the GFF data.

        Args:
            data: The GFF file data to check
            pending_ref: The pending 2DA row reference

        Returns:
            True if the 2DA row reference exists at all expected field paths, False otherwise
        """
        try:
            gff_obj = read_gff(data)
            # Get the field names that should reference this 2DA file
            twoda_resname = pending_ref.twoda_filename.lower().replace(".2da", "")
            relevant_field_names: list[str] = []
            for field_name, resource_id in GFF_FIELD_TO_2DA_MAPPING.items():
                if resource_id.resname.lower() == twoda_resname:
                    relevant_field_names.append(field_name)

            # Verify all field paths in the pending reference still have the row index
            return all(self._check_gff_field_2da_row(gff_obj.root, field_path, pending_ref.row_index, relevant_field_names) for field_path in pending_ref.field_paths)

        except Exception as e:  # noqa: BLE001
            _log_debug(f"Error verifying 2DA row location: {e.__class__.__name__}: {e}")
            return False

    def _check_gff_field_2da_row(
        self,
        struct: GFFStruct,
        field_path: str,
        row_index: int,
        relevant_field_names: list[str],
    ) -> bool:
        """Check if a GFF field at the given path contains the 2DA row index.

        Args:
            struct: The GFF struct to search
            field_path: The field path (e.g., "Appearance_Type", "PropertiesList[0].Subtype")
            row_index: The 2DA row index value to check for
            relevant_field_names: List of field names that should reference this 2DA

        Returns:
            True if the field contains the row index, False otherwise
        """
        from pykotor.resource.formats.gff.gff_data import GFFFieldType, GFFList

        # Parse field path (handle array indices)
        parts = field_path.split(".")
        current = struct

        for i, part in enumerate(parts):
            if "[" in part and "]" in part:
                # Array access like "ItemList[0]"
                field_label = part[: part.index("[")]
                index = int(part[part.index("[") + 1 : part.index("]")])
                # Get the field from current struct
                for field_label_check, field_type, field_value in current:
                    if field_label_check == field_label and field_type == GFFFieldType.List and isinstance(field_value, GFFList):
                        if index < len(field_value):
                            current = field_value[index]
                            break
                        return False
                else:
                    return False
            # Regular field access
            if i == len(parts) - 1:
                # Last part - check if it has the row index
                for field_label_check, _field_type, field_value in current:
                    if field_label_check == part:
                        # Check if this field name is relevant and has the correct row index
                        if field_label_check in relevant_field_names and isinstance(field_value, int):
                            return field_value == row_index
                        return False
                return False

            # Not the last part - navigate deeper
            for field_label_check, field_type, field_value in current:
                if field_label_check == part:
                    if field_type == GFFFieldType.Struct and isinstance(field_value, GFFStruct):
                        current = field_value
                        break
                    return False
            else:
                return False

        return False

    def _create_gff_2da_patch(
        self,
        gff_filename: str,
        field_paths: list[str],
        token_id: int,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create GFF patches that replace 2DA row references with 2DAMEMORY tokens.

        Args:
            gff_filename: GFF filename
            field_paths: List of GFF field paths that reference the 2DA row
            token_id: The 2DAMEMORY token ID to use
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, ModificationsGFF) and modification.sourcefile.lower() == gff_filename.lower():
            existing_mod = modification
            is_new = existing_mod.sourcefile not in self.written_sections
        else:
            # Find or create ModificationsGFF from all_modifications
            found_mod = next((m for m in self.all_modifications.gff if m.sourcefile == gff_filename), None)
            is_new = found_mod is None

            if found_mod is None:
                existing_mod = ModificationsGFF(gff_filename, replace=False, modifiers=[])
                self.all_modifications.gff.append(existing_mod)
            else:
                existing_mod = found_mod

        # Create ModifyFieldGFF entries for each field path
        for field_path in field_paths:
            # Create a FieldValue2DAMemory value
            field_value = FieldValue2DAMemory(token_id)

            modifier = ModifyFieldGFF(field_path, field_value)
            existing_mod.modifiers.append(modifier)

            self.log_func(f"    Creating patch: {gff_filename} -> {field_path} = 2DAMEMORY{token_id}")

        # Allocate ListIndex tokens if needed before writing
        self._allocate_listindex_tokens_for_gff(existing_mod)

        # Write to changes.ini
        if is_new:
            self._write_gff_modification(existing_mod, None)
            return

        # Re-append to update existing section
        if existing_mod.sourcefile in self.written_sections:
            self.written_sections.discard(existing_mod.sourcefile)
        self._write_to_ini([existing_mod], "gff")
        self.written_sections.add(existing_mod.sourcefile)

    def _create_immediate_2da_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        row_index: int,
        column_name: str,
        resource_path: str | None = None,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single 2DA patch for a StrRef reference immediately.

        Args:
            filename: 2DA filename (e.g., "planetary.2da")
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            row_index: The row index containing the reference
            column_name: The column name containing the reference
            resource_path: Optional path for logging
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        from pykotor.tslpatcher.mods.twoda import (
            ChangeRow2DA,
            Modifications2DA,
            Target,
            TargetType,
        )

        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, Modifications2DA) and modification.sourcefile.lower() == filename.lower():
            existing_mod = modification
            is_new_mod = existing_mod.sourcefile not in self.written_sections
        else:
            # Get or create 2DA modification from all_modifications
            found_mod = next((m for m in self.all_modifications.twoda if m.sourcefile == filename), None)
            is_new_mod = found_mod is None

            if found_mod is None:
                existing_mod = Modifications2DA(filename)
                self.all_modifications.twoda.append(existing_mod)
            else:
                existing_mod = found_mod

        # Create the patch
        change_row = ChangeRow2DA(
            identifier=f"strref_link_{old_strref}_{row_index}_{column_name}",
            target=Target(TargetType.ROW_INDEX, row_index),
            cells={column_name: RowValueTLKMemory(token_id)},
        )
        existing_mod.modifiers.append(change_row)

        # Log the patch being created
        path_info = f" at {resource_path}" if resource_path else ""
        self.log_func(f"    Creating patch: row {row_index}, column '{column_name}' -> Token {token_id}{path_info}")

        # Write to INI
        if is_new_mod:
            self._write_2da_modification(existing_mod, None)
        else:
            self.written_sections.discard(filename)
            self._write_to_ini([existing_mod], "2da")
            self.written_sections.add(filename)

    def _create_immediate_ssf_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        sound: SSFSound,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single SSF patch for a StrRef reference immediately.

        Args:
            filename: SSF filename
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            sound: The SSFSound enum identifying the sound slot
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        from pykotor.tslpatcher.memory import TokenUsageTLK  # noqa: PLC0415
        from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF  # noqa: PLC0415

        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, ModificationsSSF) and modification.sourcefile.lower() == filename.lower():
            existing_mod = modification
            is_new_mod = existing_mod.sourcefile not in self.written_sections
        else:
            # Get or create SSF modification from all_modifications
            found_mod = next((m for m in self.all_modifications.ssf if m.sourcefile == filename), None)
            is_new_mod = found_mod is None

            if found_mod is None:
                existing_mod = ModificationsSSF(filename, replace=False, modifiers=[])
                self.all_modifications.ssf.append(existing_mod)
            else:
                existing_mod = found_mod

        # Create the patch
        modify_ssf = ModifySSF(sound, TokenUsageTLK(token_id))
        existing_mod.modifiers.append(modify_ssf)

        self.log_func(f"    Creating patch: sound '{sound.name}' -> Token {token_id}")

        # Write to INI
        if is_new_mod:
            self._write_ssf_modification(existing_mod, None)
        else:
            self.written_sections.discard(filename)
            self._write_to_ini([existing_mod], "ssf")
            self.written_sections.add(filename)

    def _create_immediate_gff_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        field_path: str,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single GFF patch for a StrRef reference immediately.

        Args:
            filename: GFF filename
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            field_path: The GFF field path (e.g., "FirstName", "ItemList[0].LocalizedName")
            modification: Optional modification object to add to (if provided, use this instead of searching)
        """
        from pykotor.tslpatcher.mods.gff import FieldValueTLKMemory, LocalizedStringDelta, ModificationsGFF, ModifyFieldGFF

        # Use the provided modification if it matches, otherwise find or create one
        if modification is not None and isinstance(modification, ModificationsGFF) and modification.sourcefile.lower() == filename.lower():
            existing_mod = modification
            is_new_mod = existing_mod.sourcefile not in self.written_sections
        else:
            # Get or create GFF modification from all_modifications
            found_mod = next((m for m in self.all_modifications.gff if m.sourcefile == filename), None)
            is_new_mod = found_mod is None

            if found_mod is None:
                existing_mod = ModificationsGFF(filename, replace=False, modifiers=[])
                self.all_modifications.gff.append(existing_mod)
            else:
                existing_mod = found_mod

        # Create the patch
        locstring_delta = LocalizedStringDelta(FieldValueTLKMemory(token_id))
        modify_field = ModifyFieldGFF(field_path, FieldValueConstant(locstring_delta))
        existing_mod.modifiers.append(modify_field)

        self.log_func(f"    Creating patch: field '{field_path}' -> Token {token_id}")

        # Write to INI
        if is_new_mod:
            self._write_gff_modification(existing_mod, None)
        else:
            self.written_sections.discard(filename)
            self._write_to_ini([existing_mod], "gff")
            self.written_sections.add(filename)

    def _create_immediate_ncs_strref_patch_single(
        self,
        filename: str,
        old_strref: int,
        token_id: int,
        byte_offset: int,
        modification: PatcherModifications | None = None,
    ) -> None:
        """Create a single NCS HACKList patch for a StrRef reference immediately.

        Args:
            filename: NCS filename
            old_strref: The original StrRef value
            token_id: The TLKMEMORY token ID to use
            byte_offset: The byte offset where the StrRef constant is located
            modification: Optional modification object to add to (if provided, use this instead of searching)

        FIXME: TEMPORARILY DISABLED - Will revisit NCS scanning later.
        """
        # FIXME: TEMPORARILY DISABLED - NCS scanning will be revisited later
        return
        # # Use the provided modification if it matches, otherwise find or create one
        # if modification is not None and isinstance(modification, ModificationsNCS) and modification.sourcefile.lower() == filename.lower():
        #     existing_mod = modification
        #     is_new_mod = existing_mod.sourcefile not in self.written_sections
        # else:
        #     # Get or create NCS modification from all_modifications
        #     found_mod = next((m for m in self.all_modifications.ncs if m.sourcefile == filename), None)
        #     is_new_mod = found_mod is None
        #
        #     if found_mod is None:
        #         existing_mod = ModificationsNCS(filename, replace=False, modifiers=[])
        #         self.all_modifications.ncs.append(existing_mod)
        #     else:
        #         existing_mod = found_mod
        #
        # # Create the patch
        # # CONSTI instructions store 32-bit signed integers, so use STRREF32 token type
        # modify_ncs = ModifyNCS(
        #     token_type=NCSTokenType.STRREF32,
        #     offset=byte_offset,
        #     token_id_or_value=token_id,
        # )
        # existing_mod.modifiers.append(modify_ncs)
        #
        # self.log_func(f"    Creating patch: offset {byte_offset:#X} -> Token {token_id}")
        #
        # # Write to INI
        # if is_new_mod:
        #     self._write_ncs_modification(existing_mod, None)
        # else:
        #     self.written_sections.discard(filename)
        #     self._write_to_ini([existing_mod], "ncs")
        #     self.written_sections.add(filename)

    def _create_linking_patches_from_cache(
        self,
        mod_tlk: ModificationsTLK,
    ) -> None:
        """Create linking patches using the StrRef cache."""
        if not self.strref_cache:
            return

        strref_mappings: dict[int, int] = getattr(mod_tlk, "strref_mappings", {})
        if not strref_mappings:
            return

        self.log_func(f"\n=== Creating Linking Patches from Cache ({len(strref_mappings)} StrRefs) ===")

        for old_strref, token_id in strref_mappings.items():
            references = self.strref_cache.get_references(old_strref)

            if not references:
                continue

            self.log_func(f"  StrRef {old_strref} -> token {token_id}: {len(references)} file(s)")

            for identifier, locations in references:
                filename: str = f"{identifier.resname}.{identifier.restype.extension}".lower()
                restype: ResourceType = identifier.restype

                # 2DA files
                if restype is ResourceType.TwoDA:
                    existing_mod: Modifications2DA | None = next((m for m in self.all_modifications.twoda if m.sourcefile == filename), None)
                    is_new_mod: bool = existing_mod is None
                    if existing_mod is None:
                        existing_mod = Modifications2DA(filename)
                        # Write it immediately
                        self.all_modifications.twoda.append(existing_mod)
                        self._write_2da_modification(existing_mod, None)

                    for location in locations:
                        # Parse location: "row_N.column_name"
                        if location.startswith("row_"):
                            parts: list[str] = location.split(".")
                            row_idx_str: str = parts[0][4:]  # Remove "row_"
                            column_name: str = parts[1] if len(parts) > 1 else ""

                            if row_idx_str.isdigit():
                                row_idx: int = int(row_idx_str)
                                change_row = ChangeRow2DA(
                                    identifier=f"strref_link_{row_idx}_{column_name}",
                                    target=Target(TargetType.ROW_INDEX, row_idx),
                                    cells={column_name: RowValue2DAMemory(token_id)},
                                )
                                existing_mod.modifiers.append(change_row)

                    # Re-write INI section if we added modifiers to existing mod
                    if not is_new_mod and existing_mod.modifiers:
                        self.written_sections.discard(filename)
                        self._write_to_ini([existing_mod], "2da")
                        self.written_sections.add(filename)

                # SSF files
                elif restype is ResourceType.SSF:
                    existing_ssf_mod: ModificationsSSF | None = next((m for m in self.all_modifications.ssf if m.sourcefile == filename), None)
                    is_new_ssf_mod: bool = existing_ssf_mod is None
                    if existing_ssf_mod is None:
                        existing_ssf_mod = ModificationsSSF(filename, replace=False, modifiers=[])
                        self.all_modifications.ssf.append(existing_ssf_mod)
                        self._write_ssf_modification(existing_ssf_mod, None)

                    for location in locations:
                        # Parse location: "sound_SOUND_NAME"
                        if location.startswith("sound_"):
                            sound_name: str = location[6:]  # Remove "sound_"
                            try:
                                sound = SSFSound[sound_name]
                                modify_ssf = ModifySSF(sound, TokenUsageTLK(token_id))
                                existing_ssf_mod.modifiers.append(modify_ssf)
                            except KeyError:
                                _log_debug(f"Unknown SSF sound: {sound_name}")

                    # Re-write INI section if we added modifiers to existing mod
                    if not is_new_ssf_mod and existing_ssf_mod.modifiers:
                        self.written_sections.discard(filename)
                        self._write_to_ini([existing_ssf_mod], "ssf")
                        self.written_sections.add(filename)

                # GFF files
                else:
                    existing_gff_mod: ModificationsGFF | None = next((m for m in self.all_modifications.gff if m.sourcefile == filename), None)
                    is_new_gff_mod: bool = existing_gff_mod is None
                    if existing_gff_mod is None:
                        existing_gff_mod = ModificationsGFF(filename, replace=False, modifiers=[])
                        self.all_modifications.gff.append(existing_gff_mod)
                        self._write_gff_modification(existing_gff_mod, None)

                    for location in locations:
                        # Create LocalizedStringDelta with token
                        locstring_delta = LocalizedStringDelta(FieldValueTLKMemory(token_id))

                        modify_field = ModifyFieldGFF(
                            path=location.replace("/", "\\"),
                            value=FieldValueConstant(locstring_delta),
                            identifier=f"strref_link_{old_strref}_token_{token_id}",
                        )
                        existing_gff_mod.modifiers.append(modify_field)

                    # Re-write INI section if we added modifiers to existing mod
                    if not is_new_gff_mod and existing_gff_mod.modifiers:
                        self.written_sections.discard(filename)
                        self._write_to_ini([existing_gff_mod], "gff")
                        self.written_sections.add(filename)

        gff_count: int = len(self.all_modifications.gff)
        twoda_count: int = len(self.all_modifications.twoda)
        ssf_count: int = len(self.all_modifications.ssf)
        self.log_func(f"=== Linking Patches Created: {gff_count} GFF, {twoda_count} 2DA, {ssf_count} SSF ===")

    def _write_ssf_modification(
        self,
        mod_ssf: ModificationsSSF,
        source_data: bytes | None,
    ) -> None:
        """Write SSF resource file and INI section."""
        filename: str = mod_ssf.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written SSF: {filename}")
            return

        # Write resource file
        if source_data:
            output_path: Path = self.tslpatchdata_path / filename
            try:
                ssf_obj = read_ssf(source_data)
                write_ssf(ssf_obj, output_path, ResourceType.SSF)
                _log_verbose(f"Wrote SSF file: {filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to write SSF {filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return

        # Add to install folders
        self._add_to_install_folder("Override", filename)

        # Write INI section
        self._write_to_ini([mod_ssf], "ssf")
        self.written_sections.add(filename)

        # Track in all_modifications
        if mod_ssf not in self.all_modifications.ssf:
            self.all_modifications.ssf.append(mod_ssf)

    def _write_ncs_modification(
        self,
        mod_ncs: ModificationsNCS,
        source_data: bytes | None,
    ) -> None:
        """Write NCS resource file and INI section."""
        filename: str = mod_ncs.sourcefile

        # Skip if already written
        if filename in self.written_sections:
            _log_debug(f"Skipping already written NCS: {filename}")
            return

        # Write resource file (if needed)
        if source_data is not None:
            output_path: Path = self.tslpatchdata_path / filename
            output_path.write_bytes(source_data)
            _log_verbose(f"Wrote NCS file: {filename}")

        # Write INI section
        self._write_to_ini([mod_ncs], "ncs")
        self.written_sections.add(filename)

        # Track in all_modifications
        if mod_ncs not in self.all_modifications.ncs:
            self.all_modifications.ncs.append(mod_ncs)

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

    def _write_install_entry_to_ini(
        self,
        folder: str,
        filename: str,
    ) -> None:
        """Write a single InstallList entry to INI file in real-time."""
        # Normalize folder name
        dest_folder: str = folder if folder != "." else "Override"

        # Get or assign folder number
        is_new_folder: bool = dest_folder not in self.folder_numbers
        if is_new_folder:
            folder_num: int = self.next_folder_number
            self.folder_numbers[dest_folder] = folder_num
            self.next_folder_number += 1

            # Add install_folder#=folder line to [InstallList] section
            install_line = f"install_folder{folder_num}={self._format_ini_value(dest_folder)}"
            self._insert_into_section("[InstallList]", [install_line])

        folder_num = self.folder_numbers[dest_folder]
        folder_section: str = f"[install_folder{folder_num}]"

        # Get file number for this folder (0-indexed)
        if dest_folder not in self.install_folders:
            self.install_folders[dest_folder] = []
        file_index: int = len(self.install_folders[dest_folder])
        self.install_folders[dest_folder].append(filename)

        # Read file to find where to insert
        current_content: str = self.ini_path.read_text(encoding="utf-8")
        lines: list[str] = current_content.splitlines()

        # Find the folder section
        folder_section_idx: int | None = None
        for i, section_line in enumerate(lines):
            if section_line == folder_section:
                folder_section_idx = i
                break

        # Create folder section if it doesn't exist (only when first file is added)
        if folder_section_idx is None:
            self._insert_folder_section(folder_num, dest_folder)
            # Re-read to find the section
            current_content = self.ini_path.read_text(encoding="utf-8")
            lines = current_content.splitlines()
            for i, section_line in enumerate(lines):
                if section_line == folder_section:
                    folder_section_idx = i
                    break

        if folder_section_idx is None:
            self.log_func(f"[Error] Folder section {folder_section} not found after creation")
            return

        # Find insertion point in folder section (after header and any existing File#= lines)
        insert_idx: int = folder_section_idx + 1
        last_file_idx: int = folder_section_idx

        # Find where existing files end in this section
        for i in range(folder_section_idx + 1, len(lines)):
            file_line: str = lines[i].strip()
            # Stop at next section marker
            if file_line.startswith("[") and file_line.endswith("]") and file_line != folder_section:
                break
            # Check if this is a File#= line
            if file_line and not file_line.startswith(";") and file_line.startswith("File") and "=" in file_line:
                last_file_idx = i

        # Insert after the last file entry (or after section header if no files yet)
        insert_idx = last_file_idx + 1
        # Skip trailing blank lines before inserting
        while insert_idx < len(lines):
            line = lines[insert_idx].strip()
            if line.startswith("[") and line.endswith("]"):
                break
            if line and not line.startswith(";"):
                # Found content, insert after it
                insert_idx += 1
                continue
            # Blank line - check if next line is a section marker
            if insert_idx + 1 < len(lines) and lines[insert_idx + 1].strip().startswith("["):
                break
            insert_idx += 1

        # Insert File#=filename line
        file_line = f"File{file_index}={self._format_ini_value(filename)}"
        lines.insert(insert_idx, file_line)

        # Write back
        new_content: str = "\n".join(lines)
        if not new_content.endswith("\n"):
            new_content += "\n"
        self.ini_path.write_text(new_content, encoding="utf-8")
        _log_verbose(f"Added File{file_index}={filename} to {folder_section}")

    def _insert_folder_section(self, folder_num: int, dest_folder: str) -> None:
        """Insert a new [install_folder#] section after [InstallList]."""
        folder_section = f"[install_folder{folder_num}]"
        # Read file
        current_content: str = self.ini_path.read_text(encoding="utf-8")
        lines: list[str] = current_content.splitlines()

        # Find [InstallList] section end (where [2DAList] starts)
        install_list_idx: int | None = None
        twoda_list_idx: int | None = None

        for i, line in enumerate(lines):
            if line == "[InstallList]":
                install_list_idx = i
            elif line == "[2DAList]":
                twoda_list_idx = i
                break

        if install_list_idx is None:
            _log_debug("InstallList section not found, appending to end")
            lines.append("")
            lines.append(folder_section)
            lines.append("")
        else:
            # Insert before [2DAList] or at end if no 2DAList
            insert_idx = twoda_list_idx if twoda_list_idx is not None else len(lines)
            new_lines = ["", folder_section, ""]
            lines[insert_idx:insert_idx] = new_lines

        new_content = "\n".join(lines)
        if not new_content.endswith("\n"):
            new_content += "\n"
        self.ini_path.write_text(new_content, encoding="utf-8")
        _log_verbose(f"Created {folder_section} section")

    def _add_to_install_folder(
        self,
        folder: str,
        filename: str,
    ) -> None:
        """Add file to install folder tracking.

        The InstallList will be written when the INI file is rewritten.
        """
        if folder not in self.install_folders:
            self.install_folders[folder] = []
        if filename not in self.install_folders[folder]:
            self.install_folders[folder].append(filename)

    def add_install_file(
        self,
        folder: str,
        filename: str,
        source_path: Path | None = None,
    ) -> None:
        r"""Add a file to InstallList and copy it to tslpatchdata.

        Args:
            folder: Destination folder (e.g., "Override", "modules\\name.mod")
            filename: Filename to install
            source_path: Optional path to copy file from (can be capsule)
        """
        # Add to tracking
        self._add_to_install_folder(folder, filename)

        # Copy file if source provided
        if source_path is not None:
            # CRITICAL: ALL files go directly in tslpatchdata root, NOT in subdirectories
            # The folder parameter is only used in the INI to tell TSLPatcher where to install
            dest_path: Path = self.tslpatchdata_path / filename

            try:
                # Extract file data (may be from capsule or loose file)
                source_data: bytes | None = self._extract_file_data(source_path, filename)

                if source_data:
                    # Use appropriate io function based on extension
                    file_ext: str = PurePath(filename).suffix.lstrip(".").lower()
                    self._write_resource_with_io(source_data, dest_path, file_ext)
                    _log_verbose(f"Copied install file: {filename} -> {folder}")
                else:
                    self.log_func(f"[Warning] Could not extract data for install file: {filename}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to copy install file {filename}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")

    def _extract_file_data(
        self,
        source_path: Path,
        filename: str,
    ) -> bytes | None:
        """Extract file data from source (handles both loose files and capsules).

        Args:
            source_path: Source path (may be a capsule like danm13.mod)
            filename: Filename to extract (if source is capsule)

        Returns:
            File data bytes, or None if extraction failed
        """
        from pykotor.tools.misc import is_capsule_file  # noqa: PLC0415

        if source_path.is_file():
            # If the filename itself is the capsule, copy the entire file verbatim
            if filename.lower() == source_path.name.lower():
                return source_path.read_bytes()

            # If it's a loose file, just read it
            if not is_capsule_file(source_path.name):
                return source_path.read_bytes()

            # Otherwise extract the resource from the capsule
            try:
                capsule = Capsule(source_path)
                resref: str = PurePath(filename).stem
                res_ext: str = PurePath(filename).suffix.lstrip(".")

                for res in capsule:
                    if res.resname().lower() == resref.lower() and res.restype().extension.lower() == res_ext.lower():
                        return res.data()

                _log_debug(f"Resource {filename} not found in capsule {source_path.name}")
            except Exception as e:  # noqa: BLE001
                self.log_func(f"[Error] Failed to extract from capsule {source_path}: {e.__class__.__name__}: {e}")
                self.log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    self.log_func(f"  {line}")
                return None
            else:
                return None

        return None

    def _write_resource_with_io(
        self,
        data: bytes,
        dest_path: Path,
        file_ext: str,
    ) -> None:
        """Write resource using appropriate io function."""
        try:
            if file_ext.upper() in GFFContent.get_extensions():
                gff_obj = read_gff(data)
                write_gff(gff_obj, dest_path, ResourceType.from_extension(file_ext))
            elif file_ext == "2da":
                twoda_obj = read_2da(data)
                write_2da(twoda_obj, dest_path, ResourceType.TwoDA)
            elif file_ext == "tlk":
                tlk_obj = read_tlk(data)
                write_tlk(tlk_obj, dest_path, ResourceType.TLK)
            elif file_ext == "ssf":
                ssf_obj = read_ssf(data)
                write_ssf(ssf_obj, dest_path, ResourceType.SSF)
            elif file_ext == "lip":
                lip_obj = read_lip(data)
                write_lip(lip_obj, dest_path, ResourceType.LIP)
            else:
                # Binary file
                dest_path.write_bytes(data)
        except Exception as e:  # noqa: BLE001
            self.log_func(f"[Warning] Failed to use io function for {file_ext}, using binary write: {e.__class__.__name__}: {e}")
            self.log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                self.log_func(f"  {line}")
            dest_path.write_bytes(data)

    def _insert_into_section(self, section_marker: str, new_lines: list[str]) -> None:
        """Insert content into a specific section of the INI file.

        Args:
            section_marker: The section marker (e.g., "[TLKList]")
            new_lines: Lines to insert into the section
        """
        if not new_lines:
            return

        # Read current file content
        current_content: str = self.ini_path.read_text(encoding="utf-8")
        lines: list[str] = current_content.splitlines()

        # Find the section marker and the next section marker
        section_idx: int | None = None
        next_section_idx: int | None = None

        all_sections = ["[TLKList]", "[InstallList]", "[2DAList]", "[GFFList]", "[CompileList]", "[SSFList]", "[HACKList]"]
        current_section_pos = all_sections.index(section_marker)
        next_section_marker: str | None = all_sections[current_section_pos + 1] if current_section_pos + 1 < len(all_sections) else None

        for i, line in enumerate(lines):
            if line == section_marker:
                section_idx = i
            elif next_section_marker and line == next_section_marker:
                next_section_idx = i
                break

        if section_idx is None:
            _log_debug(f"Section marker {section_marker} not found, appending to end")
            # Fallback: append to end
            content_to_add = "\n".join(new_lines) + "\n"
            with self.ini_path.open("a", encoding="utf-8") as f:
                f.write(content_to_add)
            return

        # Special handling for [InstallList]: skip over [install_folder#] sections
        if section_marker == "[InstallList]":
            # Find the last line in [InstallList] before any [install_folder#] or [2DAList] sections
            insert_idx = section_idx + 1
            last_content_idx = section_idx
            # Find the last actual content line (install_folder#=...) in InstallList
            for i in range(section_idx + 1, len(lines)):
                line = lines[i].strip()
                if line.startswith("[") and line.endswith("]"):
                    # Hit a section marker - stop here
                    if line == "[2DAList]":
                        next_section_idx = i
                    break
                if line and not line.startswith(";") and "=" in line:
                    # This is a content line (install_folder#=...)
                    last_content_idx = i
            # Insert after the last content line, before any [install_folder#] sections
            insert_idx = last_content_idx + 1
            # Remove any trailing blank lines before inserting (but keep section marker spacing)
            # We want no blank lines between install_folder entries
            while insert_idx < len(lines):
                line = lines[insert_idx].strip()
                if line.startswith("[") and line.endswith("]"):
                    break
                if line and not line.startswith(";"):
                    # Found content - insert before it
                    break
                # Skip blank lines or comments
                insert_idx += 1
        elif next_section_idx is not None:
            # Find the last non-empty line in current section (before next section)
            insert_idx = next_section_idx - 1
            # Skip blank lines/comments at end of section
            while insert_idx > section_idx and (lines[insert_idx].strip() == "" or lines[insert_idx].strip().startswith(";")):
                insert_idx -= 1
            # Insert after the last content line
            insert_idx += 1
        else:
            # No next section - append to end of file
            insert_idx = len(lines)

        # Insert new lines
        lines[insert_idx:insert_idx] = new_lines

        # Write back
        new_content = "\n".join(lines)
        if not new_content.endswith("\n"):
            new_content += "\n"
        self.ini_path.write_text(new_content, encoding="utf-8")
        _log_debug(f"Inserted {len(new_lines)} lines into {section_marker}")

    def _write_to_ini(
        self,
        modifications: list[ModificationsTLK | Modifications2DA | ModificationsGFF | ModificationsSSF | ModificationsNCS],
        mod_type: str,
    ) -> None:
        """Rewrite the entire INI file from scratch using all accumulated modifications.

        This prevents duplicate sections by completely regenerating the file each time.

        Performance optimization: Batch writes to reduce overhead.
        """
        # Track that this section needs to be written
        self._pending_ini_writes.add(mod_type)
        self._writes_since_last_flush += 1

        # Flush if we've accumulated enough writes or if batching is disabled
        if not self._batch_writes or self._writes_since_last_flush >= self._write_batch_size:
            self._flush_pending_writes()

    def _flush_pending_writes(self) -> None:
        """Flush all pending INI writes by rewriting the complete file."""
        if self._pending_ini_writes:
            self._rewrite_ini_complete()
            self._pending_ini_writes.clear()
            self._writes_since_last_flush = 0

    def _rewrite_ini_complete(self) -> None:
        """Completely rewrite the INI file from all accumulated modifications."""
        # Replace cell values with 2DAMEMORY token references before rewriting
        self._replace_cells_with_2damemory_tokens()

        serializer = TSLPatcherINISerializer()

        # Build InstallFile list from install_folders tracking
        install_files: list[InstallFile] = []
        for folder, filenames in self.install_folders.items():
            for filename in filenames:
                from pykotor.tslpatcher.mods.install import InstallFile  # noqa: PLC0415

                install_file = InstallFile(
                    filename,
                    destination=folder,
                )
                install_files.append(install_file)

        # Create a ModificationsByType with all accumulated modifications
        modifications_by_type = ModificationsByType(
            tlk=self.all_modifications.tlk,
            install=install_files,
            twoda=self.all_modifications.twoda,
            gff=self.all_modifications.gff,
            ssf=self.all_modifications.ssf,
            ncs=self.all_modifications.ncs,
            nss=[],
        )

        # Generate complete INI content (includes header and settings)
        # Use verbose=False to avoid duplicate logging during incremental writes
        ini_content = serializer.serialize(
            modifications_by_type,
            include_header=True,
            include_settings=True,
            verbose=False,
        )

        # Write the entire file from scratch
        self.ini_path.write_text(ini_content, encoding="utf-8")
        _log_debug("Rewrote complete INI file from scratch")

    def finalize(self) -> None:
        """Finalize the INI file.

        All sections are already written incrementally in real-time.
        This method just logs a summary and flushes any pending writes.
        """
        # Flush any remaining pending writes
        self._flush_pending_writes()

        self.log_func(f"\nINI finalized at: {self.ini_path}")
        self.log_func(f"  TLK modifications: {len(self.all_modifications.tlk)}")
        self.log_func(f"  2DA modifications: {len(self.all_modifications.twoda)}")
        self.log_func(f"  GFF modifications: {len(self.all_modifications.gff)}")
        self.log_func(f"  SSF modifications: {len(self.all_modifications.ssf)}")
        self.log_func(f"  NCS modifications: {len(self.all_modifications.ncs)}")
        total_install_files: int = sum(len(files) for files in self.install_folders.values())
        self.log_func(f"  Install files: {total_install_files}")
        self.log_func(f"  Install folders: {len(self.install_folders)}")

    def write_pending_tlk_modifications(self) -> None:
        """Write all pending TLK modifications to INI immediately.

        This ensures the [TLKList] section is complete before StrRef cache building.
        """
        if not self.all_modifications.tlk:
            # [TLKList] header already written at init, nothing to do
            return

        # Write all TLK modifications that haven't been written yet
        for mod_tlk in self.all_modifications.tlk:
            filename = mod_tlk.sourcefile
            if filename not in self.written_sections:
                self._write_tlk_modification(mod_tlk)

        _log_debug(f"Written {len(self.all_modifications.tlk)} TLK modifications to INI")
