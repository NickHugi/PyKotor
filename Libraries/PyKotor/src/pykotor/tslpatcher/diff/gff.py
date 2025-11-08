from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFCompareResult


def flatten_differences(compare_result: GFFCompareResult) -> dict[str, Any]:
    """Flattens the differences from GFFCompareResult into a flat dictionary.

    Args:
    ----
        compare_result (GFFCompareResult): The result of a GFF comparison.

    Returns:
    -------
        dict: A flat dictionary representing the changes.
    """
    flat_changes: dict[str, Any] = {}
    for diff in compare_result.differences:
        path_str = str(diff.path).replace("\\", "/")
        flat_changes[path_str] = diff.new_value
    return flat_changes


def build_hierarchy(flat_changes):
    """Builds a hierarchical structure suitable for INI serialization from flat changes.

    Args:
    ----
        flat_changes (dict): The flat dictionary of changes.

    Returns:
    -------
        dict: A hierarchical dictionary representing the nested structure.
    """
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
    """Serializes a hierarchical dictionary into an INI-formatted string.

    Args:
        hierarchy (dict): The hierarchical dictionary representing nested changes.

    Returns:
        str: A string formatted in INI structure.
    """
    ini_lines: list[str] = []

    def serialize_section(
        name: str,
        content: dict[str, Any],
        indent_level: int = 0,
    ):
        """Serializes a section of the hierarchy into INI format, recursively for nested sections.

        Args:
            name (str): The name of the section.
            content (dict): The content of the section.
            indent_level (int): The current indentation level (for nested sections).
        """
        prefix: str = " " * indent_level * 4  # TODO(th3w1zard1): adjust indent later.
        if indent_level == 0:
            ini_lines.append(f"[{name}]")
        else:
            ini_lines.append(f"{prefix}{name}=")

        for key, value in content.items():
            if isinstance(value, dict):
                # Nested section
                serialize_section(key, value, indent_level + 1)
            else:
                # Key-value pair
                if value is None:
                    value_str = "null"  # TODO(th3w1zard1): determine nonexistence and use a singular value.
                elif isinstance(value, str) and " " in value:
                    value_str = f'"{value}"'  # Quote strings with spaces
                else:
                    value_str = str(value)
                ini_lines.append(f"{prefix}{key}={value_str}")

    # Start serialization with the root level
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
