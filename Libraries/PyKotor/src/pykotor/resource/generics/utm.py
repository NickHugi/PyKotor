from __future__ import annotations

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, InventoryItem, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


class UTM:
    """Stores merchant data.

    Attributes
    ----------
        resref: "ResRef" field.
        name: "LocName" field.
        tag: "Tag" field.
        mark_up: "MarkUp" field.
        mark_down: "MarkDown" field.
        on_open: "OnOpenStore" field.
        comment: "Comment" field.

        id: "ID" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.UTM

    def __init__(
        self,
    ):
        self.resref: ResRef = ResRef.from_blank()
        self.comment: str = ""
        self.tag: str = ""

        self.name: LocalizedString = LocalizedString.from_invalid()

        self.can_buy: bool = False
        self.can_sell: bool = False

        self.mark_up: int = 0
        self.mark_down: int = 0

        self.on_open: ResRef = ResRef.from_blank()

        self.inventory: list[InventoryItem] = []

        # Deprecated:
        self.id: int = 5


def construct_utm(
    gff: GFF,
) -> UTM:
    utm = UTM()

    root = gff.root
    utm.resref = root.acquire("ResRef", ResRef.from_blank())
    utm.name = root.acquire("LocName", LocalizedString.from_invalid())
    utm.tag = root.acquire("Tag", "")
    utm.mark_up = root.acquire("MarkUp", 0)
    utm.mark_down = root.acquire("MarkDown", 0)
    utm.on_open = root.acquire("OnOpenStore", ResRef.from_blank())
    utm.comment = root.acquire("Comment", "")
    utm.id = root.acquire("ID", 0)
    utm.can_buy = root.acquire("BuySellFlag", 0) & 1 != 0
    utm.can_sell = root.acquire("BuySellFlag", 0) & 2 != 0

    item_list = root.acquire("ItemList", GFFList())
    for item_struct in item_list:
        item = InventoryItem(ResRef.from_blank())
        utm.inventory.append(item)
        item.resref = item_struct.acquire("InventoryRes", ResRef.from_blank())
        item.infinite = bool(item_struct.acquire("Infinite", 0))

    return utm


def dismantle_utm(
    utm: UTM,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTM)

    root = gff.root
    root.set_resref("ResRef", utm.resref)
    root.set_locstring("LocName", utm.name)
    root.set_string("Tag", utm.tag)
    root.set_int32("MarkUp", utm.mark_up)
    root.set_int32("MarkDown", utm.mark_down)
    root.set_resref("OnOpenStore", utm.on_open)
    root.set_string("Comment", utm.comment)
    root.set_uint8("BuySellFlag", utm.can_buy + utm.can_sell * 2)

    item_list = root.set_list("ItemList", GFFList())
    for i, item in enumerate(utm.inventory):
        item_struct = item_list.add(i)
        item_struct.set_resref("InventoryRes", item.resref)
        item_struct.set_uint16("Repos_PosX", i)
        item_struct.set_uint16("Repos_posy", 0)
        if item.infinite:
            item_struct.set_uint8("Infinite", value=True)

    if use_deprecated:
        root.set_uint8("ID", utm.id)

    return gff


def read_utm(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTM:
    gff = read_gff(source, offset, size)
    return construct_utm(gff)


def write_utm(
    utm: UTM,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> None:
    gff = dismantle_utm(utm, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utm(
    utm: UTM | SOURCE_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    if not isinstance(utm, UTM):
        utm = read_utm(utm)
    gff = dismantle_utm(utm, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
