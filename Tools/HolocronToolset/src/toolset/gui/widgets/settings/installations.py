from __future__ import annotations

import os
import uuid

from typing import Any

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QSettings
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QWidget

from pykotor.common.misc import Game
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from toolset.data.settings import Settings
from utility.logger_util import RobustRootLogger, get_log_directory


class InstallationsWidget(QWidget):
    edited = QtCore.Signal()

    def __init__(self, parent: QWidget):
        """Initialize the Installations widget.

        Args:
        ----
            parent: Parent widget

        Processing Logic:
        ----------------
            - Set up model to hold installation data
            - Load global settings
            - Set up UI from designer file
            - Populate UI with initial values
            - Connect signal handlers.
        """
        super().__init__(parent)

        self.installationsModel: QStandardItemModel = QStandardItemModel()
        self.settings = GlobalSettings()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.settings import installations  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.settings import installations  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.settings import installations  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.settings import installations  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = installations.Ui_Form()
        self.ui.setupUi(self)
        self.setupValues()
        self.setupSignals()

    def setupValues(self):
        """Sets up installation values in the model.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Clears existing items from the installations model
            - Loops through installations from settings
            - Creates a QStandardItem for each installation
            - Sets data like path and tsl on the item
            - Appends the item to the installations model.
        """
        self.installationsModel.clear()
        for installation in self.settings.installations().values():
            item = QStandardItem(installation.name)
            item.setData({"path": installation.path, "tsl": installation.tsl})
            self.installationsModel.appendRow(item)

    def setupSignals(self):
        """Set up signal connections for installation management UI.

        Args:
        ----
            self: {The class instance}

        Processing Logic:
        ----------------
            - Connect add path button click to add new installation slot
            - Connect remove path button click to remove selected installation slot
            - Connect path name and directory edits to update installation slot
            - Connect TSL checkbox state change to update installation slot
            - Connect path list selection change to selection changed slot
        """
        self.ui.pathList.setModel(self.installationsModel)

        self.ui.addPathButton.clicked.connect(self.addNewInstallation)
        self.ui.removePathButton.clicked.connect(self.removeSelectedInstallation)
        self.ui.pathNameEdit.textEdited.connect(self.updateInstallation)
        self.ui.pathDirEdit.textEdited.connect(self.updateInstallation)
        self.ui.pathTslCheckbox.stateChanged.connect(self.updateInstallation)
        self.ui.pathList.selectionModel().selectionChanged.connect(self.installationSelected)

    def save(self):
        installations: dict[str, dict[str, str]] = {}

        for row in range(self.installationsModel.rowCount()):
            item: QStandardItem = self.installationsModel.item(row, 0)
            item_text: str = item.text()
            installations[item_text] = item.data()
            installations[item_text]["name"] = item_text

        self.settings.settings.setValue("installations", installations)

    def addNewInstallation(self):
        item = QStandardItem("New")
        item.setData({"path": "", "tsl": False})
        self.installationsModel.appendRow(item)
        self.edited.emit()

    def removeSelectedInstallation(self):
        if len(self.ui.pathList.selectedIndexes()) > 0:
            index = self.ui.pathList.selectedIndexes()[0]
            item = self.installationsModel.itemFromIndex(index)
            self.installationsModel.removeRow(item.row())
            self.edited.emit()

        if len(self.ui.pathList.selectedIndexes()) == 0:
            self.ui.pathFrame.setEnabled(False)

    def updateInstallation(self):
        index = self.ui.pathList.selectedIndexes()[0]
        item = self.installationsModel.itemFromIndex(index)

        data = item.data()
        data["path"] = self.ui.pathDirEdit.text()
        data["tsl"] = self.ui.pathTslCheckbox.isChecked()
        item.setData(data)

        item.setText(self.ui.pathNameEdit.text())

        self.edited.emit()

    def installationSelected(self):
        if len(self.ui.pathList.selectedIndexes()) > 0:
            self.ui.pathFrame.setEnabled(True)

            index = self.ui.pathList.selectedIndexes()[0]
            item = self.installationsModel.itemFromIndex(index)

            self.ui.pathNameEdit.setText(item.text())
            self.ui.pathDirEdit.setText(item.data()["path"])
            self.ui.pathTslCheckbox.setChecked(bool(item.data()["tsl"]))


class InstallationConfig:
    def __init__(self, name: str):
        self._settings = QSettings("HolocronToolsetV3", "Global")
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        installations: dict[str, dict[str, Any]] = self._settings.value("installations", {}, dict)
        installation = installations[self._name]

        del installations[self._name]
        installations[value] = installation
        installations[value]["name"] = value

        self._settings.setValue("installations", installations)
        self._name = value

    @property
    def path(self) -> str:
        try:
            installation = self._settings.value("installations", {})[self._name]
        except Exception:  # noqa: BLE001
            return ""
        else:
            return installation.get("path", "")

    @path.setter
    def path(self, value: str):
        try:
            installations: dict[str, dict[str, str]] = self._settings.value("installations", {})
            installations[self._name] = installations.get(self._name, {})
            installations[self._name]["path"] = value
            self._settings.setValue("installations", installations)
        except Exception:
            log = RobustRootLogger()
            log.exception("InstallationConfig.path property raised an exception.")

    @property
    def tsl(self) -> bool:
        all_installs: dict[str, dict[str, Any]] = self._settings.value("installations", {})
        installation = all_installs.get(self._name, {})
        return installation.get("tsl", False)

    @tsl.setter
    def tsl(self, value: bool):
        installations: dict[str, dict[str, Any]] = self._settings.value("installations", {})
        installations[self._name] = installations.get(self._name, {})
        installations[self._name]["tsl"] = value
        self._settings.setValue("installations", installations)


class GlobalSettings(Settings):
    def __init__(self):
        super().__init__("Global")

    def installations(self) -> dict[str, InstallationConfig]:
        """Finds and records KotOR installation paths.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            dict: A dictionary of InstallationConfig objects keyed by installation name

        """
        installations: dict[str, dict[str, Any]] = self.settings.value("installations")
        if installations is None:
            installations = {}

        if self.firstTime:
            self._handle_firsttime_user(installations)
        self.settings.setValue("installations", installations)

        return {name: InstallationConfig(name) for name in installations}

    def _handle_firsttime_user(self, installations: dict[str, dict[str, Any]]):
        """Finds KotOR installation paths on the system, checks for duplicates, and records the paths and metadata in the user settings.

        Paths are filtered to only existing ones. Duplicates are detected by path and the game name is incremented with a number.
        Each new installation is added to the installations dictionary with its name, path, and game (KotOR 1 or 2) specified.
        The installations dictionary is then saved back to the user settings.
        """
        RobustRootLogger.info("First time user, attempt auto-detection of currently installed KOTOR paths.")
        self.extractPath = str(get_log_directory(f"{uuid.uuid4().hex[:7]}_extract"))
        counters: dict[Game, int] = {Game.K1: 1, Game.K2: 1}
        # Create a set of existing paths
        existing_paths: set[CaseAwarePath] = {CaseAwarePath(inst["path"]) for inst in installations.values()}

        for game, paths in find_kotor_paths_from_default().items():
            for path in filter(CaseAwarePath.safe_isdir, paths):
                RobustRootLogger.info(f"Autodetected game {game!r} path {path}")
                if path in existing_paths:  # If the path is already recorded, skip to the next one
                    continue

                game_name = "KotOR" if game.is_k1() else "TSL"
                base_game_name = game_name  # Save the base name for potential duplicates

                # Increment the counter if the game name already exists, indicating a duplicate
                while game_name in installations:
                    counters[game] += 1
                    game_name = f"{base_game_name} ({counters[game]})"

                # Add the new installation under the unique game_name
                installations[game_name] = {
                    "name": game_name,
                    "path": str(path),
                    "tsl": game.is_k2(),
                }
                existing_paths.add(path)  # Add the new path to the set of existing paths
        self.firstTime = False

    # region Strings
    recentFiles = Settings.addSetting(
        "recentFiles",
        [],
    )
    extractPath = Settings.addSetting(
        "extractPath",
        "",
    )
    nssCompilerPath = Settings.addSetting(
        "nssCompilerPath",
        "ext/nwnnsscomp.exe" if os.name == "nt" else "ext/nwnnsscomp",
    )
    ncsDecompilerPath = Settings.addSetting(
        "ncsDecompilerPath",
        "",
    )
    selectedTheme = Settings.addSetting(
        "selectedTheme",
        "Fusion (Light)",  # Default theme
    )
    moduleSortOption = Settings.addSetting(
        "moduleSortOption",
        2,
    )
    # endregion

    # region Bools
    profileToolset = Settings.addSetting(
        "profileToolset",
        False,
    )
    disableRIMSaving = Settings.addSetting(
        "disableRIMSaving",
        True,
    )
    attemptKeepOldGFFFields = Settings.addSetting(
        "attemptKeepOldGFFFields",
        False,
    )
    useBetaChannel = Settings.addSetting(
        "useBetaChannel",
        True,
    )
    firstTime = Settings.addSetting(
        "firstTime",
        True,
    )
    gff_specializedEditors = Settings.addSetting(
        "gff_specializedEditors",
        True,
    )
    joinRIMsTogether = Settings.addSetting(
        "joinRIMsTogether",
        False,
    )
    useModuleFilenames = Settings.addSetting(
        "useModuleFilenames",
        False,
    )
    greyRIMText = Settings.addSetting(
        "greyRIMText",
        True,
    )
    showPreviewUTC = Settings.addSetting(
        "showPreviewUTC",
        True,
    )
    showPreviewUTP = Settings.addSetting(
        "showPreviewUTP",
        True,
    )
    showPreviewUTD = Settings.addSetting(
        "showPreviewUTD",
        True,
    )
    # endregion


class NoConfigurationSetError(Exception): ...
