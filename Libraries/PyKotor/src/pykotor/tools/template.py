from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.gff import GFFContent, read_gff

if TYPE_CHECKING:
    import types

    from pykotor.common.language import LocalizedString
    from pykotor.common.module import GFF


def extract_name(
    data: bytes,
) -> LocalizedString:
    """Extracts the name from GFF data.

    Args:
    ----
        data: Bytes containing GFF data
    Returns:
        LocalizedString: Extracted name string

    Processing Logic:
    ----------------
        - Read GFF data from bytes
        - Check content type and select appropriate name field
        - Return localized name string.
    """
    gff: GFF = read_gff(data)
    if gff.content == GFFContent.UTC:
        return gff.root.get_locstring("FirstName")
    if gff.content in {GFFContent.UTT, GFFContent.UTW}:
        return gff.root.get_locstring("LocalizedName")
    return gff.root.get_locstring("LocName")


def extract_tag_from_gff(
    data: bytes,
) -> str:
    gff: GFF = read_gff(data)
    return gff.root.get_string("Tag")


if __name__ == "__main__":
    import pkgutil

    def list_modules(package_name: str) -> list[str]:
        package: types.ModuleType = __import__(package_name, fromlist=[""])
        return [name for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + ".")]

    # Example usage
    package_name = "pykotor"
    modules: list[str] = list_modules(package_name)
    print(f"Total modules: {len(modules)}")
