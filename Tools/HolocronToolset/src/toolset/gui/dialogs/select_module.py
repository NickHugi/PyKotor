from __future__ import annotations

from pathlib import PurePath
from typing import TYPE_CHECKING

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QFileDialog, QListWidgetItem

from pykotor.common.module import Module

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class SelectModuleDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
    ):
        """Initializes the dialog to select a module.

        Args:
            parent (QWidget): Parent widget
            installation (HTInstallation): HT installation object

        Processing Logic:
        ----------------
            - Initializes the UI from the dialog design
            - Connects button click signals to methods
            - Builds the initial module list
            - Sets up filtering of module list.
        """
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._installation: HTInstallation = installation

        self.module: str = ""

        from toolset.uic.qtpy.dialogs.select_module import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.ui.openButton.clicked.connect(self.confirm)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.browseButton.clicked.connect(self.browse)
        self.ui.moduleList.currentRowChanged.connect(self.on_row_changed)
        self.ui.moduleList.doubleClicked.connect(self.confirm)
        self.ui.moduleList.itemDoubleClicked.connect(self.confirm)
        self.ui.filterEdit.textEdited.connect(self.on_filter_edited)

        self._build_module_list()

    def _build_module_list(self):
        """Builds a list of installed modules
        Args:
            self: The class instance
        Returns:
            None: No return value
        - Gets list of module names from installation object
        - Initializes empty set to track listed modules
        - Loops through modules list
        - Gets module root and checks if already listed
        - If not already listed, adds to list widget with name and root in brackets
        - Sets root as item data for later retrieval.
        """
        module_names: dict[str, str] = self._installation.module_names()
        listed_modules: set[str] = set()

        for module in self._installation.modules_list():
            casefold_module_file_name = str(
                PurePath(module).with_name(
                    Module.filepath_to_root(module)
                    + PurePath(module).suffix
                )
            ).casefold().strip()
            if casefold_module_file_name in listed_modules:
                continue
            listed_modules.add(casefold_module_file_name)

            item = QListWidgetItem(f"{module_names[module]}  [{casefold_module_file_name}]")
            item.setData(Qt.ItemDataRole.UserRole, casefold_module_file_name)
            self.ui.moduleList.addItem(item)  # pyright: ignore[reportCallIssue]

    def browse(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select module to open",
            str(self._installation.module_path()),
            "Module File (*.mod *.rim *.erf)",
        )

        if not filepath or not filepath.strip():
            return
        self.module = Module.filepath_to_root(filepath)
        self.accept()

    def confirm(self):
        """Confirms the selected module
        Args:
            self: The object instance
        Returns:
            None: Does not return anything
        - Gets the currently selected module from the module list widget
        - Calls accept to close the dialog and apply changes.
        """
        cur_item: QListWidgetItem | None = self.ui.moduleList.currentItem()
        if cur_item is None:
            RobustLogger().warning("currentItem() returned None in SelectModuleDialog.confirm()")
            return
        self.module = cur_item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def on_row_changed(self):
        self.ui.openButton.setEnabled(self.ui.moduleList.currentItem() is not None)

    def on_filter_edited(self):
        """Filter modules based on filter text
        Args:
            self: The class instance
        Returns:
            None
        - Get filter text from filter edit box
        - Loop through each row in module list
        - Get item at that row
        - Hide item if filter text is not present in item text
        - This will filter and show only matching items.
        """
        text = self.ui.filterEdit.text()
        for row in range(self.ui.moduleList.count()):
            item: QListWidgetItem | None = self.ui.moduleList.item(row)
            if item is None:
                RobustLogger().warning(f"found None-typed item at row {row} while filtering text.")
                continue
            item.setHidden(text.lower() not in item.text().lower())
