from typing import List, Optional, Dict

from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QWidget
from pykotor.extract.file import FileQuery
from pykotor.extract.installation import Installation
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

    def __init__(self, path: str, name: str, tsl: bool, mainWindow: QWidget):
        super().__init__(path, name, tsl)

        self.mainWindow: QWidget = mainWindow
        self.cacheCoreItems: Optional[QStandardItemModel] = None

        self._cache2da: Dict[str, TwoDA] = {}
        self._cacheTpc: Dict[str, TPC] = {}

    # region Cache 2DA
    def htGetCache2DA(self, resname: str):
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

        resources = self.resource_batch(queries, skip_modules=True)
        for resource in resources:
            self._cache2da[resource.resname] = load_2da(resource.data)

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
