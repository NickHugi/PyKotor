from contextlib import suppress
from typing import Any, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QItemSelectionRange, QSortFilterProxyModel, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QIcon, QPixmap
from PyQt5.QtWidgets import QListWidgetItem, QMenu, QWidget, QFileDialog, QShortcut
from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString, Language, Gender
from pykotor.common.misc import ResRef
from pykotor.extract.installation import Installation
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import load_gff, GFFStruct, GFFFieldType, GFFList, GFF, write_gff, GFFContent
from pykotor.resource.type import ResourceType

from editors.editor import Editor
from editors.gff import gff_editor_ui

_VALUE_NODE_ROLE = QtCore.Qt.UserRole + 1
_TYPE_NODE_ROLE = QtCore.Qt.UserRole + 2
_LABEL_NODE_ROLE = QtCore.Qt.UserRole + 3

_ID_SUBSTRING_ROLE = QtCore.Qt.UserRole + 1
_TEXT_SUBSTRING_ROLE = QtCore.Qt.UserRole + 2


class GFFEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[Installation] = None):
        supported = [ResourceType.GFF, ResourceType.UTC, ResourceType.UTP, ResourceType.UTD, ResourceType.UTI,
                     ResourceType.UTM, ResourceType.UTE, ResourceType.UTT, ResourceType.UTW, ResourceType.UTS,
                     ResourceType.DLG, ResourceType.GUI, ResourceType.ARE, ResourceType.IFO, ResourceType.GIT,
                     ResourceType.JRL, ResourceType.ITP]
        super().__init__(parent, "GFF Editor", supported, supported, installation)
        self.resize(400, 250)

        self._talktable: Optional[TalkTable] = installation.talktable() if installation else None

        self.ui = gff_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        iconVersion = "x" if installation is None else "2" if installation.tsl else "1"
        iconPath = ":/images/icons/k{}/none.png".format(iconVersion)
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

        self.ui.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.ui.treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.ui.treeView.setSortingEnabled(True)

        self.new()

    def _setupSignals(self) -> None:
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

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        gff = load_gff(data)

        self.model.clear()
        self.model.setColumnCount(1)

        rootNode = QStandardItem("[ROOT]")
        rootNode.setForeground(QBrush(QColor(0x660000)))
        self.model.appendRow(rootNode)
        self._load_struct(rootNode, gff.root)

        sourceIndex = self.model.indexFromItem(rootNode)
        proxyIndex = self.proxyModel.mapFromSource(sourceIndex)
        self.ui.treeView.expand(proxyIndex)

    def _load_struct(self, node: QStandardItem, gffStruct: GFFStruct) -> None:
        for label, ftype, value in gffStruct:
            childNode = QStandardItem("")
            childNode.setData(ftype, _TYPE_NODE_ROLE)
            childNode.setData(label, _LABEL_NODE_ROLE)

            if ftype == GFFFieldType.List:
                childNode.setForeground(QBrush(QColor(0x000088)))
                self._load_list(childNode, value)
            elif ftype == GFFFieldType.Struct:
                childNode.setForeground(QBrush(QColor(0x660000)))
                childNode.setData(value.struct_id, _VALUE_NODE_ROLE)
                self._load_struct(childNode, value)
            else:
                childNode.setData(value, _VALUE_NODE_ROLE)

            self.refreshItemText(childNode)
            node.appendRow(childNode)

    def _load_list(self, node: QStandardItem, gffList: GFFList) -> None:
        for i, gffSturct in enumerate(gffList):
            childNode = QStandardItem("")
            childNode.setForeground(QBrush(QColor(0x660000)))
            childNode.setData(gffSturct.struct_id, _VALUE_NODE_ROLE)
            node.appendRow(childNode)
            self.refreshItemText(childNode)
            self._load_struct(childNode, gffSturct)

    def build(self) -> bytes:
        try:
            content = GFFContent(self._restype.extension.upper() + " ")
        except ValueError:
            content = GFFContent.GFF

        gff = GFF(content)

        self._build_struct(self.model.item(0, 0), gff.root)

        data = bytearray()
        write_gff(gff, data)
        return data

    def _build_struct(self, item: QStandardItem, gffStruct: GFFStruct) -> None:
        for i in range(item.rowCount()):
            child = item.child(i, 0)
            label = child.data(_LABEL_NODE_ROLE)
            value = child.data(_VALUE_NODE_ROLE)
            ftype = child.data(_TYPE_NODE_ROLE)

            if ftype == GFFFieldType.UInt8: gffStruct.set_uint8(label, value)
            if ftype == GFFFieldType.UInt16: gffStruct.set_uint16(label, value)
            if ftype == GFFFieldType.UInt32: gffStruct.set_uint32(label, value)
            if ftype == GFFFieldType.UInt64: gffStruct.set_uint64(label, value)
            if ftype == GFFFieldType.Int8: gffStruct.set_int8(label, value)
            if ftype == GFFFieldType.Int16: gffStruct.set_int16(label, value)
            if ftype == GFFFieldType.Int32: gffStruct.set_int32(label, value)
            if ftype == GFFFieldType.Int64: gffStruct.set_int64(label, value)
            if ftype == GFFFieldType.Single: gffStruct.set_single(label, value)
            if ftype == GFFFieldType.Double: gffStruct.set_double(label, value)
            if ftype == GFFFieldType.ResRef: gffStruct.set_resref(label, value)
            if ftype == GFFFieldType.String: gffStruct.set_string(label, value)
            if ftype == GFFFieldType.LocalizedString: gffStruct.set_locstring(label, value)
            if ftype == GFFFieldType.Binary: gffStruct.set_binary(label, value)
            if ftype == GFFFieldType.Vector3: gffStruct.set_vector3(label, value)
            if ftype == GFFFieldType.Vector4: gffStruct.set_vector4(label, value)

            if ftype == GFFFieldType.Struct:
                childGffStruct = GFFStruct(value)
                gffStruct.set_struct(label, childGffStruct)
                self._build_struct(child, childGffStruct)

            if ftype == GFFFieldType.List:
                childGffList = GFFList()
                gffStruct.set_list(label, childGffList)
                self._build_list(child, childGffList)

    def _build_list(self, item: QStandardItem, gffList: GFFList):
        for i in range(item.rowCount()):
            child = item.child(i, 0)
            struct_id = child.data(_VALUE_NODE_ROLE)
            gffStruct = gffList.add(struct_id)
            self._build_struct(child, gffStruct)

    def new(self) -> None:
        super().new()
        self.model.clear()
        self.model.setColumnCount(1)

        rootNode = QStandardItem("[ROOT]")
        rootNode.setForeground(QBrush(QColor(0x660000)))
        self.model.appendRow(rootNode)

    def selectionChanged(self, selected: QItemSelectionRange) -> None:
        proxyIndex = selected.indexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)
        self.loadItem(item)

    def loadItem(self, item: QListWidgetItem):
        if item.data(_TYPE_NODE_ROLE) is None:  # Field-less struct (root or in list)
            self.ui.fieldBox.setEnabled(False)

            self.ui.pages.setCurrentWidget(self.ui.intPage)
            self.ui.intSpin.setRange(-1, 4294967295)
            self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
        else:
            self.ui.fieldBox.setEnabled(True)
            self.ui.typeCombo.setCurrentText(item.data(_TYPE_NODE_ROLE).name)
            self.ui.labelEdit.setText(item.data(_LABEL_NODE_ROLE))

            if item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int8:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(-128, 127)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int16:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(-32768, 32767)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int32:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(-2147483648, 2147483647)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Int64:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(-9223372036854775808, 9223372036854775807)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt8:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(0, 255)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt16:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(0, 65535)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt32:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(0, 4294967295)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.UInt64:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(0, 18446744073709551615)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Double or item.data(_TYPE_NODE_ROLE) == GFFFieldType.Single:
                self.ui.pages.setCurrentWidget(self.ui.floatPage)
                self.ui.floatSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.ResRef:
                self.ui.pages.setCurrentWidget(self.ui.linePage)
                self.ui.lineEdit.setText(item.data(_VALUE_NODE_ROLE).get())
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.String:
                self.ui.pages.setCurrentWidget(self.ui.textPage)
                self.ui.textEdit.setPlainText(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Struct:
                self.ui.pages.setCurrentWidget(self.ui.intPage)
                self.ui.intSpin.setRange(-1, 4294967295)
                self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.List:
                self.ui.pages.setCurrentWidget(self.ui.blankPage)
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Vector3:
                self.ui.pages.setCurrentWidget(self.ui.vector3Page)
                vec3 = item.data(_VALUE_NODE_ROLE)
                self.ui.xVec3Spin.setValue(vec3.x)
                self.ui.yVec3Spin.setValue(vec3.y)
                self.ui.zVec3Spin.setValue(vec3.z)
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Vector4:
                self.ui.pages.setCurrentWidget(self.ui.vector4Page)
                vec4 = item.data(_VALUE_NODE_ROLE)
                self.ui.xVec4Spin.setValue(vec4.x)
                self.ui.yVec4Spin.setValue(vec4.y)
                self.ui.zVec4Spin.setValue(vec4.z)
                self.ui.wVec4Spin.setValue(vec4.w)
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.Binary:
                self.ui.pages.setCurrentWidget(self.ui.blankPage)
                ...
            elif item.data(_TYPE_NODE_ROLE) == GFFFieldType.LocalizedString:
                locstring: LocalizedString = item.data(_VALUE_NODE_ROLE)
                self.ui.pages.setCurrentWidget(self.ui.substringPage)
                self.ui.substringEdit.setEnabled(False)
                self.ui.stringrefSpin.setValue(locstring.stringref)
                self.ui.substringList.clear()
                for language, gender, text in locstring:
                    item = QListWidgetItem(language.name.title() + ", " + gender.name.title())
                    item.setData(_TEXT_SUBSTRING_ROLE, text)
                    item.setData(_ID_SUBSTRING_ROLE, LocalizedString.substring_id(language, gender))
                    self.ui.substringList.addItem(item)

    def updateData(self) -> None:
        if len(self.ui.treeView.selectedIndexes()) == 0:
            return

        proxyIndex = self.ui.treeView.selectedIndexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)

        item.setData(self.ui.labelEdit.text(), _LABEL_NODE_ROLE)

        if item.data(_TYPE_NODE_ROLE) in [GFFFieldType.UInt8, GFFFieldType.Int8, GFFFieldType.UInt16, GFFFieldType.Int16,
                                          GFFFieldType.UInt32, GFFFieldType.Int32, GFFFieldType.UInt64, GFFFieldType.Int64]:
            item.setData(self.ui.intSpin.value(), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.Single, GFFFieldType.Double]:
            item.setData(self.ui.floatSpin.value(), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.ResRef]:
            item.setData(ResRef(self.ui.lineEdit.text()), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.String]:
            item.setData(self.ui.textEdit.toPlainText(), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.Vector3]:
            vec3 = Vector3(self.ui.xVec3Spin.value(), self.ui.yVec3Spin.value(), self.ui.zVec3Spin.value())
            item.setData(vec3, _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.Vector4]:
            vec4 = Vector4(self.ui.xVec4Spin.value(), self.ui.yVec4Spin.value(), self.ui.zVec4Spin.value(), self.ui.wVec4Spin.value())
            item.setData(vec4, _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.LocalizedString]:
            item.data(_VALUE_NODE_ROLE).stringref = self.ui.stringrefSpin.value()
        elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.Struct]:
            item.setData(self.ui.intSpin.value(), _VALUE_NODE_ROLE)
        elif item.data(_TYPE_NODE_ROLE) is None:
            item.setData(self.ui.intSpin.value(), _VALUE_NODE_ROLE)

        self.refreshItemText(item)

    def substringSelected(self) -> None:
        if len(self.ui.substringList.selectedItems()) > 0:
            item = self.ui.substringList.selectedItems()[0]
            self.ui.substringEdit.setEnabled(True)
            self.ui.substringEdit.setPlainText(item.data(_TEXT_SUBSTRING_ROLE))
        else:
            self.ui.substringEdit.setEnabled(False)

    def substringEdited(self) -> None:
        item = self.ui.substringList.selectedItems()[0]
        text = self.ui.substringEdit.toPlainText()
        item.setData(_TEXT_SUBSTRING_ROLE, text)

        substringItem = self.ui.substringList.selectedItems()[0]
        language, gender = LocalizedString.substring_pair(substringItem.data(_ID_SUBSTRING_ROLE))
        locstringItem = self.ui.treeView.selectedIndexes()[0]
        locstring: LocalizedString = locstringItem.data(_VALUE_NODE_ROLE)
        locstring.set(language, gender, text)

    def addSubstring(self) -> None:
        language = Language(self.ui.substringLangCombo.currentIndex())
        gender = Gender(self.ui.substringGenderCombo.currentIndex())
        substringId = LocalizedString.substring_id(language, gender)

        for i in range(self.ui.substringList.count()):
            item = self.ui.substringList.item(i)
            if item.data(_ID_SUBSTRING_ROLE) == substringId:
                return

        item = QListWidgetItem(language.name.title() + ", " + gender.name.title())
        item.setData(_ID_SUBSTRING_ROLE, substringId)
        item.setData(_TEXT_SUBSTRING_ROLE, "")
        self.ui.substringList.addItem(item)

        locstringItem = self.ui.treeView.selectedIndexes()[0]
        locstring: LocalizedString = locstringItem.data(_VALUE_NODE_ROLE)
        locstring.set(language, gender, "")

    def removeSubstring(self) -> None:
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
        label, ftype, value = item.data(_LABEL_NODE_ROLE), item.data(_TYPE_NODE_ROLE), item.data(_VALUE_NODE_ROLE)

        if ftype is None and item.parent() is None:
            text = "[ROOT]"
        elif ftype is None:
            text = "{} {} = {}".format(str(item.row()).ljust(16), "[Struct]".ljust(17), str(value))
        elif ftype is GFFFieldType.Struct:
            text = "{} {} = {}".format(label.ljust(16), "[Struct]".ljust(17), str(value))
        elif ftype is GFFFieldType.List:
            text = "{} {} = {}".format(label.ljust(16), "[List]".ljust(17), str(item.rowCount()))
        else:
            text = "{} {} = {}".format(label.ljust(16), ("[" + str(ftype.name) + "]").ljust(17), str(value))

        if ftype == GFFFieldType.Struct or ftype == None:
            item.setForeground(QBrush(QColor(0x660000)))
        elif ftype == GFFFieldType.List:
            item.setForeground(QBrush(QColor(0x000088)))
        else:
            item.setForeground(QBrush(QColor(0x000000)))

        item.setText(text)

    def typeChanged(self, ftypeId) -> None:
        ftype = GFFFieldType(ftypeId)
        proxyIndex = self.ui.treeView.selectedIndexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(index)
        item.setData(ftype, _TYPE_NODE_ROLE)

        numeric = isinstance(item.data(_VALUE_NODE_ROLE), int) or isinstance(item.data(_VALUE_NODE_ROLE), float)

        if not numeric and ftype in [GFFFieldType.UInt8, GFFFieldType.Int8, GFFFieldType.UInt16, GFFFieldType.Int16,
                                     GFFFieldType.UInt32, GFFFieldType.Int32, GFFFieldType.UInt64, GFFFieldType.Int64,
                                     GFFFieldType.Single, GFFFieldType.Double]:
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
            item.setData(bytes(), _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.Struct:
            item.setData(GFFStruct(), _VALUE_NODE_ROLE)
        elif ftype == GFFFieldType.List:
            item.setData(GFFList(), _VALUE_NODE_ROLE)

        self.loadItem(item)
        self.refreshItemText(item)

    def insertNode(self, parent: QStandardItem, label: str, ftype: GFFFieldType, value: Any) -> None:
        item = QStandardItem("")
        item.setData(label, _LABEL_NODE_ROLE)
        item.setData(ftype, _TYPE_NODE_ROLE)
        item.setData(value, _VALUE_NODE_ROLE)
        parent.appendRow(item)
        self.refreshItemText(item)

    def removeNode(self, item: QStandardItem) -> None:
        item.parent().removeRow(item.row())

    def removeSelectedNodes(self) -> None:
        for proxyIndex in self.ui.treeView.selectedIndexes():
            sourceIndex = self.proxyModel.mapToSource(proxyIndex)
            item = self.model.itemFromIndex(sourceIndex)
            self.removeNode(item)

    def requestContextMenu(self, point):
        proxyIndex = self.ui.treeView.indexAt(point)
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)

        if item is not None:
            menu = QMenu(self)

            if item.data(_TYPE_NODE_ROLE) == GFFFieldType.List:
                menu.addAction("Add Struct").triggered.connect(lambda: self.insertNode(item, "New Struct", GFFFieldType.Struct, GFFStruct()))
            elif item.data(_TYPE_NODE_ROLE) in [GFFFieldType.Struct, None]:
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
                menu.addAction("Add LocalizedString").triggered.connect(lambda: self.insertNode(item, "New LocalizedString", GFFFieldType.LocalizedString, LocalizedString.from_invalid()))
                menu.addAction("Add Binary").triggered.connect(lambda:self.insertNode(item, "New Binary", GFFFieldType.Binary, bytes()))
                menu.addAction("Add Vector3").triggered.connect(lambda: self.insertNode(item, "New Vector3", GFFFieldType.Vector3, Vector3.from_null()))
                menu.addAction("Add Vector4").triggered.connect(lambda: self.insertNode(item, "New Vector4", GFFFieldType.Vector4, Vector3.from_null()))
                menu.addSeparator()
                menu.addAction("Add Struct").triggered.connect(lambda: self.insertNode(item, "New Struct", GFFFieldType.Struct, GFFStruct()))
                menu.addAction("Add List").triggered.connect(lambda: self.insertNode(item, "New List", GFFFieldType.Struct, GFFList()))
                menu.addSeparator()
            else:
                ...

            if item.data(_TYPE_NODE_ROLE) is not None:
                menu.addAction("Remove").triggered.connect(lambda: self.removeNode(item))

            menu.popup(self.ui.treeView.viewport().mapToGlobal(point))

    def selectTalkTable(self) -> None:
        filepath, filter = QFileDialog.getOpenFileName(self, "Select a TLK file", "", "TalkTable (*.tlk)")
        if filepath:
            self._talktable = TalkTable(filepath)

    def changeLocstringText(self) -> None:
        if self._talktable is not None:
            text = self._talktable.string(self.ui.stringrefSpin.value())
            self.ui.tlkTextEdit.setPlainText(text)
        else:
            self.ui.tlkTextEdit.setPlainText("")


class GFFSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        leftText: str = self.sourceModel().itemFromIndex(left).data(_LABEL_NODE_ROLE)
        rightText: str = self.sourceModel().itemFromIndex(right).data(_LABEL_NODE_ROLE)

        leftText = str(self.sourceModel().itemFromIndex(left).data(_VALUE_NODE_ROLE)) if not leftText else leftText
        rightText = str(self.sourceModel().itemFromIndex(right).data(_VALUE_NODE_ROLE)) if not rightText else rightText

        if leftText.isdigit() and rightText.isdigit():
            leftInt = int(leftText)
            rightInt = int(rightText)
            return leftInt < rightInt
        else:
            return leftText < rightText
