import subprocess

from PyQt5.QtWidgets import QFileDialog

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.tools.path import CaseAwarePath, Path
from toolset.gui.widgets.settings.installations import (
    GlobalSettings,
    NoConfigurationSetError,
)


def decompileScript(compiled: bytes, tsl: bool) -> str:
    """Returns the NSS bytes of a decompiled script. If no NCS Decompiler is selected, prompts the user to find the
    executable.

    Current implementation copies the NCS to a temporary directory (configured in settings), decompiles it there,
    then returns the bytes of the new file. If no temporary directory has been configured, the user is prompted to
    select a folder. If no NCS decompiler filepath has been configured, the user is prompted to select an executable.

    Args:
    ----
        compiled: The bytes of the compiled script.
        tsl: Compile the script for TSL instead of KotOR.

    Raises:
    ------
        IOError: If an error occured writing or loading from the temp directory.
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

    ncs_decompiler_path = CaseAwarePath(global_settings.ncsDecompilerPath)
    if not ncs_decompiler_path.exists():
        ncs_decompiler_path, _ = QFileDialog.getOpenFileName(None, "Select the NCS Decompiler executable")
        ncs_decompiler_path = Path(ncs_decompiler_path)
        if not ncs_decompiler_path.exists():
            msg = "NCS Decompiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.extractPath = str(extract_path)
    global_settings.ncsDecompilerPath = str(ncs_decompiler_path)

    tempCompiledPath = extract_path / "tempscript.ncs"
    BinaryWriter.dump(tempCompiledPath, compiled)

    gameIndex = "--kotor2" if tsl else "--kotor"
    command = [global_settings.ncsDecompilerPath, gameIndex, tempCompiledPath]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    output = process.communicate()[0].decode()
    error = process.communicate()[1].decode()

    if process.returncode:
        raise ValueError(error)

    return output


def compileScript(source: str, tsl: bool) -> bytes:
    """Returns the NCS bytes of compiled source script. If no NSS Compiler is selected, prompts the user to find the
    executable.

    Current implementation copies the NSS to a temporary directory (configured in settings), compiles it there,
    then returns the bytes of the new file. If no temporary directory has been configured, the user is prompted to
    select a folder. If no NSS compiler filepath has been configured, the user is prompted to select an executable.

    Args:
    ----
        source: The text of the source script.
        tsl: Compile the script for TSL instead of KotOR.

    Raises:
    ------
        IOError: If an error occured writing or loading from the temp directory.
        ValueError: If the source script failed to compile.
        NoConfigurationSet: If no path has been set for the temp directory or NSS compiler.

    Returns:
    -------
        Bytes object of the compiled script.
    """
    global_settings = GlobalSettings()
    extract_path = Path(global_settings.extractPath)

    if not extract_path.exists():
        extract_path = Path(QFileDialog.getExistingDirectory(None, "Select a temp directory"))
        if not extract_path.exists():
            msg = "Temp directory has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    nss_compiler_path = CaseAwarePath(global_settings.nssCompilerPath)
    if not nss_compiler_path.exists():
        nss_compiler_path, _ = QFileDialog.getOpenFileName(None, "Select the NCS Compiler executable")
        nss_compiler_path = Path(nss_compiler_path)
        if not nss_compiler_path.exists():
            msg = "NCS Compiler has not been set or is invalid."
            raise NoConfigurationSetError(msg)

    global_settings.extractPath = str(extract_path)
    global_settings.nssCompilerPath = str(nss_compiler_path)

    tempSourcePath = extract_path / "tempscript.nss"
    tempCompiledPath = extract_path / "tempscript.ncs"
    BinaryWriter.dump(tempSourcePath, source.encode())

    gameIndex = "2" if tsl else "1"
    command = [global_settings.nssCompilerPath, "-c", tempSourcePath, "--outputdir", global_settings.extractPath, "-g", gameIndex]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, shell=True)

    # TODO: Cortisol
    # The version of nwnnsscomp bundled with the windows toolset uses registry key lookups. I do not think this version
    # matches the versions used by Mac/Linux. Need to try unify this so each platform uses the same version and try
    # move away from registry keys (I don't even know how Mac/Linux determine KotOR's installation path).

    output = process.communicate()[0].decode()
    error = "Compilation aborted with errors" in output

    if error:
        raise ValueError(output)

    return BinaryReader.load_file(tempCompiledPath)
