from __future__ import annotations

import os
import sys

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.tools.path import CaseAwarePath
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from utility.error_handling import format_exception_with_variables
from utility.path import Path


def decompileScript(compiled: bytes, tsl: bool) -> str:
    """Returns the NSS bytes of a decompiled script. If no NCS Decompiler is selected, prompts the user to find the executable.

    Current implementation copies the NCS to a temporary directory (configured in settings), decompiles it there,
    then returns the bytes of the new file. If no temporary directory has been configured, the user is prompted to
    select a folder. If no NCS decompiler filepath has been configured, the user is prompted to select an executable.

    Args:
    ----
        compiled: The bytes of the compiled script.
        tsl: Compile the script for TSL instead of KotOR.

    Raises:
    ------
        OSError: If an error occured writing or loading from the temp directory.
        ValueError: If the source script failed to compile.
        NoConfigurationSet: If no path has been set for the temp directory or NSS decompiler.

    Returns:
    -------
        The string of the decompiled script.
    """
    global_settings = GlobalSettings()
    extract_path = Path(global_settings.extractPath)

    if not extract_path.exists():
        extract_path = Path(QFileDialog.getExistingDirectory(None, "Select a temp directory"))
        if not extract_path.exists():
            msg = "Temp directory has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    ncs_decompiler_path = Path(global_settings.ncsDecompilerPath)
    if not ncs_decompiler_path.name or ncs_decompiler_path.suffix.lower() != ".exe" or not ncs_decompiler_path.exists():
        ncs_decompiler_path, _ = QFileDialog.getOpenFileName(None, "Select the NCS Decompiler executable")
        ncs_decompiler_path = Path(ncs_decompiler_path)
        if not ncs_decompiler_path.exists():
            global_settings.ncsDecompilerPath = ""
            msg = "NCS Decompiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.extractPath = str(extract_path)
    global_settings.ncsDecompilerPath = str(ncs_decompiler_path)

    tempCompiledPath = extract_path / "tempscript.ncs"
    tempDecompiledPath = extract_path / "tempscript_decompiled.nss"
    BinaryWriter.dump(tempCompiledPath, compiled)

    try:
        game = Game.K2 if tsl else Game.K1
        ExternalNCSCompiler(ncs_decompiler_path).decompile_script(tempCompiledPath, tempDecompiledPath, game)
        return BinaryReader.load_file(tempDecompiledPath).decode(encoding="windows-1252")
    except Exception as e:  # noqa: BLE001
        with Path("errorlog.txt").open("w") as f:
            msg = format_exception_with_variables(e)
            print(msg, sys.stderr)  # noqa: T201
            f.write(msg)

    return ""


def compileScript(source: str, tsl: bool) -> bytes | None:
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

    if not extract_path.safe_exists():
        extract_path = Path(QFileDialog.getExistingDirectory(None, "Select a temp directory"))
        if not extract_path.safe_exists():
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
        return _compile_windows(global_settings, extract_path, source, tsl)
    if returnValue is not None:  # user cancelled
        print("user exited")
        return None

    raise ValueError("Could not get the NCS bytes.")  # noqa: TRY003, EM101

def _compile_windows(
    global_settings: GlobalSettings,
    extract_path: Path,
    source: str,
    tsl: bool,
) -> bytes:
    nss_compiler_path = Path(global_settings.nssCompilerPath)
    if not nss_compiler_path.safe_exists():
        lookup_path, _ = QFileDialog.getOpenFileName(None, "Select the NCS Compiler executable")
        nss_compiler_path = Path(lookup_path)
        if not nss_compiler_path.safe_exists():
            msg = "NCS Compiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.extractPath = str(extract_path)
    global_settings.nssCompilerPath = str(nss_compiler_path)

    tempSourcePath = extract_path / "tempscript.nss"
    tempCompiledPath = extract_path / "tempscript.ncs"
    BinaryWriter.dump(tempSourcePath, source.encode(encoding="windows-1252"))

    gameEnum: Game = Game.K2 if tsl else Game.K1
    stdout, stderr = ExternalNCSCompiler(global_settings.nssCompilerPath).compile_script(tempSourcePath, tempCompiledPath, gameEnum)
    print(stdout + "\n" + stderr)
    if stderr or "Error: Syntax error" in stdout:
        raise ValueError(stdout + "\n" + stderr)

    # TODO(Cortisol): The version of nwnnsscomp bundled with the windows toolset uses registry key lookups.
    # I do not think this version matches the versions used by Mac/Linux.
    # Need to try unify this so each platform uses the same version and try
    # move away from registry keys (I don't even know how Mac/Linux determine KotOR's installation path).

    if not tempCompiledPath.exists():
        raise FileNotFoundError(f"Could not find temp compiled script at {tempCompiledPath}")  # noqa: TRY003, EM102
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
