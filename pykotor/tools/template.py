from pykotor.common.language import LocalizedString
from pykotor.resource.formats.gff import GFFContent, read_gff


def extract_name(data: bytes) -> LocalizedString:
    gff = read_gff(data)
    if gff.content in [GFFContent.UTC]:
        return gff.root.get_locstring("FirstName")
    if gff.content in [GFFContent.UTT, GFFContent.UTW]:
        return gff.root.get_locstring("LocalizedName")
    return gff.root.get_locstring("LocName")


def extract_tag(data: bytes) -> str:
    gff = read_gff(data)
    return gff.root.get_string("Tag")
