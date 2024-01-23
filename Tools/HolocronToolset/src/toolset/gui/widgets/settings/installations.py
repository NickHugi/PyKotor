from __future__ import annotations

import os
from typing import Any

from pykotor.common.misc import Game
from pykotor.tools.path import find_kotor_paths_from_default
from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QWidget
from toolset.data.settings import Settings
from utility.path import Path


class InstallationsWidget(QWidget):
    edited = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        """Initialize the Installations widget
        Args:
            parent: Parent widget
        Returns:
            None
        - Set up model to hold installation data
        - Load global settings
        - Set up UI from designer file
        - Populate UI with initial values
        - Connect signal handlers.
        """
        super().__init__(parent)

        self.installationsModel: QStandardItemModel = QStandardItemModel()
        self.settings = GlobalSettings()

        from toolset.uic.widgets.settings import installations
        self.ui = installations.Ui_Form()
        self.ui.setupUi(self)
        self.setupValues()
        self.setupSignals()

    def setupValues(self):
        """Sets up installation values in the model
        Args:
            self: The class instance
        Returns:
            None: Does not return anything
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

        Returns:
        -------
            None: {No return value}
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
        installations = {}

        for row in range(self.installationsModel.rowCount()):
            item = self.installationsModel.item(row, 0)
            installations[item.text()] = item.data()
            installations[item.text()]["name"] = item.text()

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
        self._settings = QSettings("HolocronToolset", "Global")
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        installations = self._settings.value("installations", {}, dict[str, Any])
        installation = installations[self._name]

        del installations[self._name]
        installations[value] = installation
        installations[value]["name"] = value

        self._settings.setValue("installations", installations)
        self._name = value

    @property
    def path(self) -> str:
        installation = self._settings.value("installations", {})[self._name]
        return installation["path"]

    @path.setter
    def path(self, value: str):
        installations = self._settings.value("installations", {})
        installations[self._name]["path"] = value
        self._settings.setValue("installations", installations)

    @property
    def tsl(self) -> bool:
        installation = self._settings.value("installations", {})[self._name]
        return installation["tsl"]

    @tsl.setter
    def tsl(self, value: bool):
        installations = self._settings.value("installations", {})
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

        Finds KotOR installation paths on the system, checks for duplicates, and records the paths and metadata in the user settings.
        Paths are filtered to only existing ones. Duplicates are detected by path and the game name is incremented with a number.
        Each new installation is added to the installations dictionary with its name, path, and game (KotOR 1 or 2) specified.
        The installations dictionary is then saved back to the user settings.
        """
        installations = self.settings.value("installations")
        if installations is None:
            installations = {}

        counters = {Game.K1: 1, Game.K2: 1}
        existing_paths = {Path(inst["path"]) for inst in installations.values()}  # Create a set of existing paths

        for game, paths in find_kotor_paths_from_default().items():
            for path in filter(Path.exists, paths):
                if path in existing_paths:  # If the path is already recorded, skip to the next one
                    continue

                game_name = "KotOR" if game == Game.K1 else "TSL"
                base_game_name = game_name  # Save the base name for potential duplicates

                # Increment the counter if the game name already exists, indicating a duplicate
                while game_name in installations:
                    counters[game] += 1
                    game_name = f"{base_game_name} ({counters[game]})"

                # Add the new installation under the unique game_name
                installations[game_name] = {
                    "name": game_name,
                    "path": str(path),
                    "tsl": game == Game.K2,
                }
                existing_paths.add(path)  # Add the new path to the set of existing paths

        self.settings.setValue("installations", installations)

        return {name: InstallationConfig(name) for name in installations}



    # region Strings
    extractPath = Settings._addSetting(
        "extractPath",
        "",
    )
    nssCompilerPath = Settings._addSetting(
        "nssCompilerPath",
        "ext/nwnnsscomp.exe" if os.name == "nt" else "ext/nwnnsscomp",
    )
    ncsDecompilerPath = Settings._addSetting(
        "ncsDecompilerPath",
        "",
    )
    # endregion

    # region Bools
    disableRIMSaving = Settings._addSetting(
        "disableRIMSaving",
        True,
    )
    firstTime = Settings._addSetting(
        "firstTime",
        True,
    )
    gff_specializedEditors = Settings._addSetting(
        "gff_specializedEditors",
        True,
    )
    joinRIMsTogether = Settings._addSetting(
        "joinRIMsTogether",
        False,
    )
    greyRIMText = Settings._addSetting(
        "greyRIMText",
        True,
    )
    showPreviewUTC = Settings._addSetting(
        "showPreviewUTC",
        True,
    )
    showPreviewUTP = Settings._addSetting(
        "showPreviewUTP",
        True,
    )
    showPreviewUTD = Settings._addSetting(
        "showPreviewUTD",
        True,
    )
    # endregion


class NoConfigurationSetError(Exception):
    ...
