#!/usr/bin/env python3
"""Unified diff engine utilities for KotorDiff.

This module offers two core helpers:
1. ResourceWalker - given any path (installation root, container, directory, or
   single file) it walks all addressable resources and yields ComparableResource
   objects containing data & metadata.
2. DiffDispatcher - static helpers to compare two ComparableResource objects
   using the appropriate compare() mixin where available.

The engine purpose-built to feed both 2-way and 3-way diff flows and to serve
as source of truth for changes.ini generation.

Note: Implementation starts with the major formats (GFF / 2DA / TLK / LIP).  It
is pluggable - add additional ResourceHandler instances to the `_HANDLERS` map.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Iterator, Mapping, Protocol

from kotordiff.diff_objects import DiffEngine as StructuredDiffEngine
from kotordiff.formatters import DiffFormat, FormatterFactory
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import Installation
from pykotor.resource.formats import gff, lip, tlk, twoda
from pykotor.tools.misc import is_capsule_file, is_rim_file
from utility.misc import generate_hash
from utility.system.path import Path

if TYPE_CHECKING:
    from kotordiff.formatters import DiffFormatter
    from pykotor.extract.file import FileResource

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def get_module_root(module_filepath: Path) -> str:
    """Extract the module root name, following Installation.py logic."""
    root: str = module_filepath.stem.lower()
    root = root[:-2] if root.endswith("_s") else root
    root = root[:-4] if root.endswith("_dlg") else root
    return root

def find_related_module_files(module_path: Path) -> list[Path]:
    """Find all related module files for a given module file."""
    root = get_module_root(module_path)
    module_dir = module_path.parent

    # Possible extensions for related module files
    extensions = [".rim", ".mod", "_s.rim", "_dlg.erf"]
    related_files = []

    for ext in extensions:
        candidate = module_dir / f"{root}{ext}"
        if candidate.safe_isfile():
            related_files.append(candidate)

    return related_files

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ComparableResource:
    """A uniform wrapper around any game file/resource we can diff."""

    identifier: str  # e.g. folder/file.ext   or  resref.type inside capsule
    ext: str  # normalized lowercase extension  (for external files) or resource type extension
    data: bytes


class CompositeModuleCapsule:
    """A capsule that aggregates resources from multiple related module files."""

    def __init__(self, primary_module_path: Path):
        """Initialize with a primary module file, finding all related files."""
        self.primary_path = primary_module_path
        self.related_files = find_related_module_files(primary_module_path)
        self._capsules: dict[Path, Capsule] = {}

        # Load all related capsules
        for file_path in self.related_files:
            try:
                self._capsules[file_path] = Capsule(file_path)
            except Exception:  # noqa: BLE001,S112,PERF203 # pylint: disable=W0718
                # Skip files that can't be loaded as capsules
                continue

    def __iter__(self):
        """Iterate over all resources from all related capsules."""
        for capsule in self._capsules.values():
            yield from capsule

    @property
    def name(self) -> str:
        """Get the display name for this composite capsule."""
        return self.primary_path.name


class CompareFunc(Protocol):
    def __call__(self, a: bytes, b: bytes, /) -> bool:  # noqa: D401  # pyright: ignore[reportReturnType]
        """Return True if *a* equals *b*, False otherwise."""


# ---------------------------------------------------------------------------
# Format-aware comparers
# ---------------------------------------------------------------------------


def _compare_gff(a: bytes, b: bytes) -> bool:  # noqa: D401
    return gff.read_gff(a).compare(gff.read_gff(b), lambda *_a, **_k: None)


def _compare_2da(a: bytes, b: bytes) -> bool:  # noqa: D401
    return twoda.read_2da(a).compare(twoda.read_2da(b), lambda *_a, **_k: None)  # type: ignore[arg-type]


def _compare_tlk(a: bytes, b: bytes) -> bool:  # noqa: D401
    return tlk.read_tlk(a).compare(tlk.read_tlk(b), lambda *_a, **_k: None)  # type: ignore[arg-type]


def _compare_lip(a: bytes, b: bytes) -> bool:  # noqa: D401
    return lip.read_lip(a).compare(lip.read_lip(b), lambda *_a, **_k: None)  # type: ignore[arg-type]


_HANDLERS: Mapping[str, CompareFunc] = {
    # extensions mapped to compare function
    **dict.fromkeys(gff.GFFContent.get_extensions(), _compare_gff),
    "2da": _compare_2da,
    "tlk": _compare_tlk,
    "lip": _compare_lip,
}


class DiffDispatcher:
    """Dispatch comparison to best available handler."""

    @staticmethod
    def equals(res_a: ComparableResource, res_b: ComparableResource) -> bool:
        if res_a.ext == res_b.ext:
            cmp = _HANDLERS.get(res_a.ext)
            if cmp is not None:
                try:
                    return cmp(res_a.data, res_b.data)
                except Exception:  # noqa: BLE001,S112,S110,PERF203 # pylint: disable=W0718
                    pass
        # Fallback - hash compare
        return generate_hash(res_a.data) == generate_hash(res_b.data)


class EnhancedDiffEngine:
    """Enhanced diff engine that returns structured diff results."""

    def __init__(self, diff_format: DiffFormat = DiffFormat.DEFAULT):
        self.structured_engine: StructuredDiffEngine = StructuredDiffEngine()
        self.formatter: DiffFormatter = FormatterFactory.create_formatter(diff_format)

    def compare_resources(
        self,
        res_a: ComparableResource,
        res_b: ComparableResource,
    ) -> bool:
        """Compare two resources and output formatted results."""
        # Determine the resource type for structured comparison
        resource_type = self._get_resource_type(res_a.ext)

        # Use structured diff engine
        diff_result = self.structured_engine.compare_resources(
            res_a.data,
            res_b.data,
            res_a.identifier,
            res_b.identifier,
            resource_type,
        )

        # Format and output the result
        self.formatter.output_diff(diff_result)

        # Return whether they're different (for compatibility)
        return not diff_result.is_different

    def _get_resource_type(self, ext: str) -> str:
        """Map file extension to resource type."""
        gff_extensions = gff.GFFContent.get_extensions()

        if ext in gff_extensions:
            return "gff"
        if ext == "2da":
            return "2da"
        if ext == "tlk":
            return "tlk"
        if ext == "lip":
            return "lip"
        return "bytes"


# ---------------------------------------------------------------------------
# Resource walker
# ---------------------------------------------------------------------------


class ResourceWalker:
    """Yield ComparableResource objects from any supported path type."""

    def __init__(self, root: Path, *, other_root: Path | None = None):
        self.root = root
        self.other_root = other_root  # Used to determine if composite loading should be enabled

    # public API
    def __iter__(self) -> Iterator[ComparableResource]:  # noqa: D401
        if is_capsule_file(self.root.name):
            yield from self._from_capsule(self.root)
        elif self.root.safe_isfile():
            yield self._from_file(self.root, base_prefix="")
        elif self._looks_like_install(self.root):
            yield from self._from_install(self.root)
        else:  # directory
            yield from self._from_directory(self.root)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_like_install(path: Path) -> bool:
        return bool(path.safe_isdir()) and bool(path.joinpath("chitin.key").safe_isfile())

    @staticmethod
    def _is_in_rims_folder(file_path: Path) -> bool:
        """Check if the file is in a 'rims' folder (case-insensitive)."""
        return file_path.parent.name.lower() == "rims"

    def _should_use_composite_loading(self, file_path: Path) -> bool:
        """Determine if composite module loading should be used.

        Only use composite loading when comparing module files to other module files.
        """
        if self.other_root is None:
            return True  # Default to composite loading if no comparison context

        # Check if the other root is also a module file
        if self.other_root.safe_isfile() and is_capsule_file(self.other_root.name):
            # Both are capsule files - check if they're both module files (not in rims folder)
            return not self._is_in_rims_folder(self.other_root)

        # Other root is not a module file (directory, installation, etc.)
        return False

    def _from_file(self, file_path: Path, *, base_prefix: str) -> ComparableResource:
        ext = file_path.suffix.casefold().lstrip(".")
        identifier = f"{base_prefix}{file_path.name}" if base_prefix else file_path.name
        return ComparableResource(identifier, ext, file_path.read_bytes())

    def _from_directory(self, dir_path: Path) -> Iterable[ComparableResource]:
        for f in sorted(dir_path.safe_rglob("*")):
            if f.safe_isfile():
                rel = f.relative_to(dir_path).as_posix()
                yield self._from_file(f, base_prefix=f"{rel[:-len(f.name)]}")

    def _from_capsule(self, file_path: Path) -> Iterable[ComparableResource]:
        # Check if this is a RIM file that should use composite module loading
        # Only use composite loading if both paths are module files
        should_use_composite = (
            is_rim_file(file_path.name)
            and not self._is_in_rims_folder(file_path)
            and self._should_use_composite_loading(file_path)
        )

        if should_use_composite:
            # Use CompositeModuleCapsule to include related module files
            composite = CompositeModuleCapsule(file_path)
            for res in composite:
                resname = res.resname()
                ext = res.restype().extension.casefold()
                identifier = f"{composite.name}/{resname}.{ext}"
                yield ComparableResource(identifier, ext, res.data())
        else:
            # Use regular single capsule loading
            cap = Capsule(file_path)
            for res in cap:
                resname = res.resname()
                ext = res.restype().extension.casefold()
                identifier = f"{file_path.name}/{resname}.{ext}"
                yield ComparableResource(identifier, ext, res.data())

    def _from_install(self, install_root: Path) -> Iterable[ComparableResource]:
        inst = Installation(install_root)
        # Walk key high-level locations: override, modules, rims, lips, etc.
        # Iterate installation to get FileResource objects.

        def _iter_resources(it: Iterable[FileResource]):
            for r in it:
                identifier = r.filepath().relative_to(install_root).as_posix()
                yield ComparableResource(identifier, r.restype().extension.casefold(), r.data())

        # Override files
        yield from _iter_resources(inst.override_resources())
        # Module capsules
        for mod_name in inst.modules_list():
            cap = inst.module_path() / mod_name
            yield from self._from_capsule(Path(cap))
        # RIMs
        for rim in inst.rims_path().safe_iterdir():
            if is_capsule_file(rim.name):
                yield from self._from_capsule(Path(rim))
        # Lips
        for lip_file in inst.lips_path().safe_iterdir():
            if lip_file.suffix.casefold() == ".mod":
                yield from self._from_capsule(Path(lip_file))
        # Override subfolders already handled in override_resources
