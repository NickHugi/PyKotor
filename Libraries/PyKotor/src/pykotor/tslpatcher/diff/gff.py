from __future__ import annotations


def flatten_differences(compare_result):
    """Flattens the differences from GFFCompareResult into a flat dictionary.

    Args:
    ----
        compare_result (GFFCompareResult): The result of a GFF comparison.

    Returns:
    -------
        dict: A flat dictionary representing the changes.
    """
    flat_changes = {}
    for diff in compare_result.get_differences():
        path_str = str(diff.path).replace("\\", "/")  # Use forward slashes for INI compatibility
        if diff.new_value is not None:  # Changed or added
            flat_changes[path_str] = diff.new_value
        else:  # Removed
            flat_changes[path_str] = None  # Represent removals as None or consider a special marker
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
    hierarchy = {}
    for path, value in flat_changes.items():
        parts = path.split("/")
        current_level = hierarchy
        for part in parts[:-1]:  # Navigate/create to the correct nested level, excluding the last part
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        current_level[parts[-1]] = value  # Set the final part as the value
    return hierarchy


def serialize_to_ini(hierarchy):
    """Serializes a hierarchical dictionary into an INI-formatted string.

    Args:
        hierarchy (dict): The hierarchical dictionary representing nested changes.

    Returns:
        str: A string formatted in INI structure.
    """
    ini_lines = []

    def serialize_section(name, content, indent_level=0):
        """Serializes a section of the hierarchy into INI format, recursively for nested sections.

        Args:
            name (str): The name of the section.
            content (dict): The content of the section.
            indent_level (int): The current indentation level (for nested sections).
        """
        prefix = " " * indent_level * 4  # TODO(th3w1zard1): adjust indent later.
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


if __name__ == "__main__":
    # gff_compare_result = something.compare(another)
    hierarchy = build_hierarchy(flatten_differences(gff_compare_result))
    ini_content = serialize_to_ini(hierarchy)
    print(ini_content)
