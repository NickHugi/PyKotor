from __future__ import annotations

import sys

from threading import Event
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from holopatcher import core
from pykotor.tslpatcher.logger import PatchLogger
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from argparse import Namespace

ExitCode = core.ExitCode


def execute_cli(cmdline_args: Namespace):
    """Execute command line operations in CLI mode.

    Args:
    ----
        cmdline_args: Command line arguments
    """
    logger = RobustLogger()
    patcher_logger = PatchLogger()

    # Load mod
    if not cmdline_args.tslpatchdata:
        print("[Error] No mod path specified. Use --tslpatchdata <path>", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.NUMBER_OF_ARGS)

    try:
        mod_info = core.load_mod(cmdline_args.tslpatchdata)
    except FileNotFoundError as e:
        logger.exception("Failed to load mod")
        print(f"[Error] Failed to load mod: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.NAMESPACES_INI_NOT_FOUND)

    # Select namespace
    if cmdline_args.namespace_option_index is not None:
        if cmdline_args.namespace_option_index >= len(mod_info.namespaces):
            print(f"[Error] Namespace index {cmdline_args.namespace_option_index} out of range (max: {len(mod_info.namespaces) - 1})", file=sys.stderr)  # noqa: T201
            sys.exit(ExitCode.NAMESPACE_INDEX_OUT_OF_RANGE)
        selected_namespace = mod_info.namespaces[cmdline_args.namespace_option_index].name
    else:
        selected_namespace = mod_info.namespaces[0].name

    # Validate game path
    if not cmdline_args.game_dir:
        print("[Error] No game directory specified. Use --game-dir <path>", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.NUMBER_OF_ARGS)

    try:
        game_path = core.validate_game_directory(cmdline_args.game_dir)
    except ValueError as e:
        logger.exception("Invalid game directory")
        print(f"[Error] Invalid game directory: {e.__class__.__name__}: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.NUMBER_OF_ARGS)

    # Validate paths
    if not core.validate_install_paths(mod_info.mod_path, game_path):
        print("[Error] Invalid mod or game paths", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.NUMBER_OF_ARGS)

    # Check which operation to perform
    num_cmdline_actions: int = sum([cmdline_args.install, cmdline_args.uninstall, cmdline_args.validate])
    if num_cmdline_actions > 1:
        print("[Error] Cannot run more than one of [--install, --uninstall, --validate]", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.NUMBER_OF_ARGS)
    if num_cmdline_actions == 0:
        print("[Error] Must specify one of [--install, --uninstall, --validate] for CLI mode", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.NUMBER_OF_ARGS)

    # Execute the requested operation
    try:
        if cmdline_args.install:
            print(f"[Info] Installing mod from {mod_info.mod_path} to {game_path}")  # noqa: T201
            should_cancel = Event()
            result = core.install_mod(
                mod_info.mod_path,
                game_path,
                mod_info.namespaces,
                selected_namespace,
                patcher_logger,
                should_cancel,
            )
            print(f"[Info] Install completed: {result.num_errors} errors, {result.num_warnings} warnings, {result.num_patches} patches")  # noqa: T201
            print(f"[Info] Install time: {core.format_install_time(result.install_time)}")  # noqa: T201

            if result.num_errors > 0:
                sys.exit(ExitCode.INSTALL_COMPLETED_WITH_ERRORS)
            sys.exit(ExitCode.SUCCESS)

        elif cmdline_args.uninstall:
            print(f"[Info] Uninstalling mod from {game_path}")  # noqa: T201
            fully_ran = core.uninstall_mod(mod_info.mod_path, game_path, patcher_logger)
            if fully_ran:
                print("[Info] Uninstall completed successfully")  # noqa: T201
            else:
                print("[Warning] Uninstall completed with warnings")  # noqa: T201
            sys.exit(ExitCode.SUCCESS)

        elif cmdline_args.validate:
            print("[Info] Validating mod configuration")  # noqa: T201
            core.validate_config(mod_info.mod_path, mod_info.namespaces, selected_namespace, patcher_logger)
            print("[Info] Validation completed successfully")  # noqa: T201
            sys.exit(ExitCode.SUCCESS)

    except Exception as e:  # noqa: BLE001
        logger.exception("CLI operation failed")
        error_name, msg = universal_simplify_exception(e)
        print(f"[Error] {error_name}: {msg}", file=sys.stderr)  # noqa: T201
        sys.exit(ExitCode.EXCEPTION_DURING_INSTALL)

