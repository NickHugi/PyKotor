from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, cast

from loggerplus import RobustLogger
from qtpy.QtCore import Qt
from qtpy.QtGui import QImage, QPixmap, QTransform
from qtpy.QtWidgets import QAction, QComboBox, QLineEdit, QMenu

from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from toolset.utils.window import addWindow

if TYPE_CHECKING:

    import os

    from qtpy.QtGui import QPoint, QStandardItemModel
    from qtpy.QtWidgets import QPlainTextEdit
    from typing_extensions import Literal, Self

    from pykotor.extract.file import LocationResult
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.uti import UTI
    from pykotor.tools.path import CaseAwarePath
    from utility.system.path import Path, PurePath


class HTInstallation(Installation):
    TwoDA_PORTRAITS: str = "portraits"
    TwoDA_APPEARANCES: str = "appearance"
    TwoDA_SUBRACES: str = "subrace"
    TwoDA_SPEEDS: str = "creaturespeed"
    TwoDA_SOUNDSETS: str = "soundset"
    TwoDA_FACTIONS: str = "repute"
    TwoDA_GENDERS: str = "gender"
    TwoDA_PERCEPTIONS: str = "ranges"
    TwoDA_CLASSES: str = "classes"
    TwoDA_FEATS: str = "feat"
    TwoDA_POWERS: str = "spells"
    TwoDA_BASEITEMS: str = "baseitems"
    TwoDA_PLACEABLES: str = "placeables"
    TwoDA_DOORS: str = "genericdoors"
    TwoDA_CURSORS: str = "cursors"
    TwoDA_TRAPS: str = "traps"
    TwoDA_RACES: str = "racialtypes"
    TwoDA_SKILLS: str = "skills"
    TwoDA_UPGRADES: str = "upgrade"
    TwoDA_ENC_DIFFICULTIES: str = "encdifficulty"
    TwoDA_ITEM_PROPERTIES: str = "itempropdef"
    TwoDA_IPRP_PARAMTABLE: str = "iprp_paramtable"
    TwoDA_IPRP_COSTTABLE: str = "iprp_costtable"
    TwoDA_IPRP_ABILITIES: str = "iprp_abilities"
    TwoDA_IPRP_ALIGNGRP: str = "iprp_aligngrp"
    TwoDA_IPRP_COMBATDAM: str = "iprp_combatdam"
    TwoDA_IPRP_DAMAGETYPE: str = "iprp_damagetype"
    TwoDA_IPRP_PROTECTION: str = "iprp_protection"
    TwoDA_IPRP_ACMODTYPE: str = "iprp_acmodtype"
    TwoDA_IPRP_IMMUNITY: str = "iprp_immunity"
    TwoDA_IPRP_SAVEELEMENT: str = "iprp_saveelement"
    TwoDA_IPRP_SAVINGTHROW: str = "iprp_savingthrow"
    TwoDA_IPRP_ONHIT: str = "iprp_onhit"
    TwoDA_IPRP_AMMOTYPE: str = "iprp_ammotype"
    TwoDA_IPRP_MONSTERHIT: str = "iprp_mosterhit"
    TwoDA_IPRP_WALK: str = "iprp_walk"
    TwoDA_EMOTIONS: str = "emotion"
    TwoDA_EXPRESSIONS: str = "facialanim"
    TwoDA_VIDEO_EFFECTS: str = "videoeffects"
    TwoDA_DIALOG_ANIMS: str = "dialoganimations"
    TwoDA_PLANETS: str = "planetary"
    TwoDA_PLOT: str = "plot"
    TwoDA_CAMERAS: str = "camerastyle"

    def __init__(
        self,
        path: str | os.PathLike,
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

        # New cache dictionaries
        self._cache_chitin: list[FileResource] | None = None
        self._cache_lips: dict[str, list[FileResource]] | None = None
        self._cache_modules: dict[str, list[FileResource]] | None = None
        self._cache_override: dict[str, list[FileResource]] | None = None
        self._cache_rims: dict[str, list[FileResource]] | None = None
        self._cache_saves: dict[Path, dict[Path, list[FileResource]]] | None = None
        self._cache_streammusic: list[FileResource] | None = None
        self._cache_streamsounds: list[FileResource] | None = None
        self._cache_streamwaves: list[FileResource] | None = None
        self._cache_texturepacks: dict[str, list[FileResource]] | None = None

    def _clear_cache(self, cache_name: str):
        """Clear a specific cache and print a debug message."""
        cache_attr = f"_cache_{cache_name}"
        if hasattr(self, cache_attr):
            setattr(self, cache_attr, None)
            RobustLogger().debug(f"Cleared cache for {cache_name}")

    def clear_all_caches(self):
        """Clear all caches."""
        for attr in dir(self):
            if attr.startswith("_cache_"):
                setattr(self, attr, None)
        RobustLogger().debug("Cleared all caches")

    def _get_cached_or_load(self, cache_name: str, load_method: Callable[[], Any]) -> Any:
        """Get data from cache or load it if not present."""
        cache_attr = f"_cache_{cache_name}"
        cached_data = getattr(self, cache_attr, None)
        if cached_data is None:
            cached_data = load_method()
            setattr(self, cache_attr, cached_data)
        return cached_data

    def reload_all(self): ...
    def load_chitin(self): ...
    def load_lips(self): ...
    def load_modules(self): ...
    def load_streammusic(self): ...
    def load_streamsounds(self): ...
    def load_textures(self): ...
    def load_saves(self): ...
    def load_streamwaves(self): ...
    def load_streamvoice(self): ...
    def load_override(self, directory: str | None = None): ...

    @property
    def _chitin(self) -> list[FileResource]:
        return self._get_cached_or_load("chitin", self._load_chitin)
    @_chitin.setter
    def _chitin(self, value: list[FileResource]) -> None: ...
    def _load_chitin(self) -> list[FileResource]:
        chitin_path: CaseAwarePath = self._path / "chitin.key"
        return list(Chitin(key_path=chitin_path)) if chitin_path.safe_isfile() else []

    @property
    def _female_talktable(self) -> TalkTable: return TalkTable(self._path / "dialogf.tlk")
    @_female_talktable.setter
    def _female_talktable(self, value: TalkTable) -> None: ...

    @property
    def _lips(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("lips", lambda: self.load_resources_dict(self.lips_path(), capsule_check=is_mod_file))
    @_lips.setter
    def _lips(self, value: dict[str, list[FileResource]]) -> None: ...

    @property
    def _modules(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("modules", lambda: self.load_resources_dict(self.module_path(), capsule_check=is_capsule_file))
    @_modules.setter
    def _modules(self, value: dict[str, list[FileResource]]) -> None: ...

    @property
    def _override(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("override", self._load_override)
    @_override.setter
    def _override(self, value: dict[str, list[FileResource]]) -> None: ...
    def _load_override(self) -> dict[str, list[FileResource]]:
        override_path = self.override_path()
        result = {}
        for folder in [f for f in override_path.safe_rglob("*") if f.safe_isdir()] + [override_path]:
            relative_folder: str = folder.relative_to(override_path).as_posix()
            result[relative_folder] = self.load_resources_list(folder, recurse=True)
        return result

    @property
    def _rims(self) -> dict[str, list[FileResource]]: return self.load_resources_dict(self.rims_path(), capsule_check=is_rim_file)
    @_rims.setter
    def _rims(self, value: dict[str, list[FileResource]]) -> None: ...

    @property
    def saves(self) -> dict[Path, dict[Path, list[FileResource]]]:
        return self._get_cached_or_load("saves", self._load_saves)
    @saves.setter
    def saves(self, value: dict[Path, dict[Path, list[FileResource]]]) -> None: ...
    def _load_saves(self) -> dict[Path, dict[Path, list[FileResource]]]:
        if hasattr(self, "_saves") and self._saves:
            return self._saves
        self._saves = {
            save_location: {
                save_path: [
                    FileResource(
                        ResourceIdentifier.from_path(file).resname,
                        ResourceIdentifier.from_path(file).restype,
                        file.stat().st_size,
                        0,
                        file
                    ) for file in save_path.iterdir() if file.safe_isfile()
                ] for save_path in save_location.iterdir() if save_path.safe_isdir()
            } for save_location in self.save_locations() if save_location.safe_isdir()
        }
        return self._saves
    @saves.setter
    def saves(self, value: dict[Path, dict[Path, list[FileResource]]]) -> None: ...

    @property
    def _streammusic(self) -> list[FileResource]:
        return self._get_cached_or_load("streammusic", lambda: self.load_resources_list(self.streammusic_path()))
    @_streammusic.setter
    def _streammusic(self, value: list[FileResource]) -> None: ...
    def _load_streammusic(self) -> list[FileResource]:
        return self.load_resources_list(self.streammusic_path())

    @property
    def _streamsounds(self) -> list[FileResource]:
        return self._get_cached_or_load("streamsounds", lambda: self.load_resources_list(self.streamsounds_path()))
    @_streamsounds.setter
    def _streamsounds(self, value: list[FileResource]) -> None: ...
    def _load_streamsounds(self) -> list[FileResource]:
        return self.load_resources_list(self.streamsounds_path())

    @property
    def _streamwaves(self) -> list[FileResource]:
        return self._get_cached_or_load("streamwaves", lambda: self.load_resources_list(self._find_resource_folderpath(("streamvoice", "streamwaves"))))
    @_streamwaves.setter
    def _streamwaves(self, value: list[FileResource]) -> None: ...
    def _load_streamwaves(self) -> list[FileResource]:
        return self.load_resources_list(self._find_resource_folderpath(("streamvoice", "streamwaves")))

    @property
    def _talktable(self) -> TalkTable:
        return self._get_cached_or_load("talktable", self._load_talktable)
    @_talktable.setter
    def _talktable(self, value: TalkTable) -> None: ...
    def _load_talktable(self) -> TalkTable:
        return TalkTable(self._path / "dialog.tlk")

    @property
    def _texturepacks(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("texturepacks", self._load_texturepacks)
    @_texturepacks.setter
    def _texturepacks(self, value: dict[str, list[FileResource]]) -> None: ...
    def _load_texturepacks(self) -> dict[str, list[FileResource]]:
        return self.load_resources_dict(self.texturepacks_path(), capsule_check=is_erf_file)

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

        def extendContextMenu(pos: QPoint):
            rootMenu = QMenu(widget) if isinstance(widget, QComboBox) else widget.createStandardContextMenu()
            widgetText = widget.currentText().strip() if isinstance(widget, QComboBox) else (widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()).strip()

            if widgetText:
                build_file_context_menu(rootMenu, widgetText)

            rootMenu.exec_(widget.mapToGlobal(pos))

        def build_file_context_menu(rootMenu: QMenu, widgetText: str):
            """Build and populate a file context menu for the given widget text.

            This function creates a "File..." submenu in the root menu, populates it with
            file locations based on the widget text, and adds a "Details..." action.

            Args:
                rootMenu (QMenu): The parent menu to which the file submenu will be added.
                pos (QPoint): The position where the menu should be displayed.
                widgetText (str): The text from the widget used to search for file locations.
            """
            fileMenu = QMenu("File...", widget)
            rootMenu.addMenu(fileMenu)
            rootMenu.addSeparator(rootMenu.actions()[0])

            search_order = order or [SearchLocation.CHITIN, SearchLocation.OVERRIDE, SearchLocation.MODULES, SearchLocation.RIMS]
            resource_types = resref_type if isinstance(resref_type[0], ResourceType) else resref_type
            # FIXME(th3w1zard1): Seems the override's for `locations` are wrong, need to fix
            locations: dict[str, list[LocationResult]] = self.locations(([widgetText], resource_types), search_order)  # pyright: ignore[reportArgumentType, reportAssignmentType]
            flatLocations = [item for sublist in locations.values() for item in sublist] if isinstance(locations, dict) else locations

            if flatLocations:
                for location in flatLocations:
                    displayPath = location.filepath.relative_to(self.path())
                    if location.as_file_resource().inside_bif:
                        displayPath /= location.as_file_resource().filename()
                    locationMenu = fileMenu.addMenu(str(displayPath))
                    ResourceItems(resources=[location]).build_menu(locationMenu, self)

                detailsAction = QAction("Details...", fileMenu)
                detailsAction.triggered.connect(lambda: self._openDetails(flatLocations))
                fileMenu.addAction(detailsAction)
            else:
                fileMenu.setDisabled(True)

            for action in rootMenu.actions():
                if action.text() == "File...":
                    action.setText(f"{len(flatLocations)} file(s) located")
                    break

        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(extendContextMenu)

    def _openDetails(self, locations: list[LocationResult]):
        from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
        selectionWindow = FileSelectionWindow(locations, self)
        addWindow(selectionWindow)  # ez way to get qt to call AddRef
        selectionWindow.activateWindow()

    def handle_file_system_changes(self, changed_files: list[str]):
        """Handle file system changes and update caches accordingly."""
        lower_install_path = str(self._path).lower()
        lower_lips_path = str(self.lips_path()).lower()
        lower_module_path = str(self.module_path()).lower()
        lower_override_path = str(self.override_path()).lower()
        lower_rims_path = str(self.rims_path()).lower()
        lower_streammusic_path = str(self.streammusic_path()).lower()
        lower_streamsounds_path = str(self.streamsounds_path()).lower()
        lower_streamwaves_path = str(self._find_resource_folderpath(("streamvoice", "streamwaves"))).lower()
        lower_texturepacks_path = str(self.texturepacks_path()).lower()
        lower_save_locations = [str(save_loc).lower() for save_loc in self.save_locations()]

        for path in changed_files:
            lower_path = path.lower()
            if lower_path == lower_install_path:
                self._clear_cache("chitin")
            elif lower_lips_path in lower_path:
                self._clear_cache("lips")
            elif lower_module_path in lower_path:
                self._clear_cache("modules")
            elif lower_override_path in lower_path:
                self._clear_cache("override")
            elif lower_rims_path in lower_path:
                self._clear_cache("rims")
            elif any(save_loc in lower_path for save_loc in lower_save_locations):
                self._clear_cache("saves")
            elif lower_streammusic_path in lower_path:
                self._clear_cache("streammusic")
            elif lower_streamsounds_path in lower_path:
                self._clear_cache("streamsounds")
            elif lower_streamwaves_path in lower_path:
                self._clear_cache("streamwaves")
            elif lower_texturepacks_path in lower_path:
                self._clear_cache("texturepacks")
            else:
                print(f"Unhandled file change: {path}")


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

    def getRelevantResources(self, restype: ResourceType, src_filepath: PurePath | None = None) -> set[FileResource]:
        """Get relevant resources for a given resource type and source filepath."""
        from pykotor.common.module import Module

        if src_filepath is None:
            return {res for res in self if res.restype() is restype}

        relevant_resources = {res for res in self.override_resources() + self.chitin_resources() if res.restype() is restype}

        if src_filepath.is_relative_to(self.module_path()):
            relevant_resources.update(res for cap in Module.find_capsules(self, src_filepath.name, strict=True) for res in cap if res.restype() is restype)
        elif src_filepath.is_relative_to(self.override_path()):
            relevant_resources.update(res for reslist in self._modules.values() if any(r.identifier() == src_filepath.name for r in reslist) for res in reslist if res.restype() is restype)  # noqa: E501

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
        """
        pixmap = QPixmap(":/images/inventory/unknown.png")
        baseitems: TwoDA | None = self.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().error("Failed to retrieve BASEITEMS 2DA.")
            return pixmap

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
        try:
            baseitems = self.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
            if baseitems is None:
                RobustLogger().error("Failed to retrieve BASEITEMS 2DA.")
                return "Unknown"
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to retrieve BASEITEMS 2DA.")
            return "Unknown"
        else:
            return baseitems.get_cell(baseItem, "label")

    def getModelVarName(self, modelVariation: int) -> str:
        """Get the name of the model variation from its ID."""
        return "Default" if modelVariation == 0 else f"Variation {modelVariation}"

    def getTextureVarName(self, textureVariation: int) -> str:
        """Get the name of the texture variation from its ID."""
        # Assuming texture variations have specific names or descriptions in another table
        return "Default" if textureVariation == 0 else f"Texture {textureVariation}"

    def getItemIconPath(self, baseItem: int, modelVariation: int, textureVariation: int) -> str:
        """Get the icon path based on base item, model variation, and texture variation."""
        baseitems = self.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().error("Failed to retrieve BASEITEMS 2DA.")
            return "Unknown"
        try:
            itemClass = baseitems.get_cell(baseItem, "itemclass")
            print(f"Item class: '{itemClass}'")
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Failed to get cell '{baseItem}' from BASEITEMS 2DA.")
            return "Unknown"
        else:
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
        print(f"Icon path: '{iconPath}'")
        with suppress(Exception):
            texture = self.htGetCacheTPC(iconPath.lower())
            if texture is not None:
                return self._get_icon(texture)
        return pixmap

    def _get_icon(self, texture: TPC) -> QPixmap:
        width, height, rgba = texture.convert(TPCTextureFormat.RGBA, 0)
        image = QImage(rgba, width, height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))

    @property
    def tsl(self) -> bool:
        if self._tsl is None:
            self._tsl = self.game().is_k2()
        return self._tsl
