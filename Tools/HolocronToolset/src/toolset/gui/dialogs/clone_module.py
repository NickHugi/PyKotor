from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import qtpy

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QMessageBox

from pykotor.common.module import Module
from pykotor.tools import module
from toolset.gui.dialogs.asyncloader import AsyncLoader

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation

_ROOT_INDEX = 0
_INSTALLATION_INDEX = 1


class ModuleOption(NamedTuple):
    name: str
    root: str
    files: list[str]
    installation: HTInstallation


class CloneModuleDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        active: HTInstallation,
        installations: dict[str, HTInstallation],
    ):
        """Initializes the dialog for cloning a module.

        Args:
        ----
            parent (QWidget): The parent widget.
            active (HTInstallation): The currently active installation.
            installations (dict[str, HTInstallation]): A dictionary of installations.

        Returns:
        -------
            None: Does not return anything.

        Processing Logic:
        ----------------
            - Sets up the UI from the clone_module module.
            - Stores the active installation and dictionary of installations.
            - Connects button clicks and edits to methods.
            - Loads available modules into the dropdown.
        """
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint))

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs import clone_module  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs import clone_module  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs import clone_module  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs import clone_module  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = clone_module.Ui_Dialog()
        self.ui.setupUi(self)

        self._active: HTInstallation = active
        self._installations: dict[str, HTInstallation] = {active.name: active}

        self.ui.createButton.clicked.connect(self.ok)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.filenameEdit.textChanged.connect(self.setPrefixFromFilename)
        self.ui.moduleSelect.currentIndexChanged.connect(self.changedModule)

        self.loadModules()

    def ok(self):
        """Clones a module once user accepted the dialog query.

        Clones a module from the selected root module with the given identifier, prefix, and name.
        Copies textures, lightmaps, and other assets based on checkbox selections.
        Displays status and success/failure messages.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Gets module cloning parameters from UI elements
            - Defines cloning function
            - Warns user if copying textures selected due to longer wait time
            - Runs cloning asynchronously and displays status
            - Shows success message if clone completed.
        """
        installation = self.ui.moduleSelect.currentData().installation
        root = self.ui.moduleSelect.currentData().root
        identifier = self.ui.filenameEdit.text().lower()
        prefix = self.ui.prefixEdit.text().lower()
        name = self.ui.nameEdit.text()

        copyTextures = self.ui.copyTexturesCheckbox.isChecked()
        copyLightmaps = self.ui.copyLightmapsCheckbox.isChecked()
        keepDoors = self.ui.keepDoorsCheckbox.isChecked()
        keepPlaceables = self.ui.keepPlaceablesCheckbox.isChecked()
        keepSounds = self.ui.keepSoundsCheckbox.isChecked()
        keepPathing = self.ui.keepPathingCheckbox.isChecked()

        def task():
            return module.clone_module(
                root,
                identifier,
                prefix,
                name,
                installation,
                copy_textures=copyTextures,
                copy_lightmaps=copyLightmaps,
                keep_doors=keepDoors,
                keep_placeables=keepPlaceables,
                keep_sounds=keepSounds,
                keep_pathing=keepPathing,
            )

        if copyTextures:
            QMessageBox(
                QMessageBox.Icon.Information,
                "This may take a while",
                "You have selected to create copies of the " "texture. This process may add a few extra minutes to the waiting time.",
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec_()

        if not AsyncLoader(self, "Creating module", task, "Failed to create module").exec_():
            return

        QMessageBox(
            QMessageBox.Icon.Information,
            "Clone Successful",
            f"You can now warp to the cloned module '{identifier}'.",
            flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
        ).exec_()

    def loadModules(self):
        """Loads module options from installed modules.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Loops through all installed modules
            - Extracts module name and root path for each file
            - Creates a ModuleOption for each unique root
            - Adds file paths to the ModuleOption
            - Adds the ModuleOption to the module selection UI.
        """
        options: dict[str, ModuleOption] = {}
        for installation in self._installations.values():
            for filename, name in installation.module_names().items():
                root = Module.find_root(filename)
                if root not in options:
                    options[root] = ModuleOption(name, root, [], installation)
                options[root].files.append(filename)

        for option in options.values():
            self.ui.moduleSelect.addItem(option.name, option)

    def changedModule(self, index: int):
        root = self.ui.moduleSelect.currentData().root
        self.ui.moduleRootEdit.setText(root)

    def setPrefixFromFilename(self):
        self.ui.prefixEdit.setText(self.ui.filenameEdit.text().upper()[:3])
