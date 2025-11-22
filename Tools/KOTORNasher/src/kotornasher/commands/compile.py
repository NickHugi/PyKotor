"""Compile command implementation."""
from __future__ import annotations

import glob
import shutil
import subprocess

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from logging import Logger

from kotornasher.cfg_parser import load_config
from pykotor.common.misc import Game
from pykotor.resource.formats.ncs.compilers import (
    ExternalNCSCompiler,
    InbuiltNCSCompiler,
)


def get_game_from_config() -> Game:
    """Determine which game version to compile for (K1 or K2)."""
    # This could be enhanced to read from config
    # For now, default to K2 which is more compatible
    return Game.K2


def find_nss_compiler() -> Path | None:
    """Find the NWScript compiler executable.
    
    Searches for external compilers in this order:
    1. nwnnsscomp (preferred, compatible with both K1 and K2)
    2. nwnsc (legacy, Neverwinter Nights compiler)
    
    References:
    ----------
        vendor/xoreos-tools/src/nwscript/compiler.cpp - xoreos NSS compiler
        Libraries/PyKotor/src/pykotor/resource/formats/ncs/compilers.py - PyKotor compiler implementations
    """
    import platform

    system = platform.system()
    if system == "Windows":
        compiler_names = ["nwnnsscomp.exe", "nwnsc.exe"]
    else:
        compiler_names = ["nwnnsscomp", "nwnsc"]

    # Check PATH
    for name in compiler_names:
        result = shutil.which(name)
        if result:
            return Path(result)

    return None


def use_builtin_compiler(
    nss_files: list[Path],
    cache_dir: Path,
    game: Game,
    logger,
) -> tuple[int, int]:
    """Use PyKotor's built-in NSS compiler.
    
    Args:
    ----
        nss_files: List of NSS files to compile
        cache_dir: Directory to output NCS files
        game: Which game version to compile for
        logger: Logger instance
    
    Returns:
    -------
        Tuple of (compiled_count, error_count)
    
    References:
    ----------
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts - TypeScript NSS compiler
        vendor/xoreos-tools/src/nwscript/compiler.cpp - C++ NSS compiler
        Libraries/PyKotor/src/pykotor/resource/formats/ncs/compiler/ - PyKotor compiler implementation
    """
    compiler = InbuiltNCSCompiler()
    compiled_count = 0
    error_count = 0
    
    for nss_path in nss_files:
        try:
            output_file = cache_dir / nss_path.with_suffix(".ncs").name
            compiler.compile_script(
                source_path=nss_path,
                output_path=output_file,
                game=game,
                debug=False,
            )
            logger.debug(f"Compiled: {nss_path.name} -> {output_file.name}")
            compiled_count += 1
        except Exception as e:
            logger.error(f"Compilation failed for {nss_path.name}: {e}")
            error_count += 1
    
    return compiled_count, error_count


def cmd_compile(args: Namespace, logger: Logger) -> int:
    """Handle compile command - compile NWScript sources.

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

    # Check for external compiler (optional)
    external_compiler = find_nss_compiler()
    use_external = external_compiler is not None
    
    if use_external:
        logger.info(f"Using external compiler: {external_compiler}")
    else:
        logger.info("Using PyKotor's built-in NSS compiler")
    
    # Determine game version
    game = get_game_from_config()

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
        logger.info(f"Compiling target: {target_name}")

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
        skip_compile_patterns = sources.get("skipCompile", [])

        # Add command-line skipCompile patterns
        if hasattr(args, "skipCompile") and args.skipCompile:
            skip_compile_patterns.extend(args.skipCompile)

        # Find NSS files to compile
        nss_files = []
        if hasattr(args, "files") and args.files:
            # Specific files specified
            for file_spec in args.files:
                file_path = Path(file_spec)
                if file_path.exists() and file_path.suffix == ".nss":
                    nss_files.append(file_path)
                else:
                    # Try to find by name
                    for pattern in include_patterns:
                        pattern_path = str(config.root_dir / pattern)
                        matches = glob.glob(pattern_path, recursive=True)
                        for match in matches:
                            match_path = Path(match)
                            if match_path.name == file_spec or match_path.name == f"{file_spec}.nss":
                                nss_files.append(match_path)
                                break
        else:
            # Find all NSS files matching patterns
            for pattern in include_patterns:
                pattern_path = str(config.root_dir / pattern)
                matches = glob.glob(pattern_path, recursive=True)
                for match in matches:
                    match_path = Path(match)
                    if match_path.suffix == ".nss":
                        # Check against exclude patterns
                        excluded = False
                        for exclude_pattern in exclude_patterns:
                            import fnmatch

                            if fnmatch.fnmatch(str(match_path), str(config.root_dir / exclude_pattern)):
                                excluded = True
                                break

                        # Check against skipCompile patterns
                        for skip_pattern in skip_compile_patterns:
                            import fnmatch

                            if fnmatch.fnmatch(match_path.name, skip_pattern):
                                excluded = True
                                logger.debug(f"Skipping compilation: {match_path.name}")
                                break

                        if not excluded:
                            nss_files.append(match_path)

        logger.info(f"Found {len(nss_files)} scripts to compile")

        if not nss_files:
            logger.warning("No scripts found to compile")
            continue

        # Compile scripts
        if use_external and external_compiler:
            # Use external compiler
            compiled_count = 0
            error_count = 0
            
            for nss_path in nss_files:
                try:
                    output_file = cache_dir / nss_path.with_suffix(".ncs").name

                    # Build compiler command
                    cmd = [
                        str(external_compiler),
                        str(nss_path),
                        "-o",
                        str(output_file),
                    ]

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=config.root_dir,
                    )

                    if result.returncode == 0:
                        logger.debug(f"Compiled: {nss_path.name} -> {output_file.name}")
                        compiled_count += 1
                    else:
                        logger.error(f"Compilation failed for {nss_path.name}:")
                        if result.stdout:
                            logger.error(result.stdout)
                        if result.stderr:
                            logger.error(result.stderr)
                        error_count += 1

                except Exception as e:
                    logger.error(f"Failed to compile {nss_path.name}: {e}")
                    error_count += 1
        else:
            # Use built-in PyKotor compiler
            compiled_count, error_count = use_builtin_compiler(nss_files, cache_dir, game, logger)

        logger.info(f"Compiled {compiled_count} scripts, {error_count} errors")

        if error_count > 0 and hasattr(args, "abortOnCompileError") and args.abortOnCompileError:
            logger.error("Aborting due to compilation errors")
            return 1

    return 0

