from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.erf import ERF
from pykotor.resource.formats.erf.erf_auto import read_erf
from pykotor.resource.formats.erf.erf_data import ERFType
from pykotor.resource.formats.gff import GFF
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    import os


class SaveManager:
    def __init__(self, save_folder_path: os.PathLike | str):
        self.sav: ERF
        self.res: GFF
        self.save_path: CaseAwarePath = CaseAwarePath.pathify(save_folder_path)
        self.cached_modules: list[ERF] = []  # cached modules inside the sav
        self.partytable: CaseAwarePath = CaseAwarePath()

        # GLOBALVARS.res
        self.global_bools: list[tuple[str, bool]] = []
        self.global_locs: list[tuple[str, Vector3]] = []
        self.global_numbers: list[tuple[str, int]] = []
        self.global_strings: list[tuple[str, str]] = []

        # PARTYTABLE.res
        # - gold
        # - available party members
        # - recent feedback/dlg
        # - pazaak cards/sidedecks
        # - time played/xp amount
        # - galaxymap stuff
        # - etc etc

        # SAVENFO.res
        # - also time played stored here
        # - portraits, 6 fields named 'live0-6'
        # - cheats used
        # - areaname (last?)

        # savegame.sav
        # - cached modules
        # --- each cached module's IFO has a EventQueue section, a simple tool that clears this gfflist fixes various save corruption issues.
        # - Factions file (gff), whatever this does it's found in main game files too.
        # - Multiple 'availnpc.utc' files, each representing a character in the game. Influence probably stored here?
        # - inventory
        # - ...

    def load(self):
        self.load_global_bools()

    def load_global_bools(self):
        globalvars_gff = read_gff(self.save_path / "globalvars.res")
        global_bool_categories = globalvars_gff.root.get_list("CatBoolean")
        global_bools = globalvars_gff.root.get_binary("ValBoolean")
        self.global_bools = [
            (category.get_string("Name"), bool(value))
            for category, value in zip(global_bool_categories, global_bools)
        ]

    def load_global_locs(self):
        globalvars_gff = read_gff(self.save_path / "globalvars.res")
        global_locs_categories = globalvars_gff.root.get_list("CatLocation")
        ...
        return
        global_locs = globalvars_gff.root.get_binary("ValLocation")
        self.global_locs = [
            (category.get_string("Name"), bool(value))
            for category, value in zip(global_locs_categories, global_locs)
        ]

    def load_global_numbers(self):
        globalvars_gff = read_gff(self.save_path / "globalvars.res")
        global_numbers_categories = globalvars_gff.root.get_list("CatNumber")
        ...
        return
        global_numbers = globalvars_gff.root.get_binary("ValNumber")
        self.global_numbers = [
            (category.get_string("Name"), bool(value))
            for category, value in zip(global_numbers_categories, global_numbers)
        ]

    def load_global_strings(self):
        globalvars_gff = read_gff(self.save_path / "globalvars.res")
        global_strings_categories = globalvars_gff.root.get_list("CatString")
        ...
        return
        global_strings = globalvars_gff.root.get_binary("ValString")
        self.global_strings = [
            (category.get_string("Name"), bool(value))
            for category, value in zip(global_strings_categories, global_strings)
        ]