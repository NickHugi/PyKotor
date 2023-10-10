from __future__ import annotations

from contextlib import suppress
from typing import Optional

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QDialog,
    QListWidgetItem,
    QShortcut,
    QTreeWidgetItem,
    QWidget,
)

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.uti import UTI, UTIProperty, dismantle_uti, read_uti
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor


class UTIEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.UTI]
        super().__init__(parent, "Item Editor", "item", supported, supported, installation)

        self._uti = UTI()

        from toolset.uic.editors.uti import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self.ui.descEdit.setInstallation(installation)

        QShortcut("Del", self).activated.connect(self.onDelShortcut)

        self.new()

    def _setupSignals(self) -> None:
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.editPropertyButton.clicked.connect(self.editSelectedProperty)
        self.ui.removePropertyButton.clicked.connect(self.removeSelectedProperty)
        self.ui.addPropertyButton.clicked.connect(self.addSelectedProperty)
        self.ui.availablePropertyList.doubleClicked.connect(self.onAvaialblePropertyListDoubleClicked)
        self.ui.assignedPropertiesList.doubleClicked.connect(self.onAssignedPropertyListDoubleClicked)

        self.ui.modelVarSpin.valueChanged.connect(self.onUpdateIcon)
        self.ui.bodyVarSpin.valueChanged.connect(self.onUpdateIcon)
        self.ui.textureVarSpin.valueChanged.connect(self.onUpdateIcon)
        self.ui.baseSelect.currentIndexChanged.connect(self.onUpdateIcon)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)
        self.ui.descEdit.setInstallation(installation)

        required = [HTInstallation.TwoDA_BASEITEMS, HTInstallation.TwoDA_ITEM_PROPERTIES]
        installation.htBatchCache2DA(required)

        baseitems = installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        itemProperties = installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)

        self.ui.baseSelect.clear()
        self.ui.baseSelect.setItems(baseitems.get_column("label"))

        self.ui.availablePropertyList.clear()
        for i in range(itemProperties.get_height()):
            item = QTreeWidgetItem([UTIEditor.propertyName(installation, i)])
            self.ui.availablePropertyList.addTopLevelItem(item)

            subtypeResname = itemProperties.get_cell(i, "subtyperesref")
            if subtypeResname == "":
                item.setData(0, QtCore.Qt.UserRole, i)
                item.setData(0, QtCore.Qt.UserRole + 1, i)
                continue

            subtype = installation.htGetCache2DA(subtypeResname)
            for j in range(subtype.get_height()):
                if subtypeResname == "spells":
                    print("   ", j)
                name = UTIEditor.subpropertyName(installation, i, j)
                child = QTreeWidgetItem([name])
                child.setData(0, QtCore.Qt.UserRole, i)
                child.setData(0, QtCore.Qt.UserRole + 1, j)
                item.addChild(child)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        uti = read_uti(data)
        self._loadUTI(uti)

    def _loadUTI(self, uti: UTI):
        self._uti = uti

        # Basic
        self.ui.nameEdit.setLocstring(uti.name)
        self.ui.descEdit.setLocstring(uti.description)
        self.ui.tagEdit.setText(uti.tag)
        self.ui.resrefEdit.setText(uti.resref.get())
        self.ui.baseSelect.setCurrentIndex(uti.base_item)
        self.ui.costSpin.setValue(uti.cost)
        self.ui.additionalCostSpin.setValue(uti.add_cost)
        self.ui.upgradeSpin.setValue(uti.upgrade_level)
        self.ui.plotCheckbox.setChecked(uti.plot)
        self.ui.chargesSpin.setValue(uti.charges)
        self.ui.stackSpin.setValue(uti.stack_size)
        self.ui.modelVarSpin.setValue(uti.model_variation)
        self.ui.bodyVarSpin.setValue(uti.body_variation)
        self.ui.textureVarSpin.setValue(uti.texture_variation)

        # Properties
        self.ui.assignedPropertiesList.clear()
        for utiProperty in uti.properties:
            text = self.propertySummary(utiProperty)
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, utiProperty)
            self.ui.assignedPropertiesList.addItem(item)

        # Comments
        self.ui.commentsEdit.setPlainText(uti.comment)

    def build(self) -> tuple[bytes, bytes]:
        uti = self._uti

        # Basic
        uti.name = self.ui.nameEdit.locstring()
        uti.description = self.ui.descEdit.locstring()
        uti.tag = self.ui.tagEdit.text()
        uti.resref = ResRef(self.ui.resrefEdit.text())
        uti.base_item = self.ui.baseSelect.currentIndex()
        uti.cost = self.ui.costSpin.value()
        uti.add_cost = self.ui.additionalCostSpin.value()
        uti.upgrade_level = self.ui.upgradeSpin.value()
        uti.plot = self.ui.plotCheckbox.isChecked()
        uti.charges = self.ui.chargesSpin.value()
        uti.stack_size = self.ui.stackSpin.value()
        uti.model_variation = self.ui.modelVarSpin.value()
        uti.body_variation = self.ui.bodyVarSpin.value()
        uti.texture_variation = self.ui.textureVarSpin.value()

        # Properties
        uti.properties = []
        for i in range(self.ui.assignedPropertiesList.count()):
            uti.properties.append(self.ui.assignedPropertiesList.item(i).data(QtCore.Qt.UserRole))

        # Comments
        uti.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_uti(uti)
        write_gff(gff, data)

        return data, b""

    def new(self) -> None:
        super().new()
        self._loadUTI(UTI())

    def changeName(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit, dialog.locstring)

    def changeDesc(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.descEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.descEdit, dialog.locstring)

    def generateTag(self) -> None:
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self) -> None:
        if self._resref is not None and self._resref != "":
            self.ui.resrefEdit.setText(self._resref)
        else:
            self.ui.resrefEdit.setText("m00xx_itm_000")

    def editSelectedProperty(self) -> None:
        if self.ui.assignedPropertiesList.selectedItems():
            utiProperty = self.ui.assignedPropertiesList.selectedItems()[0].data(QtCore.Qt.UserRole)
            dialog = PropertyEditor(self._installation, utiProperty)
            if dialog.exec_():
                self.ui.assignedPropertiesList.selectedItems()[0].setData(QtCore.Qt.UserRole, dialog.utiProperty())
                self.ui.assignedPropertiesList.selectedItems()[0].setText(self.propertySummary(dialog.utiProperty()))

    def addSelectedProperty(self) -> None:
        if self.ui.availablePropertyList.selectedItems():
            item = self.ui.availablePropertyList.selectedItems()[0]
            propertyId = item.data(0, QtCore.Qt.UserRole)
            subtypeId = item.data(0, QtCore.Qt.UserRole + 1)

            if propertyId is not None:
                itemprops = self._installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)

                utiProperty = UTIProperty()
                utiProperty.property_name = propertyId
                utiProperty.subtype = subtypeId
                utiProperty.cost_table = itemprops.get_row(propertyId).get_integer("costtableresref", 255)
                utiProperty.cost_value = 0
                utiProperty.param1 = itemprops.get_row(propertyId).get_integer("param1resref", 255)
                utiProperty.param1_value = 0
                utiProperty.chance_appear = 100

                text = self.propertySummary(utiProperty)
                item = QListWidgetItem(text)
                item.setData(QtCore.Qt.UserRole, utiProperty)
                self.ui.assignedPropertiesList.addItem(item)

    def removeSelectedProperty(self) -> None:
        if self.ui.assignedPropertiesList.selectedItems():
            index = self.ui.assignedPropertiesList.selectedIndexes()[0]
            self.ui.assignedPropertiesList.takeItem(index.row())

    def propertySummary(self, utiProperty: UTIProperty) -> str:
        propName = UTIEditor.propertyName(self._installation, utiProperty.property_name)
        subpropName = UTIEditor.subpropertyName(self._installation, utiProperty.property_name, utiProperty.subtype)
        costName = UTIEditor.costName(self._installation, utiProperty.cost_table, utiProperty.cost_value)

        if costName and subpropName:
            text = f"{propName}: {subpropName} [{costName}]"
        elif subpropName:
            text = f"{propName}: {subpropName}"
        elif costName:
            text = f"{propName}: [{costName}]"
        else:
            text = f"{propName}"

        return text

    def onUpdateIcon(self) -> None:
        baseItem = self.ui.baseSelect.currentIndex()
        modelVariation = self.ui.modelVarSpin.value()
        textureVariation = self.ui.textureVarSpin.value()
        self.ui.iconLabel.setPixmap(self._installation.getItemIcon(baseItem, modelVariation, textureVariation))

    def onAvaialblePropertyListDoubleClicked(self) -> None:
        for item in self.ui.availablePropertyList.selectedItems():
            if item.childCount() == 0:
                self.addSelectedProperty()

    def onAssignedPropertyListDoubleClicked(self) -> None:
        self.editSelectedProperty()

    def onDelShortcut(self) -> None:
        if self.ui.assignedPropertiesList.hasFocus():
            self.removeSelectedProperty()

    @staticmethod
    def propertyName(installation: HTInstallation, prop: int):
        properties = installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)
        stringref = properties.get_row(prop).get_integer("name")
        return installation.talktable().string(stringref)

    @staticmethod
    def subpropertyName(installation: HTInstallation, prop: int, subprop: int):
        properties = installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)
        subtypeResname = properties.get_cell(prop, "subtyperesref")
        if subtypeResname == "":
            return None
        subproperties = installation.htGetCache2DA(subtypeResname)
        headerStrref = "name" if "name" in subproperties.get_headers() else "string_ref"
        nameStrref = subproperties.get_row(subprop).get_integer(headerStrref)
        return installation.talktable().string(nameStrref) if nameStrref is not None else subproperties.get_cell(subprop, "label")

    @staticmethod
    def costName(installation: HTInstallation, cost: int, value: int):
        with suppress(Exception):
            costtableList = installation.htGetCache2DA(HTInstallation.TwoDA_IPRP_COSTTABLE)
            costtable = installation.htGetCache2DA(costtableList.get_cell(cost, "name"))
            stringref = costtable.get_row(value).get_integer("name")
            return installation.talktable().string(stringref)
        return None

    @staticmethod
    def paramName(installation: HTInstallation, paramtable: int, param: int):
        with suppress(Exception):
            paramtableList = installation.htGetCache2DA(HTInstallation.TwoDA_IPRP_PARAMTABLE)
            paramtable = installation.htGetCache2DA(paramtableList.get_cell(paramtable, "tableresref"))
            stringref = paramtable.get_row(param).get_integer("name")
            return installation.talktable().string(stringref)
        return None


class PropertyEditor(QDialog):
    def __init__(self, installation: HTInstallation, utiProperty: UTIProperty):
        super().__init__()

        from toolset.uic.dialogs.property import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.costSelectButton.clicked.connect(self.selectCost)
        self.ui.parameterSelectButton.clicked.connect(self.selectParam)
        self.ui.costList.doubleClicked.connect(self.selectCost)
        self.ui.parameterList.doubleClicked.connect(self.selectParam)

        self._installation = installation
        self._utiProperty: UTIProperty = utiProperty

        costtableList = installation.htGetCache2DA(HTInstallation.TwoDA_IPRP_COSTTABLE)
        if utiProperty.cost_table != 255:
            costtable = installation.htGetCache2DA(costtableList.get_cell(utiProperty.cost_table, "name"))
            for i in range(costtable.get_height()):
                item = QListWidgetItem(UTIEditor.costName(installation, utiProperty.cost_table, i))
                item.setData(QtCore.Qt.UserRole, i)
                self.ui.costList.addItem(item)

        if utiProperty.param1 != 0xFF:
            paramList = installation.htGetCache2DA(HTInstallation.TwoDA_IPRP_PARAMTABLE)
            paramtable = installation.htGetCache2DA(paramList.get_cell(utiProperty.param1, "tableresref"))
            for i in range(paramtable.get_height()):
                item = QListWidgetItem(UTIEditor.paramName(installation, utiProperty.param1, i))
                item.setData(QtCore.Qt.UserRole, i)
                self.ui.parameterList.addItem(item)

        upgrades = installation.htGetCache2DA(HTInstallation.TwoDA_UPGRADES)
        self.ui.upgradeSelect.addItem("[None]", None)
        for i in range(upgrades.get_height()):
            text = upgrades.get_cell(i, "label").replace("_", " ").title()
            self.ui.upgradeSelect.addItem(text, i)
        if utiProperty.upgrade_type is not None:
            self.ui.upgradeSelect.setCurrentIndex(utiProperty.upgrade_type + 1)

        self.reloadTextboxes()

    def reloadTextboxes(self) -> None:
        propertyName = UTIEditor.propertyName(self._installation, self._utiProperty.property_name)
        self.ui.propertyEdit.setText(propertyName if propertyName else "")

        subpropertyName = UTIEditor.subpropertyName(
            self._installation,
            self._utiProperty.property_name,
            self._utiProperty.subtype,
        )
        self.ui.subpropertyEdit.setText(subpropertyName if subpropertyName else "")

        costName = UTIEditor.costName(self._installation, self._utiProperty.cost_table, self._utiProperty.cost_value)
        self.ui.costEdit.setText(costName if costName else "")

        paramName = UTIEditor.paramName(self._installation, self._utiProperty.param1, self._utiProperty.param1_value)
        self.ui.parameterEdit.setText(paramName if paramName else "")

    def selectCost(self) -> None:
        if not self.ui.costList.currentItem():
            return

        self._utiProperty.cost_value = self.ui.costList.currentItem().data(QtCore.Qt.UserRole)
        self.reloadTextboxes()

    def selectParam(self) -> None:
        if not self.ui.parameterList.currentItem():
            return

        self._utiProperty.param1_value = self.ui.parameterList.currentItem().data(QtCore.Qt.UserRole)
        self.reloadTextboxes()

    def utiProperty(self) -> UTIProperty:
        self._utiProperty.upgrade_type = self.ui.upgradeSelect.currentIndex() - 1
        if self.ui.upgradeSelect.currentIndex() == 0:
            self._utiProperty.upgrade_type = None
        return self._utiProperty
