from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.erf import read_erf, write_erf
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.generics.utc import UTC, bytes_utc
from pykotor.resource.generics.utd import UTD, bytes_utd
from pykotor.resource.generics.ute import UTE, bytes_ute
from pykotor.resource.generics.utm import UTM, bytes_utm
from pykotor.resource.generics.utp import UTP, bytes_utp
from pykotor.resource.generics.uts import UTS, bytes_uts
from pykotor.resource.generics.utt import UTT, bytes_utt
from pykotor.resource.generics.utw import UTW, bytes_utw
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_or_mod_file, is_rim_file
from utility.path import Path
from PyQt5 import QtCore
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QListWidgetItem, QWidget
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class InsertInstanceDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, module: Module, restype: ResourceType):
        """Initialize a resource editor dialog
        Args:
            parent: QWidget - Parent widget
            installation: HTInstallation - HT installation object
            module: Module - Module object
            restype: ResourceType - Resource type
        Returns:
            None - Does not return anything
        Initializes the resource editor dialog:
            - Sets up UI elements
            - Connects signal handlers
            - Populates resource list
            - Initializes location selector.
        """
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Module = module
        self._restype: ResourceType = restype

        self.resname: str = ""
        self.data: bytes = b""
        self.filepath: Path | None = None

        from toolset.uic.dialogs.insert_instance import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self._setupSignals()
        self._setupLocationSelect()
        self._setupResourceList()

    def _setupSignals(self) -> None:
        self.ui.createResourceRadio.toggled.connect(self.onResourceRadioToggled)
        self.ui.reuseResourceRadio.toggled.connect(self.onResourceRadioToggled)
        self.ui.copyResourceRadio.toggled.connect(self.onResourceRadioToggled)
        self.ui.resrefEdit.textEdited.connect(self.onResRefEdited)
        self.ui.resourceFilter.textChanged.connect(self.onResourceFilterChanged)

    def _setupLocationSelect(self) -> None:
        self.ui.locationSelect.addItem(str(self._installation.override_path()), self._installation.override_path())
        for capsule in self._module.capsules():
            if is_rim_file(capsule.path()) and GlobalSettings().disableRIMSaving:
                continue
            self.ui.locationSelect.addItem(str(capsule.path()), capsule.path())
        self.ui.locationSelect.setCurrentIndex(self.ui.locationSelect.count() - 1)

    def _setupResourceList(self) -> None:
        """Populates a resource list widget with available resources.

        Args:
        ----
            self: The class instance
        Returns:
            None
        Processing Logic:
            - Loops through installation resources and adds matching type
            - Loops through module capsules and nested resources, adding matching type
            - Selects first item if list is populated.
        """
        for resource in self._installation.chitin_resources():
            if resource.restype() == self._restype:
                item = QListWidgetItem(resource.resname())
                item.setToolTip(str(resource.filepath()))
                item.setData(QtCore.Qt.UserRole, resource)
                self.ui.resourceList.addItem(item)

        for capsule in self._module.capsules():
            for resource in [resource for resource in capsule if resource.restype() == self._restype]:
                if resource.restype() == self._restype:
                    item = QListWidgetItem(resource.resname())
                    item.setToolTip(str(resource.filepath()))
                    item.setForeground(QColor(30, 30, 30))
                    item.setData(QtCore.Qt.UserRole, resource)
                    self.ui.resourceList.addItem(item)

        if self.ui.resourceList.count() > 0:
            self.ui.resourceList.item(0).setSelected(True)

    def accept(self) -> None:
        """Accepts resource selection and updates module accordingly
        Args:
            self: Accepts the class instance
        Returns:
            None: Does not return anything
        Processing Logic:
            - Checks which radio button is selected for reuse, copy or create resource
            - Sets resource name, file path and data based on selection
            - Writes data to file if resource is new
            - Adds resource location to module.
        """
        super().accept()

        new = True
        resource: FileResource = self.ui.resourceList.selectedItems()[0].data(QtCore.Qt.UserRole)

        if self.ui.reuseResourceRadio.isChecked():
            new = False
            self.resname = resource.resname()
            self.filepath = resource.filepath()
            self.data = resource.data()
        elif self.ui.copyResourceRadio.isChecked():
            self.resname = self.ui.resrefEdit.text()
            self.filepath = Path(self.ui.locationSelect.currentData())
            self.data = resource.data()
        elif self.ui.createResourceRadio.isChecked():
            self.resname = self.ui.resrefEdit.text()
            self.filepath = Path(self.ui.locationSelect.currentData())
            if self._restype == ResourceType.UTC:
                self.data = bytes_utc(UTC())
            elif self._restype == ResourceType.UTP:
                self.data = bytes_utp(UTP())
            elif self._restype == ResourceType.UTD:
                self.data = bytes_utd(UTD())
            elif self._restype == ResourceType.UTE:
                self.data = bytes_ute(UTE())
            elif self._restype == ResourceType.UTT:
                self.data = bytes_utt(UTT())
            elif self._restype == ResourceType.UTS:
                self.data = bytes_uts(UTS())
            elif self._restype == ResourceType.UTM:
                self.data = bytes_utm(UTM())
            elif self._restype == ResourceType.UTW:
                self.data = bytes_utw(UTW())
            else:
                self.data = b""

        if new and self.filepath:
            if is_erf_or_mod_file(self.filepath.name):
                erf = read_erf(self.filepath)
                erf.set_data(self.resname, self._restype, self.data)
                write_erf(erf, self.filepath)
            elif is_rim_file(self.filepath.name):
                rim = read_rim(self.filepath)
                rim.set_data(self.resname, self._restype, self.data)
                write_rim(rim, self.filepath)
            else:
                self.filepath = Path(self.filepath) / f"{self.resname}.{self._restype.extension}"
                BinaryWriter.dump(self.filepath, self.data)

        self._module.add_locations(self.resname, self._restype, [self.filepath])

    def onResourceRadioToggled(self) -> None:
        self.ui.resourceList.setEnabled(not self.ui.createResourceRadio.isChecked())
        self.ui.resourceFilter.setEnabled(not self.ui.createResourceRadio.isChecked())
        self.ui.resrefEdit.setEnabled(not self.ui.reuseResourceRadio.isChecked())

        if self.ui.reuseResourceRadio.isChecked():
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

        if self.ui.copyResourceRadio.isChecked():
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.isValidResref(self.ui.resrefEdit.text()))

        if self.ui.createResourceRadio.isChecked():
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.isValidResref(self.ui.resrefEdit.text()))

    def onResRefEdited(self, text: str) -> None:
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.isValidResref(text))

    def onResourceFilterChanged(self) -> None:
        text = self.ui.resourceFilter.text()
        for row in range(self.ui.resourceList.count()):
            item = self.ui.resourceList.item(row)
            item.setHidden(text not in item.text())

    def isValidResref(self, text: str) -> bool:
        return self._module.resource(text, self._restype) is None and text != ""
