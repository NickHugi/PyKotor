from __future__ import annotations

import sys
from argparse import ArgumentParser
from enum import IntEnum

from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.config import ModInstaller, PatcherNamespace
from pykotor.tslpatcher.reader import NamespaceReader


class ExitCode(IntEnum):
    SUCCESS = 0
    INCORRECT_ARGUMENTS = 1
    NAMESPACE_INDEX_OUT_OF_RANGE = 2
    NAMESPACES_INI_NOT_FOUND = 3
    TSLPATCHDATA_NOT_FOUND = 4
    CHANGES_INI_NOT_FOUND = 5
    KOTOR_PATH_NOT_FOUND = 6


def exit_with_incorrect_args(parser: ArgumentParser, reason_msg=None, exit_code=None):
    if reason_msg:
        print("Invalid Syntax")
        print(reason_msg)
    parser.print_help()
    print('Legacy Syntax: pykotorcli.exe ["\\path\\to\\game\\dir"] ["\\path\\to\\tslpatchdata"] {"namespace_option_index"}')
    sys.exit(exit_code or ExitCode.INCORRECT_ARGUMENTS)


def parse_args():
    parser = ArgumentParser(description="PyKotorCLI - A TSLPatcher CLI using the PyKotor library.")

    # Positional arguments for the old syntax
    parser.add_argument(
        "--game-dir",
        type=str,
        help="Path to game directory. If not specified, will parse the ini for the LookupGameFolder. If set to 1, this will autolookup based on the registry.",
    )
    parser.add_argument(
        "--tslpatchdata",
        type=str,
        help="Path to the tslpatchdata folder. If not specified, will attempt to resolve using the --changes-ini filepath.",
    )
    parser.add_argument(
        "--changes-ini",
        type=str,
        help="Path to (or the name of) the changes ini file to install. Incompatible with --namespace-option-index.",
    )
    parser.add_argument(
        "--uninstall",
        type=str,
        help="Uninstall the selected mod (not currently implemented - see the TODO section)",
    )
    parser.add_argument(
        "--namespace-option-index",
        type=int,
        help="Namespace option index. PyKotor builds each namespaces.ini option into a list, indexed by 0. The namespace option index does not rely on key/value pairs in namespaces.ini, it instead flattens all available options into a 0 based list top to bottom.",
    )

    # Add additional named arguments here if needed

    args, legacy_positional_args = parser.parse_known_args()

    # If using the old syntax, we'll manually parse the first three arguments
    if len(legacy_positional_args) >= 2:
        if args.tslpatchdata or args.namespace_option_index:
            exit_with_incorrect_args(
                parser,
                "Positional arguments are not allowed if using arg --tslpatchdata or arg --namespace-option-index",
            )
        args.game_dir = legacy_positional_args[0]
        args.tslpatchdata = legacy_positional_args[1]
        if len(legacy_positional_args) == 3:
            args.namespace_option_index = legacy_positional_args[2]

    tslpatchdata_path: CaseAwarePath | None = CaseAwarePath(args.tslpatchdata) if args.tslpatchdata else None
    changes_ini_path: CaseAwarePath | None = CaseAwarePath(args.changes_ini) if args.changes_ini else None
    game_dir: CaseAwarePath | None = CaseAwarePath(args.game_dir)

    if changes_ini_path and not changes_ini_path.suffix:
        exit_with_incorrect_args(parser, "--changes-ini argument must be a filename with the ini extension.")
    if changes_ini_path and changes_ini_path.is_absolute():
        # Find tslpatchdata in the path heirarchy of an absolute changes_ini
        if tslpatchdata_path:
            if tslpatchdata_path.name.lower() != "tslpatchdata":
                tslpatchdata_path = tslpatchdata_path / "tslpatchdata"
            if not tslpatchdata_path.exists():
                exit_with_incorrect_args(parser, "--tslpatchdata must point to the tslpatchdata folder on disk.")
            # Ensure changes_ini_path is a decendent of tslpatchdata_path
            try:
                assert changes_ini_path.relative_to(tslpatchdata_path)
            except ValueError:
                exit_with_incorrect_args(parser, "--changes-ini must be a child of --tslpatchdata folder.")
        else:
            tslpatchdata_path = changes_ini_path.parent
            while tslpatchdata_path.name.lower() != "tslpatchdata" and tslpatchdata_path != tslpatchdata_path.parent:
                tslpatchdata_path = changes_ini_path.parent
            if tslpatchdata_path == tslpatchdata_path.parent:
                exit_with_incorrect_args(parser, "--changes-ini must be a descendent of the mod's tslpatchdata folder")
    elif changes_ini_path:
        if not tslpatchdata_path:
            exit_with_incorrect_args(parser, "--changes-ini must be a full path if --tslpatchdata is not provided.")
        if tslpatchdata_path.name.lower() != "tslpatchdata":
            tslpatchdata_path = tslpatchdata_path / "tslpatchdata"
        # If changes_ini is a relative path or filename, join it with tslpatchdata
        changes_ini_path = tslpatchdata_path / changes_ini_path
    if not tslpatchdata_path:
        exit_with_incorrect_args(parser, "Please pass either --changes-ini and/or --tslpatchdata")
    elif args.namespace_option_index:
        if changes_ini_path:
            exit_with_incorrect_args(parser, "Cannot pass both --changes-ini and --namespace-option-index.")
        namespace_option_index: int | None = None
        try:
            namespace_option_index = int(args.namespace_option_index)
        except ValueError:
            exit_with_incorrect_args(
                parser,
                "Invalid namespace option index. Must be a 0-based integer index of namespaces.ini",
            )
        assert isinstance(namespace_option_index, int)
        changes_ini_path = determine_namespaces(
            tslpatchdata_path,
            namespace_option_index,
        )
    if tslpatchdata_path.name.lower() != "tslpatchdata":
        tslpatchdata_path = tslpatchdata_path / "tslpatchdata"
    if not changes_ini_path:
        changes_ini_path = tslpatchdata_path / "changes.ini"
    if game_dir is None:
        exit_with_incorrect_args(parser, "--game-dir must be passed!")

    args.tslpatchdata_path = tslpatchdata_path.resolve()
    args.changes_ini_path = changes_ini_path.resolve()
    args.game_dir_path = game_dir.resolve()

    if not tslpatchdata_path.exists():
        exit_with_incorrect_args(
            parser,
            f"tslpatchdata folder path '{tslpatchdata_path}' not found on disk.",
            ExitCode.TSLPATCHDATA_NOT_FOUND,
        )
    if not changes_ini_path.exists():
        exit_with_incorrect_args(
            parser,
            f"changes ini path '{changes_ini_path}' not found on disk.",
            ExitCode.CHANGES_INI_NOT_FOUND,
        )
    if not game_dir.exists():
        exit_with_incorrect_args(
            parser,
            "--game-dir not found on disk!",
            ExitCode.KOTOR_PATH_NOT_FOUND,
        )

    print(f"Using changes.ini path: '{str(args.changes_ini_path)!s}'")
    print(f"Using game path: '{str(args.game_dir_path)!s}'")

    return args


def install(parsed_args):
    installer = ModInstaller(
        mod_path=parsed_args.tslpatchdata_path,
        game_path=parsed_args.game_dir_path,
        changes_ini_path=parsed_args.changes_ini_path,
    )
    installer.install()

    print("Writing log file 'installlog.txt'...")
    log_file_path: CaseAwarePath = parsed_args.tslpatchdata_path.parent / "installlog.txt"
    with log_file_path.open("ax", encoding="utf-8") as log_file:
        for log in installer.log.all_logs:
            log_file.write(f"{log.message}\n")

    print("Logging finished")


# TODO(th3w1zard1): Should load the patches from the changes ini similar to install() and undo them (the inverse of installer.install())
# for example if a [InstallList] installs into a .mod archive, we should instead remove it.
# Might be difficult to determine if the file/resource already exists due to low granularity provided by changes ini.
# Perhaps we could just copy the files from the most recent backup created back to the kotor dir.
# Copying the backup would work, we'd also need the backup to write the state of the kotor directory.
# This would allow us to determine if another mod was already installed on top of the one being uninstalled. Could output something like:
# 'file doesn't match what this mod installed, please first uninstall the other mod. Continue anyway? (y/N)'
def uninstall(parsed_args):
    print("An uninstall is not currently implemented. Please copy the files manually from the backup folder instead.")


def main():
    parsed_args = parse_args()
    if parsed_args.uninstall:
        uninstall(parsed_args)
    else:
        install(parsed_args)


def determine_namespaces(
    tslpatchdata_path: CaseAwarePath,
    namespace_index: int,
) -> CaseAwarePath:
    namespaces_ini_path: CaseAwarePath = CaseAwarePath(
        tslpatchdata_path,
        "namespaces.ini",
    )
    print(f"Using namespaces.ini path: {namespaces_ini_path} from provided list index {namespace_index}")
    if not namespaces_ini_path.exists():
        print("The 'namespaces.ini' file was not found in the specified tslpatchdata path.")
        sys.exit(ExitCode.NAMESPACES_INI_NOT_FOUND)

    loaded_namespaces: list[PatcherNamespace] = NamespaceReader.from_filepath(namespaces_ini_path)
    if namespace_index >= len(loaded_namespaces):
        print("Namespace index is out of range. Must be a zero-based integer list index from the namespaces.ini")
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
sys.exit(ExitCode.SUCCESS)
