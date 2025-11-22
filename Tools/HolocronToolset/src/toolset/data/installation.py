from __future__ import annotations

import os

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QPoint,
    Qt,
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QImage, QPixmap, QTransform
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QComboBox,
    QLineEdit,
    QMenu,
)

from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.extract.savedata import SaveFolderEntry
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.extract.twoda import TwoDARegistry
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from toolset.utils.window import add_window

if TYPE_CHECKING:
    from pathlib import Path

    import os


    from qtpy.QtGui import QStandardItemModel
    from qtpy.QtWidgets import QPlainTextEdit
    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.formats.tpc.tpc_data import TPCMipmap
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.uti import UTI


class HTInstallation(Installation):
    TwoDA_PORTRAITS: str = TwoDARegistry.PORTRAITS
    TwoDA_APPEARANCES: str = TwoDARegistry.APPEARANCES
    TwoDA_SUBRACES: str = TwoDARegistry.SUBRACES
    TwoDA_SPEEDS: str = TwoDARegistry.SPEEDS
    TwoDA_SOUNDSETS: str = TwoDARegistry.SOUNDSETS
    TwoDA_FACTIONS: str = TwoDARegistry.FACTIONS
    TwoDA_GENDERS: str = TwoDARegistry.GENDERS
    TwoDA_PERCEPTIONS: str = TwoDARegistry.PERCEPTIONS
    TwoDA_CLASSES: str = TwoDARegistry.CLASSES
    TwoDA_FEATS: str = TwoDARegistry.FEATS
    TwoDA_POWERS: str = TwoDARegistry.POWERS
    TwoDA_BASEITEMS: str = TwoDARegistry.BASEITEMS
    TwoDA_PLACEABLES: str = TwoDARegistry.PLACEABLES
    TwoDA_DOORS: str = TwoDARegistry.DOORS
    TwoDA_CURSORS: str = TwoDARegistry.CURSORS
    TwoDA_TRAPS: str = TwoDARegistry.TRAPS
    TwoDA_RACES: str = TwoDARegistry.RACES
    TwoDA_SKILLS: str = TwoDARegistry.SKILLS
    TwoDA_UPGRADES: str = TwoDARegistry.UPGRADES
    TwoDA_ENC_DIFFICULTIES: str = TwoDARegistry.ENC_DIFFICULTIES
    TwoDA_ITEM_PROPERTIES: str = TwoDARegistry.ITEM_PROPERTIES
    TwoDA_IPRP_PARAMTABLE: str = TwoDARegistry.IPRP_PARAMTABLE
    TwoDA_IPRP_COSTTABLE: str = TwoDARegistry.IPRP_COSTTABLE
    TwoDA_IPRP_ABILITIES: str = TwoDARegistry.IPRP_ABILITIES
    TwoDA_IPRP_ALIGNGRP: str = TwoDARegistry.IPRP_ALIGNGRP
    TwoDA_IPRP_COMBATDAM: str = TwoDARegistry.IPRP_COMBATDAM
    TwoDA_IPRP_DAMAGETYPE: str = TwoDARegistry.IPRP_DAMAGETYPE
    TwoDA_IPRP_PROTECTION: str = TwoDARegistry.IPRP_PROTECTION
    TwoDA_IPRP_ACMODTYPE: str = TwoDARegistry.IPRP_ACMODTYPE
    TwoDA_IPRP_IMMUNITY: str = TwoDARegistry.IPRP_IMMUNITY
    TwoDA_IPRP_SAVEELEMENT: str = TwoDARegistry.IPRP_SAVEELEMENT
    TwoDA_IPRP_SAVINGTHROW: str = TwoDARegistry.IPRP_SAVINGTHROW
    TwoDA_IPRP_ONHIT: str = TwoDARegistry.IPRP_ONHIT
    TwoDA_IPRP_AMMOTYPE: str = TwoDARegistry.IPRP_AMMOTYPE
    TwoDA_IPRP_MONSTERHIT: str = TwoDARegistry.IPRP_MONSTERHIT
    TwoDA_IPRP_WALK: str = TwoDARegistry.IPRP_WALK
    TwoDA_EMOTIONS: str = TwoDARegistry.EMOTIONS
    TwoDA_EXPRESSIONS: str = TwoDARegistry.EXPRESSIONS
    TwoDA_VIDEO_EFFECTS: str = TwoDARegistry.VIDEO_EFFECTS
    TwoDA_DIALOG_ANIMS: str = TwoDARegistry.DIALOG_ANIMS
    TwoDA_PLANETS: str = TwoDARegistry.PLANETS
    TwoDA_PLOT: str = TwoDARegistry.PLOT
    TwoDA_CAMERAS: str = TwoDARegistry.CAMERAS

    def __init__(
        self,
        path: str | os.PathLike,
        name: str,
        *,
        tsl: bool | None = None,
        progress_callback: Callable[[int | str, Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"]], Any] | None = None,
    ):
        super().__init__(path, progress_callback=progress_callback)

        self.name: str = name
        self.cache_core_items: QStandardItemModel | None = None

        self._tsl: bool | None = tsl
        self._cache2da: dict[str, TwoDA] = {}
        self._cache_tpc: dict[str, TPC] = {}

        # New cache dictionaries
        self._cache_chitin: list[FileResource] = []
        self._cache_lips: dict[str, list[FileResource]] = {}
        self._cache_modules: dict[str, list[FileResource]] = {}
        self._cache_override: dict[str, list[FileResource]] = {}
        self._cache_rims: dict[str, list[FileResource]] = {}
        self._cache_saves: dict[Path, dict[Path, list[FileResource]]] = {}
        self._cache_streammusic: list[FileResource] = []
        self._cache_streamsounds: list[FileResource] = []
        self._cache_streamwaves: list[FileResource] = []
        self._cache_texturepacks: dict[str, list[FileResource]] = {}

    def _clear_cache(
        self,
        cache_name: Literal[
            "core_items",
            "chitin",
            "lips",
            "modules",
            "override",
            "rims",
            "saves",
            "streammusic",
            "streamsounds",
            "streamwaves",
            "texturepacks",
        ],
    ):
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
        if not cached_data:
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
    def _chitin(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_chitin(self) -> list[FileResource]:
        chitin_path: Path = self._path / "chitin.key"
        return list(Chitin(key_path=chitin_path)) if chitin_path.is_file() else []

    @property
    def _female_talktable(self) -> TalkTable:
        return TalkTable(self._path / "dialogf.tlk")

    @_female_talktable.setter
    def _female_talktable(self, value: TalkTable) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]

    @property
    def _lips(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load(
            "lips",
            lambda: self.load_resources_dict(self.lips_path(), capsule_check=is_mod_file),
        )

    @_lips.setter
    def _lips(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]

    @property
    def _modules(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load(
            "modules",
            lambda: self.load_resources_dict(self.module_path(), capsule_check=is_capsule_file),
        )

    @_modules.setter
    def _modules(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]

    @property
    def _override(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("override", self._load_override)

    @_override.setter
    def _override(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_override(self) -> dict[str, list[FileResource]]:
        override_path: Path = self.override_path()
        result: dict[str, list[FileResource]] = {}
        for folder in [f for f in override_path.rglob("*") if f.is_dir()] + [override_path]:
            relative_folder: str = folder.relative_to(override_path).as_posix()
            result[relative_folder] = self.load_resources_list(folder, recurse=True)
        return result

    @property
    def _rims(self) -> dict[str, list[FileResource]]:
        return self.load_resources_dict(self.rims_path(), capsule_check=is_rim_file)

    @_rims.setter
    def _rims(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]

    @property
    def saves(self) -> dict[Path, dict[Path, list[FileResource]]]:
        return self._get_cached_or_load("saves", self._load_saves)

    @saves.setter
    def saves(self, value: dict[Path, dict[Path, list[FileResource]]]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_saves(self) -> dict[Path, dict[Path, list[FileResource]]]:  # pylint: disable=unused-argument
        if getattr(self, "_saves", None):
            return self._saves
        self._saves = {  # pylint: disable=attribute-defined-outside-init
            save_location: {
                save_path: [FileResource(ResourceIdentifier.from_path(file).resname, ResourceIdentifier.from_path(file).restype, file.stat().st_size, 0, file) for file in save_path.iterdir() if file.is_file()] for save_path in save_location.iterdir() if save_path.is_dir()
            }
            for save_location in self.save_locations()
            if save_location.is_dir()
        }
        return self._saves

    @saves.setter
    def saves(self, value: dict[Path, dict[Path, list[FileResource]]]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]

    @property
    def _streammusic(self) -> list[FileResource]:
        return self._get_cached_or_load("streammusic", lambda: self.load_resources_list(self.streammusic_path()))

    @_streammusic.setter
    def _streammusic(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_streammusic(self) -> list[FileResource]:
        return self.load_resources_list(self.streammusic_path())

    @property
    def _streamsounds(self) -> list[FileResource]:
        return self._get_cached_or_load("streamsounds", lambda: self.load_resources_list(self.streamsounds_path()))

    @_streamsounds.setter
    def _streamsounds(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_streamsounds(self) -> list[FileResource]:
        return self.load_resources_list(self.streamsounds_path())

    @property
    def _streamwaves(self) -> list[FileResource]:
        return self._get_cached_or_load("streamwaves", lambda: self.load_resources_list(self._find_resource_folderpath(("streamwaves", "streamvoice")), recurse=True))

    @_streamwaves.setter
    def _streamwaves(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_streamwaves(self) -> list[FileResource]:
        return self.load_resources_list(self._find_resource_folderpath(("streamwaves", "streamvoice")), recurse=True)

    @property
    def _streamvoice(self) -> list[FileResource]:
        return self._get_cached_or_load("streamvoice", lambda: self.load_resources_list(self._find_resource_folderpath(("streamvoice", "streamwaves")), recurse=True))

    @_streamvoice.setter
    def _streamvoice(self, value: list[FileResource]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_streamvoice(self) -> list[FileResource]:
        return self.load_resources_list(self._find_resource_folderpath(("streamvoice", "streamwaves")), recurse=True)

    @property
    def _talktable(self) -> TalkTable:
        return self._get_cached_or_load("talktable", self._load_talktable)

    @_talktable.setter
    def _talktable(self, value: TalkTable) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_talktable(self) -> TalkTable:
        return TalkTable(self._path / "dialog.tlk")

    @property
    def _texturepacks(self) -> dict[str, list[FileResource]]:
        return self._get_cached_or_load("texturepacks", self._load_texturepacks)

    @_texturepacks.setter
    def _texturepacks(self, value: dict[str, list[FileResource]]) -> None: ...  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleVariableOverride]
    def _load_texturepacks(self) -> dict[str, list[FileResource]]:
        return self.load_resources_dict(self.texturepacks_path(), capsule_check=is_erf_file)

    @classmethod
    def from_base_instance(cls, installation: Installation) -> Self:
        """Create a new HTInstallation instance from an existing Installation instance."""
        ht_installation: HTInstallation = installation  # type: ignore[assignment]
        ht_installation.__class__ = cls
        assert isinstance(ht_installation, cls)
        ht_installation.name = f"NonHTInit_{installation.__class__.__name__}_{id(installation)}"
        ht_installation._tsl = installation.game().is_k2()  # noqa: SLF001  # pylint: disable=protected-access
        ht_installation.cache_core_items = None
        ht_installation._cache2da = {}  # noqa: SLF001  # pylint: disable=protected-access
        ht_installation._cache_tpc = {}  # noqa: SLF001  # pylint: disable=protected-access

        return ht_installation

    def setup_file_context_menu(
        self,
        widget: QPlainTextEdit | QLineEdit | QComboBox,
        resref_type: list[ResourceType] | list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
    ):
        from toolset.gui.dialogs.load_from_location_result import ResourceItems

        @Slot(QPoint)
        def extend_context_menu(pos: QPoint):
            root_menu = QMenu(widget) if isinstance(widget, QComboBox) else widget.createStandardContextMenu()
            widget_text: str = widget.currentText().strip() if isinstance(widget, QComboBox) else (widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()).strip()

            build_file_context_menu(root_menu, widget_text)
            root_menu.exec(widget.mapToGlobal(pos))

        def build_file_context_menu(root_menu: QMenu, widget_text: str):
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

            search_order: list[SearchLocation] = order or [SearchLocation.CHITIN, SearchLocation.OVERRIDE, SearchLocation.MODULES, SearchLocation.RIMS]
            resource_types: list[ResourceType] | list[ResourceIdentifier] = resref_type if isinstance(resref_type[0], ResourceType) else resref_type
            # FIXME(th3w1zard1): Seems the type hinter override's for `locations` are wrong, need to fix
            locations: dict[str, list[LocationResult]] = self.locations(
                ([widget_text], resource_types),  # pyright: ignore[reportArgumentType, reportAssignmentType]
                search_order,
            )
            flat_locations: list[LocationResult] = [item for sublist in locations.values() for item in sublist] if isinstance(locations, dict) else locations

            if flat_locations:
                for location in flat_locations:
                    display_path: Path = location.filepath.relative_to(self.path())
                    file_resource: FileResource = location.as_file_resource()
                    if file_resource.inside_bif:
                        display_path /= file_resource.filename()
                    location_menu: QMenu | None = file_menu.addMenu(str(display_path))
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
        selection_window.show()
        selection_window.activateWindow()
        add_window(selection_window)

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
        lower_save_locations: list[str] = [str(save_loc).lower() for save_loc in self.save_locations()]

        for path in changed_files:
            lower_path: str = path.lower()
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
                RobustLogger().warning(f"Unhandled file change: '{path}'")

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
            result: ResourceResult | None = self.resource(resname, ResourceType.TwoDA, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            if result is None:
                return None
            self._cache2da[resname] = read_2da(result.data)
        return self._cache2da[resname]

    def get_relevant_resources(self, restype: ResourceType, src_filepath: Path | None = None) -> set[FileResource]:
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

        relevant_resources: set[FileResource] = {res for res in (*self.override_resources(), *self.chitin_resources()) if res.restype() is restype}

        src_absolute = Path(src_filepath).absolute()
        module_path = Path(self.module_path()).absolute()
        override_path = Path(self.override_path()).absolute()

        def _is_within(child: Path, parent: Path) -> bool:
            try:
                child.relative_to(parent)
            except ValueError:
                return False
            return True

        if _is_within(src_absolute, module_path):
            relevant_resources.update(res for cap in Module.get_capsules_dict_matching(self, src_filepath.name).values() if cap is not None for res in cap if res.restype() is restype)
        elif _is_within(src_absolute, override_path):
            relevant_resources.update(res for reslist in self._modules.values() if any(r.identifier() == src_filepath.name for r in reslist) for res in reslist if res.restype() is restype)  # noqa: E501

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
        queries: list[ResourceIdentifier] = []
        if reload:
            queries.extend(ResourceIdentifier(resname, ResourceType.TwoDA) for resname in resnames)
        else:
            queries.extend(ResourceIdentifier(resname, ResourceType.TwoDA) for resname in resnames if resname not in self._cache2da)

        if not queries:
            return

        resources: dict[ResourceIdentifier, ResourceResult | None] = self.resources(queries, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
        for iden, resource in resources.items():
            if not resource:
                continue
            self._cache2da[iden.resname] = read_2da(resource.data)

    def htClearCache2DA(self):
        self._cache2da = {}

    # endregion

    # region Cache TPC
    def ht_get_cache_tpc(self, resname: str) -> TPC | None:
        if resname not in self._cache_tpc:
            tex: TPC | None = self.texture(
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
        queries: list[str] = list(names) if reload else [name for name in names if name not in self._cache_tpc]

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
        pixmap = QPixmap(":/images/inventory/unknown.png")
        baseitems: TwoDA | None = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().error("Failed to retrieve BASEITEMS 2DA.")
            return pixmap

        with suppress(Exception):
            item_class: str = baseitems.get_cell(uti.base_item, "itemclass")
            variation: int = uti.model_variation if uti.model_variation != 0 else uti.texture_variation
            texture_resname: str = f'i{item_class}_{str(variation).rjust(3, "0")}'
            texture: TPC | None = self.ht_get_cache_tpc(texture_resname.lower())

            if texture is not None:
                return self._get_icon(texture)
        return pixmap

    def get_item_base_name(self, base_item: int) -> str:
        """Get the name of the base item from its ID."""
        try:
            baseitems: TwoDA | None = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
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
        baseitems: TwoDA | None = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().warning("Failed to retrieve `baseitems.2da` from your installation.")
            return "Unknown"
        try:
            item_class: str = baseitems.get_cell(base_item, "itemclass")
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception(f"An exception occurred while getting cell '{base_item}' from `baseitems.2da`.")
            return "Unknown"
        else:
            variation: int = model_variation if model_variation != 0 else texture_variation
            return f"i{item_class}_{str(variation).rjust(3, '0')}"

    def get_item_icon(
        self,
        base_item: int,
        model_variation: int,
        texture_variation: int,
    ) -> QPixmap:
        pixmap = QPixmap(":/images/inventory/unknown.png")
        icon_path: str = self.get_item_icon_path(base_item, model_variation, texture_variation)
        print(f"Icon path: '{icon_path}'")
        try:
            texture: TPC | None = self.ht_get_cache_tpc(os.path.basename(icon_path.lower()))  # noqa: PTH119
            if texture is None:
                return pixmap
            return self._get_icon(texture)
        except Exception as e:  # noqa: BLE001
            RobustLogger().error(
                f"An error occurred loading the icon at '{icon_path}' " f"model variation '{model_variation}' and " f"texture variation '{texture_variation}'.",
                exc_info=e,
            )
            return pixmap
        return pixmap

    def _get_icon(self, texture: TPC, mipmap: int = 0) -> QPixmap:
        if texture.format().is_dxt():
            texture.decode()
        mm: TPCMipmap = texture.get(0, mipmap)
        image = QImage(bytes(mm.data), mm.width, mm.height, mm.tpc_format.to_qimage_format())
        return QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))

    @property
    def tsl(self) -> bool:
        if self._tsl is None:
            self._tsl = self.game().is_k2()
        return self._tsl

    def is_save_corrupted(self, save_path: Path) -> bool:
        """Check if a save game is corrupted.
        
        Args:
        ----
            save_path: Path to the save game folder
            
        Returns:
        -------
            True if the save is corrupted, False otherwise
            
        Processing Logic:
        ----------------
            - Try to use cached SaveFolderEntry if available from parent class
            - Otherwise create and load a new SaveFolderEntry
            - Check if it's corrupted using the is_corrupted() method
            - Return the result
        """
        try:
            # Try to use cached SaveFolderEntry from parent Installation class if available
            if hasattr(self, "save_folders") and save_path in self.save_folders:
                save_folder = self.save_folders[save_path]
            else:
                # Fallback: create a new SaveFolderEntry
                save_folder = SaveFolderEntry(str(save_path))
            
            # Load the save folder (required before checking corruption)
            save_folder.load()
            return save_folder.sav.is_corrupted()
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            # If we can't load the save, assume it's not corrupted (safer than false positives)
            RobustLogger().warning(f"Failed to check corruption for save at '{save_path}'")
            return False
