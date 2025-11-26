"""PyKotor tools package.

This package contains utility functions for working with KotOR game resources,
including model manipulation, door handling, creature management, and kit generation.
"""

# Lazy import to avoid circular dependency
def __getattr__(name: str):
    if name == "extract_kit_from_rim":
        from pykotor.tools.kit import extract_kit_from_rim
        return extract_kit_from_rim
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "extract_kit_from_rim",
]

