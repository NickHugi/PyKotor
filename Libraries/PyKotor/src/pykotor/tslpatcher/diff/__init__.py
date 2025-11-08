"""TSLPatcher diff module - tools for analyzing and generating patch data.

This module provides:
- analyzers: Convert raw diffs into TSLPatcher modification structures
- cache: Diff result caching system
- engine: Core comparison operations for diff detection
- enhanced_engine: Enhanced diff engine with formatting support
- formatters: Output formatters for different diff formats
- generator: Generate complete tslpatchdata folder structures
- objects: Structured diff result objects
- resolution: Resource resolution order handling for installation comparisons
- structured: Detailed diff results for INI generation
"""

from __future__ import annotations

from pykotor.tslpatcher.diff.analyzers import DiffAnalyzerFactory
from pykotor.tslpatcher.diff.cache import DiffCache, load_diff_cache, restore_strref_cache_from_cache, save_diff_cache
from pykotor.tslpatcher.diff.engine import (
    CachedFileComparison,
    DiffContext,
    diff_capsule_files,
    diff_data,
    diff_directories,
)
from pykotor.tslpatcher.diff.enhanced_engine import EnhancedDiffEngine
from pykotor.tslpatcher.diff.formatters import (
    ContextFormatter,
    DefaultFormatter,
    DiffFormatter,
    FormatterFactory,
    SideBySideFormatter,
    UnifiedFormatter,
)
from pykotor.tslpatcher.diff.generator import (
    TSLPatchDataGenerator,
    determine_install_folders,
    validate_tslpatchdata_arguments,
)
from pykotor.tslpatcher.writer import IncrementalTSLPatchDataWriter
from pykotor.tslpatcher.diff.objects import DiffEngine, DiffFormat, DiffType
from pykotor.tslpatcher.diff.resolution import (
    ResolvedResource,
    build_resource_index,
    collect_all_resource_identifiers,
    determine_tslpatcher_destination,
    diff_installations_with_resolution,
    explain_resolution_order,
    get_location_display_name,
    resolve_resource_in_installation,
)
from pykotor.tools.reference_cache import StrRefReferenceCache

__all__ = [
    "CachedFileComparison",
    "ContextFormatter",
    "DefaultFormatter",
    "DiffAnalyzerFactory",
    "DiffCache",
    "DiffContext",
    "DiffEngine",
    "DiffFormat",
    "DiffFormatter",
    "DiffType",
    "EnhancedDiffEngine",
    "FormatterFactory",
    "IncrementalTSLPatchDataWriter",
    "ResolvedResource",
    "SideBySideFormatter",
    "StrRefReferenceCache",
    "TSLPatchDataGenerator",
    "UnifiedFormatter",
    "build_resource_index",
    "collect_all_resource_identifiers",
    "determine_install_folders",
    "determine_tslpatcher_destination",
    "diff_capsule_files",
    "diff_data",
    "diff_directories",
    "diff_installations_with_resolution",
    "explain_resolution_order",
    "get_location_display_name",
    "load_diff_cache",
    "resolve_resource_in_installation",
    "restore_strref_cache_from_cache",
    "save_diff_cache",
    "validate_tslpatchdata_arguments",
]
