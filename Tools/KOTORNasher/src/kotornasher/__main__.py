#!/usr/bin/env python3
"""KOTORNasher - A build tool for KOTOR projects.

This is a 1:1 implementation of nasher's syntax for KOTOR development.
"""
from __future__ import annotations

import os
import pathlib
import sys

from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

# Configure sys.path for development mode
if not getattr(sys, "frozen", False):

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        update_sys_path(utility_path.parent)
    kotornasher_path = pathlib.Path(__file__).parent
    if kotornasher_path.exists():
        update_sys_path(kotornasher_path.parent)

from kotornasher.commands import (  # noqa: E402
    cmd_compile,
    cmd_config,
    cmd_convert,
    cmd_init,
    cmd_install,
    cmd_launch,
    cmd_list,
    cmd_pack,
    cmd_unpack,
)
from kotornasher.config import VERSION  # noqa: E402
from kotornasher.logger import setup_logger  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Sequence


def create_parser() -> ArgumentParser:
    """Create the main argument parser."""
    parser = ArgumentParser(
        prog="kotornasher",
        description="A build tool for KOTOR projects (nasher-compatible syntax)",
    )

    # Global options
    parser.add_argument("--version", action="version", version=f"KOTORNasher {VERSION}")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("--yes", action="store_true", help="Automatically answer yes to all prompts")
    parser.add_argument("--no", action="store_true", help="Automatically answer no to all prompts")
    parser.add_argument("--default", action="store_true", help="Automatically accept the default answer to prompts")
    parser.add_argument("--verbose", action="store_true", help="Increase feedback verbosity")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (implies --verbose)")
    parser.add_argument("--quiet", action="store_true", help="Disable all logging except errors")
    parser.add_argument("--no-color", action="store_true", dest="no_color", help="Disable color output")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # config command
    config_parser = subparsers.add_parser(
        "config",
        help="Get, set, or unset user-defined configuration options",
    )
    config_parser.add_argument("key", nargs="?", help="Configuration key")
    config_parser.add_argument("value", nargs="?", help="Configuration value")
    config_parser.add_argument("--global", action="store_true", dest="global_config", help="Apply to all packages (default)")
    config_parser.add_argument("--local", action="store_true", help="Apply to current package only")
    config_parser.add_argument("--get", action="store_true", help="Get the value of key (default when value not passed)")
    config_parser.add_argument("--set", action="store_true", help="Set key to value (default when value is passed)")
    config_parser.add_argument("--unset", action="store_true", help="Delete the key/value pair for key")
    config_parser.add_argument("--list", action="store_true", help="List all key/value pairs in the config file")

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Create a new kotornasher package",
    )
    init_parser.add_argument("dir", nargs="?", default=".", help="Directory to initialize (default: current directory)")
    init_parser.add_argument("file", nargs="?", help="File to unpack into the new package")
    init_parser.add_argument("--default", action="store_true", help="Skip package generation dialog")
    init_parser.add_argument("--vcs", choices=["none", "git"], default="git", help="Version control system to use")
    init_parser.add_argument("--file", dest="init_file", help="File to unpack into the package")

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List all targets defined in kotornasher.cfg",
    )
    list_parser.add_argument("targets", nargs="*", help="Specific targets to list")
    list_parser.add_argument("--quiet", action="store_true", help="List only target names")
    list_parser.add_argument("--verbose", action="store_true", help="List source files as well")

    # unpack command
    unpack_parser = subparsers.add_parser(
        "unpack",
        help="Unpack a file into the project source tree",
    )
    unpack_parser.add_argument("target", nargs="?", help="Target to unpack")
    unpack_parser.add_argument("file", nargs="?", help="File to unpack")
    unpack_parser.add_argument("--file", dest="unpack_file", help="File or directory to unpack into the target's source tree")
    unpack_parser.add_argument("--removeDeleted", action="store_true", help="Remove source files not present in the file being unpacked")
    unpack_parser.add_argument("--no-removeDeleted", action="store_false", dest="removeDeleted", help="Do not remove source files not present in the file being unpacked")

    # convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert all JSON sources to their GFF counterparts",
    )
    convert_parser.add_argument("targets", nargs="*", default=[], help="Targets to convert (use 'all' for all targets)")
    convert_parser.add_argument("--clean", action="store_true", help="Clear the cache before converting")
    convert_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
    convert_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
    convert_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")

    # compile command
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile all nss sources for target",
    )
    compile_parser.add_argument("targets", nargs="*", default=[], help="Targets to compile (use 'all' for all targets)")
    compile_parser.add_argument("--clean", action="store_true", help="Clear the cache before compiling")
    compile_parser.add_argument("-f", "--file", action="append", dest="files", help="Compile specific file(s)")
    compile_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")

    # pack command
    pack_parser = subparsers.add_parser(
        "pack",
        help="Convert, compile, and pack all sources for target",
    )
    pack_parser.add_argument("targets", nargs="*", default=[], help="Targets to pack (use 'all' for all targets)")
    pack_parser.add_argument("--clean", action="store_true", help="Clear the cache before packing")
    pack_parser.add_argument("--file", dest="pack_file", help="Specify the location for the output file")
    pack_parser.add_argument("--noConvert", action="store_true", help="Do not convert updated json files")
    pack_parser.add_argument("--noCompile", action="store_true", help="Do not recompile updated scripts")
    pack_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")
    pack_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
    pack_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
    pack_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")
    pack_parser.add_argument("--abortOnCompileError", action="store_true", help="Abort packing if errors encountered during compilation")
    pack_parser.add_argument("--packUnchanged", action="store_true", help="Continue packing if there are no changed files")
    pack_parser.add_argument("--overwritePackedFile", choices=["ask", "default", "always", "never"], help="How to handle existing packed file in project dir")

    # install command
    install_parser = subparsers.add_parser(
        "install",
        help="Convert, compile, pack, and install target",
    )
    install_parser.add_argument("targets", nargs="*", default=[], help="Targets to install (use 'all' for all targets)")
    install_parser.add_argument("--clean", action="store_true", help="Clear the cache before packing")
    install_parser.add_argument("--noConvert", action="store_true", help="Do not convert updated json files")
    install_parser.add_argument("--noCompile", action="store_true", help="Do not recompile updated scripts")
    install_parser.add_argument("--noPack", action="store_true", help="Do not re-pack the file (implies --noConvert and --noCompile)")
    install_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")
    install_parser.add_argument("--file", dest="install_file", help="Specify the file to install")
    install_parser.add_argument("--installDir", help="The location of the KOTOR user directory")
    install_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
    install_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
    install_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")
    install_parser.add_argument("--abortOnCompileError", action="store_true", help="Abort installation if errors encountered during compilation")
    install_parser.add_argument("--packUnchanged", action="store_true", help="Continue packing if there are no changed files")
    install_parser.add_argument("--overwritePackedFile", choices=["ask", "default", "always", "never"], help="How to handle existing packed file in project dir")
    install_parser.add_argument("--overwriteInstalledFile", choices=["ask", "default", "always", "never"], help="How to handle existing installed file in installDir")

    # launch command (with aliases)
    for launch_alias in ["launch", "serve", "play", "test"]:
        launch_parser = subparsers.add_parser(
            launch_alias,
            help="Convert, compile, pack, install, and launch target in-game",
        )
        launch_parser.add_argument("targets", nargs="*", default=[], help="Target to launch")
        launch_parser.add_argument("--clean", action="store_true", help="Clear the cache before packing")
        launch_parser.add_argument("--noConvert", action="store_true", help="Do not convert updated json files")
        launch_parser.add_argument("--noCompile", action="store_true", help="Do not recompile updated scripts")
        launch_parser.add_argument("--noPack", action="store_true", help="Do not re-pack the file")
        launch_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")
        launch_parser.add_argument("--file", dest="launch_file", help="Specify the file to install")
        launch_parser.add_argument("--installDir", help="The location of the KOTOR user directory")
        launch_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
        launch_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
        launch_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")
        launch_parser.add_argument("--abortOnCompileError", action="store_true", help="Abort launching if errors encountered during compilation")
        launch_parser.add_argument("--packUnchanged", action="store_true", help="Continue packing if there are no changed files")
        launch_parser.add_argument("--gameBin", help="Path to the swkotor binary file")
        launch_parser.add_argument("--serverBin", help="Path to the kotor server binary file (if applicable)")

    return parser


def main(argv: Sequence[str] | None = None):
    """Main entry point for KOTORNasher."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    log_level = "DEBUG" if args.debug else ("ERROR" if args.quiet else ("INFO" if not args.verbose else "DEBUG"))
    use_color = not args.no_color
    logger = setup_logger(log_level, use_color)

    # Show help if no command specified
    if not args.command or (hasattr(args, "help") and args.help):
        parser.print_help()
        return 0

    # Dispatch to appropriate command handler
    try:
        if args.command == "config":
            return cmd_config(args, logger)
        elif args.command == "init":
            return cmd_init(args, logger)
        elif args.command == "list":
            return cmd_list(args, logger)
        elif args.command == "unpack":
            return cmd_unpack(args, logger)
        elif args.command == "convert":
            return cmd_convert(args, logger)
        elif args.command == "compile":
            return cmd_compile(args, logger)
        elif args.command == "pack":
            return cmd_pack(args, logger)
        elif args.command == "install":
            return cmd_install(args, logger)
        elif args.command in ("launch", "serve", "play", "test"):
            return cmd_launch(args, logger)
        else:
            logger.error(f"Unknown command: {args.command}")
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())



