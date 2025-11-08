from __future__ import annotations

import uuid

from pathlib import Path

from loggerplus import RobustLogger
from qtpy.QtWidgets import QFileDialog

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, KnownExternalCompilers
from pykotor.tools.registry import SpoofKotorRegistry
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from toolset.utils.script_utils import NoOpRegistrySpoofer, handle_permission_error, setup_extract_path

log = RobustLogger()

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