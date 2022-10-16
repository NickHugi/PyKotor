import os
import subprocess

from PyQt5.QtWidgets import QFileDialog

from gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from pykotor.common.stream import BinaryWriter, BinaryReader


def decompileScript(compiled: bytes, tsl: bool) -> str:
    """
    Returns the NSS bytes of a decompiled script. If no NCS Decompiler is selected, prompts the user to find the
    executable.

    Current implementation copies the NCS to a temporary directory (configured in settings), decompiles it there,
    then returns the bytes of the new file. If no temporary directory has been configured, the user is prompted to
    select a folder. If no NCS decompiler filepath has been configured, the user is prompted to select an executable.

    Args:
        compiled: The bytes of the compiled script.
        tsl: Compile the script for TSL instead of KotOR.

    Raises:
        IOError: If an error occured writing or loading from the temp directory.
        ValueError: If the source script failed to compile.
        NoConfigurationSet: If no path has been set for the temp directory or NSS decompiler.

    Returns:
        The string of the decompiled script.
    """
    global_settings = GlobalSettings()

    if not os.path.exists(global_settings.extractPath):
        global_settings.extractPath = QFileDialog.getExistingDirectory(None, "Select a temp directory")
        if not os.path.exists(global_settings.extractPath):
            raise NoConfigurationSetError("Temp directory has not been set or is invalid.")

    if not os.path.exists(global_settings.ncsDecompilerPath):
        global_settings.ncsDecompilerPath, _ = QFileDialog.getOpenFileName(None, "Select the NCS Decompiler executable")
        if not os.path.exists(global_settings.ncsDecompilerPath):
            raise NoConfigurationSetError("NCS Decompiler has not been set or is invalid.")

    tempCompiledPath = "{}/tempscript.ncs".format(global_settings.extractPath)
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
    """
    Returns the NCS bytes of compiled source script. If no NSS Compiler is selected, prompts the user to find the
    executable.

    Current implementation copies the NSS to a temporary directory (configured in settings), compiles it there,
    then returns the bytes of the new file. If no temporary directory has been configured, the user is prompted to
    select a folder. If no NSS compiler filepath has been configured, the user is prompted to select an executable.

    Args:
        source: The text of the source script.
        tsl: Compile the script for TSL instead of KotOR.

    Raises:
        IOError: If an error occured writing or loading from the temp directory.
        ValueError: If the source script failed to compile.
        NoConfigurationSet: If no path has been set for the temp directory or NSS compiler.

    Returns:
        Bytes object of the compiled script.
    """
    global_settings = GlobalSettings()

    if not os.path.exists(global_settings.extractPath):
        global_settings.extractPath = QFileDialog.getExistingDirectory(None, "Select a temp directory")
        if not os.path.exists(global_settings.extractPath):
            raise NoConfigurationSetError("Temp directory has not been set or is invalid.")

    if not os.path.exists(global_settings.nssCompilerPath):
        global_settings.nssCompilerPath, _ = QFileDialog.getOpenFileName(None, "Select the NCS Compiler executable")
        if not os.path.exists(global_settings.nssCompilerPath):
            raise NoConfigurationSetError("NCS Compiler has not been set or is invalid.")

    tempSourcePath = "{}/tempscript.nss".format(global_settings.extractPath)
    tempCompiledPath = "{}/tempscript.ncs".format(global_settings.extractPath)
    BinaryWriter.dump(tempSourcePath, source.encode())

    gameIndex = "2" if tsl else "1"
    command = [global_settings.nssCompilerPath, "-c", tempSourcePath, "--outputdir", global_settings.extractPath, "-g", gameIndex]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, shell=True)

    output = process.communicate()[0].decode()
    #output = output[output.index("Compiling: tempscript.nss") + 25:]
    #i think it works now lmao
    #it says it couldn't load NwnStdLoader and lookup path is broken but at the same time it compiled the NCS file
    #print(output[0:])
    error = "Compilation aborted with errors" in output

    if error:
        raise ValueError(output)

    return BinaryReader.load_file(tempCompiledPath)
