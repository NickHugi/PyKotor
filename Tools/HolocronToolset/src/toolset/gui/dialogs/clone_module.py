from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QMessageBox

from pykotor.common.module import Module
from pykotor.tools import module
from toolset.gui.common.localization import translate as tr, trf
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
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint
            & ~QtCore.Qt.WindowType.WindowMinMaxButtonsHint
        )

        from toolset.uic.qtpy.dialogs.clone_module import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self._active: HTInstallation = active
        self._installations: dict[str, HTInstallation] = {active.name: active}

        self.ui.createButton.clicked.connect(self.ok)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.filenameEdit.textChanged.connect(self.set_prefix_from_filename)
        self.ui.moduleSelect.currentIndexChanged.connect(self.changed_module)

        self.load_modules()

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
        installation: HTInstallation = self.ui.moduleSelect.currentData().installation
        root: str = self.ui.moduleSelect.currentData().root
        identifier: str = self.ui.filenameEdit.text().lower()
        prefix: str = self.ui.prefixEdit.text().lower()
        name: str = self.ui.nameEdit.text()

        copy_textures: bool = self.ui.copyTexturesCheckbox.isChecked()
        copy_lightmaps: bool = self.ui.copyLightmapsCheckbox.isChecked()
        keep_doors: bool = self.ui.keepDoorsCheckbox.isChecked()
        keep_placeables: bool = self.ui.keepPlaceablesCheckbox.isChecked()
        keep_sounds: bool = self.ui.keepSoundsCheckbox.isChecked()
        keep_pathing: bool = self.ui.keepPathingCheckbox.isChecked()

        def task():
            return module.clone_module(
                root,
                identifier,
                prefix,
                name,
                installation,
                copy_textures=copy_textures,
                copy_lightmaps=copy_lightmaps,
                keep_doors=keep_doors,
                keep_placeables=keep_placeables,
                keep_sounds=keep_sounds,
                keep_pathing=keep_pathing,
            )

        if copy_textures:
            QMessageBox(
                QMessageBox.Icon.Information,
                tr("This may take a while"),
                tr("You have selected to create copies of the texture. This process may add a few extra minutes to the waiting time."),
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec()

        if not AsyncLoader(self, "Creating module", task, "Failed to create module").exec():
            return

        QMessageBox(
            QMessageBox.Icon.Information,
            tr("Clone Successful"),
            trf("You can now warp to the cloned module '{identifier}'.", identifier=identifier),
            flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
        ).exec()

    def load_modules(self):
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
                root: str = Module.filepath_to_root(filename)
                if root not in options:
                    options[root] = ModuleOption(name, root, [], installation)
                options[root].files.append(filename)

        for option in options.values():
            self.ui.moduleSelect.addItem(option.name, option)

    def changed_module(
        self,
        index: int,
    ):
        root: str = self.ui.moduleSelect.currentData().root
        self.ui.moduleRootEdit.setText(root)

    def set_prefix_from_filename(self):
        self.ui.prefixEdit.setText(self.ui.filenameEdit.text().upper()[:3])
