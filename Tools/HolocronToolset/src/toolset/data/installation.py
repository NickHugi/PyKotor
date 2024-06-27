from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, Collection, cast

from qtpy.QtCore import Qt
from qtpy.QtGui import QImage, QPixmap, QTransform
from qtpy.QtWidgets import QAction, QComboBox, QLineEdit, QMenu

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.type import ResourceType
from toolset.utils.window import addWindow

if TYPE_CHECKING:

    from qtpy.QtGui import QStandardItemModel
    from qtpy.QtWidgets import QPlainTextEdit
    from typing_extensions import Literal, Self

    from pykotor.extract.file import FileResource, LocationResult
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.uti import UTI
    from utility.system.path import PurePath


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
    TwoDA_EMOTIONS = "emotion"
    TwoDA_EXPRESSIONS = "facialanim"
    TwoDA_VIDEO_EFFECTS = "videoeffects"
    TwoDA_DIALOG_ANIMS = "dialoganimations"
    TwoDA_PLANETS = "planetary"
    TwoDA_PLOT = "plot"
    TwoDA_CAMERAS = "camerastyle"

    def __init__(
        self,
        path: str,
        name: str,
        *,
        tsl: bool | None = None,
        progress_callback: Callable[[int | str, Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"]], Any] | None = None
    ):
        super().__init__(path, progress_callback=progress_callback)

        self.name: str = name
        self.cacheCoreItems: QStandardItemModel | None = None

        self._tsl: bool | None = tsl
        self._cache2da: dict[str, TwoDA] = {}
        self._cacheTpc: dict[str, TPC] = {}

    @property
    def tsl(self) -> bool:
        if self._tsl is None:
            self._tsl = self.game().is_k2()
        return self._tsl

    @classmethod
    def from_base_instance(cls, installation: Installation) -> Self:
        ht_installation = cast(cls, installation)

        ht_installation.name = f"NonHTInit_{installation.__class__.__name__}_{id(installation)}"
        ht_installation._tsl = installation.game().is_k2()  # noqa: SLF001
        ht_installation.cacheCoreItems = None
        ht_installation._cache2da = {}  # noqa: SLF001
        ht_installation._cacheTpc = {}  # noqa: SLF001

        ht_installation.__class__ = cls
        return ht_installation

    def setupFileContextMenu(
        self,
        widget: QPlainTextEdit | QLineEdit | QComboBox,
        resref_type: list[ResourceType] | list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
    ):
        from toolset.gui.dialogs.load_from_location_result import ResourceItems
        def extendContextMenu(pos):
            if isinstance(widget, QComboBox):
                rootMenu = QMenu(widget)
                widgetText = widget.currentText().strip()
                firstAction = None
            else:
                rootMenu = widget.createStandardContextMenu()
                widgetText = (widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()).strip()
                firstAction = rootMenu.actions()[0] if rootMenu.actions() else None

            print("<SDM> [extendContextMenu scope] rootMenu: ", rootMenu)
            print("<SDM> [extendContextMenu scope] widgetText: ", widgetText)

            if widgetText:
                fileMenu = QMenu("File...", widget)
                print("<SDM> [extendContextMenu scope] fileMenu: ", fileMenu)

                if firstAction:
                    rootMenu.insertMenu(firstAction, fileMenu)
                    rootMenu.insertSeparator(firstAction)
                else:
                    rootMenu.addMenu(fileMenu)

                rootMenu.insertMenu(firstAction, fileMenu)
                rootMenu.insertSeparator(firstAction)
                search_order = order or [
                    SearchLocation.CHITIN,
                    SearchLocation.OVERRIDE,
                    SearchLocation.MODULES,
                    SearchLocation.RIMS,
                ]
                print("<SDM> [extendContextMenu scope] search_order: ", search_order)

                locations = self.locations(([widgetText], resref_type if isinstance(resref_type, Collection) and len(resref_type) > 1 and isinstance(resref_type[1], ResourceType) else resref_type), search_order)
                print("<SDM> [extendContextMenu scope] locations: ", locations)

                flatLocations = [item for sublist in locations.values() for item in sublist] if isinstance(locations, dict) else locations
                print("<SDM> [extendContextMenu scope] flatLocations: ", flatLocations)

                if flatLocations:
                    for location in flatLocations:
                        displayPath = location.filepath.relative_to(self.path())
                        if location.as_file_resource().inside_bif:
                            displayPath /= location.as_file_resource().filename()
                        displayPathStr = str(displayPath)
                        print("<SDM> [extendContextMenu scope] displayPathStr: ", displayPathStr)

                        locationMenu = fileMenu.addMenu(displayPathStr)
                        print("<SDM> [extendContextMenu scope] locationMenu: ", locationMenu)

                        resourceMenuBuilder = ResourceItems(resources=[location])
                        print("<SDM> [extendContextMenu scope] resourceMenuBuilder: ", resourceMenuBuilder)

                        resourceMenuBuilder.build_menu(locationMenu, self)

                    detailsAction = QAction("Details...", fileMenu)
                    print("<SDM> [extendContextMenu scope] detailsAction: ", detailsAction)

                    detailsAction.triggered.connect(lambda: self._openDetails(flatLocations))
                    fileMenu.addAction(detailsAction)
                else:
                    fileMenu.setDisabled(True)
                for action in rootMenu.actions():
                    if action.text() == "File...":
                        action.setText(f"{len(flatLocations)} file(s) located")
                        break

            rootMenu.exec_(widget.mapToGlobal(pos))

        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(extendContextMenu)

    def _openDetails(self, locations: list[LocationResult]):
        from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
        selectionWindow = FileSelectionWindow(locations, self)
        print("<SDM> [_openDetails scope] selectionWindow: %s", selectionWindow)

        addWindow(selectionWindow)
        selectionWindow.activateWindow()


    # region Cache 2DA
    def htGetCache2DA(self, resname: str) -> TwoDA | None:
        """Gets a 2DA resource from the cache or loads it if not present.

        Args:
        ----
            resname: The name of the 2DA resource to retrieve

        Returns:
        -------
            2DA: The retrieved 2DA data

        Processing Logic:
        ----------------
            - Check if the 2DA is already cached
            - If not cached, retrieve the 2DA data from the resource system
            - Parse and cache the retrieved 2DA data
            - Return the cached 2DA data.
        """
        resname = resname.lower()
        if resname not in self._cache2da:
            result = self.resource(resname, ResourceType.TwoDA, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            if result is None:
                return None
            self._cache2da[resname] = read_2da(result.data)
        return self._cache2da[resname]

    def getRelevantResources(
        self,
        restype: ResourceType,
        src_filepath: PurePath | None = None,
    ) -> set[FileResource]:
        """Use logic to get a list of relevant resources for various contexts."""
        from pykotor.common.module import Module
        if src_filepath is not None:
            relevant_resources = {res for res in self.override_resources() if res.restype() is restype}
            relevant_resources.update(res for res in self.chitin_resources() if res.restype() is restype)
            if src_filepath.is_relative_to(self.module_path()):
                relevant_resources.update(
                    res
                    for cap in Module.find_capsules(self, src_filepath.name, strict=True)
                    for res in cap
                    if res.restype() is restype
                )
            elif src_filepath.is_relative_to(self.override_path()):
                relevant_resources.update(
                    res
                    for relevant_reslist in (
                        reslist
                        for reslist in self._modules.values()
                        if any(res.identifier() == src_filepath.name for res in reslist)
                    )
                    for res in relevant_reslist
                    if res.restype() is restype
                )
        else:
            relevant_resources = {res for res in self if res.restype() is restype}
        return relevant_resources

    def htBatchCache2DA(self, resnames: list[str], *, reload: bool = False):
        """Cache 2D array resources in batch.

        Args:
        ----
            resnames: List of resource names to cache
            reload: Whether to reload cached resources

        Processing Logic:
        ----------------
            1. Check if reload is True, query all resources. Else, query only non-cached resources
            2. Query the resources from override and chitin locations
            3. Read and cache the 2DA data for each queried resource.
        """
        if reload:
            queries = [ResourceIdentifier(resname, ResourceType.TwoDA) for resname in resnames]
        else:
            queries = [ResourceIdentifier(resname, ResourceType.TwoDA) for resname in resnames if resname not in self._cache2da]

        if not queries:
            return

        resources = self.resources(queries, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
        for iden, resource in resources.items():
            if not resource:
                continue
            self._cache2da[iden.resname] = read_2da(resource.data)

    def htClearCache2DA(self):
        self._cache2da = {}

    # endregion

    # region Cache TPC
    def htGetCacheTPC(self, resname: str) -> TPC | None:
        """Gets cached TPC texture or loads and caches it.

        Args:
        ----
            resname: Resource name as string

        Returns:
        -------
            TPC: Loaded TPC texture or None

        Processing Logic:
        ----------------
            - Check if texture is already cached in _cacheTpc dict
            - If not cached, load texture from search locations
            - Cache loaded texture in _cacheTpc dict
            - Return cached texture or None if not found.
        """
        if resname not in self._cacheTpc:
            tex = self.texture(resname, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.TEXTURES_GUI])
            if tex is not None:
                self._cacheTpc[resname] = tex
        return self._cacheTpc.get(resname, None)

    def htBatchCacheTPC(self, names: list[str], *, reload: bool = False):
        """Cache textures for batch queries.

        Args:
        ----
            names: List of texture names to cache
            reload: Reload textures from source if True

        Processing Logic:
        ----------------
            - Check if textures need reloading from source
            - Filter names not already in cache
            - Loop through remaining names and cache textures from sources.
        """
        queries = list(names) if reload else [name for name in names if name not in self._cacheTpc]

        if not queries:
            return

        for resname in queries:
            tex = self.texture(resname, [SearchLocation.TEXTURES_TPA, SearchLocation.TEXTURES_GUI])
            if tex is not None:
                self._cacheTpc[resname] = tex

    def htClearCacheTPC(self):
        self._cacheTpc = {}

    # endregion

    def getItemIconFromUTI(self, uti: UTI) -> QPixmap:
        """Gets the item icon from the UTI.

        Args:
        ----
            uti (UTI): The UTI of the item

        Returns:
        -------
            QPixmap: The icon pixmap for the item

        Processing Logic:
        ----------------
            - Looks up the item class and variation from the UTI in the base items 2DA
            - Constructs the texture resource name from the item class and variation
            - Looks up the texture from the texture cache
            - Returns the icon pixmap if a texture is found, otherwise returns a default icon.
        """
        pixmap = QPixmap(":/images/inventory/unknown.png")
        baseitems = self.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)

        with suppress(Exception):
            itemClass = baseitems.get_cell(uti.base_item, "itemclass")
            variation = uti.model_variation if uti.model_variation != 0 else uti.texture_variation
            textureResname = f'i{itemClass}_{str(variation).rjust(3, "0")}'
            texture = self.htGetCacheTPC(textureResname.lower())

            if texture is not None:
                return self._get_icon(texture)
        return pixmap

    def getItemBaseName(self, baseItem: int) -> str:
        """Get the name of the base item from its ID."""
        baseitems = self.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        with suppress(Exception):
            return baseitems.get_cell(baseItem, "label")
        return "Unknown"

    def getModelVarName(self, modelVariation: int) -> str:
        """Get the name of the model variation from its ID."""
        return "Default" if modelVariation == 0 else f"Variation {modelVariation}"

    def getTextureVarName(self, textureVariation: int) -> str:
        """Get the name of the texture variation from its ID."""
        # Assuming texture variations have specific names or descriptions in another table
        return "Default" if textureVariation == 0 else f"Texture {textureVariation}"

    def getItemIconPath(self, baseItem: int, modelVariation: int, textureVariation: int) -> str:
        """Get the icon path based on base item, model variation, and texture variation."""
        itemClass = self.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS).get_cell(baseItem, "itemclass")
        variation = modelVariation if modelVariation != 0 else textureVariation
        return f"i{itemClass}_{str(variation).rjust(3, '0')}"

    def getItemIcon(
        self,
        baseItem: int,
        modelVariation: int,
        textureVariation: int,
    ) -> QPixmap:
        """Get item icon from base item and variations.

        Args:
        ----
            baseItem: int - Base item id
            modelVariation: int - Model variation
            textureVariation: int - Texture variation

        Returns:
        -------
            QPixmap - Item icon pixmap

        Processing Logic:
        ----------------
            1. Get base item class from cache
            2. Get texture resource name from item class and variation
            3. Get texture from cache using resource name
            4. Return icon pixmap from texture if found, else return default.
        """
        pixmap = QPixmap(":/images/inventory/unknown.png")
        iconPath = self.getItemIconPath(baseItem, modelVariation, textureVariation)

        with suppress(Exception):
            texture = self.htGetCacheTPC(iconPath.lower())
            if texture is not None:
                return self._get_icon(texture)
        return pixmap

    def _get_icon(self, texture: TPC) -> QPixmap:
        width, height, rgba = texture.convert(TPCTextureFormat.RGBA, 0)
        image = QImage(rgba, width, height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
