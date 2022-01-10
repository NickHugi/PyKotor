from __future__ import annotations

from typing import List

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef, Game
from pykotor.resource.formats.gff import GFF, GFFList


class UTM:
    """
    Stores merchant data.

    Attributes:
        resref: "ResRef" field.
        name: "LocName" field.
        tag: "Tag" field.
        mark_up: "MarkUp" field.
        mark_down: "MarkDown" field.
        on_open: "OnOpenStore" field.
        comment: "Comment" field.

        id: "ID" field. Not used by the game engine.
    """

    def __init__(self):
        self.resref: ResRef = ResRef.from_blank()
        self.comment: str = ""
        self.tag: str = ""

        self.name: LocalizedString = LocalizedString.from_invalid()

        self.can_buy: bool = False
        self.can_sell: bool = False

        self.mark_up: int = 0
        self.mark_down: int = 0

        self.on_open: ResRef = ResRef.from_blank()

        self.inventory: List[UTMItem] = []

        # Deprecated:
        self.id: int = 0


class UTMItem:
    """
    Stores the data for items that can be bought from a merchant.

    Attributes:
        resref: "InventoryRes" field.
        infinite: "Infinite" field.
    """

    def __init__(self):
        self.resref: ResRef = ResRef.from_blank()
        self.infinite: bool = False


def construct_utm(gff: GFF) -> UTM:
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
        item = UTMItem()
        utm.inventory.append(item)
        item.resref = item_struct.acquire("InventoryRes", ResRef.from_blank())
        item.infinite = bool(item_struct.acquire("Infinite", 0))

    return utm
    
    
def dismantle_utm(utm: UTM, game: Game = Game.K2, *, use_deprecated: bool = True) -> GFF:
    gff = GFF()

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
            item_struct.set_uint8("Infinite", True)

    if use_deprecated:
        root.set_uint8("ID", utm.id)

    return gff
