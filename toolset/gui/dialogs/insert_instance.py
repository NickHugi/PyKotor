from PyQt5 import QtCore
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QListWidgetItem, \
    QDialog, QDialogButtonBox

from gui.widgets.settings.installations import GlobalSettings
from pykotor.common.module import Module
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.erf import read_erf, write_erf
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.generics.utc import bytes_utc, UTC
from pykotor.resource.generics.utd import bytes_utd, UTD
from pykotor.resource.generics.ute import bytes_ute, UTE
from pykotor.resource.generics.utm import UTM, bytes_utm
from pykotor.resource.generics.utp import bytes_utp, UTP
from pykotor.resource.generics.uts import bytes_uts, UTS
from pykotor.resource.generics.utt import bytes_utt, UTT
from pykotor.resource.generics.utw import bytes_utw, UTW
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation


class InsertInstanceDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, module: Module, restype: ResourceType):
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Module = module
        self._restype: ResourceType = restype

        self.resname: str = ""
        self.data: bytes = b''
        self.filepath: str = ""

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
        self.ui.locationSelect.addItem(self._installation.override_path(), self._installation.override_path())
        for capsule in self._module.capsules():
            if capsule.path().endswith(".rim") and GlobalSettings().disableRIMSaving:
                continue
            self.ui.locationSelect.addItem(capsule.path(), capsule.path())
        self.ui.locationSelect.setCurrentIndex(self.ui.locationSelect.count()-1)

    def _setupResourceList(self) -> None:
        for resource in self._installation.chitin_resources():
            if resource.restype() == self._restype:
                item = QListWidgetItem(resource.resname())
                item.setToolTip(resource.filepath())
                item.setData(QtCore.Qt.UserRole, resource)
                self.ui.resourceList.addItem(item)

        for capsule in self._module.capsules():
            for resource in [resource for resource in capsule if resource.restype() == self._restype]:
                if resource.restype() == self._restype:
                    item = QListWidgetItem(resource.resname())
                    item.setToolTip(resource.filepath())
                    item.setForeground(QColor(30, 30, 30))
                    item.setData(QtCore.Qt.UserRole, resource)
                    self.ui.resourceList.addItem(item)

        if self.ui.resourceList.count() > 0:
            self.ui.resourceList.item(0).setSelected(True)

    def accept(self) -> None:
        super().accept()

        new = True
        resource = self.ui.resourceList.selectedItems()[0].data(QtCore.Qt.UserRole)

        if self.ui.reuseResourceRadio.isChecked():
            new = False
            self.resname = resource.resname()
            self.filepath = resource.filepath()
            self.data = resource.data()
        elif self.ui.copyResourceRadio.isChecked():
            self.resname = self.ui.resrefEdit.text()
            self.filepath = self.ui.locationSelect.currentData()
            self.data = resource.data()
        elif self.ui.createResourceRadio.isChecked():
            self.resname = self.ui.resrefEdit.text()
            self.filepath = self.ui.locationSelect.currentData()
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
                self.data = b''

        if new:
            if self.filepath.endswith(".erf") or self.filepath.endswith(".mod"):
                erf = read_erf(self.filepath)
                erf.set(self.resname, self._restype, self.data)
                write_erf(erf, self.filepath)
            elif self.filepath.endswith(".rim"):
                rim = read_rim(self.filepath)
                rim.set(self.resname, self._restype, self.data)
                write_rim(rim, self.filepath)
            else:
                self.filepath = "{}/{}.{}".format(self.filepath, self.resname, self._restype.extension)
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
