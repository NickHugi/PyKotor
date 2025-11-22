"""Convert command implementation.

This module handles conversion of JSON source files to binary GFF format for packing.

References:
----------
    vendor/KotOR.js/src/formats/gff/GFFObject.ts - TypeScript GFF implementation
    vendor/xoreos-tools/src/aurora/gff3file.cpp - C++ GFF implementation  
    vendor/Kotor.NET/Kotor.NET/GFF/ - C# GFF implementation
    Libraries/PyKotor/src/pykotor/resource/formats/gff/ - PyKotor GFF implementation (used here)
"""
from __future__ import annotations

import glob
import shutil

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

from kotornasher.cfg_parser import load_config
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.type import ResourceType


def cmd_convert(args: Namespace, logger: Logger) -> int:
    """Handle convert command - convert JSON sources to GFF.

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
        logger.info(f"Converting target: {target_name}")

        # Get cache directory
        cache_dir = config.root_dir / ".kotornasher" / "cache" / target_name
        if args.clean and cache_dir.exists():
            logger.info(f"Cleaning cache: {cache_dir}")
            shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Get source patterns
        sources = config.get_target_sources(target)
        include_patterns = sources.get("include", [])
        exclude_patterns = sources.get("exclude", [])

        # Find JSON files to convert
        json_files = []
        for pattern in include_patterns:
            # Expand pattern
            pattern_path = str(config.root_dir / pattern)
            matches = glob.glob(pattern_path, recursive=True)
            for match in matches:
                match_path = Path(match)
                if match_path.suffix == ".json":
                    # Check against exclude patterns
                    excluded = False
                    for exclude_pattern in exclude_patterns:
                        import fnmatch

                        if fnmatch.fnmatch(str(match_path), str(config.root_dir / exclude_pattern)):
                            excluded = True
                            break
                    if not excluded:
                        json_files.append(match_path)

        logger.info(f"Found {len(json_files)} JSON files to convert")

        # Convert each JSON file
        converted_count = 0
        for json_path in json_files:
            try:
                # Determine GFF type from filename
                # e.g., "myfile.utc.json" -> "myfile.utc"
                stem = json_path.stem
                if "." in stem:
                    # Has extension like "myfile.utc" from "myfile.utc.json"
                    gff_filename = stem
                    ext = gff_filename.split(".")[-1]
                else:
                    # No extension, can't convert
                    logger.warning(f"Cannot determine GFF type for {json_path.name}")
                    continue

                # Get ResourceType from extension
                try:
                    resource_type = ResourceType.from_extension(ext)
                except ValueError:
                    logger.warning(f"Unknown resource type for {json_path.name}, skipping")
                    continue

                # Read JSON using PyKotor's JSON reader
                gff = read_gff(json_path, file_format=ResourceType.GFF_JSON)

                # Write to cache as binary GFF
                cache_file = cache_dir / gff_filename
                write_gff(gff, cache_file, file_format=ResourceType.GFF)

                logger.debug(f"Converted: {json_path.relative_to(config.root_dir)} -> {cache_file.relative_to(config.root_dir)}")
                converted_count += 1

            except Exception as e:
                logger.error(f"Failed to convert {json_path.name}: {e}")

        logger.info(f"Converted {converted_count} files")

        # Handle module.ifo modifications if specified
        if args.modName or args.modMinGameVersion or args.modDescription:
            ifo_path = cache_dir / "module.ifo"
            if ifo_path.exists():
                try:
                    ifo = read_gff(ifo_path)
                    modified = False

                    if args.modName:
                        ifo.root.set_string("Mod_Name", args.modName)
                        modified = True
                        logger.info(f"Set Mod_Name to: {args.modName}")

                    if args.modMinGameVersion:
                        ifo.root.set_string("Mod_MinGameVersion", args.modMinGameVersion)
                        modified = True
                        logger.info(f"Set Mod_MinGameVersion to: {args.modMinGameVersion}")

                    if args.modDescription:
                        ifo.root.set_string("Mod_Description", args.modDescription)
                        modified = True
                        logger.info(f"Set Mod_Description to: {args.modDescription}")

                    if modified:
                        write_gff(ifo, ifo_path, file_format=ResourceType.GFF)
                except Exception as e:
                    logger.error(f"Failed to modify module.ifo: {e}")

    return 0

