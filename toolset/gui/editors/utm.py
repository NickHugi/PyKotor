from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Optional

from pykotor.common.misc import ResRef
from pykotor.common.module import Module
from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.utm import UTM, dismantle_utm, read_utm
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.dialogs.inventory import InventoryEditor
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class UTMEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.UTM]
        super().__init__(parent, "Merchant Editor", "merchant", supported, supported, installation)

        self._utm = UTM()

        from toolset.uic.editors.utm import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self.new()

    def _setupSignals(self) -> None:
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.inventoryButton.clicked.connect(self.openInventory)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        utm = read_utm(data)
        self._loadUTM(utm)

    def _loadUTM(self, utm: UTM) -> None:
        self._utm = utm

        # Basic
        self.ui.nameEdit.setLocstring(utm.name)
        self.ui.tagEdit.setText(utm.tag)
        self.ui.resrefEdit.setText(utm.resref.get())
        self.ui.idSpin.setValue(utm.id)
        self.ui.markUpSpin.setValue(utm.mark_up)
        self.ui.markDownSpin.setValue(utm.mark_down)
        self.ui.onOpenEdit.setText(utm.on_open.get())
        self.ui.storeFlagSelect.setCurrentIndex((int(utm.can_buy) + int(utm.can_sell) * 2) - 1)

        # Comments
        self.ui.commentsEdit.setPlainText(utm.comment)

    def build(self) -> tuple[bytes, bytes]:
        utm = self._utm

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
        gff = dismantle_utm(utm)
        write_gff(gff, data)

        return data, b""

    def new(self) -> None:
        super().new()
        self._loadUTM(UTM())

    def changeName(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit, dialog.locstring)

    def generateTag(self) -> None:
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self) -> None:
        if self._resref is not None and self._resref != "":
            self.ui.resrefEdit.setText(self._resref)
        else:
            self.ui.resrefEdit.setText("m00xx_mer_000")

    def openInventory(self) -> None:
        capsules = []

        with suppress(Exception):
            root = Module.get_root(self._filepath)
            capsulesPaths = [path for path in self._installation.module_names() if root in path and path != self._filepath]
            capsules.extend([Capsule(self._installation.module_path() + path) for path in capsulesPaths])

        inventoryEditor = InventoryEditor(self, self._installation, capsules, [], self._utm.inventory, {}, False, True, True)
        if inventoryEditor.exec_():
            self._utm.inventory = inventoryEditor.inventory
