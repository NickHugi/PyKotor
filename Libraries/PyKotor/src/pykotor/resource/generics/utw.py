from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, bytes_gff, read_gff, write_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTW:
    """Stores waypoint data.

    UTW files are GFF-based format files that store waypoint definitions including
    map notes, appearance, and location data.

    References:
    ----------
        vendor/reone/src/libs/resource/parser/gff/utw.cpp:28-42 (UTW parsing from GFF)
        vendor/reone/include/reone/resource/parser/gff/utw.h:28-40 (UTW structure definitions)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorUTW/UTW.cs:11-25 (UTW class definition)
        vendor/KotOR.js/src/module/ModuleWaypoint.ts:15-80 (Waypoint module object)
        Note: UTW files are GFF format files with specific structure definitions

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this waypoint template.
            Reference: reone/utw.cpp:40 (TemplateResRef field)
            Reference: reone/utw.h:39 (TemplateResRef field)
            Reference: Kotor.NET/UTW.cs:15 (TemplateResRef property)

        tag: "Tag" field. Tag identifier for this waypoint.
            Reference: reone/utw.cpp:39 (Tag field)
            Reference: reone/utw.h:38 (Tag field)
            Reference: Kotor.NET/UTW.cs:16 (Tag property)

        name: "LocalizedName" field. Localized name of the waypoint.
            Reference: reone/utw.cpp:35 (LocalizedName field)
            Reference: reone/utw.h:34 (LocalizedName field)
            Reference: Kotor.NET/UTW.cs:17 (LocalizedName property)

        has_map_note: "HasMapNote" field. Whether waypoint has a map note.
            Reference: reone/utw.cpp:33 (HasMapNote field)
            Reference: reone/utw.h:32 (HasMapNote field)
            Reference: Kotor.NET/UTW.cs:19 (HasMapNote property)

        map_note: "MapNote" field. Localized map note text.
            Reference: reone/utw.cpp:36 (MapNote field)
            Reference: reone/utw.h:35 (MapNote field)
            Reference: Kotor.NET/UTW.cs:20 (MapNote property)

        map_note_enabled: "MapNoteEnabled" field. Whether map note is enabled.
            Reference: reone/utw.cpp:37 (MapNoteEnabled field)
            Reference: reone/utw.h:36 (MapNoteEnabled field)
            Reference: Kotor.NET/UTW.cs:21 (MapNoteEnabled property)

        appearance_id: "Appearance" field. Appearance type identifier. Used in toolset only.
            Reference: reone/utw.cpp:30 (Appearance field)
            Reference: reone/utw.h:29 (Appearance field)
            Reference: Kotor.NET/UTW.cs:13 (Appearance property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: reone/utw.cpp:38 (PaletteID field)
            Reference: reone/utw.h:37 (PaletteID field)
            Reference: Kotor.NET/UTW.cs:22 (PaletteID property)

        comment: "Comment" field. Developer comment. Used in toolset only.
            Reference: reone/utw.cpp:31 (Comment field)
            Reference: reone/utw.h:30 (Comment field)
            Reference: Kotor.NET/UTW.cs:23 (Comment property)

        linked_to: "LinkedTo" field. Linked waypoint tag. Not used by the game engine.
            Reference: reone/utw.cpp:34 (LinkedTo field)
            Reference: reone/utw.h:33 (LinkedTo field)
            Reference: Kotor.NET/UTW.cs:14 (LinkedTo property)

        description: "Description" field. Localized description. Not used by the game engine.
            Reference: reone/utw.cpp:32 (Description field)
            Reference: reone/utw.h:31 (Description field)
            Reference: Kotor.NET/UTW.cs:18 (Description property)
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

    root: GFFStruct = gff.root
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
    game: Game = Game.K2,  # noqa: ARG001
    *,
    use_deprecated: bool = True,  # noqa: ARG001
) -> GFF:
    gff = GFF(GFFContent.UTW)

    root: GFFStruct = gff.root
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
    gff: GFF = read_gff(source, offset, size)
    return construct_utw(gff)


def write_utw(
    utw: UTW,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_utw(utw, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utw(
    utw: UTW,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_utw(utw, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
