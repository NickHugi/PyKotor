from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.gff import GFFContent, read_gff

if TYPE_CHECKING:
    from pykotor.common.language import LocalizedString


def extract_name(data: bytes) -> LocalizedString:
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
    gff = read_gff(data)
    if gff.content == GFFContent.UTC:
        return gff.root.get_locstring("FirstName")
    if gff.content in {GFFContent.UTT, GFFContent.UTW}:
        return gff.root.get_locstring("LocalizedName")
    return gff.root.get_locstring("LocName")


def extract_tag(data: bytes) -> str:
    gff = read_gff(data)
    return gff.root.get_string("Tag")
