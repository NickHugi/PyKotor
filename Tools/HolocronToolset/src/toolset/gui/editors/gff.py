from __future__ import annotations

from typing import TYPE_CHECKING, Any

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QSortFilterProxyModel
from qtpy.QtGui import QBrush, QColor, QFont, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QFileDialog, QLabel, QListWidgetItem, QMenu, QPushButton, QShortcut, QSizePolicy, QVBoxLayout

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import ResRef
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct, read_gff, write_gff
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QItemSelectionRange, QModelIndex
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation

_VALUE_NODE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
_TYPE_NODE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2
_LABEL_NODE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 3

_ID_SUBSTRING_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
_TEXT_SUBSTRING_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2


class GFFEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported: list[ResourceType] = [restype for restype in ResourceType if restype.contents == "gff"]
        super().__init__(parent, "GFF Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        self._talktable: TalkTable | None = installation.talktable() if installation else None
        self._gff_content: GFFContent | None = None

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.gff import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.gff import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.gff import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.gff import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ui.treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)  # type: ignore[arg-type]

        self.ui.treeView.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)  # type: ignore[arg-type]
        self.ui.treeView.setSortingEnabled(True)

        # Make the right panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setupSignals(self):
        """Sets up signals and connections for the GUI.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Connects actions to methods like selecting talk tables
            - Sets up models and views for the tree widget
            - Connects editing signals from widgets to updateData()
            - Connects context menu requests
            - Connects type combo box changes.
        """
        self.ui.actionSetTLK.triggered.connect(self.selectTalkTable)

        self.model: QStandardItemModel = QStandardItemModel(self)
        self.proxyModel: QSortFilterProxyModel = GFFSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        self.ui.treeView.setModel(self.proxyModel)

        self.ui.treeView.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.ui.intSpin.editingFinished.connect(self.updateData)
        self.ui.floatSpin.editingFinished.connect(self.updateData)
        self.ui.lineEdit.editingFinished.connect(self.updateData)
        self.ui.textEdit.textChanged.connect(self.updateData)
        self.ui.xVec3Spin.editingFinished.connect(self.updateData)
        self.ui.yVec3Spin.editingFinished.connect(self.updateData)
        self.ui.zVec3Spin.editingFinished.connect(self.updateData)
        self.ui.xVec4Spin.editingFinished.connect(self.updateData)
        self.ui.yVec4Spin.editingFinished.connect(self.updateData)
        self.ui.zVec4Spin.editingFinished.connect(self.updateData)
        self.ui.wVec4Spin.editingFinished.connect(self.updateData)
        self.ui.labelEdit.editingFinished.connect(self.updateData)

        self.ui.stringrefSpin.valueChanged.connect(self.changeLocstringText)
        self.ui.stringrefSpin.editingFinished.connect(self.updateData)
        self.ui.substringList.itemSelectionChanged.connect(self.substringSelected)
        self.ui.addSubstringButton.clicked.connect(self.addSubstring)
        self.ui.removeSubstringButton.clicked.connect(self.removeSubstring)
        self.ui.substringEdit.textChanged.connect(self.substringEdited)

        self.ui.treeView.customContextMenuRequested.connect(self.requestContextMenu)

        self.ui.typeCombo.activated.connect(self.typeChanged)

        QShortcut("Del", self).activated.connect(self.removeSelectedNodes)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Loads resource data from a file into the model.

        Args:
        ----
            filepath: {Path or filename to load from}
            resref: {Unique identifier for resource}
            restype: {Type of resource}
            data: {Resource data}.

        Processing Logic:
        ----------------
            - Reads GFF data structure from loaded bytes
            - Clears existing model data
            - Sets model column count to 1
            - Adds root node to model
            - Recursively loads GFF structure into model from root node
            - Expands root node in tree view after loading.
        """
        super().load(filepath, resref, restype, data)
        gff: GFF = read_gff(data)
        self._gff_content = gff.content

        self.model.clear()
        self.model.setColumnCount(1)

        rootNode = QStandardItem("[ROOT]")
        self.applyPalette(rootNode, GFFFieldType.Struct)
        #rootNode.setForeground(QBrush(QColor(0x660000)))
        self.model.appendRow(rootNode)
        self._load_struct(rootNode, gff.root)

        sourceIndex = self.model.indexFromItem(rootNode)
        proxyIndex = self.proxyModel.mapFromSource(sourceIndex)
        self.ui.treeView.expand(proxyIndex)  # type: ignore[arg-type]

    def _load_struct(self, node: QStandardItem, gffStruct: GFFStruct):
        """Loads a GFFStruct into a QStandardItem node.

        Args:
        ----
            node: QStandardItem - The parent node to load the struct into
            gffStruct: GFFStruct - The struct to load

        Processing Logic:
        ----------------
            - Loops through each field in the struct
            - Creates a child node for each field
            - Sets the node type, label and value
            - Handles list and struct field types recursively
            - Appends the child node to the parent node.
        """
        for label, ftype, value in gffStruct:
            childNode = QStandardItem("")
            childNode.setData(ftype, _TYPE_NODE_ROLE)
            childNode.setData(label, _LABEL_NODE_ROLE)

            if ftype == GFFFieldType.List:
                self.applyPalette(childNode, GFFFieldType.List)
                #childNode.setForeground(QBrush(QColor(0x000088)))
                self._load_list(childNode, value)
            elif ftype == GFFFieldType.Struct:
                self.applyPalette(childNode, GFFFieldType.Struct)
                #childNode.setForeground(QBrush(QColor(0x660000)))
                childNode.setData(value.struct_id, _VALUE_NODE_ROLE)
                self._load_struct(childNode, value)
            else:
                childNode.setData(value, _VALUE_NODE_ROLE)

            self.applyPalette(node, GFFFieldType.Struct)
            self.refreshItemText(childNode)
            node.appendRow(childNode)

    def _load_list(self, node: QStandardItem, gffList: GFFList):
        """Load GFF data into a tree view.

        Args:
        ----
            node: QStandardItem - Parent node to add children
            gffList: GFFList - List of GFF structures to load

        Processing Logic:
        ----------------
            - Loop through each GFF structure in the list
            - Create a child node for each structure
            - Set the node text and color
            - Add the node to the parent node
            - Load any child data for the structure into the node.
        """
        for gffStruct in gffList:
            childNode = QStandardItem("")
            self.applyPalette(childNode, GFFFieldType.Struct)
            #childNode.setForeground(QBrush(QColor(0x660000)))
            childNode.setData(gffStruct.struct_id, _VALUE_NODE_ROLE)
            node.appendRow(childNode)
            self.refreshItemText(childNode)
            self._load_struct(childNode, gffStruct)

        self.applyPalette(node, GFFFieldType.List)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a GFF file from the model.

        Args:
        ----
            self: The object calling the function.

        Returns:
        -------
            bytes: The built GFF file
            bytes: An empty byte array (superclass uses for mdx)
        """
        gff_content = self._gff_content or GFFContent.from_res(self._resname or "")
        gff_type = ResourceType.GFF

        gff = GFF(gff_content)
        self._build_struct(self.model.item(0, 0), gff.root)

        data = bytearray()
        write_gff(gff, data, gff_type)
        return data, b""

    def _build_struct(self, item: QStandardItem, gffStruct: GFFStruct):
        """Builds a GFF structure from a QStandardItem model.

        Args:
        ----
            item: QStandardItem - Item containing node data
            gffStruct: GFFStruct - Structure to populate.

        Processing Logic:
        ----------------
            - Loops through each child node of the item
            - Gets label, value, and type from node data
            - Calls corresponding set method on gffStruct based on type
            - Recursively builds child structures and lists.
        """
        for i in range(item.rowCount()):
            child: QStandardItem | None = item.child(i, 0)
            label = child.data(_LABEL_NODE_ROLE)
            value = child.data(_VALUE_NODE_ROLE)
            ftype = child.data(_TYPE_NODE_ROLE)

            if ftype == GFFFieldType.UInt8:
                gffStruct.set_uint8(label, value)
            if ftype == GFFFieldType.UInt16:
                gffStruct.set_uint16(label, value)
            if ftype == GFFFieldType.UInt32:
                gffStruct.set_uint32(label, value)
            if ftype == GFFFieldType.UInt64:
                gffStruct.set_uint64(label, value)
            if ftype == GFFFieldType.Int8:
                gffStruct.set_int8(label, value)
            if ftype == GFFFieldType.Int16:
                gffStruct.set_int16(label, value)
            if ftype == GFFFieldType.Int32:
                gffStruct.set_int32(label, value)
            if ftype == GFFFieldType.Int64:
                gffStruct.set_int64(label, value)
            if ftype == GFFFieldType.Single:
                gffStruct.set_single(label, value)
            if ftype == GFFFieldType.Double:
                gffStruct.set_double(label, value)
            if ftype == GFFFieldType.ResRef:
                gffStruct.set_resref(label, value)
            if ftype == GFFFieldType.String:
                gffStruct.set_string(label, value)
            if ftype == GFFFieldType.LocalizedString:
                gffStruct.set_locstring(label, value)
            if ftype == GFFFieldType.Binary:
                gffStruct.set_binary(label, value)
            if ftype == GFFFieldType.Vector3:
                gffStruct.set_vector3(label, value)
            if ftype == GFFFieldType.Vector4:
                gffStruct.set_vector4(label, value)

            if ftype == GFFFieldType.Struct:
                childGffStruct = GFFStruct(value)
                gffStruct.set_struct(label, childGffStruct)
                self._build_struct(child, childGffStruct)

            if ftype == GFFFieldType.List:
                childGffList = GFFList()
                gffStruct.set_list(label, childGffList)
                self._build_list(child, childGffList)

    def _build_list(self, item: QStandardItem, gffList: GFFList):
        """Builds a list of GFF structures from a QStandardItem tree.

        Args:
        ----
            item: QStandardItem: The root item of the tree
            gffList: GFFList: The list to populate.

        Processing Logic:
        ----------------
            - Loops through each child row of the item
            - Gets the struct ID from the child data
            - Adds a new GFF structure to the list with that ID
            - Recursively builds the child structure.
        """
        for i in range(item.rowCount()):
            child = item.child(i, 0)
            assert child is not None, f"child cannot be None in {self!r}._build_list({item!r}, {gffList!r})"
            struct_id = child.data(_VALUE_NODE_ROLE)
            gffStruct: GFFStruct = gffList.add(struct_id)
            self._build_struct(child, gffStruct)

    def new(self):
        super().new()
        self.model.clear()
        self.model.setColumnCount(1)

        rootNode = QStandardItem("[ROOT]")
        self.applyPalette(rootNode, GFFFieldType.Struct)
        #rootNode.setForeground(QBrush(QColor(0x660000)))
        self.model.appendRow(rootNode)

    def selectionChanged(self, selected: QItemSelectionRange):
        """Updates UI when selection changes in view.

        Args:
        ----
            selected: QItemSelectionRange: The currently selected item range

        Processes selection change:
            - Gets the proxy index of the selected item
            - Maps the proxy index to the source index
            - Gets the item from the source model using the source index
            - Loads the selected item into the UI.
        """
        proxyIndex = selected.indexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)
        assert item is not None
        self.loadItem(item)

    def loadItem(self, item: QListWidgetItem):
        """Load item into UI widgets.

        Args:
        ----
            item: QListWidgetItem: Item to load.

        Load item data into UI widgets:
            - Set current widget based on field type
            - Populate spinboxes, line edits, text edits with value
            - Populate dropdowns and lists
            - Handle specialized types like vectors and localized strings.
        """

        def set_spinbox(minv: int, maxv: int, item: QListWidgetItem):
            self.ui.pages.setCurrentWidget(self.ui.intPage)
            self.ui.intSpin.setRange(minv, maxv)
            self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))

        if item.data(_TYPE_NODE_ROLE) is None:  # Field-less struct (root or in list)
            self.ui.fieldBox.setEnabled(False)
            set_spinbox(-1, 0xFFFFFFFF, item)
            return
        if self.ui.blankPage.layout() is not None:
            while self.ui.blankPage.layout().count():
                child = self.ui.blankPage.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        self.ui.fieldBox.setEnabled(True)
        self.ui.typeCombo.setCurrentText(item.data(_TYPE_NODE_ROLE).name)
        self.ui.labelEdit.setText(item.data(_LABEL_NODE_ROLE))

        if item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int8:
            set_spinbox(-0x80, 0x7F, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int16:
            set_spinbox(-0x8000, 0x7FFF, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int32:
            set_spinbox(-0x80000000, 0x7FFFFFFF, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int64:
            set_spinbox(-0x8000000000000000, 0x7FFFFFFFFFFFFFFF, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt8:
            set_spinbox(0, 0xFF, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt16:
            set_spinbox(0, 0xFFFF, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt32:
            set_spinbox(0, 0xFFFFFFFF, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt64:
            set_spinbox(0, 0xFFFFFFFFFFFFFFFF, item)
        elif item.data(_TYPE_NODE_ROLE) in {GFFFieldType.Double, GFFFieldType.Single}:
            self.ui.pages.setCurrentWidget(self.ui.floatPage)
            self.ui.floatSpin.setValue(item.data(_VALUE_NODE_ROLE))
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.ResRef:
            self.ui.pages.setCurrentWidget(self.ui.linePage)
            self.ui.lineEdit.setText(str(item.data(_VALUE_NODE_ROLE)))
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.String:
            self.ui.pages.setCurrentWidget(self.ui.textPage)
            self.ui.textEdit.setPlainText(str(item.data(_VALUE_NODE_ROLE)))
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Struct:
            set_spinbox(-1, 0xFFFFFFFF, item)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.List:
            self.ui.pages.setCurrentWidget(self.ui.blankPage)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Vector3:
            self.ui.pages.setCurrentWidget(self.ui.vector3Page)
            vec3: Vector3 = item.data(_VALUE_NODE_ROLE)
            self.ui.xVec3Spin.setValue(vec3.x)
            self.ui.yVec3Spin.setValue(vec3.y)
            self.ui.zVec3Spin.setValue(vec3.z)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Vector4:
            self.ui.pages.setCurrentWidget(self.ui.vector4Page)
            vec4: Vector4 = item.data(_VALUE_NODE_ROLE)
            self.ui.xVec4Spin.setValue(vec4.x)
            self.ui.yVec4Spin.setValue(vec4.y)
            self.ui.zVec4Spin.setValue(vec4.z)
            self.ui.wVec4Spin.setValue(vec4.w)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Binary:
            binaryData: bytes = item.data(_VALUE_NODE_ROLE)
            self.ui.pages.setCurrentWidget(self.ui.blankPage)
            if self.ui.blankPage.layout() is None:
                layout = QVBoxLayout(self.ui.blankPage)
                self.ui.blankPage.setLayout(layout)
            else:
                while self.ui.blankPage.layout().count():
                    child = self.ui.blankPage.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            hexDataStr = " ".join(f"{b:02X}" for b in binaryData)
            binaryDataLabel = QLabel(f"{hexDataStr}")
            binaryDataLabel.setWordWrap(True)
            binaryDataLabel.setFont(QFont("Courier New", 7))
            binaryDataLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            binaryDataLabel.setMaximumWidth(self.ui.blankPage.width() - 20)  # -20 otherwise the pane grows for some reason.
            self.ui.blankPage.layout().addWidget(binaryDataLabel)
            copyButton = QPushButton("Copy Binary Data")
            self.ui.blankPage.layout().addWidget(copyButton)
            copyButton.clicked.connect(lambda: QApplication.clipboard().setText(hexDataStr))
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.LocalizedString:
            locstring: LocalizedString = item.data(_VALUE_NODE_ROLE)
            self.ui.pages.setCurrentWidget(self.ui.substringPage)
            self.ui.substringEdit.setEnabled(False)
            self.ui.stringrefSpin.setValue(locstring.stringref)
            self.ui.substringList.clear()
            for language, gender, text in locstring:
                item = QListWidgetItem(f"{language.name.title()}, {gender.name.title()}")
                item.setData(_TEXT_SUBSTRING_ROLE, text)
                item.setData(_ID_SUBSTRING_ROLE, LocalizedString.substring_id(language, gender))
                self.ui.substringList.addItem(item)

    def updateData(self):
        """Updates data in the GFF tree model.

        Args:
        ----
            self: The class instance

        Updates the selected item's:
        - Label
        - Value based on type:
            - Integer, float, string, vector, etc
        - Refreshes the item text
        """
        if not self.ui.treeView.selectedIndexes():
            return

        proxyIndex = self.ui.treeView.selectedIndexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)

        item.setData(self.ui.labelEdit.text(), _LABEL_NODE_ROLE)

        if item.data(_TYPE_NODE_ROLE) in {
            GFFFieldType.UInt8,
            GFFFieldType.Int8,
            GFFFieldType.UInt16,
            GFFFieldType.Int16,
            GFFFieldType.UInt32,
            GFFFieldType.Int32,
            GFFFieldType.UInt64,
            GFFFieldType.Int64,
        }:
            item.setData(self.ui.intSpin.value(), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) in {GFFFieldType.Single, GFFFieldType.Double}:
            item.setData(self.ui.floatSpin.value(), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.ResRef:
            item.setData(ResRef(self.ui.lineEdit.text()), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.String:
            item.setData(self.ui.textEdit.toPlainText(), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Vector3:
            vec3 = Vector3(self.ui.xVec3Spin.value(), self.ui.yVec3Spin.value(), self.ui.zVec3Spin.value())
            item.setData(vec3, _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Vector4:
            vec4 = Vector4(self.ui.xVec4Spin.value(), self.ui.yVec4Spin.value(), self.ui.zVec4Spin.value(), self.ui.wVec4Spin.value())
            item.setData(vec4, _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.LocalizedString:
            item.data(_VALUE_NODE_ROLE).stringref = self.ui.stringrefSpin.value()
        elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Struct or item.data(_TYPE_NODE_ROLE) is None:
            item.setData(self.ui.intSpin.value(), _VALUE_NODE_ROLE)
        self.refreshItemText(item)

    def substringSelected(self):
        if len(self.ui.substringList.selectedItems()) > 0:
            item: QListWidgetItem = self.ui.substringList.selectedItems()[0]
            self.ui.substringEdit.setEnabled(True)
            self.ui.substringEdit.setPlainText(item.data(_TEXT_SUBSTRING_ROLE))
        else:
            self.ui.substringEdit.setEnabled(False)

    def substringEdited(self):
        """Edits the selected substring in the list.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Get the selected substring item from the list
            - Get the edited text from the text edit field
            - Set the text data on the selected item
            - Get the selected substring item and language/gender pair
            - Get the selected localization string item
            - Set the edited text on the localization string
        """
        item: QListWidgetItem = self.ui.substringList.selectedItems()[0]
        text: str = self.ui.substringEdit.toPlainText()
        item.setData(_TEXT_SUBSTRING_ROLE, text)

        substringItem: QListWidgetItem = self.ui.substringList.selectedItems()[0]
        language, gender = LocalizedString.substring_pair(substringItem.data(_ID_SUBSTRING_ROLE))
        locstringItem: QModelIndex = self.ui.treeView.selectedIndexes()[0]
        locstring: LocalizedString = locstringItem.data(_VALUE_NODE_ROLE)
        locstring.set_data(language, gender, text)

    def addSubstring(self):
        """Adds a substring to the selected localized string.

        Processing Logic:
        ----------------
            - Gets the selected language and gender from combo boxes
            - Generates a unique substring ID based on language and gender
            - Loops through existing substring list to check for duplicate ID
            - If no duplicate, adds a new item to the substring list with the ID and empty text
            - Gets the selected localized string node from the tree view
            - Sets the empty substring data on the localized string based on the selected language and gender.
        """
        language = Language(self.ui.substringLangCombo.currentIndex())
        gender = Gender(self.ui.substringGenderCombo.currentIndex())
        substringId = LocalizedString.substring_id(language, gender)

        for i in range(self.ui.substringList.count()):
            item = self.ui.substringList.item(i)
            if item.data(_ID_SUBSTRING_ROLE) == substringId:
                print(f"Substring ID '{substringId}' already exists, exit")
                return

        item = QListWidgetItem(f"{language.name.title()}, {gender.name.title()}")
        item.setData(_ID_SUBSTRING_ROLE, substringId)
        item.setData(_TEXT_SUBSTRING_ROLE, "")
        self.ui.substringList.addItem(item)

        locstringItem = self.ui.treeView.selectedIndexes()[0]
        locstring: LocalizedString = locstringItem.data(_VALUE_NODE_ROLE)
        locstring.set_data(language, gender, "")

    def removeSubstring(self):
        """Removes a substring from a localized string.

        Args:
        ----
            language: The language of the substring to remove.
            gender: The gender of the substring to remove.

        Processing Logic:
        ----------------
            - Gets the substring ID from the language and gender indexes
            - Loops through the substring list backwards and removes any items with a matching ID
            - Gets the selected localized string from the tree view
            - Removes the substring from the localized string using the language and gender
        """
        language = Language(self.ui.substringLangCombo.currentIndex())
        gender = Gender(self.ui.substringGenderCombo.currentIndex())
        substringId = LocalizedString.substring_id(language, gender)
        for i in range(self.ui.substringList.count())[::-1]:
            item = self.ui.substringList.item(i)
            if item.data(_ID_SUBSTRING_ROLE) == substringId:
                self.ui.substringList.takeItem(i)

        locstringItem = self.ui.treeView.selectedIndexes()[0]
        locstring: LocalizedString = locstringItem.data(_VALUE_NODE_ROLE)
        locstring.remove(language, gender)

    def refreshItemText(self, item: QStandardItem):
        """Refreshes the text of an item in the tree view.

        Args:
        ----
            item: QStandardItem: The item whose text needs to be refreshed.

        Refreshes the text of the item based on its data:
        - Sets the text based on the item's label, type and value
        - Sets the foreground color based on the item's type
        - Updates the item with the refreshed text.
        """
        label: str
        ftype: GFFFieldType
        value: Any
        try:
            label, ftype, value = item.data(_LABEL_NODE_ROLE), item.data(_TYPE_NODE_ROLE), item.data(_VALUE_NODE_ROLE)
        except RuntimeError:  # wrapped C/C++ object of type QStandardItem has been deleted?
            return

        if ftype is None and item.parent() is None:
            text = "[ROOT]"
        elif ftype is None:
            text = f'{str(item.row()).ljust(16)} {"[Struct]".ljust(17)} = {value}'
        elif ftype is GFFFieldType.Struct:
            text = f'{label.ljust(16)} {"[Struct]".ljust(17)} = {value}'
        elif ftype is GFFFieldType.List:
            text = f'{label.ljust(16)} {"[List]".ljust(17)} = {item.rowCount()}'
        else:
            text = f'{label.ljust(16)} {f"[{ftype.name}]".ljust(17)} = {value}'
        self.applyPalette(item, ftype)

        #if ftype == GFFFieldType.Struct or ftype is None:
        #    item.setForeground(QBrush(QColor(0x660000)))
        #elif ftype == GFFFieldType.List:
        #    item.setForeground(QBrush(QColor(0x000088)))
        #else:
        #    item.setForeground(QBrush(QColor(0x000000)))

        item.setText(text)

    def typeChanged(self, ftypeId: int):
        """Changes the type of a selected node.

        Args:
        ----
            ftypeId: {The ID of the new field type}.

        Processing Logic:
        ----------------
            - Gets the new field type object from the ID
            - Gets the selected node from the UI
            - Sets the new type on the node
            - Sets a default value based on the new type
            - Refreshes the UI to show the changes.
        """
        ftype = GFFFieldType(ftypeId)
        proxyIndex = self.ui.treeView.selectedIndexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)
        item.setData(ftype, _TYPE_NODE_ROLE)

        numeric = isinstance(item.data(_VALUE_NODE_ROLE), (float, int))

        if not numeric and ftype in {
            GFFFieldType.UInt8,
            GFFFieldType.Int8,
            GFFFieldType.UInt16,
            GFFFieldType.Int16,
            GFFFieldType.UInt32,
            GFFFieldType.Int32,
            GFFFieldType.UInt64,
            GFFFieldType.Int64,
            GFFFieldType.Single,
            GFFFieldType.Double,
        }:
            # If the old data does not store a number but the new one does, set the value to 0.
            item.setData(0, _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.String:
            item.setData("", _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.LocalizedString:
            item.setData(LocalizedString.from_invalid(), _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.ResRef:
            item.setData(ResRef.from_blank(), _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.Vector3:
            item.setData(Vector3.from_null(), _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.Vector4:
            item.setData(Vector4.from_null(), _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.Binary:
            item.setData(b"", _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.Struct:
            item.setData(GFFStruct(), _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.List:
            item.setData(GFFList(), _VALUE_NODE_ROLE)

        assert item is not None
        self.loadItem(item)  # type: ignore[]
        self.refreshItemText(item)

    def insertNode(self, parent: QStandardItem, label: str, ftype: GFFFieldType, value: Any) -> QStandardItem:
        """Inserts a new child node under the given parent node.

        Args:
        ----
            parent: The parent QStandardItem node to insert under
            label: The label of the new node
            ftype: The field type of the new node
            value: The value of the new node

        Processing Logic:
        ----------------
            1. Creates a new empty QStandardItem
            2. Sets the label, type and value data roles on the new item
            3. Appends the new item as a child to the parent node
            4. Refreshes the text of the new item.
        """
        item = QStandardItem("")
        item.setData(label, _LABEL_NODE_ROLE)
        item.setData(ftype, _TYPE_NODE_ROLE)
        item.setData(value, _VALUE_NODE_ROLE)
        parent.appendRow(item)
        self.refreshItemText(item)
        return item

    def addNode(self, item: QStandardItem):
        """Add a node from the tree model.

        Args:
        ----
            item: The item to add
        """

        def set_spinbox(minv: int, maxv: int, item: QListWidgetItem):
            self.ui.pages.setCurrentWidget(self.ui.intPage)
            self.ui.intSpin.setRange(minv, maxv)
            self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))

        parentType = item.data(_TYPE_NODE_ROLE)
        newValue = GFFStruct()
        newLabel = "[New Struct]"
        if parentType == GFFFieldType.List:
            self.ui.fieldBox.setEnabled(False)
            newValue = newValue.struct_id
            newLabel = str(item.rowCount())
        newItem = self.insertNode(item, newLabel, GFFFieldType.Struct, newValue)
        set_spinbox(-1, 0xFFFFFFFF, newItem)

    def removeNode(self, item: QStandardItem):
        """Remove a node from the tree model.

        Args:
        ----
            item: The item to remove
        """
        item.parent().removeRow(item.row())
        self.refreshItemText(item)

    def removeSelectedNodes(self):
        """Removes selected nodes from the tree.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Loops through the selected indexes in the tree view.
            - Maps each proxy index to its corresponding source index.
            - Gets the item from the source model using the source index.
            - Calls removeNode() to remove the item from the model.
        """
        for proxyIndex in self.ui.treeView.selectedIndexes():
            sourceIndex = self.proxyModel.mapToSource(proxyIndex)
            item = self.model.itemFromIndex(sourceIndex)
            assert item is not None
            self.removeNode(item)

    def requestContextMenu(self, point):
        """Generates context menu for tree view item at given point.

        Args:
        ----
            point: Point in global coordinates

        Processing Logic:
        ----------------
            - Gets proxy and source index for item at point
            - Gets item from model using source index
            - Builds context menu with actions depending on item type
            - Connects actions to methods
            - Pops up menu at point.
        """
        proxyIndex = self.ui.treeView.indexAt(point)
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)
        if item is None:
            return

        menu = QMenu(self)
        nested_type = item.data(_TYPE_NODE_ROLE)
        if nested_type == GFFFieldType.List:
            menu.addAction("Add Struct").triggered.connect(lambda: self.addNode(item))
        elif nested_type in {GFFFieldType.Struct, None}:
            self._build_context_menu_gff_struct(menu, item)
        menu.addAction("Remove").triggered.connect(lambda: self.removeNode(item))
        menu.popup(self.ui.treeView.viewport().mapToGlobal(point))

    def _build_context_menu_gff_struct(self, menu: QMenu, item: QStandardItem):
        """Builds a context menu for a GFF node item.

        Args:
        ----
            menu: QMenu - The menu to build actions on
            item: QStandardItem - The item node for the menu

        Processing Logic:
        ----------------
            - Adds actions to add primitive numeric, string and vector node types
            - Adds actions to add struct and list node types
            - Connects each action to call self.insertNode() and pass relevant args.
        """
        menu.addAction("Add UInt8").triggered.connect(lambda: self.insertNode(item, "New UInt8", GFFFieldType.UInt8, 0))
        menu.addAction("Add UInt16").triggered.connect(lambda: self.insertNode(item, "New UInt16", GFFFieldType.UInt16, 0))
        menu.addAction("Add UInt32").triggered.connect(lambda: self.insertNode(item, "New UInt32", GFFFieldType.UInt32, 0))
        menu.addAction("Add UInt64").triggered.connect(lambda: self.insertNode(item, "New UInt64", GFFFieldType.UInt64, 0))
        menu.addAction("Add Int8").triggered.connect(lambda: self.insertNode(item, "New Int8", GFFFieldType.Int8, 0))
        menu.addAction("Add Int16").triggered.connect(lambda: self.insertNode(item, "New Int16", GFFFieldType.Int16, 0))
        menu.addAction("Add Int32").triggered.connect(lambda: self.insertNode(item, "New Int32", GFFFieldType.Int32, 0))
        menu.addAction("Add Int64").triggered.connect(lambda: self.insertNode(item, "New Int64", GFFFieldType.Int64, 0))
        menu.addAction("Add Single").triggered.connect(lambda: self.insertNode(item, "New Single", GFFFieldType.Single, 0.0))
        menu.addAction("Add Double").triggered.connect(lambda: self.insertNode(item, "New Double", GFFFieldType.Double, 0.0))
        menu.addAction("Add ResRef").triggered.connect(lambda: self.insertNode(item, "New ResRef", GFFFieldType.ResRef, 0))
        menu.addAction("Add String").triggered.connect(lambda: self.insertNode(item, "New String", GFFFieldType.String, 0))
        menu.addAction("Add LocalizedString").triggered.connect(
            lambda: self.insertNode(
                item,
                "New LocalizedString",
                GFFFieldType.LocalizedString,
                LocalizedString.from_invalid(),
            ),
        )
        menu.addAction("Add Binary").triggered.connect(lambda: self.insertNode(item, "New Binary", GFFFieldType.Binary, b""))
        menu.addAction("Add Vector3").triggered.connect(lambda: self.insertNode(item, "New Vector3", GFFFieldType.Vector3, Vector3.from_null()))
        menu.addAction("Add Vector4").triggered.connect(lambda: self.insertNode(item, "New Vector4", GFFFieldType.Vector4, Vector3.from_null()))
        menu.addSeparator()
        menu.addAction("Add Struct").triggered.connect(lambda: self.insertNode(item, "New Struct", GFFFieldType.Struct, GFFStruct()))
        menu.addAction("Add List").triggered.connect(lambda: self.insertNode(item, "New List", GFFFieldType.List, GFFList()))
        menu.addSeparator()

    def selectTalkTable(self):
        """Select a TLK file using a file dialog.

        Args:
        ----
            self: The class instance
        """
        filepath, filter = QFileDialog.getOpenFileName(self, "Select a TLK file", "", "TalkTable (*.tlk)")
        if not filepath:
            return
        self._talktable = TalkTable(filepath)

    def changeLocstringText(self):
        """Changes the text displayed based on the selected string reference.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Checks if talktable is not None
            - Gets the string from talktable based on the selected string reference value
            - Sets the text edit plain text to the retrieved string
            - If talktable is None, sets the text edit plain text to empty string.
        """
        if self._talktable is not None:
            text = self._talktable.string(self.ui.stringrefSpin.value())
            self.ui.tlkTextEdit.setPlainText(text)
        else:
            self.ui.tlkTextEdit.setPlainText("")

    def adjustColor(self, base_color, hue_shift=0, saturation_factor=1.0, value_factor=1.0) -> QColor:
        color = QColor(base_color)
        h, s, v, a = color.getHsv()

        # Calculate new HSV values
        h = (h + hue_shift) % 360
        s = min(max(int(s * saturation_factor), 0), 255)
        v = min(max(int(v * value_factor), 0), 255)

        # Ensure HSV values are within valid ranges
        if h < 0 or h > 359:
            h = max(0, min(h, 359))
        if s < 0 or s > 255:
            s = max(0, min(s, 255))
        if v < 0 or v > 255:
            v = max(0, min(v, 255))

        color.setHsv(h, s, v, a)
        return color

    def applyPalette(self, item, ftype):
        palette = self.palette()
        number_base_color = palette.highlight().color()
        field_type_colors = {
            GFFFieldType.UInt8: self.adjustColor(number_base_color, saturation_factor=1.0, value_factor=1.0),
            GFFFieldType.Int8: self.adjustColor(number_base_color, saturation_factor=0.8, value_factor=0.9),
            GFFFieldType.UInt16: self.adjustColor(number_base_color, hue_shift=15, saturation_factor=1.0, value_factor=1.0),
            GFFFieldType.Int16: self.adjustColor(number_base_color, hue_shift=15, saturation_factor=0.8, value_factor=0.9),
            GFFFieldType.UInt32: self.adjustColor(number_base_color, hue_shift=30, saturation_factor=1.0, value_factor=1.2),
            GFFFieldType.Int32: self.adjustColor(number_base_color, hue_shift=30, saturation_factor=0.9, value_factor=1.1),
            GFFFieldType.UInt64: self.adjustColor(number_base_color, hue_shift=45, saturation_factor=1.0, value_factor=1.0),
            GFFFieldType.Int64: self.adjustColor(number_base_color, hue_shift=45, saturation_factor=0.8, value_factor=0.9),
            GFFFieldType.Single: self.adjustColor(number_base_color, hue_shift=60, saturation_factor=1.0, value_factor=1.0),
            GFFFieldType.Double: self.adjustColor(number_base_color, hue_shift=60, saturation_factor=0.8, value_factor=0.9),
            GFFFieldType.ResRef: palette.windowText().color(),
            GFFFieldType.String: palette.text().color(),
            GFFFieldType.LocalizedString: palette.buttonText().color(),
            GFFFieldType.Vector3: self.adjustColor(palette.buttonText().color(), hue_shift=90, saturation_factor=0.8, value_factor=1.1),
            GFFFieldType.Vector4: self.adjustColor(palette.buttonText().color(), hue_shift=90, saturation_factor=0.8, value_factor=1.3),
            GFFFieldType.Struct: QColor("darkGreen"),
            GFFFieldType.List: self.adjustColor(palette.highlight().color(), hue_shift=120, saturation_factor=0.8, value_factor=1.1),
            GFFFieldType.Binary: palette.midlight().color(),
        }
        if ftype in field_type_colors:
            item.setForeground(QBrush(field_type_colors[ftype]))


class GFFSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """Compares two model indexes and returns whether the left is less than the right.

        Args:
        ----
            left: {QModelIndex}: The left model index to compare
            right: {QModelIndex}: The right model index to compare

        Processing Logic:
        ----------------
            - Extract text from each index using _LABEL_NODE_ROLE and _VALUE_NODE_ROLE roles
            - If both texts are digits, convert to ints and compare numerically
            - Otherwise compare strings alphabetically.
        """
        leftText: str = self.sourceModel().itemFromIndex(left).data(_LABEL_NODE_ROLE)
        rightText: str = self.sourceModel().itemFromIndex(right).data(_LABEL_NODE_ROLE)

        leftText = leftText or str(self.sourceModel().itemFromIndex(left).data(_VALUE_NODE_ROLE))
        rightText = rightText or str(self.sourceModel().itemFromIndex(right).data(_VALUE_NODE_ROLE))

        if leftText.isdigit() and rightText.isdigit():
            leftInt = int(leftText)
            rightInt = int(rightText)
            return leftInt < rightInt
        return leftText < rightText
