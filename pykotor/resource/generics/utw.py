from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent


class UTW:
    """
    Stores waypoint data.

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

    def __init__(self):
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


def construct_utw(gff: GFF) -> UTW:
    utw = UTW()

    root = gff.root
    utw.appearance_id = root.acquire("Appearance", 0)
    utw.linked_to = root.acquire("LinkedTo", "")
    utw.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    utw.tag = root.acquire("Tag", "")
    utw.name = root.acquire("LocalizedName", LocalizedString.from_invalid())
    utw.description = root.acquire("Description", LocalizedString.from_invalid())
    utw.has_map_note = root.acquire("HasMapNote", 0)
    utw.map_note = root.acquire("MapNote", LocalizedString.from_invalid())
    utw.map_note_enabled = root.acquire("MapNoteEnabled", 0)
    utw.palette_id = root.acquire("PaletteID", 0)
    utw.comment = root.acquire("Comment", "")

    return utw


def dismantle_utw(utw: UTW, game: Game = Game.K2, *, use_deprecated: bool = True) -> GFF:
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
