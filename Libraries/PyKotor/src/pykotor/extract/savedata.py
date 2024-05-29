from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector4
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf.erf_auto import read_erf
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.generics.utc import read_utc
from pykotor.resource.generics.uti import construct_uti_from_struct
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    import os

    from pykotor.common.module import Module
    from pykotor.resource.formats.erf.erf_data import ERF
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utc import UTC
    from pykotor.resource.generics.uti import UTI

class SaveInfo:
    """SAVENFO.res
    # - also time played stored here
    # - portraits, 6 fields named 'live0-6'
    # - cheats used
    # - areaname (last?).
    """

    IDENTIFIER: ResourceIdentifier = ResourceIdentifier("savenfo", ResourceType.RES)

    def __init__(self, path: os.PathLike | str, ident: ResourceIdentifier | None = None):
        ident = self.IDENTIFIER if ident is None else ident
        self.save_info_path: CaseAwarePath = CaseAwarePath.pathify(path) / str(ident)

        self.area_name: str = ""
        self.cheat_used: bool = False  # Also in PartyTable?
        self.gameplay_hint: int = 0  # Some strref to the tlk, also in loadscreenhints.2da
        self.last_module: str = ""  # Confirmed (e.g. 'danm13')

        # Xbox live stuff.
        self.live1: str = ""
        self.live2: str = ""
        self.live3: str = ""
        self.live4: str = ""
        self.live5: str = ""
        self.live6: str = ""
        self.livecontent: int = 0

        # Presumably these are the portraits of the current party.
        self.portrait0: ResRef = ResRef.from_blank()
        self.portrait1: ResRef = ResRef.from_blank()
        self.portrait2: ResRef = ResRef.from_blank()
        self.savegame_name: str = ""  # Confirmed. User-customized save name.
        self.story_hint: int = 0  # Some strref to the tlk, also in loadscreenhints.2da
        self.time_played: int = 0  # Also in PartyTable

    def load(self):
        ...

class JournalEntry:
    def __init__(self):
        self.date: int = -1  # uint32
        self.plot_id: str = ""
        self.state: int = -1  # int32
        self.time: int = -1  # uint32, guessing the 'total played time' value is moved here when the journal changes.

class AvailableNPCEntry:
    def __init__(self):
        self.npc_available: bool = False
        self.npc_selected: bool = False

class PartyMemberEntry:
    def __init__(self):
        self.is_leader: bool = False
        self.index: int = -1  # probably the index in availnpc or some global ordered list of companions.

class GalaxyMapEntry:
    def __init__(self):
        ...

class PartyTable:
    """PARTYTABLE.res
    # - gold
    # - available party members
    # - recent feedback/dlg
    # - pazaak cards/sidedecks
    # - time played/xp amount
    # - galaxymap stuff
    # - etc etc.
    """

    IDENTIFIER: ResourceIdentifier = ResourceIdentifier("partytable", ResourceType.RES)

    def __init__(self, path: os.PathLike | str, ident: ResourceIdentifier | None = None):
        ident = self.IDENTIFIER if ident is None else ident
        self.party_table_path: CaseAwarePath = CaseAwarePath.pathify(path) / str(ident)
        self.galaxy_map: dict | None = None
        self.jnl_entries: list[JournalEntry] = []
        self.jnl_sort_order: int = 0
        self.pt_aistate: int = 0
        self.pt_avail_npcs: list[AvailableNPCEntry] = []
        self.pt_cheat_used: bool = False  # Assuming this is a boolean based on the UIInt8 type
        self.pt_controlled_npc: int = -1  # Defaults to -1, assuming it represents 'none' or similar
        self.pt_cost_mult_lis: list = []
        self.pt_dlg_msg_list: list = []
        self.pt_fb_msg_list: list = []  # feedback, cbf implementing.
        self.pt_followstate: int = 0
        self.pt_gold: int = 0
        self.pt_last_gui_pnl: int = 0  # another enum
        self.pt_members: list[PartyMemberEntry] = []
        self.pt_num_members: int = 0
        self.pt_pazaakcards: list = []  # cbf
        self.pt_pazaakdecks: list = []  # cbf
        self.time_played: int = -1
        self.pt_solomode: bool = False  # probably the option in the game that determines whether the party members follow the leader.
        self.pt_tut_wnd_shown: bytes = b""  # Presumably what tutorial information has already been shown to the user. cbf
        self.pt_xp_pool: int = 0

    def load(self):
        party_table_gff = read_gff(self.party_table_path)
        ...

class GlobalVars:

    IDENTIFIER: ResourceIdentifier = ResourceIdentifier("globalvars", ResourceType.RES)

    def __init__(self, path: os.PathLike | str, ident: ResourceIdentifier | None = None):
        ident = self.IDENTIFIER if ident is None else ident
        self.globals_filepath = CaseAwarePath.pathify(path) / str(ident)

        self.global_bools: list[tuple[str, bool]] = []
        self.global_locs: list[tuple[str, Vector4]] = []
        self.global_numbers: list[tuple[str, int]] = []
        self.global_strings: list[tuple[str, str]] = []

    def load(self):
        globalvars_gff = read_gff(self.globals_filepath)

        # Booleans
        global_bool_categories = globalvars_gff.root.get_list("CatBoolean")
        global_bools = globalvars_gff.root.get_binary("ValBoolean")
        self.global_bools = [
            (category.get_string("Name"), bool(value))
            for category, value in zip(global_bool_categories, global_bools)
        ]

        # Locations
        global_locs_categories = globalvars_gff.root.get_list("CatLocation")
        global_locs = globalvars_gff.root.get_binary("ValLocation")
        with BinaryReader.from_bytes(global_locs) as reader:
            self.global_locs = [
                (
                    category.get_string("Name"),
                    Vector4(
                        reader.read_single(),
                        reader.read_single(),
                        reader.read_single(),
                        reader.read_single(),
                    ),
                )
                for category in global_locs_categories
            ]

        # Numbers
        global_numbers_categories = globalvars_gff.root.get_list("CatNumber")
        global_numbers = globalvars_gff.root.get_binary("ValNumber")
        with BinaryReader.from_bytes(global_numbers) as reader:
            self.global_number = [
                (
                    category.get_string("Name"),
                    reader.read_uint8(),
                )
                for category in global_numbers_categories
            ]

        # Strings
        global_strings_categories = globalvars_gff.root.get_list("CatString")
        global_strings = globalvars_gff.root.get_list("ValString")
        self.global_string = [
            (
                category.get_string("Name"),
                value.get_string("String"),
            )
            for category, value in zip(global_strings_categories, global_strings)
        ]

class SaveNestedCapsule:
    """savegame.sav
    - cached modules
    --- each cached module's IFO has a EventQueue section, a simple tool that clears this gfflist fixes various save corruption issues.
    - Factions file (gff), whatever this does it's found in main game files too.
    - Multiple 'availnpc.utc' files, each representing a character in the game. Influence probably stored here?
    - inventory
    - ...
    """
    IDENTIFIER: ResourceIdentifier = ResourceIdentifier("savegame", ResourceType.SAV)
    INVENTORY_IDENTIFIER: ResourceIdentifier = ResourceIdentifier("inventory", ResourceType.RES)

    def __init__(self, path: os.PathLike | str, ident: ResourceIdentifier | None = None):
        ident = self.IDENTIFIER if ident is None else ident
        self.nested_capsule_path = CaseAwarePath.pathify(path) / str(ident)
        self.nested_resources_path = Capsule(self.nested_capsule_path)
        self.cached_modules: list[ERF] = []  # cached modules inside the sav
        self.cached_characters: list[UTC] = []  # cached availnpc utc's
        self.inventory: list[UTI] = []
        self.repute: GFF  # factions file.

    def load(self):
        self.load_cached()

    def load_cached(self, *, reload: bool = False):
        for resource in self.nested_resources_path.resources(reload=reload):
            if resource.restype() is ResourceType.SAV:
                sav = read_erf(resource.data())
                self.cached_modules.append(sav)
            if resource.restype() is ResourceType.UTC:
                utc = read_utc(resource.data())
                self.cached_characters.append(utc)
            if resource.identifier() == self.INVENTORY_IDENTIFIER:
                inventory_gff = read_gff(resource.data())
                item_list = inventory_gff.root.get_list("ItemList")
                for item in item_list:
                    uti = construct_uti_from_struct(item)
                    self.inventory.append(uti)

    def update_nested_module(self, module: Module):
        """Updates a module in a save and retains all of the original bools/strings that were set.

        This function is useful if you've updated a module and don't want to recreate a save to test it.
        """
        # Should just copy the resources from the module, and update the static lists that only exist in the save data.
        # Could diff them but it'd be easier/more readable to hardcode them in.
        # Might be useful to hook up the toolset's Watchdog up to this in an optional feature the user can activate in Settings.

class SaveFolderEntry:
    """Represents all data in a single save."""

    SAVE_INFO_NAME: ResourceIdentifier = ResourceIdentifier("savenfo", ResourceType.RES)
    SCREENSHOT_NAME: ResourceIdentifier = ResourceIdentifier("screen", ResourceType.TGA)

    def __init__(self, save_folder_path: os.PathLike | str):
        """Initializes a single save entry in KOTOR 1 and 2.

        Args:
        ----
            - save_folder_path (os.PathLike | str): The path to the save folder (e.g. path to '000057 - game56').

        Processing Logic:
        ----------------
            - Sets the save path to the given save folder path.
            - Initializes all resources and abstracts them away.
        """
        self.save_path: CaseAwarePath = CaseAwarePath.pathify(save_folder_path)

        self.sav: SaveNestedCapsule = SaveNestedCapsule(self.save_path)
        self.partytable: PartyTable = PartyTable(self.save_path)
        self.save_info: SaveInfo = SaveInfo(self.save_path)
        self.globals: GlobalVars = GlobalVars(self.save_path)

    def load(self):
        print("Loading nested save capsule...")
        self.sav.load()
        print("Loading party table...")
        self.partytable.load()
        print("Loading save info...")
        self.save_info.load()
        print("Loading save globals...")
        self.globals.load()

    def save(self):
        ...


if __name__ == "__main__":
    game59_save = SaveFolderEntry(r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II\saves\000002 - Game1")
    game59_save.load()
    game59_save.save()
