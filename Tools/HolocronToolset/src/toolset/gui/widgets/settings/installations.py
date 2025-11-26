from __future__ import annotations

import os
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from loggerplus import RobustLogger, get_log_directory
from qtpy.QtCore import (
    QModelIndex,
    QSettings,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QWidget

from pykotor.common.misc import Game
from pykotor.tools.path import find_kotor_paths_from_default
from toolset.data.settings import Settings

if TYPE_CHECKING:
    from qtpy.QtCore import QItemSelectionModel, QModelIndex
    from typing_extensions import Literal, TypedDict  # pyright: ignore[reportMissingModuleSource]

    from toolset.data.installation import HTInstallation  # noqa: F401
    from toolset.data.settings import SettingsProperty

    class InstallationDetailDict(TypedDict):
        name: str
        path: str
        tsl: bool

    class InstallationsDict(TypedDict):
        installations: dict[str, InstallationDetailDict]


class InstallationsWidget(QWidget):
    sig_settings_edited: ClassVar[Signal] = Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)

        self.installations_model: QStandardItemModel = QStandardItemModel()
        self.settings: GlobalSettings = GlobalSettings()

        from toolset.uic.qtpy.widgets.settings.installations import Ui_Form

        self.ui: Ui_Form = Ui_Form()
        self.ui.setupUi(self)
        self.setup_values()
        self.setup_signals()

    def setup_values(self):
        self.installations_model.clear()
        for installation in self.settings.installations().values():
            item = QStandardItem(installation.name)
            item.setData({"path": installation.path, "tsl": installation.tsl})
            self.installations_model.appendRow(item)

    def setup_signals(self):
        self.ui.pathList.setModel(self.installations_model)

        self.ui.addPathButton.clicked.connect(self.add_new_installation)
        self.ui.removePathButton.clicked.connect(self.remove_selected_installation)
        self.ui.pathNameEdit.textEdited.connect(self.update_installation)
        self.ui.pathDirEdit.textEdited.connect(self.update_installation)
        self.ui.pathTslCheckbox.stateChanged.connect(self.update_installation)
        select_model: QItemSelectionModel | None = self.ui.pathList.selectionModel()
        assert select_model is not None, "select_model cannot be None in setup_signals"
        select_model.selectionChanged.connect(self.installation_selected)

    def save(self):
        installations: dict[str, dict[str, str]] = {}

        for row in range(self.installations_model.rowCount()):
            item: QStandardItem | None = self.installations_model.item(row, 0)
            if item is None:
                continue
            item_text: str = item.text()
            installations[item_text] = item.data()
            installations[item_text]["name"] = item_text

        self.settings.settings.setValue("installations", installations)

    def add_new_installation(self):
        from toolset.gui.common.localization import translate as tr
        item: QStandardItem = QStandardItem(tr("New"))
        item.setData({"path": "", "tsl": False})
        self.installations_model.appendRow(item)
        self.sig_settings_edited.emit()

    def remove_selected_installation(self):
        if len(self.ui.pathList.selectedIndexes()) > 0:
            index: QModelIndex = self.ui.pathList.selectedIndexes()[0]
            item: QStandardItem | None = self.installations_model.itemFromIndex(index)
            assert item is not None, "Item should not be None in remove_selected_installation"
            self.installations_model.removeRow(item.row())
            self.sig_settings_edited.emit()

        if len(self.ui.pathList.selectedIndexes()) == 0:
            self.ui.pathFrame.setEnabled(False)

    def update_installation(self):
        index: QModelIndex = self.ui.pathList.selectedIndexes()[0]
        item: QStandardItem | None = self.installations_model.itemFromIndex(index)
        assert item is not None, "Item should not be None in update_installation"

        data: dict[str, Any] = item.data()
        data["path"] = self.ui.pathDirEdit.text()
        data["tsl"] = self.ui.pathTslCheckbox.isChecked()
        item.setData(data)

        item.setText(self.ui.pathNameEdit.text())

        self.sig_settings_edited.emit()

    def installation_selected(self):
        if len(self.ui.pathList.selectedIndexes()) > 0:
            self.ui.pathFrame.setEnabled(True)

        index: QModelIndex = self.ui.pathList.selectedIndexes()[0]
        item: QStandardItem | None = self.installations_model.itemFromIndex(index)
        assert item is not None, "Item should not be None in installation_selected"
        item_text: str = item.text()
        item_data: dict[str, Any] = item.data()

        self.ui.pathNameEdit.setText(item_text)
        self.ui.pathDirEdit.setText(item_data["path"])
        self.ui.pathTslCheckbox.setChecked(bool(item_data["tsl"]))


class InstallationConfig:
    def __init__(
        self,
        name: str,
    ):
        self._settings: QSettings = QSettings("HolocronToolsetV3", "Global")
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(
        self,
        value: str,
    ):
        installations: dict[str, dict[str, Any]] = self._settings.value("installations", {}, dict)
        installation: dict[str, Any] = installations[self._name]

        del installations[self._name]
        installations[value] = installation
        installations[value]["name"] = value

        self._settings.setValue("installations", installations)
        self._name = value

    @property
    def path(self) -> str:
        try:
            installation: dict[str, Any] = self._settings.value("installations", {})[self._name]
        except Exception:  # noqa: BLE001
            return ""
        else:
            return installation.get("path", "")

    @path.setter
    def path(
        self,
        value: str,
    ):
        try:
            installations: dict[str, dict[str, str]] = self._settings.value("installations", {})
            installations[self._name] = installations.get(self._name, {})
            installations[self._name]["path"] = value
            self._settings.setValue("installations", installations)
        except Exception:
            log = RobustLogger()
            log.exception("InstallationConfig.path property raised an exception.")

    @property
    def tsl(self) -> bool:
        all_installs: dict[str, dict[str, Any]] = self._settings.value("installations", {})
        installation: dict[str, Any] = all_installs.get(self._name, {})
        return installation.get("tsl", False)

    @tsl.setter
    def tsl(
        self,
        value: bool,
    ):
        installations: dict[str, dict[str, Any]] = self._settings.value("installations", {})
        installations[self._name] = installations.get(self._name, {})
        installations[self._name]["tsl"] = value
        self._settings.setValue("installations", installations)


class GlobalSettings(Settings):
    def __init__(self):
        super().__init__("Global")

    def installations(self) -> dict[str, InstallationConfig]:
        installations: dict[str, dict[str, Any]] = self.settings.value("installations")
        if installations is None:
            installations = {}

        if self.firstTime:
            self.firstTime = False
            self._handle_firsttime_user(installations)
        self.settings.setValue("installations", installations)

        return {
            name: InstallationConfig(name)
            for name in installations
        }

    def _handle_firsttime_user(
        self,
        installations: dict[str, dict[str, Any]],
    ):
        """Finds KotOR installation paths on the system, checks for duplicates, and records the paths and metadata in the user settings.

        Paths are filtered to only existing ones. Duplicates are detected by path and the game name is incremented with a number.
        Each new installation is added to the installations dictionary with its name, path, and game (KotOR 1 or 2) specified.
        The installations dictionary is then saved back to the user settings.
        """
        self.firstTime = False
        RobustLogger().info("First time user, attempt auto-detection of currently installed KOTOR paths.")
        self.extractPath = str(get_log_directory(f"{uuid.uuid4().hex[:7]}_extract"))
        counters: dict[Game, int] = {Game.K1: 1, Game.K2: 1}
        # Create a set of existing paths
        existing_paths: set[Path] = {Path(inst["path"]) for inst in installations.values()}

        for game, paths in find_kotor_paths_from_default().items():
            for path in filter(CaseAwarePath.is_dir, paths):
                RobustLogger().info(f"Autodetected game {game!r} path {path}")
                if path in existing_paths:
                    continue
                game_name: Literal["KotOR", "TSL"] = "KotOR" if game.is_k1() else "TSL"
                base_game_name: Literal["KotOR", "TSL"] = game_name
                while game_name in installations:
                    counters[game] += 1
                    game_name = f"{base_game_name} ({counters[game]})"  # type: ignore[assignment]
                installations[game_name] = {
                    "name": game_name,
                    "path": str(path),
                    "tsl": game.is_k2(),
                }
                existing_paths.add(path)

    # region Strings
    recentFiles: SettingsProperty[list[str]] = Settings.addSetting(
        "recentFiles",
        [],
    )
    extractPath: SettingsProperty[str] = Settings.addSetting(
        "extractPath",
        "",
    )
    nssCompilerPath: SettingsProperty[str] = Settings.addSetting(
        "nssCompilerPath",
        "ext/nwnnsscomp.exe" if os.name == "nt" else "ext/nwnnsscomp",
    )
    ncsDecompilerPath: SettingsProperty[str] = Settings.addSetting(
        "ncsDecompilerPath",
        "",
    )
    selectedTheme: SettingsProperty[str] = Settings.addSetting(
        "selectedTheme",
        "fusion (light)",  # Default theme
    )
    selectedStyle: SettingsProperty[str] = Settings.addSetting(
        "selectedStyle",
        "",  # Empty means use theme's default style
    )
    selectedLanguage: SettingsProperty[int] = Settings.addSetting(
        "selectedLanguage",
        0,  # Default to English (ToolsetLanguage.ENGLISH)
    )
    # endregion

    # region Numbers
    moduleSortOption: SettingsProperty[int] = Settings.addSetting(
        "moduleSortOption",
        2,
    )
    # endregion

    # region Bools
    loadEntireInstallation: SettingsProperty[bool] = Settings.addSetting(
        "load_entire_installation",
        False,
    )
    disableRIMSaving: SettingsProperty[bool] = Settings.addSetting(
        "disableRIMSaving",
        True,
    )
    attemptKeepOldGFFFields: SettingsProperty[bool] = Settings.addSetting(
        "attemptKeepOldGFFFields",
        False,
    )
    useBetaChannel: SettingsProperty[bool] = Settings.addSetting(
        "useBetaChannel",
        True,
    )
    firstTime: SettingsProperty[bool] = Settings.addSetting(
        "firstTime",
        True,
    )
    gffSpecializedEditors: SettingsProperty[bool] = Settings.addSetting(
        "gffSpecializedEditors",
        True,
    )
    joinRIMsTogether: SettingsProperty[bool] = Settings.addSetting(
        "joinRIMsTogether",
        True,
    )
    useModuleFilenames: SettingsProperty[bool] = Settings.addSetting(
        "useModuleFilenames",
        False,
    )
    greyRIMText: SettingsProperty[bool] = Settings.addSetting(
        "greyRIMText",
        True,
    )
    showPreviewUTC: SettingsProperty[bool] = Settings.addSetting(
        "showPreviewUTC",
        True,
    )
    showPreviewUTP: SettingsProperty[bool] = Settings.addSetting(
        "showPreviewUTP",
        True,
    )
    showPreviewUTD: SettingsProperty[bool] = Settings.addSetting(
        "showPreviewUTD",
        True,
    )
    # endregion


class NoConfigurationSetError(Exception):
    ...
