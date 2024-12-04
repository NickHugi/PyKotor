from __future__ import annotations

import os
import re
import uuid

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtWidgets import QFileDialog, QMessageBox

from pykotor.common.misc import Game
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.ncs.compiler.classes import EntryPointError
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, KnownExternalCompilers
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.resource.type import ResourceType
from pykotor.tools.registry import SpoofKotorRegistry
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from toolset.utils.script_utils import NoOpRegistrySpoofer, handle_permission_error, setup_extract_path

if TYPE_CHECKING:
    from typing_extensions import LiteralString

log = RobustLogger()

def ht_compile_script(
    source: str,
    installation_path: Path,
    *,
    tsl: bool,
) -> bytes | None:
    """Returns the NCS bytes of compiled source script using either nwnnsscomp.exe (Windows only) or our built-in compiler.

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

    # All the abstraction work is now complete... verify the file exists one last time then return the compiled script's data.
    if not tempCompiledPath.is_file():
        import errno
        raise FileNotFoundError(errno.ENOENT, "Could not find the temp compiled script!", str(tempCompiledPath))  # noqa: TRY003, EM102
    return tempCompiledPath.read_bytes()

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