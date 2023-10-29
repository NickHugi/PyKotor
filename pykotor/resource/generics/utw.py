from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class UTW:
    """Stores waypoint data.

    resref: "TemplateResRef" field.
    tag: "Tag" field.
    name: "LocalizedName" field.
    has_map_note: "HasMapNote" field.
    map_note: "MapNote" field.
    map_note_enabled: "MapNoteEnabled" field.

    palette_id: "PaletteID" field. Used in toolset use only.
    comment: "Comment" field. Used in toolset only.
    appearance_id: "Appearance" field. Used in toolset use only.

    linked_to: "LinkedTo" field. Not used by the game engine.
    description: "Description" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.UTW

    def __init__(
        self,
    ):
        self.resref: ResRef = ResRef.from_blank()
        self.comment: str = ""
        self.tag: str = ""

        self.name: LocalizedString = LocalizedString.from_invalid()

        self.has_map_note: bool = False
        self.map_note_enabled: bool = False
        self.map_note: LocalizedString = LocalizedString.from_invalid()

        self.appearance_id: int = 0
        self.palette_id: int = 0

        # Deprecated:
        self.linked_to: str = ""
        self.description: LocalizedString = LocalizedString.from_invalid()


def construct_utw(
    gff: GFF,
) -> UTW:
    utw = UTW()

    root = gff.root
    utw.appearance_id = root.acquire("Appearance", 0)
    utw.linked_to = root.acquire("LinkedTo", "")
    utw.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    utw.tag = root.acquire("Tag", "")
    utw.name = root.acquire("LocalizedName", LocalizedString.from_invalid())
    utw.description = root.acquire("Description", LocalizedString.from_invalid())
    utw.has_map_note = bool(root.acquire("HasMapNote", 0))
    utw.map_note = root.acquire("MapNote", LocalizedString.from_invalid())
    utw.map_note_enabled = bool(root.acquire("MapNoteEnabled", 0))
    utw.palette_id = root.acquire("PaletteID", 0)
    utw.comment = root.acquire("Comment", "")

    return utw


def dismantle_utw(
    utw: UTW,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTW)

    root = gff.root
    root.set_uint8("Appearance", utw.appearance_id)
    root.set_string("LinkedTo", utw.linked_to)
    root.set_resref("TemplateResRef", utw.resref)
    root.set_string("Tag", utw.tag)
    root.set_locstring("LocalizedName", utw.name)
    root.set_locstring("Description", utw.description)
    root.set_uint8("HasMapNote", utw.has_map_note)
    root.set_locstring("MapNote", utw.map_note)
    root.set_uint8("MapNoteEnabled", utw.map_note_enabled)
    root.set_uint8("PaletteID", utw.palette_id)
    root.set_string("Comment", utw.comment)

    return gff


def read_utw(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTW:
    gff = read_gff(source, offset, size)
    return construct_utw(gff)


def write_utw(
    utw: UTW,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> None:
    gff = dismantle_utw(utw, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utw(
    utw: UTW,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_utw(utw, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
