import os
import sys

from enum import Enum
from pykotor.tslpatcher.config import ModInstaller
from pykotor.tslpatcher.reader import NamespaceReader

# Override the print function to flush immediately
def custom_print(*args, **kwargs):
    BUILTINS_PRINT(*args, **kwargs)
    sys.stdout.flush()

# Replace the built-in print function
BUILTINS_PRINT = print
print = custom_print

# Replace the print function in the imported modules
sys.modules["pykotor.tslpatcher.reader"].print = custom_print
sys.modules["pykotor.tslpatcher.config"].print = custom_print

class ExitCode(Enum):
    SUCCESS = 0
    NUMBER_OF_ARGS = 1
    NAMESPACES_INI_NOT_FOUND = 2
    NAMESPACE_INDEX_OUT_OF_RANGE = 3
    CHANGES_INI_NOT_FOUND = 4

if len(sys.argv) < 3 or len(sys.argv) > 4:
    print(
        'Syntax: pykotorcli.exe ["\\path\\to\\game\\dir"] ["\\path\\to\\tslpatchdata"] {"namespace_option_index"}'
    )
    sys.exit(ExitCode.NUMBER_OF_ARGS)


GAME_PATH = sys.argv[1]
TSLPATCHDATA_PATH = sys.argv[2]
NAMESPACE_INDEX = None
CHANGES_INI_PATH = None

if len(sys.argv) == 3:
    CHANGES_INI_PATH = os.path.join(TSLPATCHDATA_PATH, "tslpatchdata", "changes.ini")
elif len(sys.argv) == 4:
    try:
        NAMESPACE_INDEX = int(sys.argv[3])
    except ValueError:
        print("Invalid namespace_option_index. It should be an integer.")
        sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)
    namespaces_ini_path = os.path.join(TSLPATCHDATA_PATH, "tslpatchdata", "namespaces.ini")
    print(f"Using namespaces.ini path: {namespaces_ini_path}")
    if not os.path.exists(namespaces_ini_path):
        print("The 'namespaces.ini' file was not found in the specified tslpatchdata path.")
        sys.exit(ExitCode.NAMESPACES_INI_NOT_FOUND)
    loaded_namespaces = NamespaceReader.from_filepath(namespaces_ini_path)
    if NAMESPACE_INDEX is None or NAMESPACE_INDEX >= len(loaded_namespaces):
        print("Namespace index is out of range.")
        sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)
    if loaded_namespaces[NAMESPACE_INDEX].data_folderpath:
        CHANGES_INI_PATH = os.path.join(
            TSLPATCHDATA_PATH,
            "tslpatchdata",
            loaded_namespaces[NAMESPACE_INDEX].data_folderpath,
            loaded_namespaces[NAMESPACE_INDEX].ini_filename,
        )
    else:
        CHANGES_INI_PATH = os.path.join(
            TSLPATCHDATA_PATH, "tslpatchdata", loaded_namespaces[NAMESPACE_INDEX].ini_filename
        )

print(f"Using changes.ini path: {CHANGES_INI_PATH}")
if not os.path.exists(CHANGES_INI_PATH):
    print("The 'changes.ini' file could not be found.")
    sys.exit(ExitCode.CHANGES_INI_NOT_FOUND)

MOD_PATH = os.path.dirname(os.path.abspath(CHANGES_INI_PATH))
INI_NAME = os.path.basename(CHANGES_INI_PATH)

INSTALLER = ModInstaller(MOD_PATH, GAME_PATH, INI_NAME)
INSTALLER.install()

print("Writing log file 'installlog.txt'...")


LOG_FILE_PATH = os.path.join(TSLPATCHDATA_PATH, "installlog.txt")
with open(LOG_FILE_PATH, "w", encoding="utf-8") as log_file:
    for note in INSTALLER.log.notes:
        log_file.write(f"{note.message}\n")
    for warning in INSTALLER.log.warnings:
        log_file.write(f"Warning: {warning.message}\n")
    for error in INSTALLER.log.errors:
        log_file.write(f"Error: {error.message}\n")


print("Logging finished")

sys.exit()
