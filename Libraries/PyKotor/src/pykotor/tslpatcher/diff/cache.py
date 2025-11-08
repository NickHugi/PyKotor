#!/usr/bin/env python3
"""Diff result caching system.

This module provides functionality to save and load diff results to/from
YAML cache files, allowing reuse of diff analysis without re-scanning files.

The cache includes:
- File comparison metadata (which files changed, added, removed)
- Copies of modified/different files for regenerating diffs
- StrRef reference cache (which files reference which StrRefs) for TLK linking

This allows --from-results to skip both file scanning and StrRef cache building,
significantly speeding up repeated TSLPatcher data generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

import yaml

from pykotor.tslpatcher.diff.engine import CachedFileComparison

if TYPE_CHECKING:
    from pathlib import Path

    from pykotor.common.misc import Game
    from pykotor.tools.reference_cache import StrRefReferenceCache


@dataclass
class DiffCache:
    """Cache of diff results that can be saved/loaded.

    Includes both file comparison results and StrRef reference cache data.
    When saved with --save-results, the cache includes:
    - File comparison metadata (which files changed, added, removed)
    - Copies of modified files for regenerating diffs
    - StrRef reference cache (which files reference which StrRefs)

    When loaded with --from-results, the cache can be used to:
    - Regenerate diff output without re-scanning installations
    - Generate TSLPatcher data without rebuilding StrRef cache
    """

    version: str
    mine: str
    older: str
    yours: str | None = None
    timestamp: str = ""
    files: list[CachedFileComparison] | None = None
    # StrRef cache data (for TLK linking patches)
    strref_cache_game: str | None = None  # Game type (K1/K2) for StrRef cache
    strref_cache_data: dict[str, Any] | None = None  # Serialized StrRef cache

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.files is None:
            self.files = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result: dict[str, Any] = {
            "version": self.version,
            "mine": self.mine,
            "older": self.older,
            "yours": self.yours,
            "timestamp": self.timestamp,
            "files": [
                {
                    "rel_path": f.rel_path,
                    "status": f.status,
                    "ext": f.ext,
                    "left_exists": f.left_exists,
                    "right_exists": f.right_exists,
                }
                for f in self.files or []
            ],
        }

        # Add StrRef cache data if present
        if self.strref_cache_game is not None:
            result["strref_cache_game"] = self.strref_cache_game
        if self.strref_cache_data is not None:
            result["strref_cache_data"] = self.strref_cache_data

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiffCache:
        """Load from dictionary (YAML deserialization)."""
        return cls(
            version=data["version"],
            mine=data["mine"],
            older=data["older"],
            yours=data.get("yours"),
            timestamp=data["timestamp"],
            files=[
                CachedFileComparison(
                    rel_path=f["rel_path"],
                    status=f["status"],
                    ext=f["ext"],
                    left_exists=f["left_exists"],
                    right_exists=f["right_exists"],
                )
                for f in data.get("files", [])
            ],
            strref_cache_game=data.get("strref_cache_game"),
            strref_cache_data=data.get("strref_cache_data"),
        )


def save_diff_cache(
    cache: DiffCache,
    cache_file: Path,
    mine: Path,
    older: Path,
    *,
    strref_cache: StrRefReferenceCache | None = None,
    log_func: Callable[[str], None] | None = None,
) -> None:
    """Save diff cache to YAML file with companion data directory.

    Args:
        cache: DiffCache object to save
        cache_file: Path to save the YAML cache file
        mine: Path to the first comparison directory
        older: Path to the second comparison directory
        strref_cache: Optional StrRef cache to include in the saved cache
        log_func: Optional logging function (default: print)
    """
    if log_func is None:
        log_func = print

    # Add StrRef cache to DiffCache if provided
    if strref_cache is not None:
        cache.strref_cache_game = str(strref_cache.game)
        cache.strref_cache_data = strref_cache.to_dict()
        log_func(f"  Including StrRef cache: {len(strref_cache._cache)} StrRefs, {strref_cache._total_references_found} references")

    # Create companion data directory
    cache_dir = cache_file.parent / f"{cache_file.stem}_data"
    cache_dir.mkdir(exist_ok=True)

    left_dir = cache_dir / "left"
    right_dir = cache_dir / "right"
    left_dir.mkdir(exist_ok=True)
    right_dir.mkdir(exist_ok=True)

    # Copy modified/different files to cache
    files_list = cache.files if cache.files is not None else []
    for file_comp in files_list:
        if file_comp.status in ("modified", "missing_right") and file_comp.left_exists:
            src = mine / file_comp.rel_path
            if src.is_file():
                dst = left_dir / file_comp.rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())

        if file_comp.status in ("modified", "missing_left") and file_comp.right_exists:
            src = older / file_comp.rel_path
            if src.is_file():
                dst = right_dir / file_comp.rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())

    # Save metadata to YAML
    cache_file.write_text(yaml.dump(cache.to_dict(), default_flow_style=False), encoding="utf-8")
    log_func(f"Saved diff cache to: {cache_file}")
    log_func(f"  Cached {len(files_list)} file comparisons")
    if strref_cache is not None:
        stats: dict[str, int] = strref_cache.get_statistics()
        log_func(f"  Cached StrRef data: {stats['unique_strrefs']} StrRefs, {stats['total_references']} references")
    log_func(f"  Cache data directory: {cache_dir}")


def load_diff_cache(
    cache_file: Path,
    *,
    log_func: Callable[[str], None] | None = None,
) -> tuple[DiffCache, Path, Path]:
    """Load diff cache from YAML file.

    Args:
        cache_file: Path to the YAML cache file
        log_func: Optional logging function (default: print)

    Returns:
        Tuple of (cache, left_dir, right_dir)
    """
    if log_func is None:
        log_func = print

    cache_data = yaml.safe_load(cache_file.read_text(encoding="utf-8"))
    cache = DiffCache.from_dict(cache_data)

    # Determine data directory paths
    cache_dir = cache_file.parent / f"{cache_file.stem}_data"
    left_dir = cache_dir / "left"
    right_dir = cache_dir / "right"

    log_func(f"Loaded diff cache from: {cache_file}")
    file_count = len(cache.files) if cache.files is not None else 0
    log_func(f"  Cached {file_count} file comparisons")
    log_func(f"  Original mine: {cache.mine}")
    log_func(f"  Original older: {cache.older}")

    # Log StrRef cache data if present
    if cache.strref_cache_data is not None:
        strref_count: int = len(cache.strref_cache_data)
        total_refs: int = sum(len(ref["locations"]) for refs in cache.strref_cache_data.values() for ref in refs)
        log_func(f"  Cached StrRef data: {strref_count} StrRefs, {total_refs} references (game: {cache.strref_cache_game})")

    return cache, left_dir, right_dir


def restore_strref_cache_from_cache(
    cache: DiffCache,
    game: Game | None = None,
) -> StrRefReferenceCache | None:
    """Restore StrRef cache from DiffCache.

    Args:
        cache: DiffCache object with strref_cache_data
        game: Optional Game instance (if None, will be parsed from cache.strref_cache_game)

    Returns:
        Restored StrRefReferenceCache or None if no cache data available
    """
    from pykotor.tools.reference_cache import StrRefReferenceCache  # noqa: PLC0415

    if cache.strref_cache_data is None:
        return None

    # Determine game from cache if not provided
    if game is None:
        if cache.strref_cache_game is None:
            return None

        from pykotor.common.misc import Game  # noqa: PLC0415

        game_str: str = cache.strref_cache_game.upper()
        if "K1" in game_str or "KOTOR1" in game_str:
            game = Game.K1
        elif "K2" in game_str or "KOTOR2" in game_str or "TSL" in game_str:
            game = Game.K2
        else:
            return None

    return StrRefReferenceCache.from_dict(game, cache.strref_cache_data)
