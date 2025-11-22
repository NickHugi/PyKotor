"""Unpack command implementation.

This module handles unpacking of module/ERF/hak files into JSON source files.

References:
----------
    vendor/KotOR.js/src/resource/ERFObject.ts - TypeScript ERF implementation
    vendor/xoreos-tools/src/aurora/erffile.cpp - C++ ERF implementation
    vendor/Kotor.NET/Kotor.NET/ERF/ - C# ERF implementation
    Libraries/PyKotor/src/pykotor/resource/formats/erf/ - PyKotor ERF implementation (used here)
    Libraries/PyKotor/src/pykotor/resource/formats/gff/ - PyKotor GFF-to-JSON (used here)
"""
from __future__ import annotations

import glob
import hashlib
import shutil

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

from kotornasher.cfg_parser import load_config
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.type import ResourceType


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA1 hash of a file."""
    sha1 = hashlib.sha1()
    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()


def cmd_unpack(args: Namespace, logger: Logger) -> int:
    """Handle unpack command - unpack a file into source tree.

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

    # Determine target
    target_name = args.target
    target = config.get_target(target_name)
    if target is None:
        if target_name:
            logger.error(f"Target not found: {target_name}")
        else:
            logger.error("No default target found")
        return 1

    target_name = target.get("name", "unnamed")
    logger.info(f"Unpacking target: {target_name}")

    # Determine file to unpack
    unpack_file = args.unpack_file or args.file
    if unpack_file:
        file_path = Path(unpack_file)
    else:
        # Try to find the target's file
        target_file = config.resolve_target_value(target, "file")
        if not target_file:
            logger.error("No file specified and target has no file defined")
            return 1

        # Check in current directory first
        file_path = Path(target_file)
        if not file_path.exists():
            # Try to find in KOTOR installation directory
            # This would require Installation detection - for now just error
            logger.error(f"File not found: {target_file}")
            return 1

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1

    logger.info(f"Unpacking from: {file_path}")

    # Determine file type and unpack
    try:
        suffix = file_path.suffix.lower()
        archive = None

        if suffix in (".mod", ".erf", ".sav"):
            archive = read_erf(file_path)
        elif suffix == ".rim":
            archive = read_rim(file_path)
        else:
            logger.error(f"Unsupported file type: {suffix}")
            return 1

        if archive is None:
            logger.error("Failed to read archive")
            return 1

        logger.info(f"Archive contains {len(list(archive))} resources")

        # Get target rules
        rules = config.get_target_rules(target)
        sources = config.get_target_sources(target)

        # Create cache directory for tracking
        cache_dir = config.root_dir / ".kotornasher" / "cache" / target_name
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Track unpacked files
        unpacked_files = []

        # Unpack each resource
        for resource in archive:
            resref = resource.resname
            restype = resource.restype
            filename = f"{resref}.{restype.extension}"

            # Determine destination based on rules
            destination = None

            # Check existing source tree first
            include_patterns = sources.get("include", [])
            for pattern in include_patterns:
                # Expand glob pattern
                pattern_path = config.root_dir / pattern.replace("**", "*")
                matches = list(glob.glob(str(pattern_path), recursive=True))
                for match in matches:
                    match_path = Path(match)
                    if match_path.name == filename:
                        destination = match_path
                        break
                if destination:
                    break

            # If not found in source tree, check rules
            if not destination:
                for pattern, path_str in rules.items():
                    import fnmatch

                    if fnmatch.fnmatch(filename, pattern):
                        dest_dir = config.root_dir / path_str
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        destination = dest_dir / filename
                        break

            # If still not found, put in unknown directory
            if not destination:
                unknown_dir = config.root_dir / "unknown"
                unknown_dir.mkdir(parents=True, exist_ok=True)
                destination = unknown_dir / filename
                logger.warning(f"No rule matched {filename}, placing in unknown/")

            # Get resource data
            resource_data = bytes(resource.data)

            # Convert to JSON if GFF format
            if restype.is_gff():
                # Convert GFF to JSON using PyKotor's JSON writer
                try:
                    gff = read_gff(resource_data)
                    
                    # Write as JSON
                    json_dest = destination.with_suffix(destination.suffix + ".json")
                    write_gff(gff, json_dest, file_format=ResourceType.GFF_JSON)
                    
                    destination = json_dest
                    logger.debug(f"Converted {filename} to JSON: {destination.relative_to(config.root_dir)}")
                except Exception as e:
                    logger.warning(f"Failed to convert {filename} to JSON: {e}")
                    # Fall back to binary write
                    destination.write_bytes(resource_data)
                    logger.debug(f"Extracted {filename} (binary fallback): {destination.relative_to(config.root_dir)}")
            else:
                # Write binary file for non-GFF resources
                destination.write_bytes(resource_data)
                logger.debug(f"Extracted {filename}: {destination.relative_to(config.root_dir)}")

            unpacked_files.append(destination)

        logger.info(f"Successfully unpacked {len(unpacked_files)} files")

        # Handle removeDeleted option
        if hasattr(args, "removeDeleted") and args.removeDeleted:
            logger.info("Checking for deleted files...")
            # This would compare against previous unpack and remove files not in current archive
            # Implementation would require tracking previous unpacks

    except Exception as e:
        logger.exception(f"Failed to unpack: {e}")
        return 1

    return 0

