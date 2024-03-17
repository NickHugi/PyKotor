from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QDialog, QListWidgetItem, QShortcut, QTreeWidgetItem

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.uti import UTI, UTIProperty, dismantle_uti, read_uti
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from utility.error_handling import assert_with_variable_trace, format_exception_with_variables

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal

    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTIEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initializes the Item Editor window.

        Args:
        ----
            parent: {QWidget}: The parent widget
            installation: {HTInstallation | None}: The installation object

        Processing Logic:
        ----------------
            - Initializes supported resource types
            - Calls super().__init__ to initialize base class
            - Initializes UTI object
            - Sets up UI from designer file
            - Sets up menus
            - Sets up signals
            - Sets up installation
            - Sets installation on description editor
            - Connects delete shortcut
            - Calls new() to start with a new empty item.
        """
        supported = [ResourceType.UTI]
        super().__init__(parent, "Item Editor", "item", supported, supported, installation)

        self._uti = UTI()

        if qtpy.API_NAME == "PySide2":
            pass  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            pass  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            pass  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            pass  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self.ui.descEdit.setInstallation(installation)

        QShortcut("Del", self).activated.connect(self.onDelShortcut)

        self.new()

    def _setupSignals(self):
        """Set up signal connections for UI elements."""
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
        """Sets up the installation for editing.

        Args:
        ----
            installation (HTInstallation): The installation to set up.

        Processing Logic:
        ----------------
            - Sets the installation property on the UI
            - Loads required 2DAs into the installation cache
            - Populates base item select from baseitems 2DA
            - Populates available properties list from item properties 2DA
            - Adds subproperties from subtype 2DAs to their parent properties.
        """
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)
        self.ui.descEdit.setInstallation(installation)

        required: list[str] = [HTInstallation.TwoDA_BASEITEMS, HTInstallation.TwoDA_ITEM_PROPERTIES]
        installation.htBatchCache2DA(required)

        baseitems: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        itemProperties: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)

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

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)

        uti = read_uti(data)
        self._loadUTI(uti)

    def _loadUTI(self, uti: UTI):
        """Loads a UTI object into the UI.

        Args:
        ----
            uti: UTI - The UTI object to load

        Loads UTI data:
            - Loads basic UTI data like name, description etc into corresponding UI elements.
            - Loads properties and comments from UTI object into UI lists and text editors.
        """
        self._uti = uti

        # Basic
        self.ui.nameEdit.setLocstring(uti.name)
        self.ui.descEdit.setLocstring(uti.description)
        self.ui.tagEdit.setText(uti.tag)
        self.ui.resrefEdit.setText(str(uti.resref))
        self.ui.baseSelect.setCurrentIndex(uti.base_item)
        self.ui.costSpin.setValue(uti.cost)
        self.ui.additionalCostSpin.setValue(uti.add_cost)
        self.ui.upgradeSpin.setValue(uti.upgrade_level)
        self.ui.plotCheckbox.setChecked(bool(uti.plot))
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
        """Builds a UTI object from UI input.

        Args:
        ----
            self: The object instance
        Returns:
            tuple[bytes, bytes]: Byte data and empty string

        Processing Logic:
        ----------------
            - Populate UTI object properties from UI elements
            - Convert UTI to GFF structure
            - Write GFF to byte array
            - Return byte array and empty string
        """
        uti: UTI = deepcopy(self._uti)

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

        uti.properties = [
            self.ui.assignedPropertiesList.item(i).data(QtCore.Qt.UserRole)
            for i in range(self.ui.assignedPropertiesList.count())
        ]
        # Comments
        uti.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_uti(uti)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTI(UTI())

    def changeName(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def changeDesc(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.descEdit.locstring())
        if dialog.exec_():
            self._loadLocstring(self.ui.descEdit.ui.locstringText, dialog.locstring)

    def generateTag(self):
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resname is not None and self._resname != "":
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_itm_000")

    def editSelectedProperty(self):
        if self.ui.assignedPropertiesList.selectedItems():
            utiProperty = self.ui.assignedPropertiesList.selectedItems()[0].data(QtCore.Qt.UserRole)
            dialog = PropertyEditor(self._installation, utiProperty)
            if dialog.exec_():
                self.ui.assignedPropertiesList.selectedItems()[0].setData(QtCore.Qt.UserRole, dialog.utiProperty())
                self.ui.assignedPropertiesList.selectedItems()[0].setText(self.propertySummary(dialog.utiProperty()))

    def addSelectedProperty(self):
        if not self.ui.availablePropertyList.selectedItems():
            return
        item = self.ui.availablePropertyList.selectedItems()[0]
        propertyId = item.data(0, QtCore.Qt.UserRole)
        subtypeId = item.data(0, QtCore.Qt.UserRole + 1)

        if propertyId is not None:
            self._add_property_main(propertyId, subtypeId)

    def _add_property_main(self, propertyId, subtypeId):
        """Adds a property to an item.

        Args:
        ----
            propertyId: The id of the property to add.
            subtypeId: The subtype id of the item.

        Processing Logic:
        ----------------
            - Gets the item properties table from the installation.
            - Creates a UTIProperty object and populates it with data from the table.
            - Adds a summary of the property to the assigned properties list widget.
            - Sets the UTIProperty as user data on the list item.
        """
        itemprops: TwoDA = self._installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)

        utiProperty = UTIProperty()
        utiProperty.property_name = propertyId
        utiProperty.subtype = subtypeId
        utiProperty.cost_table = itemprops.get_row(propertyId).get_integer("costtableresref", 255)
        utiProperty.cost_value = 0
        utiProperty.param1 = itemprops.get_row(propertyId).get_integer("param1resref", 255)
        utiProperty.param1_value = 0
        utiProperty.chance_appear = 100

        text: str = self.propertySummary(utiProperty)
        item = QListWidgetItem(text)
        item.setData(QtCore.Qt.UserRole, utiProperty)
        self.ui.assignedPropertiesList.addItem(item)

    def removeSelectedProperty(self):
        if self.ui.assignedPropertiesList.selectedItems():
            index = self.ui.assignedPropertiesList.selectedIndexes()[0]
            self.ui.assignedPropertiesList.takeItem(index.row())

    def propertySummary(self, utiProperty: UTIProperty) -> str:
        """Retrieve the property, subproperty and cost names from the UTIEditor.

        Processing Logic:
        ----------------
            - It returns a formatted string combining the retrieved names.
            - If a cost or subproperty is not present, it is omitted from the returned string.
        """
        propName: str = UTIEditor.propertyName(self._installation, utiProperty.property_name)
        subpropName: str | None = UTIEditor.subpropertyName(self._installation, utiProperty.property_name, utiProperty.subtype)
        costName: str | None = UTIEditor.costName(self._installation, utiProperty.cost_table, utiProperty.cost_value)

        if costName and subpropName:
            return f"{propName}: {subpropName} [{costName}]"
        if subpropName:
            return f"{propName}: {subpropName}"
        if costName:
            return f"{propName}: [{costName}]"
        return f"{propName}"

    def onUpdateIcon(self):
        baseItem: int = self.ui.baseSelect.currentIndex()
        modelVariation: int = self.ui.modelVarSpin.value()
        textureVariation: int = self.ui.textureVarSpin.value()
        self.ui.iconLabel.setPixmap(self._installation.getItemIcon(baseItem, modelVariation, textureVariation))

    def onAvaialblePropertyListDoubleClicked(self):
        for item in self.ui.availablePropertyList.selectedItems():
            if item.childCount() == 0:
                self.addSelectedProperty()

    def onAssignedPropertyListDoubleClicked(self):
        self.editSelectedProperty()

    def onDelShortcut(self):
        if self.ui.assignedPropertiesList.hasFocus():
            self.removeSelectedProperty()

    @staticmethod
    def propertyName(installation: HTInstallation, prop: int) -> str:
        properties: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)
        stringref: int | None = properties.get_row(prop).get_integer("name")
        assert stringref is not None, assert_with_variable_trace(stringref is not None)
        return installation.talktable().string(stringref)

    @staticmethod
    def subpropertyName(installation: HTInstallation, prop: int, subprop: int) -> None | str:
        """Gets the name of a subproperty of an item property.

        Args:
        ----
            installation: HTInstallation - The installation object
            prop: int - The property index
            subprop: int - The subproperty index.

        Returns:
        -------
            string - The name of the subproperty

        Processing Logic:
        ----------------
            - Gets the item properties 2DA from the cache
            - Gets the subtype resource reference from the property row
            - Gets the subproperties 2DA from the subtype resource
            - Gets the name string reference from the subproperty row
            - Returns the string from the talktable or the label if name is None
        """
        properties: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_ITEM_PROPERTIES)
        subtypeResname: str = properties.get_cell(prop, "subtyperesref")
        if not subtypeResname:
            return None
        subproperties: TwoDA = installation.htGetCache2DA(subtypeResname)
        headerStrref: Literal["name", "string_ref"] = "name" if "name" in subproperties.get_headers() else "string_ref"
        nameStrref: int | None = subproperties.get_row(subprop).get_integer(headerStrref)
        return (
            installation.talktable().string(nameStrref)
            if nameStrref is not None
            else subproperties.get_cell(subprop, "label")
        )

    @staticmethod
    def costName(installation: HTInstallation, cost: int, value: int):
        try:
            costtableList: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_IPRP_COSTTABLE)
            costtable: TwoDA = installation.htGetCache2DA(costtableList.get_cell(cost, "name"))
            stringref: int | None = costtable.get_row(value).get_integer("name")
            return installation.talktable().string(stringref)  # FIXME: stringref is None in many occasions
        except Exception as e:
            print(format_exception_with_variables(e, message="This exception has been suppressed"))
        return None

    @staticmethod
    def paramName(installation: HTInstallation, paramtable: int, param: int):
        try:
            paramtableList: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_IPRP_PARAMTABLE)
            paramtable_twoda: TwoDA = installation.htGetCache2DA(paramtableList.get_cell(paramtable, "tableresref"))
            stringref: int | None = paramtable_twoda.get_row(param).get_integer("name")
            return installation.talktable().string(stringref)
        except Exception as e:
            print(format_exception_with_variables(e, message="This exception has been suppressed."))
        return None


class PropertyEditor(QDialog):
    def __init__(self, installation: HTInstallation, utiProperty: UTIProperty):
        """Initializes the UTI property editor dialog.

        Args:
        ----
            installation: {HTInstallation object}: The installation object
            utiProperty: {UTIProperty object}: The UTI property object

        Processing Logic:
        ----------------
            - Connects UI elements to callback functions
            - Populates cost and parameter lists from installation data
            - Populates upgrade dropdown from installation data
            - Sets initial values of textboxes from utiProperty.
        """
        super().__init__()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.property import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.property import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.property import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.property import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.costSelectButton.clicked.connect(self.selectCost)
        self.ui.parameterSelectButton.clicked.connect(self.selectParam)
        self.ui.costList.doubleClicked.connect(self.selectCost)
        self.ui.parameterList.doubleClicked.connect(self.selectParam)

        self._installation = installation
        self._utiProperty: UTIProperty = utiProperty

        costtableList = installation.htGetCache2DA(HTInstallation.TwoDA_IPRP_COSTTABLE)
        if utiProperty.cost_table != 0xFF:  # noqa: PLR2004
            costtable = installation.htGetCache2DA(costtableList.get_cell(utiProperty.cost_table, "name"))
            for i in range(costtable.get_height()):
                item = QListWidgetItem(UTIEditor.costName(installation, utiProperty.cost_table, i))
                item.setData(QtCore.Qt.UserRole, i)
                self.ui.costList.addItem(item)

        if utiProperty.param1 != 0xFF:  # noqa: PLR2004
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

    def reloadTextboxes(self):
        """Reloads textboxes with property names."""
        propertyName: str = UTIEditor.propertyName(self._installation, self._utiProperty.property_name)
        self.ui.propertyEdit.setText(propertyName or "")

        subpropertyName: str | None = UTIEditor.subpropertyName(self._installation, self._utiProperty.property_name, self._utiProperty.subtype)
        self.ui.subpropertyEdit.setText(subpropertyName or "")

        costName: str | None = UTIEditor.costName(self._installation, self._utiProperty.cost_table, self._utiProperty.cost_value)
        self.ui.costEdit.setText(costName or "")

        paramName: str | None = UTIEditor.paramName(self._installation, self._utiProperty.param1, self._utiProperty.param1_value)
        self.ui.parameterEdit.setText(paramName or "")

    def selectCost(self):
        if not self.ui.costList.currentItem():
            return

        self._utiProperty.cost_value = self.ui.costList.currentItem().data(QtCore.Qt.UserRole)
        self.reloadTextboxes()

    def selectParam(self):
        if not self.ui.parameterList.currentItem():
            return

        self._utiProperty.param1_value = self.ui.parameterList.currentItem().data(QtCore.Qt.UserRole)
        self.reloadTextboxes()

    def utiProperty(self) -> UTIProperty:
        self._utiProperty.upgrade_type = self.ui.upgradeSelect.currentIndex() - 1
        if self.ui.upgradeSelect.currentIndex() == 0:
            self._utiProperty.upgrade_type = None
        return self._utiProperty
