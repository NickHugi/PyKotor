"""List command implementation."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

from kotornasher.cfg_parser import load_config


def cmd_list(args: Namespace, logger: Logger) -> int:
    """Handle list command - list all targets.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    # Load configuration
    config = load_config(logger)
    if config is None:
        return 1

    # Get targets to list
    targets_to_list = args.targets if args.targets else None

    # Get all targets
    all_targets = config.targets
    if not all_targets:
        logger.info("No targets defined in kotornasher.cfg")
        return 0

    # Filter targets if specific ones were requested
    if targets_to_list:
        targets = [t for t in all_targets if t.get("name") in targets_to_list]
        if not targets:
            logger.error(f"No matching targets found: {', '.join(targets_to_list)}")
            return 1
    else:
        targets = all_targets

    # Display targets
    for i, target in enumerate(targets):
        name = target.get("name", "unnamed")
        is_default = i == 0 or config.package.get("default") == name

        if args.quiet:
            # Quiet mode: just names
            print(name)
        else:
            # Normal mode: name, description, file
            description = target.get("description", "")
            file = config.resolve_target_value(target, "file", "")

            default_marker = " (default)" if is_default else ""
            logger.info(f"\n{name}{default_marker}")
            if description:
                logger.info(f"  Description: {description}")
            if file:
                logger.info(f"  File: {file}")

            # Verbose mode: show sources
            if args.verbose:
                sources = config.get_target_sources(target)
                if sources.get("include"):
                    logger.info("  Sources:")
                    for pattern in sources["include"]:
                        logger.info(f"    include: {pattern}")
                if sources.get("exclude"):
                    for pattern in sources["exclude"]:
                        logger.info(f"    exclude: {pattern}")
                if sources.get("filter"):
                    for pattern in sources["filter"]:
                        logger.info(f"    filter: {pattern}")

    return 0



