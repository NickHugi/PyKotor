from __future__ import annotations

import os

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QPoint,
    Qt,
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
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
from toolset.utils.window import add_window

if TYPE_CHECKING:
    from pathlib import Path, PurePath

    from qtpy.QtGui import QStandardItemModel
    from qtpy.QtWidgets import QPlainTextEdit
    from typing_extensions import Literal, Self

    from pykotor.extract.file import LocationResult
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.uti import UTI
    from pykotor.tools.path import CaseAwarePath


T = TypeVar("T")


class HTInstallation(Installation):
    """A specialized Installation class that extends the base Installation class with toolset-related functionality.

    While Installation is intending to load all resources from an installation immediately, HTInstallation
    adds additional caching and loading methods for resources.

    Ideally we want all IO to be non-blocking and asynchronous, and load resources as they are needed in the processpoolexecutor.
    """

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
        self.cache_core_items: QStandardItemModel | None = None

        self._tsl: bool | None = tsl
        self._cache2da: dict[str, TwoDA] = {}
        self._cache_tpc: dict[str, TPC] = {}

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
        if not hasattr(self, cache_attr):
            RobustLogger().warning(f"Cache for '{cache_name}' not found")
            return
        setattr(self, cache_attr, None)
        RobustLogger().debug(f"Cleared cache for '{cache_name}'")

    def clear_all_caches(self):
        """Clear all caches."""
        for attr in dir(self):
            if attr.startswith("_cache_"):
                setattr(self, attr, None)
        RobustLogger().debug("Cleared all caches")

    def _get_cached_or_load(self, cache_name: str, load_method: Callable[[], T]) -> T:
        """Get data from cache or load it if not present."""
        cache_attr = f"_cache_{cache_name}"
        cached_data: Any | None = getattr(self, cache_attr, None)
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
    def _chitin(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument
    def _load_chitin(self) -> list[FileResource]:
        chitin_path: CaseAwarePath = self._path / "chitin.key"
        return list(Chitin(key_path=chitin_path)) if chitin_path.is_file() else []

    @property
    def _female_talktable(self) -> TalkTable: return TalkTable(self._path / "dialogf.tlk")
    @_female_talktable.setter
    def _female_talktable(self, value: TalkTable) -> None: ...  # pylint: disable=unused-argument

    @property
    def _lips(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("lips", lambda: self.load_resources_dict(self.lips_path(), capsule_check=is_mod_file))
    @_lips.setter
    def _lips(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument

    @property
    def _modules(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("modules", lambda: self.load_resources_dict(self.module_path(), capsule_check=is_capsule_file))
    @_modules.setter
    def _modules(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument

    @property
    def _override(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("override", self._load_override)
    @_override.setter
    def _override(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument
    def _load_override(self) -> dict[str, list[FileResource]]:
        override_path = self.override_path()
        result = {}
        for folder in [f for f in override_path.rglob("*") if f.is_dir()] + [override_path]:
            relative_folder: str = folder.relative_to(override_path).as_posix()
            result[relative_folder] = self.load_resources_list(folder, recurse=True)
        return result

    @property
    def _rims(self) -> dict[str, list[FileResource]]: return self.load_resources_dict(self.rims_path(), capsule_check=is_rim_file)
    @_rims.setter
    def _rims(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument

    @property
    def saves(self) -> dict[Path, dict[Path, list[FileResource]]]:
        return self._get_cached_or_load("saves", self._load_saves)
    @saves.setter
    def saves(self, value: dict[Path, dict[Path, list[FileResource]]]) -> None: ...  # pylint: disable=unused-argument
    def _load_saves(self) -> dict[Path, dict[Path, list[FileResource]]]:  # pylint: disable=unused-argument
        if getattr(self, "_saves", None):
            return self._saves
        self._saves = {  # pylint: disable=attribute-defined-outside-init
            save_location: {
                save_path: [
                    FileResource(
                        ResourceIdentifier.from_path(file).resname,
                        ResourceIdentifier.from_path(file).restype,
                        file.stat().st_size,
                        0,
                        file
                    ) for file in save_path.iterdir() if file.is_file()
                ] for save_path in save_location.iterdir() if save_path.is_dir()
            } for save_location in self.save_locations() if save_location.is_dir()
        }
        return self._saves
    @saves.setter
    def saves(self, value: dict[Path, dict[Path, list[FileResource]]]) -> None: ...  # pylint: disable=unused-argument

    @property
    def _streammusic(self) -> list[FileResource]:
        return self._get_cached_or_load("streammusic", lambda: self.load_resources_list(self.streammusic_path()))
    @_streammusic.setter
    def _streammusic(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument
    def _load_streammusic(self) -> list[FileResource]:
        return self.load_resources_list(self.streammusic_path())

    @property
    def _streamsounds(self) -> list[FileResource]:
        return self._get_cached_or_load("streamsounds", lambda: self.load_resources_list(self.streamsounds_path()))
    @_streamsounds.setter
    def _streamsounds(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument
    def _load_streamsounds(self) -> list[FileResource]:
        return self.load_resources_list(self.streamsounds_path())

    @property
    def _streamwaves(self) -> list[FileResource]:
        return self._get_cached_or_load("streamwaves", lambda: self.load_resources_list(self._find_resource_folderpath(("streamvoice", "streamwaves"))))
    @_streamwaves.setter
    def _streamwaves(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument
    def _load_streamwaves(self) -> list[FileResource]:
        return self.load_resources_list(self._find_resource_folderpath(("streamvoice", "streamwaves")))

    @property
    def _talktable(self) -> TalkTable:
        return self._get_cached_or_load("talktable", self._load_talktable)
    @_talktable.setter
    def _talktable(self, value: TalkTable) -> None: ...  # pylint: disable=unused-argument
    def _load_talktable(self) -> TalkTable:
        return TalkTable(self._path / "dialog.tlk")

    @property
    def _texturepacks(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("texturepacks", self._load_texturepacks)
    @_texturepacks.setter
    def _texturepacks(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument
    def _load_texturepacks(self) -> dict[str, list[FileResource]]:
        return self.load_resources_dict(self.texturepacks_path(), capsule_check=is_erf_file)

    @classmethod
    def from_base_instance(cls, installation: Installation) -> Self:
        """Create a new HTInstallation instance from an existing Installation instance."""
        ht_installation = cast(cls, installation)

        ht_installation.name = f"NonHTInit_{installation.__class__.__name__}_{id(installation)}"
        ht_installation._tsl = installation.game().is_k2()  # noqa: SLF001  # pylint: disable=protected-access
        ht_installation.cache_core_items = None
        ht_installation._cache2da = {}  # noqa: SLF001  # pylint: disable=protected-access
        ht_installation._cache_tpc = {}  # noqa: SLF001  # pylint: disable=protected-access

        ht_installation.__class__ = cls
        return ht_installation

    def setup_file_context_menu(
        self,
        widget: QPlainTextEdit | QLineEdit | QComboBox,
        resref_type: list[ResourceType] | list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
    ):
        """Set up a file context menu for the given widget.

        This function sets up a context menu for a given widget (QPlainTextEdit, QLineEdit, or QComboBox)
        to allow for quick access to file locations related to the widget's text.

        Args:
            widget (QPlainTextEdit | QLineEdit | QComboBox): The widget to create a context menu for.
            resref_type (list[ResourceType] | list[ResourceIdentifier]): The type of resource to search for.
            order (list[SearchLocation] | None): The order in which to search for resources.
              Defaults to [SearchLocation.CHITIN, SearchLocation.OVERRIDE, SearchLocation.MODULES, SearchLocation.RIMS].
        """
        from toolset.gui.dialogs.load_from_location_result import ResourceItems

        @Slot(QPoint)
        def extend_context_menu(pos: QPoint):
            root_menu = QMenu(widget) if isinstance(widget, QComboBox) else widget.createStandardContextMenu()
            widget_text = (
                widget.currentText().strip()
                if isinstance(widget, QComboBox)
                else (
                    widget.text()
                    if isinstance(widget, QLineEdit)
                    else widget.toPlainText()
                ).strip()
            )

            if widget_text:
                build_file_context_menu(root_menu, widget_text)

            root_menu.exec_(widget.mapToGlobal(pos))

        def build_file_context_menu(root_menu: QMenu, widgetText: str):
            """Build and populate a file context menu for the given widget text.

            This function creates a "File..." submenu in the root menu, populates it with
            file locations based on the widget text, and adds a "Details..." action.

            Args:
                rootMenu (QMenu): The parent menu to which the file submenu will be added.
                pos (QPoint): The position where the menu should be displayed.
                widgetText (str): The text from the widget used to search for file locations.
            """
            file_menu = QMenu("File...", widget)
            root_menu.addMenu(file_menu)
            root_menu.addSeparator()

            search_order = order or [SearchLocation.CHITIN, SearchLocation.OVERRIDE, SearchLocation.MODULES, SearchLocation.RIMS]
            resource_types = resref_type if isinstance(resref_type[0], ResourceType) else resref_type
            # FIXME(th3w1zard1): Seems the type hinter override's for `locations` are wrong, need to fix
            locations: dict[str, list[LocationResult]] = self.locations(
                ([widgetText], resource_types),  # pyright: ignore[reportArgumentType, reportAssignmentType]
                search_order
            )
            flat_locations: list[LocationResult] = (
                [
                    item
                    for sublist in locations.values()
                    for item in sublist
                ]
                if isinstance(locations, dict)
                else locations
            )

            if flat_locations:
                for location in flat_locations:
                    display_path = location.filepath.relative_to(self.path())
                    if location.as_file_resource().inside_bif:
                        display_path /= location.as_file_resource().filename()
                    location_menu = file_menu.addMenu(str(display_path))
                    ResourceItems(resources=[location]).build_menu(location_menu, self)

                details_action = QAction("Details...", file_menu)
                details_action.triggered.connect(lambda: self._open_details(flat_locations))
                file_menu.addAction(details_action)
            else:
                file_menu.setDisabled(True)

            for action in root_menu.actions():
                if action.text() == "File...":
                    action.setText(f"{len(flat_locations)} file(s) located")
                    break

        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(extend_context_menu)

    @Slot(list)
    def _open_details(self, locations: list[LocationResult]):
        from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
        selection_window = FileSelectionWindow(locations, self)
        add_window(selection_window)  # ez way to get qt to call AddRef
        selection_window.activateWindow()

    @Slot(list)
    def handle_file_system_changes(self, changed_files: list[str]):
        """Handle file system changes and update caches accordingly.

        This function handles changes in the file system by clearing specific caches
        based on the changed files. It ensures that the caches are updated correctly
        when files are modified, added, or removed.

        Args:
            changed_files (list[str]): A list of file paths that have changed.
        """
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
    def ht_get_cache_2da(self, resname: str) -> TwoDA | None:
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

    def get_relevant_resources(self, restype: ResourceType, src_filepath: PurePath | None = None) -> set[FileResource]:
        """Get relevant resources for a given resource type and source filepath.

        This function retrieves relevant resources based on the specified resource type
        and an optional source file path. It uses the installation's resources and caches
        to determine which resources are relevant.

        Args:
        ----
            restype (ResourceType): The type of resource to retrieve.
            src_filepath (PurePath | None): The source file path to use for determining relevant resources.

        Returns:
        -------
            set[FileResource]: A set of relevant resources.

        Processing Logic:
        ----------------
            - If no source file path is provided, return all resources of the specified type.
            - If a source file path is provided, check if it is inside the module or override folder.
            - If inside module, add all resources of the specified type from the module.
            - If inside override, add all resources of the specified type from the override.
            - Return the set of relevant resources.
        """
        from pykotor.common.module import Module

        if src_filepath is None:
            return {res for res in self if res.restype() is restype}

        relevant_resources: set[FileResource] = {
            res
            for res in (*self.override_resources(), *self.chitin_resources())
            if res.restype() is restype
        }

        if os.path.commonpath([src_filepath, self.module_path()]) == self.module_path():
            relevant_resources.update(
                res
                for cap in Module.find_capsules(self, src_filepath.name, strict=True)
                for res in cap
                if res.restype() is restype
            )
        elif os.path.commonpath([src_filepath, self.override_path()]) == self.override_path():
            relevant_resources.update(
                res
                for reslist in self._modules.values()
                if any(r.identifier() == src_filepath.name for r in reslist)
                for res in reslist
                if res.restype() is restype
            )  # noqa: E501

        return relevant_resources

    def ht_batch_cache_2da(self, resnames: list[str], *, reload: bool = False):
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
            queries = [
                ResourceIdentifier(resname, ResourceType.TwoDA)
                for resname in resnames
                if resname not in self._cache2da
            ]

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
    def ht_get_cache_tpc(self, resname: str) -> TPC | None:
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
        if resname not in self._cache_tpc:
            tex = self.texture(
                resname,
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.TEXTURES_GUI,
                ],
            )
            if tex is not None:
                self._cache_tpc[resname] = tex
        return self._cache_tpc.get(resname, None)

    def ht_batch_cache_tpc(self, names: list[str], *, reload: bool = False):
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
        queries: list[str] = (
            list(names)
            if reload
            else [name for name in names if name not in self._cache_tpc]
        )

        if not queries:
            return

        for resname in queries:
            tex: TPC | None = self.texture(
                resname,
                [
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.TEXTURES_GUI,
                ],
            )
            if tex is not None:
                self._cache_tpc[resname] = tex

    def ht_clear_cache_tpc(self):
        self._cache_tpc = {}

    # endregion

    def get_item_icon_from_uti(self, uti: UTI) -> QPixmap:
        """Gets the item icon from the UTI.

        Args:
        ----
            uti (UTI): The UTI of the item

        Returns:
        -------
            QPixmap: The icon pixmap for the item
        """
        pixmap = QPixmap(":/images/inventory/unknown.png")
        baseitems: TwoDA | None = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().error("Failed to retrieve BASEITEMS 2DA.")
            return pixmap

        with suppress(Exception):
            item_class = baseitems.get_cell(uti.base_item, "itemclass")
            variation = uti.model_variation if uti.model_variation != 0 else uti.texture_variation
            texture_resname = f'i{item_class}_{str(variation).rjust(3, "0")}'
            texture = self.ht_get_cache_tpc(texture_resname.lower())

            if texture is not None:
                return self._get_icon(texture)
        return pixmap

    def get_item_base_name(self, base_item: int) -> str:
        """Get the name of the base item from its ID."""
        try:
            baseitems = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
            if baseitems is None:
                RobustLogger().error("Failed to retrieve `baseitems.2da` from your installation.")
                return "Unknown"
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("An exception occurred while retrieving `baseitems.2da` from your installation.")
            return "Unknown"
        else:
            return baseitems.get_cell(base_item, "label")

    def get_model_var_name(self, model_variation: int) -> str:
        """Get the name of the model variation from its ID."""
        return "Default" if model_variation == 0 else f"Variation {model_variation}"

    def get_texture_var_name(self, texture_variation: int) -> str:
        """Get the name of the texture variation from its ID."""
        return "Default" if texture_variation == 0 else f"Texture {texture_variation}"

    def get_item_icon_path(self, base_item: int, model_variation: int, texture_variation: int) -> str:
        """Get the icon path based on base item, model variation, and texture variation."""
        baseitems = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().error("Failed to retrieve `baseitems.2da` from your installation.")
            return "Unknown"
        try:
            itemClass = baseitems.get_cell(base_item, "itemclass")
            print(f"Item class: '{itemClass}'")
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception(f"An exception occurred while getting cell '{base_item}' from `baseitems.2da`.")
            return "Unknown"
        else:
            variation = model_variation if model_variation != 0 else texture_variation
            return f"i{itemClass}_{str(variation).rjust(3, '0')}"

    def getItemIcon(
        self,
        base_item: int,
        model_variation: int,
        texture_variation: int,
    ) -> QPixmap:
        """Get item icon from base item and variations.

        Args:
        ----
            base_item: int - Base item id
            model_variation: int - Model variation
            texture_variation: int - Texture variation

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
        icon_path = self.get_item_icon_path(base_item, model_variation, texture_variation)
        print(f"Icon path: '{icon_path}'")
        with suppress(Exception):
            texture = self.ht_get_cache_tpc(icon_path.lower())
            if texture is not None:
                return self._get_icon(texture)
        return pixmap

    def _get_icon(self, texture: TPC) -> QPixmap:
        """Convert TPC texture to QPixmap.

        Args:
        ----
            texture (TPC): The TPC texture to convert.

        Returns:
        -------
            QPixmap: The converted QPixmap.

        Processing Logic:
        ----------------
            1. Convert TPC texture to RGBA format
            2. Create QImage from RGBA data
            3. Return QPixmap transformed to show image correctly.
        """
        width, height, rgba = texture.convert(TPCTextureFormat.RGBA, 0)
        image = QImage(rgba, width, height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))

    @property
    def tsl(self) -> bool:
        if self._tsl is None:
            self._tsl = self.game().is_k2()
        return self._tsl
