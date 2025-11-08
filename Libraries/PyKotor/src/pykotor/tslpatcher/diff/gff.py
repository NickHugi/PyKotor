from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFCompareResult


def flatten_differences(compare_result: GFFCompareResult) -> dict[str, Any]:
    """Flattens the differences from GFFCompareResult into a flat dictionary."""
    flat_changes: dict[str, Any] = {}
    differences = getattr(compare_result, "differences", None)
    if differences is None:
        differences = compare_result.get_differences()
    for diff in differences:
        path_str = str(diff.path).replace("\\", "/")  # Use forward slashes for INI compatibility
        flat_changes[path_str] = diff.new_value if diff.new_value is not None else None
    return flat_changes


def build_hierarchy(flat_changes: dict[str, Any]) -> dict[str, Any]:
    """Build a hierarchical structure suitable for INI serialization from flat changes."""
    hierarchy: dict[str, Any] = {}
    for path, value in flat_changes.items():
        parts = path.split("/")
        current_level: dict[str, Any] = hierarchy
        for part in parts[:-1]:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        current_level[parts[-1]] = value
    return hierarchy


def serialize_to_ini(hierarchy: dict[str, Any]) -> str:
    """Serializes a hierarchical dictionary into an INI-formatted string."""
    ini_lines: list[str] = []

    def serialize_section(
        name: str,
        content: dict[str, Any],
        indent_level: int = 0,
    ) -> None:
        """Serializes a section of the hierarchy into INI format, recursively for nested sections."""
        prefix: str = " " * indent_level * 4  # TODO(th3w1zard1): adjust indent later.
        if indent_level == 0:
            ini_lines.append(f"[{name}]")
        else:
            ini_lines.append(f"{prefix}{name}=")

        for key, value in content.items():
            if isinstance(value, dict):
                serialize_section(key, value, indent_level + 1)
            else:
                if value is None:
                    value_str = "null"
                elif isinstance(value, str) and " " in value:
                    value_str = f'"{value}"'
                else:
                    value_str = str(value)
                ini_lines.append(f"{prefix}{key}={value_str}")

    for section_name, section_content in hierarchy.items():
        serialize_section(section_name, section_content)

    return "\n".join(ini_lines)


# Example usage - requires a GFFCompareResult object:
# if __name__ == "__main__":
#     from pykotor.resource.formats.gff import read_gff
#     gff1 = read_gff("file1.utc")
#     gff2 = read_gff("file2.utc")
#     compare_result = gff1.compare_detailed(gff2)
#     hierarchy = build_hierarchy(flatten_differences(compare_result))
#     ini_content = serialize_to_ini(hierarchy)
#     print(ini_content)
