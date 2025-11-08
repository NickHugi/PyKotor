from __future__ import annotations

import os
import re
import uuid

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtWidgets import QFileDialog, QMessageBox

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryWriter
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.ncs.compiler.classes import EntryPointError
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, KnownExternalCompilers
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.resource.type import ResourceType
from pykotor.tools.registry import SpoofKotorRegistry
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError

if TYPE_CHECKING:
    from typing_extensions import LiteralString

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


log = RobustLogger()

class NoOpRegistrySpoofer:
    def __enter__(self):
        log.debug("Enter NoOpRegistrySpoofer")
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug(f"NoOpRegistrySpoofer.__exit__({exc_type}, {exc_val}, {exc_tb})")


def ht_decompile_script(
    compiled_bytes: bytes,
    installation_path: Path,
    *,
    tsl: bool,
) -> str:
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
    extract_path: Path = setup_extract_path()

    ncs_decompiler_path = Path(global_settings.ncsDecompilerPath)
    if (
        not ncs_decompiler_path.name
        or ncs_decompiler_path.suffix.lower() != ".exe"  # TODO: require something with Xoreos-tools on unix and make this nt-specific.
        or not ncs_decompiler_path.is_file()
    ):
        lookup_path, _filter = QFileDialog.getOpenFileName(None, "Select the NCS Decompiler executable")
        ncs_decompiler_path = Path(lookup_path)
        if not ncs_decompiler_path.is_file():
            global_settings.ncsDecompilerPath = ""
            msg = "NCS Decompiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.extractPath = str(extract_path)
    global_settings.ncsDecompilerPath = str(ncs_decompiler_path)

    tempscript_filestem: str = f"tempscript_{uuid.uuid1().hex[:7]}"
    tempCompiledPath: Path = extract_path / f"{tempscript_filestem}.ncs"
    temp_decompiled_path: Path = extract_path / f"{tempscript_filestem}_decompiled.txt"
    BinaryWriter.dump(tempCompiledPath, compiled_bytes)

    gameEnum: Game = Game.K2 if tsl else Game.K1
    extCompiler = ExternalNCSCompiler(global_settings.nssCompilerPath)

    # Use polymorphism to allow easy conditional usage of the registry spoofer.
    reg_spoofer: SpoofKotorRegistry | NoOpRegistrySpoofer
    if extCompiler.get_info() in {
        KnownExternalCompilers.KOTOR_SCRIPTING_TOOL,
        KnownExternalCompilers.KOTOR_TOOL,
    }:
        reg_spoofer = SpoofKotorRegistry(installation_path, gameEnum)
    else:
        reg_spoofer = NoOpRegistrySpoofer()
    try:
        with reg_spoofer:
            stdout, stderr = extCompiler.decompile_script(tempCompiledPath, temp_decompiled_path, gameEnum)
    except PermissionError as e:
        handle_permission_error(reg_spoofer, extCompiler, installation_path, e)
        # Attempt to decompile anyway.
        stdout, stderr = extCompiler.decompile_script(tempCompiledPath, temp_decompiled_path, gameEnum)
    except Exception:
        log.exception("Exception in extCompiler.decompile_script() call.")
        raise
    log.debug("stdout: %s\nstderr: %s", stdout, stderr)
    if stderr:
        raise ValueError(stderr)  # noqa: TRY301
    return temp_decompiled_path.read_text(encoding="windows-1252")

def setup_extract_path() -> Path:
    global_settings = GlobalSettings()
    extract_path = Path(global_settings.extractPath)

    if not extract_path.is_dir():
        extract_path_str = QFileDialog.getExistingDirectory(None, "Select a temp directory")
        extract_path = Path(extract_path_str) if extract_path_str else None
        if not extract_path or not extract_path.is_dir():
            msg = "Temp directory has not been set or is invalid."
            raise NoConfigurationSetError(msg)
    return extract_path

def ht_compile_script(
    source: str,
    installation_path: Path,
    *,
    tsl: bool,
) -> bytes | None:
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
    extract_path: Path = setup_extract_path()

    return_value: int | None = None
    if os.name == "nt":
        return_value = _prompt_user_for_compiler_option()

    if os.name == "posix" or return_value == QMessageBox.StandardButton.Yes:
        log.debug("user chose Yes, compiling with builtin")
        return bytes(bytes_ncs(compile_nss(source, Game.K2 if tsl else Game.K1, library_lookup=[extract_path])))
    if return_value == QMessageBox.StandardButton.No:
        log.debug("user chose No, compiling with nwnnsscomp")
        return _execute_nwnnsscomp_compile(global_settings, extract_path, source, installation_path, tsl=tsl)
    if return_value is not None:  # user cancelled
        log.debug("user exited")
        return None

    # This should never be reached, leave in for static type checkers.
    raise ValueError("Could not get the NCS bytes.")  # noqa: TRY003, EM101

def _prompt_additional_include_dirs(  # noqa: PLR0913
    extCompiler: ExternalNCSCompiler,
    source: str,
    stderr: str,
    tempSourcePath: os.PathLike | str,
    tempCompiledPath: os.PathLike | str,
    extract_path: Path,
    gameEnum: Game,
) -> tuple[str, str]:
    stdout = ""
    include_missing_errstr = "Unable to open the include file"
    pattern: LiteralString = rf'{include_missing_errstr} "([^"\n]*)"'
    while include_missing_errstr in stderr:
        match: re.Match | None = re.search(pattern, stderr)
        include_path_str = QFileDialog.getExistingDirectory(
            None,
            f"Script requires include file '{Path(match[1]).name if match else '<unknown>'}', please choose the directory it's in.",
            options=QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        if not include_path_str or not include_path_str.strip():
            log.debug("user cancelled include dir lookup for nss compilation with nwnnsscomp")
            break
        include_path = Path(include_path_str)
        source_nss_lowercase = source.lower()

        # Copy the include files at the path to the compilation working dir.
        for file in include_path.rglob("*"):
            if file.stem.lower() not in source_nss_lowercase and file.stem.lower() not in stderr.lower():
                continue  # Skip any files in the include_path that aren't referenced by the script (faster)

            if ResourceIdentifier.from_path(file).restype is not ResourceType.NSS:
                log.debug("%s is not an NSS script, skipping...", file.name)
                continue
            if not file.is_file():
                log.debug("%s is a directory, skipping...", file.name)
                continue
            new_include_script_path = extract_path / file.name

            log.info("Copying include script '%s' to '%s'", file, new_include_script_path)
            new_include_script_path.write_bytes(file.read_bytes())

        stdout, stderr = extCompiler.compile_script(tempSourcePath, tempCompiledPath, gameEnum)
        log.debug("stdout: %s\nstderr: %s", stdout, stderr)

    return stdout, stderr

def _execute_nwnnsscomp_compile(
    global_settings: GlobalSettings,
    extract_path: Path,
    source: str,
    installation_path: Path,
    *,
    tsl: bool,
) -> bytes:
    nss_compiler_path = Path(global_settings.nssCompilerPath)
    if not nss_compiler_path.is_file():
        lookup_path, _ = QFileDialog.getOpenFileName(None, "Select the NCS Compiler executable")
        nss_compiler_path = Path(lookup_path)
        if not nss_compiler_path.is_file():
            msg = "NCS Compiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.nssCompilerPath = str(nss_compiler_path)

    tempscript_filestem: str = f"tempscript_{uuid.uuid1().hex[:7]}"
    tempSourcePath: Path = extract_path / f"{tempscript_filestem}.nss"
    tempCompiledPath: Path = extract_path / f"{tempscript_filestem}.ncs"
    tempSourcePath.write_text(source)

    gameEnum: Game = Game.K2 if tsl else Game.K1
    extCompiler = ExternalNCSCompiler(global_settings.nssCompilerPath)

    def _try_compile_script():
        try:
            stdout, stderr = extCompiler.compile_script(tempSourcePath, tempCompiledPath, gameEnum)
            log.debug("stdout: %s\nstderr: %s", stdout, stderr)
        except EntryPointError:
            QMessageBox.warning(
                None,
                "Include scripts cannot be compiled",
                "This script is an include script, compiling it serves no purpose. If this warning is incorrect, check that your script has an entry point and then compile again.",
            )
            raise  # TODO(th3w1zard1): return something ignorable.
        else:
            if stderr:
                stdout, stderr = _prompt_additional_include_dirs(
                    extCompiler,
                    source,
                    stderr,
                    tempSourcePath,
                    tempCompiledPath,
                    extract_path,
                    gameEnum
                )
            if stderr:
                raise ValueError(f"{stdout}\n{stderr}")

    # Use polymorphism to allow easy conditional usage of the registry spoofer.
    reg_spoofer: SpoofKotorRegistry | NoOpRegistrySpoofer
    if extCompiler.get_info() in {
        KnownExternalCompilers.KOTOR_SCRIPTING_TOOL,
        KnownExternalCompilers.KOTOR_TOOL,
    }:
        reg_spoofer = SpoofKotorRegistry(installation_path, gameEnum)
    else:
        reg_spoofer = NoOpRegistrySpoofer()

    # Compile the script with nwnnsscomp.
    try:
        with reg_spoofer:
            _try_compile_script()
    except PermissionError as e:
        handle_permission_error(reg_spoofer, extCompiler, installation_path, e)
        # Spoofing was required but failed, attempt to compile anyway...
        _try_compile_script()

    # TODO(NickHugi): The version of nwnnsscomp bundled with the windows toolset uses registry key lookups.
    # I do not think this version matches the versions used by Mac/Linux.
    # Need to try unify this so each platform uses the same version and try
    # move away from registry keys (I don't even know how Mac/Linux determine KotOR's installation path).

    # All the abstraction work is now complete... verify the file exists one last time then return the compiled script's data.
    if not tempCompiledPath.is_file():
        import errno
        raise FileNotFoundError(errno.ENOENT, "Could not find the temp compiled script!", str(tempCompiledPath))  # noqa: TRY003, EM102
    return tempCompiledPath.read_bytes()


def handle_permission_error(
    reg_spoofer: SpoofKotorRegistry | NoOpRegistrySpoofer,
    extCompiler: ExternalNCSCompiler,
    installation_path: Path,
    e: PermissionError,
):
    if isinstance(reg_spoofer, NoOpRegistrySpoofer):
        raise

    # Spoofing was required but failed. Show the relevant message.
    msg: str = NON_TSLPATCHER_NWNNSSCOMP_PERMISSION_MSG.format(
        extCompiler.get_info().value.name,
        reg_spoofer.registry_path,
        installation_path,
        reg_spoofer.original_value,
        str(e),
    )
    log.warning(msg.replace("<br>", "\n"))
    longMsgBoxErr = QMessageBox(
        QMessageBox.Icon.Warning,
        "Permission denied when attempting to update nwnnsscomp in registry",
        msg,
    )
    longMsgBoxErr.setIcon(QMessageBox.Icon.Warning)
    longMsgBoxErr.exec()


def _prompt_user_for_compiler_option() -> int:
    # Create the message box
    msgBox = QMessageBox()

    # Set the message box properties
    msgBox.setIcon(QMessageBox.Icon.Question)
    msgBox.setWindowTitle("Choose a NCS compiler")
    msgBox.setText("Would you like to use 'nwnnsscomp.exe' or Holocron Toolset's built-in compiler?")
    msgBox.setInformativeText("Choose one of the options below:")
    msgBox.setStandardButtons(
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
        | QMessageBox.StandardButton.Abort
    )
    msgBox.setDefaultButton(QMessageBox.StandardButton.Abort)

    # Set the button text
    msgBox.button(QMessageBox.StandardButton.Yes).setText("Built-In Compiler")  # type: ignore[union-attr]
    msgBox.button(QMessageBox.StandardButton.No).setText("nwnnsscomp.exe")  # type: ignore[union-attr]
    msgBox.button(QMessageBox.StandardButton.Abort).setText("Cancel")  # type: ignore[union-attr]

    return msgBox.exec()
