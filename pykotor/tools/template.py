from pykotor.common.language import LocalizedString
from pykotor.resource.formats.gff import read_gff, GFFContent


def extract_name(data: bytes) -> LocalizedString:
    gff = read_gff(data)
    if gff.content in [GFFContent.UTC]:
        return gff.root.get_locstring("FirstName")
    elif gff.content in [GFFContent.UTT, GFFContent.UTW]:
        return gff.root.get_locstring("LocalizedName")
    else:
        return gff.root.get_locstring("LocName")


def extract_tag(data: bytes) -> str:
    gff = read_gff(data)
    return gff.root.get_string("Tag")
