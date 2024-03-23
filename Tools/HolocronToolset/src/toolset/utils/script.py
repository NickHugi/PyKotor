from __future__ import annotations

import os
import re
import sys
import uuid

from contextlib import suppress

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.ncs.compiler.classes import EntryPointError
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath
from pykotor.tools.registry import resolve_reg_key_to_path, set_registry_key_value
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from utility.error_handling import format_exception_with_variables
from utility.misc import ProcessorArchitecture
from utility.system.path import Path

NON_TSLPATCHER_NWNNSSCOMP_PERMISSION_MSG = (
    "PyKotor has detected you are using the {} version of nwnnsscomp.<br>"
    " This version doesn't have any known functional problems, though it DOES require that the registry"
    " key path:<br>{}<br>matches your KotOR installation path.<br><br>"
    "Your installation path ({}),<br>"
    "DOES NOT MATCH the registry value ({})<br><br>"
    "Due to the above, the compilation/decompilation will most likely fail.<br>"
    "Either restart HolocronToolset with admin privileges, or download and use the"
    " TSLPatcher version of nwnnsscomp to fix this issue.<br><br>"
    "Error details: {}"
)

def decompileScript(compiled_bytes: bytes, installation_path: Path, *, tsl: bool) -> str:
    """Returns the NSS bytes of a decompiled script. If no NCS Decompiler is selected, prompts the user to find the executable.

    Current implementation copies the NCS to a temporary directory (configured in settings), decompiles it there,
    then returns the bytes of the new file. If no temporary directory has been configured, the user is prompted to
    select a folder. If no NCS decompiler filepath has been configured, the user is prompted to select an executable.

    Args:
    ----
        compiled_bytes: The bytes of the compiled script.
        tsl: Compile the script for TSL instead of KotOR.

    Raises:
    ------
        OSError: If an error occured writing or loading from the temp directory.
        ValueError: If the compiled bytes failed to decompile.
        NoConfigurationSet: If no path has been set for the temp directory or NSS decompiler.

    Returns:
    -------
        The string of the decompiled script.
    """
    global_settings = GlobalSettings()
    extract_path = Path(global_settings.extractPath)

    if not extract_path.safe_isdir():
        extract_path = Path(QFileDialog.getExistingDirectory(None, "Select a temp directory"))
        if not extract_path.safe_isdir():
            msg = "Temp directory has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    ncs_decompiler_path = Path(global_settings.ncsDecompilerPath)
    if not ncs_decompiler_path.name or ncs_decompiler_path.suffix.lower() != ".exe" or not ncs_decompiler_path.safe_isfile():
        ncs_decompiler_path, _ = QFileDialog.getOpenFileName(None, "Select the NCS Decompiler executable")
        ncs_decompiler_path = Path(ncs_decompiler_path)
        if not ncs_decompiler_path.safe_isfile():
            global_settings.ncsDecompilerPath = ""
            msg = "NCS Decompiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.extractPath = str(extract_path)
    global_settings.ncsDecompilerPath = str(ncs_decompiler_path)

    rand_id = uuid.uuid1().hex[:6]
    tempscript_filestem = f"tempscript_{rand_id}"
    tempCompiledPath = extract_path / f"{tempscript_filestem}.ncs"
    tempDecompiledPath = extract_path / f"{tempscript_filestem}_decompiled.txt"
    BinaryWriter.dump(tempCompiledPath, compiled_bytes)
    orig_regkey_value = None

    try:
        game = Game.K2 if tsl else Game.K1
        extCompiler = ExternalNCSCompiler(ncs_decompiler_path)
        if extCompiler.get_info().name != "TSLPatcher":
            # Set the registry temporarily so nwnnsscomp doesn't fail with 'Error: Couldn't initialize the NwnStdLoader'
            if ProcessorArchitecture.from_os() == ProcessorArchitecture.BIT_64:
                if tsl:
                    orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2"
                else:
                    orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR"
            elif tsl:
                orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2"
            else:
                orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR"

            orig_regkey_value = resolve_reg_key_to_path(orig_regkey_path, "Path")
            installation_path_str = str(installation_path)
            if orig_regkey_value != installation_path_str:
                try:
                    set_registry_key_value(orig_regkey_path, "Path", installation_path_str)
                except PermissionError as e:
                    print(f"Permission denied: {e}")
                    msg = NON_TSLPATCHER_NWNNSSCOMP_PERMISSION_MSG.format(extCompiler.get_info().name, orig_regkey_path, installation_path_str, orig_regkey_value, str(e))
                    QMessageBox(
                        QMessageBox.Warning,
                        "Permission denied when attempting to update nwnnsscomp in registry",
                        msg,
                    ).exec_()
        stdout, stderr = extCompiler.decompile_script(tempCompiledPath, tempDecompiledPath, game)
        print(stdout, "\n", stderr)
        if stderr:
            raise ValueError(stderr)  # noqa: TRY301
        return BinaryReader.load_file(tempDecompiledPath).decode(encoding="windows-1252")
    except Exception as e:
        with Path("errorlog.txt", encoding="utf-8").open("a") as f:
            msg = format_exception_with_variables(e)
            print(msg, sys.stderr)  # noqa: T201
            f.write(msg)
        raise
    finally:
        if orig_regkey_value and orig_regkey_path and orig_regkey_value != str(installation_path):
            with suppress(PermissionError):
                set_registry_key_value(orig_regkey_path, "Path", orig_regkey_value)


def compileScript(source: str, installation_path: Path, *, tsl: bool) -> bytes | None:
    # sourcery skip: assign-if-exp, introduce-default-else
    """Returns the NCS bytes of compiled source script using either nwnnsscomp.exe (Windows only) or our built-in compiler. If no NSS Compiler is selected, prompts the user to find the executable.

    Current implementation copies the NSS to a temporary directory (configured in settings), compiles it there,
    then returns the bytes of the new file. If no temporary directory has been configured, the user is prompted to
    select a folder. If no NSS compiler filepath has been configured, the user is prompted to select an executable.

    Args:
    ----
        source: The text of the source script.
        tsl: Compile the script for TSL instead of KotOR.

    Raises:
    ------
        OSError: If an error occured writing or loading from the temp directory.
        ValueError: If the source script failed to compile.
        NoConfigurationSet: If no path has been set for the temp directory or NSS compiler.

    Returns:
    -------
        Bytes object of the compiled script.
    """
    global_settings = GlobalSettings()
    extract_path = Path(global_settings.extractPath)

    if not extract_path.safe_isdir():
        extract_path_str = QFileDialog.getExistingDirectory(None, "Select a temp directory")
        extract_path = Path(extract_path_str) if extract_path_str else None
        if not extract_path or not extract_path.safe_isdir():
            msg = "Temp directory has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    returnValue: int | None = None
    if os.name == "nt":
        returnValue = _prompt_user_for_compiler_option()

    if os.name == "posix" or returnValue == QMessageBox.Yes:
        print("user chose Yes, compiling with builtin")
        return bytes_ncs(compile_nss(source, Game.K2 if tsl else Game.K1, library_lookup=[CaseAwarePath(extract_path)]))
    if returnValue == QMessageBox.No:
        print("user chose No, compiling with nwnnsscomp")
        return _compile_windows(global_settings, extract_path, source, tsl, installation_path)
    if returnValue is not None:  # user cancelled
        print("user exited")
        return None

    raise ValueError("Could not get the NCS bytes.")  # noqa: TRY003, EM101


def _compile_windows(
    global_settings: GlobalSettings,
    extract_path: Path,
    source: str,
    tsl: bool,
    installation_path: Path,
) -> bytes:
    nss_compiler_path = Path(global_settings.nssCompilerPath)
    if not nss_compiler_path.safe_isfile():
        lookup_path, _ = QFileDialog.getOpenFileName(None, "Select the NCS Compiler executable")
        nss_compiler_path = Path(lookup_path)
        if not nss_compiler_path.safe_isfile():
            msg = "NCS Compiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.extractPath = str(extract_path)
    global_settings.nssCompilerPath = str(nss_compiler_path)

    rand_id = uuid.uuid1().hex[:6]
    tempscript_filestem = f"tempscript_{rand_id}"
    tempSourcePath = extract_path / f"{tempscript_filestem}.nss"
    tempCompiledPath = extract_path / f"{tempscript_filestem}.ncs"
    BinaryWriter.dump(tempSourcePath, source.encode(encoding="windows-1252"))

    gameEnum: Game = Game.K2 if tsl else Game.K1
    extCompiler = ExternalNCSCompiler(global_settings.nssCompilerPath)
    orig_regkey_path = None
    orig_regkey_value = None
    try:
        if extCompiler.get_info().name != "TSLPatcher":
            # Set the registry temporarily so nwnnsscomp doesn't fail with 'Error: Couldn't initialize the NwnStdLoader'
            if ProcessorArchitecture.from_os() == ProcessorArchitecture.BIT_64:
                if tsl:
                    orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\LucasArts\KotOR2"
                else:
                    orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\BioWare\SW\KOTOR"
            elif tsl:
                orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\LucasArts\KotOR2"
            else:
                orig_regkey_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\BioWare\SW\KOTOR"

            orig_regkey_value = resolve_reg_key_to_path(orig_regkey_path, "Path")
            installation_path_str = str(installation_path)
            if orig_regkey_value != installation_path_str:
                try:
                    set_registry_key_value(orig_regkey_path, "Path", installation_path_str)
                except PermissionError as e:
                    print(f"Permission denied: {e}")
                    msg = NON_TSLPATCHER_NWNNSSCOMP_PERMISSION_MSG.format(extCompiler.get_info().name, orig_regkey_path, installation_path_str, orig_regkey_value, str(e))
                    QMessageBox(
                        QMessageBox.Warning,
                        "Permission denied when attempting to update nwnnsscomp in registry",
                        msg,
                    ).exec_()
        try:
            stdout, stderr = extCompiler.compile_script(tempSourcePath, tempCompiledPath, gameEnum)
        except EntryPointError:
            QMessageBox.warning(
                None,
                "Include scripts cannot be compiled",
                "This script is an include script, compiling it serves no purpose. If this warning is incorrect, check that your script has an entry point and then compile again.",
            )
            raise  # TODO: return something ignorable.

        print(stdout + "\n" + stderr)
        if stderr:
            pattern = r'Unable to open the include file "([^"\n]*)"'
            while "Unable to open the include file" in stderr:
                match: re.Match | None = re.search(pattern, stderr)
                include_path_str = QFileDialog.getExistingDirectory(
                    None,
                    f"Script requires include file '{Path(match[1]).name if match else '<unknown>'}', please choose the directory it's in.",
                    options=QFileDialog.Options(),
                )
                if not include_path_str or not include_path_str.strip():
                    print("user cancelled include dir lookup for nss compilation with nwnnsscomp")
                    break
                include_path = Path(include_path_str)
                source_nss_lowercase = source.lower()
                for file in include_path.rglob("*"):
                    if file.stem.lower() not in source_nss_lowercase and file.stem.lower() not in stderr.lower():
                        continue
                    if ResourceIdentifier.from_path(file).restype != ResourceType.NSS:
                        print(f"{file.name} is not an NSS script, skipping...")
                        continue
                    if not file.safe_isfile():
                        print(f"{file.name} is a directory, skipping...")
                        continue
                    new_include_script_path = extract_path / file.name

                    print(f"Copying include script '{file}' to '{new_include_script_path}'")
                    BinaryWriter.dump(new_include_script_path, BinaryReader.load_file(file))

                stdout, stderr = extCompiler.compile_script(tempSourcePath, tempCompiledPath, gameEnum)
                print(stdout + "\n" + stderr)
            if "Error: Syntax error" in stderr:
                raise ValueError(stdout + "\n" + stderr)

        # TODO(written by NickHugi): The version of nwnnsscomp bundled with the windows toolset uses registry key lookups.
        # I do not think this version matches the versions used by Mac/Linux.
        # Need to try unify this so each platform uses the same version and try
        # move away from registry keys (I don't even know how Mac/Linux determine KotOR's installation path).

        if not tempCompiledPath.safe_isfile():
            raise FileNotFoundError(f"Could not find temp compiled script at '{tempCompiledPath}'")  # noqa: TRY003, EM102
    finally:
        if orig_regkey_value and orig_regkey_path and orig_regkey_value != str(installation_path):
            with suppress(PermissionError):
                set_registry_key_value(orig_regkey_path, "Path", orig_regkey_value)

    return BinaryReader.load_file(tempCompiledPath)


def _prompt_user_for_compiler_option() -> int:
    # Create the message box
    msgBox = QMessageBox()

    # Set the message box properties
    msgBox.setIcon(QMessageBox.Question)
    msgBox.setWindowTitle("Choose a NCS compiler")
    msgBox.setText("Would you like to use 'nwnnsscomp.exe' or Holocron Toolset's built-in compiler?")
    msgBox.setInformativeText("Choose one of the options below:")
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Abort)
    msgBox.setDefaultButton(QMessageBox.Abort)

    # Set the button text
    msgBox.button(QMessageBox.Yes).setText("Built-In Compiler")  # type: ignore[union-attr]
    msgBox.button(QMessageBox.No).setText("nwnnsscomp.exe")  # type: ignore[union-attr]
    msgBox.button(QMessageBox.Abort).setText("Cancel")  # type: ignore[union-attr]

    return msgBox.exec_()
