from __future__ import annotations


def version_to_toolset_tag(
    version: str,
) -> str:
    major_minor_patch_count = 2
    if version.count(".") == major_minor_patch_count:
        second_dot_index: int = version.find(".", version.find(".") + 1)  # Find the index of the second dot
        version = version[:second_dot_index] + version[second_dot_index + 1 :]  # Remove the second dot by slicing and concatenating
    return f"v{version}-toolset"


def toolset_tag_to_version(
    tag: str,
) -> str:
    numeric_part: str = "".join([c for c in tag if c.isdigit() or c == "."])
    parts: list[str] = numeric_part.split(".")

    major_minor_patch_len = 3
    if len(parts) == major_minor_patch_len:
        return ".".join(parts)
    major_minor_len = 2
    if len(parts) == major_minor_len:
        return ".".join(parts)

    # Handle the legacy typo format (missing second dot)
    major_len = 1
    major: str = parts[0]
    if len(parts) > major_len:
        # Assume the minor version always precedes the concatenated patch version
        minor: str = parts[1][0]  # Take the first digit as the minor version
        patch: str = parts[1][1:]  # The rest is considered the patch
        return f"{major}.{minor}.{patch}"

    return f"{major}.0.0"  # In case there's only a major version
