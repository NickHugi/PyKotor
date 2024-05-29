from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from pykotor.common.misc import ResRef
from pykotor.common.module import Module
from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.utm import UTM, dismantle_utm, read_utm
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.dialogs.inventory import InventoryEditor
from toolset.gui.editor import Editor
from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.common.misc import CaseInsensitiveDict
    from pykotor.resource.formats.gff.gff_data import GFF
    from toolset.data.installation import HTInstallation


class UTMEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation
        | None = None,
    ):
        """Initialize the Merchant Editor window.

        Args:
        ----
            parent: {Widget that is the parent of this window}
            installation: {Optional HTInstallation object to load data from}.

        Processing Logic:
        ----------------
            - Sets up the UI from the designer file
            - Initializes menus and signals
            - Loads data from the provided installation if given
            - Calls new() to start with a blank merchant
        """
        supported: list[ResourceType] = [ResourceType.UTM, ResourceType.BTM]
        super().__init__(parent, "Merchant Editor", "merchant", supported, supported, installation)

        self._utm: UTM = UTM()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.utm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.utm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.utm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.utm import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self.new()

    def _setupSignals(self):
        """Sets up signal connections for UI buttons."""
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.inventoryButton.clicked.connect(self.openInventory)

    def _setupInstallation(self, installation: HTInstallation):
        """Sets up the installation for editing.

        Args:
        ----
            installation: The installation to edit

        Processing Logic:
        ----------------
            - Sets the internal installation reference to the passed in installation
            - Sets the installation on the UI name edit to the passed installation
            - Allows editing of the installation details in the UI.
        """
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        utm: UTM = read_utm(data)
        self._loadUTM(utm)

    def _loadUTM(self, utm: UTM):
        """Loads UTM data into UI elements.

        Args:
        ----
            utm (UTM): UTM object to load data from

        Processing Logic:
        ----------------
            - Sets name, tag, resref, id, markups from UTM object
            - Sets can_buy, can_sell flags from UTM object
            - Sets comment text from UTM object.
        """
        self._utm = utm

        # Basic
        self.ui.nameEdit.setLocstring(utm.name)
        self.ui.tagEdit.setText(utm.tag)
        self.ui.resrefEdit.setText(str(utm.resref))
        self.ui.idSpin.setValue(utm.id)
        self.ui.markUpSpin.setValue(utm.mark_up)
        self.ui.markDownSpin.setValue(utm.mark_down)
        self.ui.onOpenEdit.setText(str(utm.on_open))
        self.ui.storeFlagSelect.setCurrentIndex((int(utm.can_buy) + int(utm.can_sell) * 2) - 1)

        # Comments
        self.ui.commentsEdit.setPlainText(utm.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTM object from UI fields.

        Returns:
        -------
            data: The built UTM data.
            b"": An empty bytes object.

        Processing Logic:
        ----------------
            - Populate UTM object fields from UI elements
            - Convert UTM to GFF format
            - Write GFF to bytearray
            - Return bytearray and empty bytes
        """
        utm: UTM = deepcopy(self._utm)

        # Basic
        utm.name = self.ui.nameEdit.locstring()
        utm.tag = self.ui.tagEdit.text()
        utm.resref = ResRef(self.ui.resrefEdit.text())
        utm.id = self.ui.idSpin.value()
        utm.mark_up = self.ui.markUpSpin.value()
        utm.mark_down = self.ui.markDownSpin.value()
        utm.on_open = ResRef(self.ui.onOpenEdit.text())
        utm.can_buy = bool((self.ui.storeFlagSelect.currentIndex() + 1) & 1)
        utm.can_sell = bool((self.ui.storeFlagSelect.currentIndex() + 1) & 2)

        # Comments
        utm.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff: GFF = dismantle_utm(utm)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTM(UTM())

    def changeName(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generateTag(self):
        if not self.ui.resrefEdit.text():
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resname:
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_mer_000")

    def openInventory(self):
        capsules: list[Capsule] = []

        try:
            root: str = Module.find_root(self._filepath)
            case_root = root.casefold()
            module_names: CaseInsensitiveDict[str] = self._installation.module_names()
            filepath_str = str(self._filepath)
            capsulesPaths: list[str] = [path for path in module_names if case_root in path and path != filepath_str]
            capsules.extend([Capsule(self._installation.module_path() / path) for path in capsulesPaths])
        except Exception as e:
            print(format_exception_with_variables(e, message="This exception has been suppressed."))

        inventoryEditor = InventoryEditor(
            self,
            self._installation,
            capsules,
            [],
            self._utm.inventory,
            {},
            droid=False,
            hide_equipment=True,
            is_store=True,
        )
        if inventoryEditor.exec_():
            self._utm.inventory = inventoryEditor.inventory
