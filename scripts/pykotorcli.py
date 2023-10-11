from __future__ import annotations

import argparse
import sys
from enum import IntEnum

from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.config import ModInstaller, PatcherNamespace
from pykotor.tslpatcher.reader import NamespaceReader


class ExitCode(IntEnum):
    SUCCESS = 0
    NUMBER_OF_ARGS = 1
    NAMESPACES_INI_NOT_FOUND = 2
    NAMESPACE_INDEX_OUT_OF_RANGE = 3
    CHANGES_INI_NOT_FOUND = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TSLPatcher CLI written in PyKotor")

    # Positional arguments for the old syntax
    parser.add_argument("--game-dir", type=str, help="Path to game directory")
    parser.add_argument("--tslpatchdata", type=str, help="Path to tslpatchdata")
    parser.add_argument(
        "--namespace-option-index",
        type=int,
        help="Namespace option index",
    )

    # Add additional named arguments here if needed

    args, unknown = parser.parse_known_args()

    # If using the old syntax, we'll manually parse the first three arguments
    if len(unknown) >= 2:
        args.game_dir = unknown[0]
        args.tslpatchdata = unknown[1]
        if len(unknown) == 3:
            try:
                args.namespace_option_index = int(unknown[2])
            except ValueError:
                print("Invalid namespace_option_index. It should be an integer.")
                sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)

    return args


def main():
    args = parse_args()

    if args.game_dir is None or args.tslpatchdata is None:
        print(
            'Syntax: pykotorcli.exe ["\\path\\to\\game\\dir"] ["\\path\\to\\tslpatchdata"] {"namespace_option_index"}',
        )
        sys.exit(ExitCode.NUMBER_OF_ARGS)

    game_path: CaseAwarePath = CaseAwarePath(args.game_dir).resolve()  # argument 1
    tslpatchdata_path: CaseAwarePath = CaseAwarePath(
        args.tslpatchdata,
    ).resolve()  # argument 2
    namespace_index: int | None = None  # argument 3
    changes_ini_path: CaseAwarePath

    if len(sys.argv) == 3:
        changes_ini_path = CaseAwarePath(
            tslpatchdata_path,
            "tslpatchdata",
            "changes.ini",
        ).resolve()
    elif len(sys.argv) == 4:
        namespace_index = int(args.namespace_option_index)
        changes_ini_path = determine_namespaces(
            tslpatchdata_path,
            namespace_index,
        )
    else:
        sys.exit(ExitCode.CHANGES_INI_NOT_FOUND)

    print(f"Using changes.ini path: {str(changes_ini_path)!s}")
    if not changes_ini_path.exists():
        print(
            "The 'changes.ini' file does not exist anywhere in the tslpatchdata provided.",
        )
        sys.exit(ExitCode.CHANGES_INI_NOT_FOUND)

    mod_path: CaseAwarePath = changes_ini_path.parent
    ini_name: str = changes_ini_path.name

    installer = ModInstaller(mod_path, game_path, ini_name)

    # def profile_installation():

    installer.install()

    print("Writing log file 'installlog.txt'...")
    log_file_path: CaseAwarePath = tslpatchdata_path / "installlog.txt"
    with log_file_path.open("w", encoding="utf-8") as log_file:
        for log in installer.log.all_logs:
            log_file.write(f"{log.message}\n")

    print("Logging finished")
    sys.exit(ExitCode.SUCCESS)


def determine_namespaces(
    tslpatchdata_path: CaseAwarePath,
    namespace_index: int,
) -> CaseAwarePath:
    try:
        namespace_index = int(sys.argv[3])
    except ValueError:
        print("Invalid namespace_option_index. It should be an integer.")
        sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)

    namespaces_ini_path: CaseAwarePath = CaseAwarePath(
        tslpatchdata_path,
        "tslpatchdata",
        "namespaces.ini",
    )
    print(f"Using namespaces.ini path: {namespaces_ini_path}")
    if not namespaces_ini_path.exists():
        print(
            "The 'namespaces.ini' file was not found in the specified tslpatchdata path.",
        )
        sys.exit(ExitCode.NAMESPACES_INI_NOT_FOUND)

    loaded_namespaces: list[PatcherNamespace] = NamespaceReader.from_filepath(namespaces_ini_path)
    if namespace_index >= len(loaded_namespaces):
        print("Namespace index is out of range.")
        sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)

    return (
        tslpatchdata_path.joinpath(
            "tslpatchdata",
            loaded_namespaces[namespace_index].data_folderpath,
            loaded_namespaces[namespace_index].ini_filename,
        )
        if loaded_namespaces[namespace_index].data_folderpath
        else tslpatchdata_path.joinpath(
            "tslpatchdata",
            loaded_namespaces[namespace_index].ini_filename,
        )
    )


main()
sys.exit()
