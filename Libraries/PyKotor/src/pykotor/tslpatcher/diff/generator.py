"""TSLPatcher data folder generator.

This module creates complete tslpatchdata folder structures with all necessary
resource files (TLK, 2DA, GFF, SSF) based on modifications detected by KotorDiff.
"""

from __future__ import annotations

import os
import traceback

from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import Installation
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.gff.gff_auto import read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.lip.lip_auto import read_lip, write_lip
from pykotor.resource.formats.ssf.ssf_auto import read_ssf, write_ssf
from pykotor.resource.formats.ssf.ssf_data import SSF
from pykotor.resource.formats.tlk.tlk_auto import read_tlk, write_tlk
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.formats.twoda.twoda_auto import read_2da, write_2da
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.gff import AddFieldGFF, AddStructToListGFF, FieldValue, FieldValueConstant, ModifyFieldGFF
from pykotor.tslpatcher.mods.install import InstallFile
from pykotor.tslpatcher.mods.ssf import ModifySSF

if TYPE_CHECKING:
    from pathlib import PureWindowsPath

    from pykotor.tslpatcher.mods.gff import FieldValue2DAMemory, FieldValueTLKMemory, ModificationsGFF
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.tlk import ModificationsTLK
    from pykotor.tslpatcher.mods.twoda import Modifications2DA
    from pykotor.tslpatcher.writer import ModificationsByType


# Logging helpers
# Log level: 0 = normal, 1 = verbose, 2 = debug
_log_level = 2 if os.environ.get("KOTORDIFF_DEBUG") else (1 if os.environ.get("KOTORDIFF_VERBOSE") else 0)


def _log_debug(msg: str) -> None:
    """Log debug message if debug level is enabled."""
    if _log_level >= 2:  # noqa: PLR2004
        print(f"[DEBUG] {msg}")


def _log_verbose(msg: str) -> None:
    """Log verbose message if verbose level is enabled."""
    if _log_level >= 1:
        print(f"[VERBOSE] {msg}")


def _log_error(msg: str) -> None:
    """Log error message."""
    if _log_level >= 1:
        print(f"[ERROR] {msg}")


class TSLPatchDataGenerator:
    """Generates complete tslpatchdata folder structures with all necessary files."""

    def __init__(self, tslpatchdata_path: Path):
        """Initialize generator with target tslpatchdata path.

        Args:
            tslpatchdata_path: Path where tslpatchdata folder will be created
        """
        self.tslpatchdata_path = tslpatchdata_path
        self.tslpatchdata_path.mkdir(parents=True, exist_ok=True)
        _log_debug(f"TSLPatchDataGenerator initialized at: {self.tslpatchdata_path}")

    def generate_all_files(
        self,
        modifications: ModificationsByType,
        base_data_path: Path | None = None,
    ) -> dict[str, Path]:
        """Generate all necessary resource files for TSLPatcher installation.

        Args:
            modifications: All modifications to be applied
            base_data_path: Optional path to base game data (for reading original files)

        Returns:
            Dictionary mapping file types to their generated paths
        """
        _log_debug("Generating all TSLPatcher data files...")
        generated_files: dict[str, Path] = {}

        # Generate TLK files
        if modifications.tlk:
            _log_verbose(f"Generating {len(modifications.tlk)} TLK file(s)")
            tlk_files = self._generate_tlk_files(modifications.tlk, base_data_path)
            generated_files.update(tlk_files)

        # Generate 2DA files
        if modifications.twoda:
            _log_verbose(f"Generating {len(modifications.twoda)} 2DA file(s)")
            twoda_files = self._generate_2da_files(modifications.twoda, base_data_path)
            generated_files.update(twoda_files)

        # Generate GFF files
        if modifications.gff:
            _log_verbose(f"Generating {len(modifications.gff)} GFF file(s)")
            gff_files = self._generate_gff_files(modifications.gff, base_data_path)
            generated_files.update(gff_files)

        # Generate SSF files
        if modifications.ssf:
            _log_verbose(f"Generating {len(modifications.ssf)} SSF file(s)")
            ssf_files = self._generate_ssf_files(modifications.ssf, base_data_path)
            generated_files.update(ssf_files)

        # Copy missing files from install folders if base_data_path provided
        if modifications.install and base_data_path:
            _log_verbose(f"Copying {len(modifications.install)} files from install folders")
            install_files = self._copy_install_files(modifications.install, base_data_path)
            generated_files.update(install_files)

        _log_debug(f"Generated {len(generated_files)} total resource files")
        return generated_files

    def _copy_install_files(
        self,
        install_files: list[InstallFile],
        base_data_path: Path,
    ) -> dict[str, Path]:
        """Copy files from install folders to tslpatchdata.

        CRITICAL: Only copy files that will be INSTALLED (don't exist in vanilla).
        Files that will be PATCHED should NOT be copied here.

        Args:
            install_files: List of InstallFile objects
            base_data_path: Base path to read files from (the modded installation)

        Returns:
            Dictionary of copied file paths
        """
        _log_debug("Note: Only copying files for [InstallList], NOT files for [GFFList]/[2DAList]/etc")
        copied_files: dict[str, Path] = {}

        # Group files by folder for efficient processing
        files_by_folder: dict[str, list[str]] = {}
        for install_file in install_files:
            folder = install_file.destination if install_file.destination != "." else "Override"
            filename = install_file.saveas or install_file.sourcefile
            if folder not in files_by_folder:
                files_by_folder[folder] = []
            files_by_folder[folder].append(filename)

        for folder, filenames in files_by_folder.items():
            _log_debug(f"Processing install folder: {folder} ({len(filenames)} files)")

            source_folder = base_data_path / folder
            for filename in filenames:
                source_file = source_folder / filename

                if folder == "modules":
                    dest_file = self.tslpatchdata_path / filename
                    try:
                        if base_data_path is not None and source_file.is_file():
                            dest_file.write_bytes(source_file.read_bytes())
                            _log_debug(f"Copied module capsule: {filename}")
                        else:
                            empty_mod = ERF(ERFType.MOD)
                            write_erf(empty_mod, dest_file, ResourceType.MOD)
                            _log_debug(f"Created empty module capsule: {filename}")
                        copied_files[filename] = dest_file
                    except Exception as e:  # noqa: BLE001
                        _log_error(f"Failed to prepare module capsule {filename}: {e}")
                    continue

                # For module-specific resources, need to extract from capsule
                if folder.startswith("modules\\"):
                    # Extract from module capsule
                    module_name = folder.split("\\")[1]
                    module_path = base_data_path / "modules" / module_name

                    if module_path.is_file():
                        try:
                            capsule = Capsule(module_path)

                            # Find the resource
                            resref_name = Path(filename).stem
                            res_ext = Path(filename).suffix.lstrip(".")

                            for res in capsule:
                                if res.resname().lower() == f"{resref_name}.{res_ext}".lower():
                                    # Found it - write using appropriate io function
                                    dest_file = self.tslpatchdata_path / filename
                                    self._write_resource_with_io(res.data(), dest_file, res_ext)
                                    copied_files[filename] = dest_file
                                    _log_debug(f"Extracted from module: {filename}")
                                    break
                        except Exception as e:  # noqa: BLE001
                            _log_error(f"Failed to extract {filename} from {module_name}: {e}")
                    continue

                # For regular files, copy from source folder
                if source_file.is_file():
                    from pykotor.tools.misc import is_capsule_file  # noqa: PLC0415

                    if is_capsule_file(filename):
                        # Capsule entries should have been handled earlier (e.g., folder == "modules")
                        _log_debug(f"Skipping capsule resource already processed: {filename}")
                        continue

                    dest_file = self.tslpatchdata_path / filename

                    # Determine file extension
                    file_ext = Path(filename).suffix.lstrip(".").lower()

                    # Copy using appropriate method
                    try:
                        source_data = source_file.read_bytes()
                        self._write_resource_with_io(source_data, dest_file, file_ext)
                        copied_files[filename] = dest_file
                        _log_debug(f"Copied: {filename}")
                    except Exception as e:  # noqa: BLE001
                        _log_error(f"Failed to copy {filename}: {e}")

        return copied_files

    def _write_resource_with_io(
        self,
        data: bytes,
        dest_path: Path,
        file_ext: str,
    ) -> None:
        """Write resource data using appropriate io_<format>.py function.

        Args:
            data: Resource data to write
            dest_path: Destination file path
            file_ext: File extension (determines which io function to use)
        """
        try:
            # Use appropriate io function based on file type
            if file_ext.upper() in GFFContent.get_extensions():
                # GFF-based format - use io_gff
                gff_obj = read_gff(data)
                write_gff(gff_obj, dest_path, ResourceType.from_extension(file_ext))
                _log_debug(f"Wrote GFF file using io_gff: {dest_path.name}")

            elif file_ext == "2da":
                # 2DA file - use io_2da
                twoda_obj = read_2da(data)
                write_2da(twoda_obj, dest_path, ResourceType.TwoDA)
                _log_debug(f"Wrote 2DA file using io_2da: {dest_path.name}")

            elif file_ext == "tlk":
                # TLK file - use io_tlk (already handled in _generate_tlk_files, shouldn't reach here)
                tlk_obj = read_tlk(data)
                write_tlk(tlk_obj, dest_path, ResourceType.TLK)
                _log_debug(f"Wrote TLK file using io_tlk: {dest_path.name}")

            elif file_ext == "ssf":
                # SSF file - use io_ssf
                ssf_obj = read_ssf(data)
                write_ssf(ssf_obj, dest_path, ResourceType.SSF)
                _log_debug(f"Wrote SSF file using io_ssf: {dest_path.name}")

            elif file_ext == "lip":
                # LIP file - use io_lip
                lip_obj = read_lip(data)
                write_lip(lip_obj, dest_path, ResourceType.LIP)
                _log_debug(f"Wrote LIP file using io_lip: {dest_path.name}")

            else:
                # For other formats (NCS, MDL, MDX, WAV, TGA, BIK, etc.), write as binary
                # These are compiled/binary formats that don't have read/write in PyKotor or shouldn't be modified
                dest_path.write_bytes(data)
                _log_debug(f"Wrote binary file: {dest_path.name}")

        except Exception as e:  # noqa: BLE001
            # If parsing fails, fall back to binary write
            _log_error(f"Failed to use io function for {file_ext}, falling back to binary write: {e}")
            dest_path.write_bytes(data)

    def _generate_tlk_files(
        self,
        tlk_modifications: list[ModificationsTLK],
        base_data_path: Path | None = None,
    ) -> dict[str, Path]:
        """Generate TLK files (append.tlk only) from modifications.

        Per TSLPatcher design, only appends are supported (no replace.tlk).

        Args:
            tlk_modifications: List of TLK modifications
            base_data_path: Optional base path for reading original files

        Returns:
            Dictionary of generated TLK file paths
        """
        if not tlk_modifications:
            return {}

        generated: dict[str, Path] = {}

        for mod_tlk in tlk_modifications:
            # All modifiers should be appends (no replacements per TSLPatcher design)
            appends = [m for m in mod_tlk.modifiers if not m.is_replacement]

            # Warn if any replacements are found (shouldn't happen)
            replacements = [m for m in mod_tlk.modifiers if m.is_replacement]
            if replacements:
                _log_error(f"WARNING: Found {len(replacements)} replacement modifiers in TLK - TSLPatcher only supports appends!")

            # Create append.tlk with all modifiers
            if appends:
                _log_debug(f"Creating append.tlk with {len(appends)} entries")
                append_tlk = TLK()
                append_tlk.resize(len(appends))

                # Sort by token_id (which is the index in append.tlk)
                sorted_appends = sorted(appends, key=lambda m: m.token_id)

                for append_idx, modifier in enumerate(sorted_appends):
                    text = modifier.text if modifier.text else ""
                    sound_str = str(modifier.sound) if modifier.sound else ""
                    append_tlk.replace(append_idx, text, sound_str)

                append_path = self.tslpatchdata_path / "append.tlk"
                write_tlk(append_tlk, append_path, ResourceType.TLK)
                generated["append.tlk"] = append_path
                _log_verbose(f"Generated append.tlk at: {append_path}")

        return generated

    def _generate_2da_files(
        self,
        twoda_modifications: list[Modifications2DA],
        base_data_path: Path | None = None,
    ) -> dict[str, Path]:
        """Generate 2DA files from modifications.

        TSLPatcher patches 2DA files, but we need to include the base 2DA files
        in tslpatchdata/Override so TSLPatcher can apply the patches.

        Args:
            twoda_modifications: List of 2DA modifications
            base_data_path: Optional base path for reading original files

        Returns:
            Dictionary of generated 2DA file paths
        """
        if not twoda_modifications:
            return {}

        generated: dict[str, Path] = {}

        for mod_2da in twoda_modifications:
            filename = mod_2da.sourcefile
            output_path = self.tslpatchdata_path / filename

            # Try to load base 2DA file from base_data_path
            if base_data_path is not None:
                # Try Override first, then other locations
                potential_paths = [
                    base_data_path / "Override" / filename,
                    base_data_path / filename,
                ]

                for potential_path in potential_paths:
                    if potential_path.is_file():
                        try:
                            # Copy using io_2da to ensure proper format
                            twoda_obj = read_2da(potential_path)
                            write_2da(twoda_obj, output_path, ResourceType.TwoDA)
                            generated[filename] = output_path
                            _log_debug(f"Generated 2DA file from base: {filename}")
                            break
                        except Exception as e:  # noqa: BLE001
                            _log_error(f"Failed to read base 2DA {potential_path}: {e}")
                            continue

            # If we couldn't find/copy the base file, log a warning
            if filename not in generated:
                _log_error(f"Could not find base 2DA file for {filename} - TSLPatcher may fail without it")

        return generated

    def _generate_gff_files(
        self,
        gff_modifications: list[ModificationsGFF],
        base_data_path: Path | None = None,
    ) -> dict[str, Path]:
        """Generate GFF files from modifications.

        Creates physical GFF files in tslpatchdata root directory. For replacement files,
        applies all modifications. For patch files, copies the base file as-is (TSLPatcher
        will apply modifications at install time).

        Note: ALL files are written to tslpatchdata root, regardless of their destination.
        The destination field (Override, modules/xxx.mod, etc.) is stored on the modification
        objects and used later by determine_install_folders() to generate the INI's [InstallList].

        Args:
            gff_modifications: List of GFF modifications
            base_data_path: Optional base path for reading original files

        Returns:
            Dictionary mapping filenames to generated file paths
        """
        generated: dict[str, Path] = {}

        for mod_gff in gff_modifications:
            # ALL files should be copied to tslpatchdata (TSLPatcher needs base files to patch)
            replace_file = getattr(mod_gff, "replace_file", False)

            if replace_file:
                _log_debug(f"Generating replacement GFF file: {mod_gff.sourcefile}")
            else:
                _log_debug(f"Copying base GFF file for patching: {mod_gff.sourcefile}")

            # Get the actual filename (might be different from sourcefile)
            filename: str = getattr(mod_gff, "saveas", mod_gff.sourcefile)

            # CRITICAL: ALL files go directly in tslpatchdata root, NOT in subdirectories
            # The destination field tells TSLPatcher where to install them at runtime
            output_path: Path = self.tslpatchdata_path / filename

            # Try to load base file if base_data_path provided, otherwise create new
            base_gff: GFF = self._load_or_create_gff(base_data_path, filename)

            # For replace operations, apply modifications
            # For patch operations, just copy the base file as-is
            if replace_file:
                # Apply all modifications to generate the replacement file
                self._apply_gff_modifications(base_gff, mod_gff.modifiers)
                _log_verbose(f"Generated replacement GFF file: {output_path}")
            else:
                # Just copy the base file (TSLPatcher will apply patches at install time)
                _log_verbose(f"Copied base GFF file for patching: {output_path}")

            # Write the GFF file
            write_gff(base_gff, output_path, ResourceType.GFF)
            generated[filename] = output_path

        return generated

    def _load_or_create_gff(self, base_data_path: Path | None, filename: str) -> GFF:
        """Load base GFF file or create new one.

        Args:
            base_data_path: Optional base path for reading original files
            filename: Name of the GFF file

        Returns:
            Loaded or newly created GFF object (never None)
        """
        # Try to load base file if base_data_path provided
        if base_data_path is not None:
            potential_base = base_data_path / filename
            if potential_base.is_file():
                try:
                    base_gff = read_gff(potential_base)
                    _log_debug(f"Loaded base GFF from: {potential_base}")
                except Exception as e:  # noqa: BLE001
                    print("Full traceback:")
                    for line in traceback.format_exc().splitlines():
                        print(f"  {line}")
                    _log_debug(f"Could not load base GFF {potential_base}: {e}")
                else:
                    return base_gff

        # Create new GFF structure
        ext = PurePath(filename).suffix.lstrip(".")

        # Try to get GFFContent from extension
        try:
            gff_content = GFFContent[ext.upper()] if ext else GFFContent.GFF
        except (KeyError, AttributeError):
            gff_content = GFFContent.GFF

        base_gff = GFF(gff_content)
        _log_debug(f"Created new GFF with content type: {gff_content}")
        return base_gff

    def _apply_gff_modifications(
        self,
        gff: GFF,
        modifiers: list[Any],
    ):
        """Apply GFF modifications to a GFF structure.

        Args:
            gff: GFF structure to modify
            modifiers: List of GFF modifiers to apply
        """
        for modifier in modifiers:
            if isinstance(modifier, ModifyFieldGFF):
                self._apply_modify_field(gff.root, modifier)
            elif isinstance(modifier, AddFieldGFF):
                self._apply_add_field(gff.root, modifier)
            elif isinstance(modifier, AddStructToListGFF):
                self._apply_add_struct_to_list(gff.root, modifier)

    def _navigate_to_parent_struct(
        self,
        root_struct: GFFStruct,
        path_parts: list[str],
        context: str = "modification",
    ) -> GFFStruct | None:
        """Navigate to parent struct following path.

        Args:
            root_struct: Root GFF structure
            path_parts: Path components to navigate (excluding final field)
            context: Context string for error messages

        Returns:
            Parent struct if navigation successful, None otherwise
        """
        current_struct: GFFStruct | None = root_struct

        for part in path_parts[:-1]:
            if current_struct is None:
                _log_error(f"Cannot navigate {context}: current_struct is None at '{part}'")
                return None

            if part.isdigit():
                # List index navigation
                if not isinstance(current_struct, GFFList):
                    _log_error(f"Path part '{part}' expects list but got {type(current_struct).__name__} during {context}")
                    return None
                list_index = int(part)
                list_item = current_struct.at(list_index)
                if list_item is None:
                    _log_error(f"List index {list_index} out of bounds during {context}")
                    return None
                current_struct = list_item
            # Struct field navigation
            else:
                nested_struct = current_struct.get_struct(part)
                if nested_struct is None:
                    _log_error(f"Cannot navigate to struct field '{part}' during {context} - field missing or wrong type")
                    return None
                current_struct = nested_struct

        return current_struct

    def _apply_modify_field(
        self,
        root_struct: GFFStruct,
        modifier: ModifyFieldGFF,
    ):
        """Apply a ModifyFieldGFF modification.

        Args:
            root_struct: Root GFF structure
            modifier: Modification to apply
        """
        # Navigate to the correct struct
        path_parts = str(modifier.path).replace("\\", "/").split("/")
        current_struct = self._navigate_to_parent_struct(root_struct, path_parts, f"ModifyField: {modifier.path}")

        if current_struct is None:
            return

        # Set the field value
        field_label = path_parts[-1]
        value = self._extract_field_value(modifier.value)
        self._set_field_value(current_struct, field_label, value)

    def _set_field_value(
        self,
        struct: GFFStruct,
        field_label: str,
        value: Any,
    ) -> None:
        """Set field value using appropriate setter based on value type.

        Args:
            struct: GFF structure to modify
            field_label: Label of field to set
            value: Value to set
        """
        if isinstance(value, int):
            struct.set_uint32(field_label, value)
        elif isinstance(value, float):
            struct.set_single(field_label, value)
        elif isinstance(value, str):
            struct.set_string(field_label, value)
        elif isinstance(value, ResRef):
            struct.set_resref(field_label, value)
        elif isinstance(value, LocalizedString):
            struct.set_locstring(field_label, value)
        else:
            _log_error(f"Unknown value type for field '{field_label}': {type(value).__name__}")

    def _navigate_to_struct_creating_if_needed(self, root_struct: GFFStruct, path_parts: list[str], context: str = "AddField") -> GFFStruct | None:
        """Navigate through path, creating structs as needed.

        Args:
            root_struct: Root GFF structure
            path_parts: Path components to navigate
            context: Context for error messages

        Returns:
            Target struct, or None on navigation error
        """
        current_struct: GFFStruct = root_struct

        for part in path_parts:
            if not part or not part.strip():
                _log_debug(f"Skipping empty path part in {context}")
                continue

            if part.isdigit():
                # List index navigation
                if not isinstance(current_struct, GFFList):
                    _log_error(f"Expected list at '{part}' but got {type(current_struct).__name__} in {context}")
                    return None
                list_item = current_struct.at(int(part))
                if list_item is None:
                    _log_error(f"List index {part} out of bounds in {context}")
                    return None
                current_struct = list_item
            # Struct field - check if exists, create if not
            elif current_struct.exists(part):
                nested_struct = current_struct.get_struct(part)
                if nested_struct is None:
                    _log_error(f"Field '{part}' exists but is not a struct in {context}")
                    return None
                current_struct = nested_struct
            else:
                # Create new struct if field doesn't exist
                _log_debug(f"Creating new struct at field '{part}' in {context}")
                new_struct = GFFStruct()
                current_struct.set_struct(part, new_struct)
                current_struct = new_struct

        return current_struct

    def _apply_nested_modifiers(
        self,
        current_struct: GFFStruct,
        modifier: AddFieldGFF,
    ):
        """Apply nested modifiers to a struct or list field.

        Args:
            current_struct: Current GFF structure
            modifier: Parent modifier with nested modifiers
        """
        if not modifier.modifiers:
            return

        if modifier.field_type == GFFFieldType.Struct:
            nested_struct = current_struct.get_struct(modifier.label)
            if nested_struct is None:
                _log_error(f"Cannot apply nested modifiers: struct field '{modifier.label}' not found after creation")
                return
            for nested_mod in modifier.modifiers:
                if isinstance(nested_mod, AddFieldGFF):
                    self._apply_add_field(nested_struct, nested_mod)
                elif isinstance(nested_mod, AddStructToListGFF):
                    _log_error(f"Unexpected AddStructToListGFF in Struct context for '{modifier.label}'")

        elif modifier.field_type == GFFFieldType.List:
            # Lists handle their own nested modifiers via AddStructToListGFF
            _log_debug(f"List field '{modifier.label}' created, nested modifiers handled by AddStructToListGFF")

    def _apply_add_field(
        self,
        root_struct: GFFStruct,
        modifier: AddFieldGFF,
    ):
        """Apply an AddFieldGFF modification.

        Args:
            root_struct: Root GFF structure
            modifier: Modification to apply
        """
        # Navigate to parent struct, creating intermediate structs as needed
        path_parts = str(modifier.path).replace("\\", "/").split("/") if modifier.path else []
        current_struct = self._navigate_to_struct_creating_if_needed(root_struct, path_parts, f"AddField: {modifier.label}")

        if current_struct is None:
            return

        # Add the field to the struct
        value = self._extract_field_value(modifier.value)
        self._set_field_by_type(current_struct, modifier.label, modifier.field_type, value)

        # Recursively apply nested modifiers if present
        if modifier.field_type in (GFFFieldType.Struct, GFFFieldType.List):
            self._apply_nested_modifiers(current_struct, modifier)

    def _navigate_to_list_creating_if_needed(
        self,
        root_struct: GFFStruct,
        path_parts: list[str],
        context: str = "AddStructToList",
    ) -> GFFList | None:
        """Navigate to target list, creating if needed.

        Args:
            root_struct: Root GFF structure
            path_parts: Path components to navigate
            context: Context for error messages

        Returns:
            Target GFFList or None on error
        """
        current_obj: GFFStruct | GFFList = root_struct

        for part in path_parts:
            if not part or not part.strip():
                _log_debug(f"Skipping empty path part in {context}")
                continue

            if part.isdigit():
                # List index navigation
                if not isinstance(current_obj, GFFList):
                    _log_error(f"Expected list at index '{part}' but got {type(current_obj).__name__} in {context}")
                    return None
                item = current_obj.at(int(part))
                if item is None:
                    _log_error(f"List index {part} out of bounds in {context}")
                    return None
                current_obj = item

            # Struct field navigation
            elif isinstance(current_obj, GFFStruct):
                navigated_obj = self._navigate_struct_field_to_list(current_obj, part, context)
                if navigated_obj is None:
                    return None
                current_obj = navigated_obj
            else:
                _log_error(f"Cannot navigate from {type(current_obj).__name__} at '{part}' in {context}")
                return None

        # Verify final object is a list
        if not isinstance(current_obj, GFFList):
            _log_error(f"Path '{'/'.join(path_parts)}' did not resolve to GFFList in {context}, got {type(current_obj).__name__}")
            return None

        return current_obj

    def _navigate_struct_field_to_list(
        self,
        current_struct: GFFStruct,
        field_name: str,
        context: str,
    ) -> GFFList | GFFStruct | None:
        """Navigate struct field, handling List/Struct types.

        Returns:
            The navigated object (GFFList or GFFStruct) or None on error
        """
        if not current_struct.exists(field_name):
            # Field doesn't exist - create new list
            _log_debug(f"Creating new GFFList for field '{field_name}' in {context}")
            new_list = GFFList()
            current_struct.set_list(field_name, new_list)
            return new_list

        # Field exists - navigate to it
        # Access the field object directly from _fields
        field = current_struct._fields[field_name]
        field_type = field.field_type()

        # Navigate based on field type
        if field_type == GFFFieldType.List:
            result_list: GFFList | None = current_struct.get_list(field_name)
            if result_list is None:
                _log_error(f"get_list('{field_name}') returned None in {context}")
            return result_list

        if field_type == GFFFieldType.Struct:
            result_struct: GFFStruct | None = current_struct.get_struct(field_name)
            if result_struct is None:
                _log_error(f"get_struct('{field_name}') returned None in {context}")
            return result_struct

        _log_error(f"Field '{field_name}' has type {field_type.name}, expected List or Struct in {context}")
        return None

    def _extract_struct_from_modifier(
        self,
        modifier: AddStructToListGFF,
    ) -> GFFStruct:
        """Extract or create GFFStruct from modifier value.

        Args:
            modifier: Modifier containing struct value

        Returns:
            GFFStruct object
        """
        if isinstance(modifier.value, FieldValueConstant) and isinstance(modifier.value.stored, GFFStruct):
            return modifier.value.stored

        # Create new struct with appropriate struct_id
        if isinstance(modifier.value, FieldValueConstant) and isinstance(modifier.value.stored, dict):
            struct_id = modifier.value.stored.get("struct_id", 0)
            return GFFStruct(struct_id)

        return GFFStruct()

    def _apply_add_struct_to_list(
        self,
        root_struct: GFFStruct,
        modifier: AddStructToListGFF,
    ):
        """Apply an AddStructToListGFF modification.

        Args:
            root_struct: Root GFF structure
            modifier: Modification to apply
        """
        # Navigate to the target list
        path_parts = str(modifier.path).replace("\\", "/").split("/") if modifier.path else []
        target_list = self._navigate_to_list_creating_if_needed(root_struct, path_parts, f"AddStructToList: {modifier.identifier}")

        if target_list is None:
            return

        # Extract struct from modifier
        new_struct = self._extract_struct_from_modifier(modifier)

        # Add the struct to the list
        struct_id = new_struct.struct_id if hasattr(new_struct, "struct_id") else 0
        added_struct = target_list.add(struct_id)

        # Copy fields from new_struct to added_struct
        for field_label, field_type, field_value in new_struct:
            self._set_field_by_type(added_struct, field_label, field_type, field_value)

        # Apply nested modifiers to the added struct
        for nested_mod in modifier.modifiers:
            if isinstance(nested_mod, AddFieldGFF):
                self._apply_add_field(added_struct, nested_mod)
            elif isinstance(nested_mod, AddStructToListGFF):
                self._apply_add_struct_to_list(added_struct, nested_mod)

    def _set_field_by_type(
        self,
        struct: GFFStruct,
        label: str,
        field_type: GFFFieldType,
        value: Any,
    ):
        """Set a field on a GFF struct using the appropriate setter.

        Args:
            struct: GFF structure
            label: Field label
            field_type: Field type
            value: Value to set
        """
        setters = {
            GFFFieldType.UInt8: lambda: struct.set_uint8(label, int(value)),
            GFFFieldType.Int8: lambda: struct.set_int8(label, int(value)),
            GFFFieldType.UInt16: lambda: struct.set_uint16(label, int(value)),
            GFFFieldType.Int16: lambda: struct.set_int16(label, int(value)),
            GFFFieldType.UInt32: lambda: struct.set_uint32(label, int(value)),
            GFFFieldType.Int32: lambda: struct.set_int32(label, int(value)),
            GFFFieldType.UInt64: lambda: struct.set_uint64(label, int(value)),
            GFFFieldType.Int64: lambda: struct.set_int64(label, int(value)),
            GFFFieldType.Single: lambda: struct.set_single(label, float(value)),
            GFFFieldType.Double: lambda: struct.set_double(label, float(value)),
            GFFFieldType.String: lambda: struct.set_string(label, str(value)),
            GFFFieldType.ResRef: lambda: struct.set_resref(label, ResRef(str(value))),
            GFFFieldType.LocalizedString: lambda: struct.set_locstring(label, value),
            GFFFieldType.Vector3: lambda: struct.set_vector3(label, value),
            GFFFieldType.Vector4: lambda: struct.set_vector4(label, value),
            GFFFieldType.Struct: lambda: struct.set_struct(label, value),
            GFFFieldType.List: lambda: struct.set_list(label, value if isinstance(value, GFFList) else GFFList()),
        }

        setter = setters.get(field_type)
        if setter:
            try:
                setter()
            except Exception as e:  # noqa: BLE001
                _log_debug(f"Error setting field {label} with type {field_type}: {e}")
        else:
            _log_debug(f"No setter for field type: {field_type}")

    def _extract_field_value(
        self,
        field_value: FieldValue,
    ) -> ResRef | str | PureWindowsPath | int | float | object | FieldValueConstant | FieldValue2DAMemory | FieldValueTLKMemory | FieldValue:
        """Extract the actual value from a FieldValue wrapper.

        Args:
            field_value: FieldValue wrapper or raw value

        Returns:
            The actual value to be used
        """
        if isinstance(field_value, FieldValueConstant) and hasattr(field_value, "stored"):
            return field_value.stored
        if isinstance(field_value, FieldValue) and hasattr(field_value, "value") and callable(field_value.value):
            return field_value.value(None, None)  # type: ignore[arg-type]
        return field_value

    def _generate_ssf_files(
        self,
        ssf_modifications: list[ModificationsSSF],
        base_data_path: Path | None = None,
    ) -> dict[str, Path]:
        """Generate SSF files from modifications.

        Args:
            ssf_modifications: List of SSF modifications
            base_data_path: Optional base path for reading original files

        Returns:
            Dictionary of generated SSF file paths
        """
        generated: dict[str, Path] = {}

        for mod_ssf in ssf_modifications:
            # Check if this is a replace operation or patch operation
            replace_file = getattr(mod_ssf, "replace_file", False)

            if replace_file:
                _log_debug(f"Generating replacement SSF file: '{mod_ssf.sourcefile}'")
            else:
                _log_debug(f"Copying base SSF file for patching: '{mod_ssf.sourcefile}'")

            # Create new SSF or load base
            ssf: SSF | None = None
            if base_data_path:
                potential_base = base_data_path / mod_ssf.sourcefile
                if potential_base.is_file():
                    try:
                        ssf = read_ssf(potential_base)
                        _log_debug(f"Loaded base SSF from: '{potential_base}'")
                    except Exception as e:  # noqa: BLE001
                        _log_debug(f"Could not load base SSF '{potential_base}': {e.__class__.__name__}: {e}")  # noqa: BLE001
                        print("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            print(f"  {line}")

            if not ssf:
                ssf = SSF()
                _log_debug("Created new SSF")

            # For replace operations, apply modifications
            # For patch operations, just copy the base file as-is
            if replace_file:
                # Apply modifications to generate the replacement file
                for modifier in mod_ssf.modifiers:
                    if isinstance(modifier, ModifySSF):
                        # Apply modifier using the same pattern as ssf.py
                        ssf.set_data(modifier.sound, int(modifier.stringref.value(PatcherMemory())))
                _log_verbose(f"Generated replacement SSF file: '{mod_ssf.sourcefile}'")
            else:
                # Just copy the base file (TSLPatcher will apply patches at install time)
                _log_verbose(f"Copied base SSF file for patching: '{mod_ssf.sourcefile}'")

            # Write SSF file
            output_path = self.tslpatchdata_path / mod_ssf.sourcefile
            write_ssf(ssf, output_path, ResourceType.SSF)
            generated[mod_ssf.sourcefile] = output_path

        return generated


def _validate_ini_filename(ini: str | None) -> str:
    """Validate and normalize INI filename.

    Args:
        ini: Raw INI filename

    Returns:
        Normalized INI filename with .ini extension

    Raises:
        ValueError: If filename contains path separators or has wrong extension
    """
    if not ini:
        return "changes.ini"

    # Check for path separators
    if "/" in ini or "\\" in ini or os.sep in ini:
        msg = f"--ini must be a filename only (not a path): {ini}"
        raise ValueError(msg)

    # Ensure .ini extension
    if ini.endswith(".ini"):
        return ini

    # Check for other extensions
    if "." in ini:
        ext = PurePath(ini).suffix
        if ext and ext != ".ini":
            msg = f"--ini must have .ini extension (got {ext})"
            raise ValueError(msg)
        # Has a dot but no extension, add .ini
        return f"{ini}.ini" if ini.endswith(".") else ini

    # No extension at all, add .ini
    return f"{ini}.ini"


def _validate_installation_path(path: Path | None) -> bool:
    """Check if path is a valid KOTOR installation.

    Args:
        path: Path to check

    Returns:
        True if path is a valid installation directory
    """
    if not path or not path.is_dir():
        return False

    try:
        return Installation.determine_game(path) is not None
    except Exception as e:  # noqa: BLE001
        _log_debug(f"Installation check failed for '{path}': {e.__class__.__name__}: {e}")
        print("Full traceback:")
        for line in traceback.format_exc().splitlines():
            print(f"  {line}")
        return False


def validate_tslpatchdata_arguments(
    ini: str | None,
    tslpatchdata: str | None,
    files_and_folders_and_installations: list[Path | Installation] | None,
) -> tuple[str, Path] | tuple[None, None]:
    """Validate --ini and --tslpatchdata arguments.

    Args:
        ini: The ini filename argument value
        tslpatchdata: The tslpatchdata folder argument value
        files_and_folders_and_installations: All user-provided paths (any length)

    Returns:
        Tuple of (validated_ini_filename, tslpatchdata_folder_path) or (None, None) if not applicable

    Raises:
        ValueError: If validation fails with detailed error message
    """
    # Early exit if neither argument provided
    if not ini and not tslpatchdata:
        return None, None

    # Validate argument combination
    if ini and not tslpatchdata:
        msg = "--ini requires --tslpatchdata to be specified"
        raise ValueError(msg)

    # Set defaults
    if tslpatchdata and not ini:
        ini = "changes.ini"

    # Should not happen but check anyway
    if not tslpatchdata:
        return None, None

    # Validate and normalize INI filename
    validated_ini = _validate_ini_filename(ini)

    # Validate at least one provided path is an Installation
    has_any_install: bool = False
    if files_and_folders_and_installations:
        for p in files_and_folders_and_installations:
            # Already an Installation object
            if isinstance(p, Installation):
                has_any_install = True
                break

            # Try to verify by constructing an Installation from the path
            if isinstance(p, Path):
                try:
                    _ = Installation(p)
                    has_any_install = True
                    break
                except Exception:
                    # Fall back to determine_game heuristic
                    if _validate_installation_path(p):
                        has_any_install = True
                        break

    if not has_any_install:
        msg = "--tslpatchdata requires at least one provided path to be a valid KOTOR Installation"
        raise ValueError(msg)

    # Normalize tslpatchdata path
    tslpatchdata_path = CaseAwarePath(tslpatchdata).resolve()
    if tslpatchdata_path.name.lower() != "tslpatchdata":
        tslpatchdata_path = tslpatchdata_path / "tslpatchdata"

    _log_debug(f"Validated arguments: ini={validated_ini}, tslpatchdata_path={tslpatchdata_path}")

    return validated_ini, tslpatchdata_path


def _add_file_to_folder(
    install_folders: dict[str, list[str]],
    folder: str,
    filename: str,
) -> None:
    """Add a file to an install folder, creating folder entry if needed.

    Args:
        install_folders: Dictionary of install folders
        folder: Folder name
        filename: File to add
    """
    if folder not in install_folders:
        install_folders[folder] = []
    if filename not in install_folders[folder]:
        install_folders[folder].append(filename)


def _process_tlk_modifications(
    modifications: list[ModificationsTLK],
    install_folders: dict[str, list[str]],
) -> None:
    """Process TLK modifications to determine install files.

    Per TSLPatcher design, only append.tlk is generated (no replace.tlk).

    Args:
        modifications: TLK modifications list
        install_folders: Dictionary to update with folder/file mappings
    """
    for mod_tlk in modifications:
        folder = "."  # TLK files go to game root

        # Only check for appends (TSLPatcher doesn't support replacements)
        has_appends = any(not m.is_replacement for m in mod_tlk.modifiers)

        # Warn if replacements found (shouldn't happen)
        has_replacements = any(m.is_replacement for m in mod_tlk.modifiers)
        if has_replacements:
            _log_debug("WARNING: Found replacement modifiers in TLK - TSLPatcher only supports appends!")

        if has_appends:
            _add_file_to_folder(install_folders, folder, "append.tlk")


def _process_2da_modifications(
    modifications: list[Modifications2DA],
    install_folders: dict[str, list[str]],
) -> None:
    """Process 2DA modifications to determine install files.

    Args:
        modifications: 2DA modifications list
        install_folders: Dictionary to update with folder/file mappings
    """
    for mod_2da in modifications:
        _add_file_to_folder(install_folders, "Override", mod_2da.sourcefile)


def _process_gff_modifications(
    modifications: list[ModificationsGFF],
    install_folders: dict[str, list[str]],
) -> None:
    """Process GFF modifications to determine install files.

    Args:
        modifications: GFF modifications list
        install_folders: Dictionary to update with folder/file mappings
    """
    for mod_gff in modifications:
        destination = mod_gff.destination
        filename = mod_gff.saveas
        _add_file_to_folder(install_folders, destination, filename)


def _process_ssf_modifications(
    modifications: list[ModificationsSSF],
    install_folders: dict[str, list[str]],
) -> None:
    """Process SSF modifications to determine install files.

    Args:
        modifications: SSF modifications list
        install_folders: Dictionary to update with folder/file mappings
    """
    for mod_ssf in modifications:
        _add_file_to_folder(install_folders, "Override", mod_ssf.sourcefile)


def _merge_existing_install_files(
    existing_install: list[InstallFile],
    install_folders: dict[str, list[str]],
) -> None:
    """Merge existing install file lists into install_folders.

    Args:
        existing_install: Existing InstallFile objects
        install_folders: Dictionary to update
    """
    for install_file in existing_install:
        folder = install_file.destination if install_file.destination != "." else "Override"
        filename = install_file.saveas or install_file.sourcefile
        _add_file_to_folder(install_folders, folder, filename)


def determine_install_folders(modifications: ModificationsByType) -> list[InstallFile]:
    """Determine which install folders are needed based on modifications.

    Args:
        modifications: All modifications

    Returns:
        List of InstallFile objects for InstallList
    """
    install_folders: dict[str, list[str]] = {}

    # Process each modification type
    _process_tlk_modifications(modifications.tlk, install_folders)
    _process_2da_modifications(modifications.twoda, install_folders)
    _process_gff_modifications(modifications.gff, install_folders)
    _process_ssf_modifications(modifications.ssf, install_folders)
    _merge_existing_install_files(modifications.install, install_folders)

    # Convert dict to list of InstallFile objects
    install_files: list[InstallFile] = []

    for folder, filenames in install_folders.items():
        install_files.extend(InstallFile(filename, destination=folder) for filename in filenames)

    return install_files
