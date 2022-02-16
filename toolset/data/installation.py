from typing import List, Optional, Dict

from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QWidget
from pykotor.extract.file import FileQuery
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.tpc import TPC
from pykotor.resource.formats.twoda import TwoDA, load_2da
from pykotor.resource.generics.uti import UTI
from pykotor.resource.type import ResourceType


class HTInstallation(Installation):

    TwoDA_PORTRAITS = "portraits"
    TwoDA_APPEARANCES = "appearance"
    TwoDA_SUBRACES = "subrace"
    TwoDA_SPEEDS = "creaturespeed"
    TwoDA_SOUNDSETS = "soundset"
    TwoDA_FACTIONS = "repute"
    TwoDA_GENDERS = "gender"
    TwoDA_PERCEPTIONS = "ranges"
    TwoDA_CLASSES = "classes"
    TwoDA_FEATS = "feat"
    TwoDA_POWERS = "spells"
    TwoDA_BASEITEMS = "baseitems"
    TwoDA_PLACEABLES = "placeables"
    TwoDA_DOORS = "genericdoors"
    TwoDA_CURSORS = "cursors"
    TwoDA_TRAPS = "traps"
    TwoDA_RACES = "racialtypes"
    TwoDA_SKILLS = "skills"
    TwoDA_UPGRADES = "upgrade"
    TwoDA_ENC_DIFFICULTIES = "encdifficulty"
    TwoDA_ITEM_PROPERTIES = "itempropdef"
    TwoDA_IPRP_PARAMTABLE = "iprp_paramtable"
    TwoDA_IPRP_COSTTABLE = "iprp_costtable"
    TwoDA_IPRP_ABILITIES = "iprp_abilities"
    TwoDA_IPRP_ALIGNGRP = "iprp_aligngrp"
    TwoDA_IPRP_COMBATDAM = "iprp_combatdam"
    TwoDA_IPRP_DAMAGETYPE = "iprp_damagetype"
    TwoDA_IPRP_PROTECTION = "iprp_protection"
    TwoDA_IPRP_ACMODTYPE = "iprp_acmodtype"
    TwoDA_IPRP_IMMUNITY = "iprp_immunity"
    TwoDA_IPRP_SAVEELEMENT = "iprp_saveelement"
    TwoDA_IPRP_SAVINGTHROW = "iprp_savingthrow"
    TwoDA_IPRP_ONHIT = "iprp_onhit"
    TwoDA_IPRP_AMMOTYPE = "iprp_ammotype"
    TwoDA_IPRP_MONSTERHIT = "iprp_mosterhit"
    TwoDA_IPRP_WALK = "iprp_walk"

    def __init__(self, path: str, name: str, tsl: bool, mainWindow: QWidget):
        super().__init__(path, name, tsl)

        self.mainWindow: QWidget = mainWindow
        self.cacheCoreItems: Optional[QStandardItemModel] = None

        self._cache2da: Dict[str, TwoDA] = {}
        self._cacheTpc: Dict[str, TPC] = {}

    # region Cache 2DA
    def htGetCache2DA(self, resname: str):
        resname = resname.lower()
        if resname not in self._cache2da:
            self._cache2da[resname] = self.twoda(resname)
        return self._cache2da[resname]

    def htBatchCache2DA(self, resnames: List[str], reload: bool = False):
        if reload:
            queries = [FileQuery(resname, ResourceType.TwoDA) for resname in resnames]
        else:
            queries = [FileQuery(resname, ResourceType.TwoDA) for resname in resnames if resname not in self._cache2da]

        if not queries:
            return

        resources = self.resource_batch(queries, [SearchLocation.CHITIN, SearchLocation.OVERRIDE])
        for resource in resources:
            self._cache2da[resource.resname.lower()] = load_2da(resource.data)

    def htClearCache2DA(self):
        self._cache2da = {}
    # endregion

    # region Cache TPC
    def htGetCacheTPC(self, resname: str) -> Optional[TPC]:
        if resname not in self._cacheTpc:
            self._cacheTpc[resname] = self.texture(resname, skip_modules=True, skip_chitin=True, skip_gui=False)
        return self._cacheTpc[resname] if resname in self._cacheTpc else None

    def htBatchCacheTPC(self, names: List[str], reload: bool = False):
        if reload:
            queries = [name for name in names]
        else:
            queries = [name for name in names if name not in self._cache2da]

        if not queries:
            return

        for resname in queries:
            self._cacheTpc[resname] = self.texture(resname, skip_modules=True, skip_chitin=True, skip_gui=False)

    def htClearCacheTPC(self):
        self._cacheTpc = {}
    # endregion
