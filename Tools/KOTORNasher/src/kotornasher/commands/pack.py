"""Pack command implementation.

This module handles packing source files into KOTOR module/ERF/hak files.

References:
----------
    vendor/KotOR.js/src/resource/ERFObject.ts - TypeScript ERF packing
    vendor/xoreos-tools/src/aurora/erffile.cpp - C++ ERF writer
    vendor/Kotor.NET/Kotor.NET/ERF/ - C# ERF implementation
    vendor/reone/src/libs/resource/format/erfreader.cpp - reone ERF reader (reference)
    Libraries/PyKotor/src/pykotor/resource/formats/erf/ - PyKotor ERF implementation (used here)
"""
from __future__ import annotations

import glob

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

from kotornasher.cfg_parser import load_config
from kotornasher.commands.compile import cmd_compile
from kotornasher.commands.convert import cmd_convert
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.type import ResourceType


def should_overwrite_file(file_path: Path, source_newest: float, mode: str, logger: Logger) -> bool:
    """Determine if file should be overwritten based on mode.

    Args:
    ----
        file_path: Path to the existing file
        source_newest: Timestamp of newest source file
        mode: Overwrite mode (ask/default/always/never)
        logger: Logger instance

    Returns:
    -------
        True if file should be overwritten
    """
    if mode == "always":
        return True
    if mode == "never":
        return False

    existing_time = file_path.stat().st_mtime
    if mode == "default":
        # Overwrite if existing is older than source
        return existing_time < source_newest

    # mode == "ask"
    logger.info(f"File exists: {file_path}")
    logger.info(f"  Existing: {existing_time}")
    logger.info(f"  Source:   {source_newest}")
    response = input("Overwrite? (yes/no): ").strip().lower()
    return response in ("yes", "y")


def cmd_pack(args: Namespace, logger: Logger) -> int:
    """Handle pack command - pack sources into module/erf/hak.

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

    # Determine targets
    target_names = args.targets if args.targets else [None]
    if "all" in target_names:
        targets = config.targets
    else:
        targets = []
        for name in target_names:
            target = config.get_target(name)
            if target is None:
                if name:
                    logger.error(f"Target not found: {name}")
                else:
                    logger.error("No default target found")
                return 1
            targets.append(target)

    # Process each target
    for target in targets:
        target_name = target.get("name", "unnamed")
        logger.info(f"Packing target: {target_name}")

        # Run convert unless --noConvert
        if not getattr(args, "noConvert", False):
            logger.info("Converting JSON to GFF...")
            convert_result = cmd_convert(args, logger)
            if convert_result != 0:
                logger.error("Convert failed")
                return convert_result

        # Run compile unless --noCompile
        if not getattr(args, "noCompile", False):
            logger.info("Compiling scripts...")
            compile_result = cmd_compile(args, logger)
            if compile_result != 0 and getattr(args, "abortOnCompileError", False):
                logger.error("Compile failed, aborting pack")
                return compile_result

        # Get cache directory
        cache_dir = config.root_dir / ".kotornasher" / "cache" / target_name
        if not cache_dir.exists():
            logger.error(f"Cache directory not found: {cache_dir}")
            logger.info("Run 'kotornasher convert' and 'kotornasher compile' first")
            return 1

        # Determine output file
        if hasattr(args, "pack_file") and args.pack_file:
            output_file = Path(args.pack_file)
        else:
            output_filename = config.resolve_target_value(target, "file")
            if not output_filename:
                logger.error("No output file specified for target")
                return 1
            output_file = config.root_dir / output_filename

        logger.info(f"Output file: {output_file}")

        # Check if output file exists
        if output_file.exists():
            # Find newest source file
            sources = config.get_target_sources(target)
            include_patterns = sources.get("include", [])
            newest_source_time = 0.0
            for pattern in include_patterns:
                pattern_path = str(config.root_dir / pattern)
                matches = glob.glob(pattern_path, recursive=True)
                for match in matches:
                    match_path = Path(match)
                    if match_path.is_file():
                        mtime = match_path.stat().st_mtime
                        newest_source_time = max(newest_source_time, mtime)

            overwrite_mode = getattr(args, "overwritePackedFile", "ask")
            if not should_overwrite_file(output_file, newest_source_time, overwrite_mode, logger):
                logger.info("Keeping existing file, skipping pack")
                continue

        # Collect files from cache
        cache_files = list(cache_dir.glob("**/*"))
        cache_files = [f for f in cache_files if f.is_file()]

        # Apply filter patterns
        sources = config.get_target_sources(target)
        filter_patterns = sources.get("filter", [])
        filtered_files = []
        for cache_file in cache_files:
            import fnmatch

            should_filter = False
            for pattern in filter_patterns:
                if fnmatch.fnmatch(cache_file.name, pattern):
                    should_filter = True
                    logger.debug(f"Filtering out: {cache_file.name}")
                    break
            if not should_filter:
                filtered_files.append(cache_file)

        logger.info(f"Packing {len(filtered_files)} files")

        # Determine archive type
        suffix = output_file.suffix.lower()
        if suffix in (".mod", ".erf", ".sav"):
            # Create ERF archive
            try:
                erf = ERF()
                if suffix == ".mod":
                    erf.erf_type = ERFType.MOD
                elif suffix == ".sav":
                    erf.erf_type = ERFType.SAV
                else:
                    erf.erf_type = ERFType.ERF

                # Add files to ERF
                for cache_file in filtered_files:
                    # Determine resref and restype
                    name_parts = cache_file.stem.split(".")
                    if len(name_parts) >= 2:
                        resref = ".".join(name_parts[:-1])
                        ext = name_parts[-1]
                    else:
                        resref = cache_file.stem
                        ext = cache_file.suffix.lstrip(".")

                    # Get ResourceType
                    try:
                        restype = ResourceType.from_extension(ext)
                    except ValueError:
                        logger.warning(f"Unknown resource type for {cache_file.name}, skipping")
                        continue

                    # Read file data
                    file_data = cache_file.read_bytes()

                    # Add to ERF
                    erf.set(resref, restype, file_data)

                # Write ERF
                output_file.parent.mkdir(parents=True, exist_ok=True)
                write_erf(erf, output_file)
                logger.info(f"Successfully packed {output_file}")

            except Exception as e:
                logger.exception(f"Failed to pack ERF: {e}")
                return 1

        elif suffix == ".rim":
            logger.error("RIM packing not yet implemented")
            return 1
        else:
            logger.error(f"Unsupported output file type: {suffix}")
            return 1

    return 0

