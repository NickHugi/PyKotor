from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from qtpy import QtCore
from qtpy.QtCore import QSortFilterProxyModel
from qtpy.QtGui import QBrush, QColor, QFont, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,  # pyright: ignore[reportPrivateImportUsage]
    QSizePolicy,
    QVBoxLayout,
)

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import ResRef
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct, read_gff, write_gff
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QItemSelectionRange, QModelIndex, QPoint
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation

_VALUE_NODE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
_TYPE_NODE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2
_LABEL_NODE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 3

_ID_SUBSTRING_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
_TEXT_SUBSTRING_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2


class GFFEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [restype for restype in ResourceType if restype.contents == "gff"]
        super().__init__(parent, "GFF Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        self._talktable: TalkTable | None = installation.talktable() if installation else None
        self._gff_content: GFFContent | None = None

        from toolset.uic.qtpy.editors.gff import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()

        self.ui.treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        self.ui.treeView.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.ui.treeView.setSortingEnabled(True)

        # Make the right panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setup_signals(self):
        self.ui.actionSetTLK.triggered.connect(self.select_talk_table)

        self.model: QStandardItemModel = QStandardItemModel(self)
        self.proxy_model: QSortFilterProxyModel = GFFSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.ui.treeView.setModel(self.proxy_model)

        selectionModel = self.ui.treeView.selectionModel()
        assert selectionModel is not None
        selectionModel.selectionChanged.connect(self.selection_changed)
        self.ui.intSpin.editingFinished.connect(self.update_data)
        self.ui.floatSpin.editingFinished.connect(self.update_data)
        self.ui.lineEdit.editingFinished.connect(self.update_data)
        self.ui.textEdit.textChanged.connect(self.update_data)
        self.ui.xVec3Spin.editingFinished.connect(self.update_data)
        self.ui.yVec3Spin.editingFinished.connect(self.update_data)
        self.ui.zVec3Spin.editingFinished.connect(self.update_data)
        self.ui.xVec4Spin.editingFinished.connect(self.update_data)
        self.ui.yVec4Spin.editingFinished.connect(self.update_data)
        self.ui.zVec4Spin.editingFinished.connect(self.update_data)
        self.ui.wVec4Spin.editingFinished.connect(self.update_data)
        self.ui.labelEdit.editingFinished.connect(self.update_data)

        self.ui.stringrefSpin.valueChanged.connect(self.change_locstring_text)
        self.ui.stringrefSpin.editingFinished.connect(self.update_data)
        self.ui.substringList.itemSelectionChanged.connect(self.substringSelected)
        self.ui.addSubstringButton.clicked.connect(self.add_substring)
        self.ui.removeSubstringButton.clicked.connect(self.remove_substring)
        self.ui.substringEdit.textChanged.connect(self.substring_edited)

        self.ui.treeView.customContextMenuRequested.connect(self.on_context_menu)

        self.ui.typeCombo.activated.connect(self.typeChanged)

        QShortcut("Del", self).activated.connect(self.remove_selectedNodes)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)
        gff: GFF = read_gff(data)
        self._gff_content = gff.content

        self.model.clear()
        self.model.setColumnCount(1)

        root_node = QStandardItem("[ROOT]")
        self.apply_palette(root_node, GFFFieldType.Struct)
        #root_node.setForeground(QBrush(QColor(0x660000)))
        self.model.appendRow(root_node)
        self._load_struct(root_node, gff.root)

        source_index = self.model.indexFromItem(root_node)
        proxy_index = self.proxy_model.mapFromSource(source_index)
        self.ui.treeView.expand(proxy_index)

    def _load_struct(self, node: QStandardItem, gff_struct: GFFStruct):
        for label, ftype, value in gff_struct:
            child_node = QStandardItem("")
            child_node.setData(ftype, _TYPE_NODE_ROLE)
            child_node.setData(label, _LABEL_NODE_ROLE)

            if ftype == GFFFieldType.List:
                self.apply_palette(child_node, GFFFieldType.List)
                #child_node.setForeground(QBrush(QColor(0x000088)))
                self._load_list(child_node, value)
            elif ftype == GFFFieldType.Struct:
                assert isinstance(value, GFFStruct)
                self.apply_palette(child_node, GFFFieldType.Struct)
                #child_node.setForeground(QBrush(QColor(0x660000)))
                child_node.setData(value.struct_id, _VALUE_NODE_ROLE)
                self._load_struct(child_node, value)
            else:
                child_node.setData(value, _VALUE_NODE_ROLE)

            self.apply_palette(node, GFFFieldType.Struct)
            self.refresh_item_text(child_node)
            node.appendRow(child_node)

    def _load_list(self, node: QStandardItem, gff_list: GFFList):
        for gff_struct in gff_list:
            child_node = QStandardItem("")
            self.apply_palette(child_node, GFFFieldType.Struct)
            #child_node.setForeground(QBrush(QColor(0x660000)))
            child_node.setData(gff_struct.struct_id, _VALUE_NODE_ROLE)
            node.appendRow(child_node)
            self.refresh_item_text(child_node)
            self._load_struct(child_node, gff_struct)

        self.apply_palette(node, GFFFieldType.List)

    def build(self) -> tuple[bytes, bytes]:
        gff_content = self._gff_content or GFFContent.from_res(self._resname or "")
        assert gff_content is not None
        gff_type = ResourceType.GFF

        gff = GFF(gff_content)
        self._build_struct(self.model.item(0, 0), gff.root)

        data = bytearray()
        write_gff(gff, data, gff_type)
        return bytes(data), b""

    def _build_struct(self, item: QStandardItem, gff_struct: GFFStruct):
        for i in range(item.rowCount()):
            child: QStandardItem | None = item.child(i, 0)
            assert child is not None
            label = child.data(_LABEL_NODE_ROLE)
            value = child.data(_VALUE_NODE_ROLE)
            ftype = child.data(_TYPE_NODE_ROLE)

            if ftype == GFFFieldType.UInt8:
                gff_struct.set_uint8(label, value)
            if ftype == GFFFieldType.UInt16:
                gff_struct.set_uint16(label, value)
            if ftype == GFFFieldType.UInt32:
                gff_struct.set_uint32(label, value)
            if ftype == GFFFieldType.UInt64:
                gff_struct.set_uint64(label, value)
            if ftype == GFFFieldType.Int8:
                gff_struct.set_int8(label, value)
            if ftype == GFFFieldType.Int16:
                gff_struct.set_int16(label, value)
            if ftype == GFFFieldType.Int32:
                gff_struct.set_int32(label, value)
            if ftype == GFFFieldType.Int64:
                gff_struct.set_int64(label, value)
            if ftype == GFFFieldType.Single:
                gff_struct.set_single(label, value)
            if ftype == GFFFieldType.Double:
                gff_struct.set_double(label, value)
            if ftype == GFFFieldType.ResRef:
                gff_struct.set_resref(label, value)
            if ftype == GFFFieldType.String:
                gff_struct.set_string(label, value)
            if ftype == GFFFieldType.LocalizedString:
                gff_struct.set_locstring(label, value)
            if ftype == GFFFieldType.Binary:
                gff_struct.set_binary(label, value)
            if ftype == GFFFieldType.Vector3:
                gff_struct.set_vector3(label, value)
            if ftype == GFFFieldType.Vector4:
                gff_struct.set_vector4(label, value)

            if ftype == GFFFieldType.Struct:
                childGffStruct = GFFStruct(value)
                gff_struct.set_struct(label, childGffStruct)
                self._build_struct(child, childGffStruct)

            if ftype == GFFFieldType.List:
                childGffList = GFFList()
                gff_struct.set_list(label, childGffList)
                self._build_list(child, childGffList)

    def _build_list(self, item: QStandardItem, gff_list: GFFList):
        for i in range(item.rowCount()):
            child = item.child(i, 0)
            assert child is not None, f"child cannot be None in {self!r}._build_list({item!r}, {gff_list!r})"
            struct_id = child.data(_VALUE_NODE_ROLE)
            gff_struct: GFFStruct = gff_list.add(struct_id)
            self._build_struct(child, gff_struct)

    def new(self):
        super().new()
        self.model.clear()
        self.model.setColumnCount(1)

        root_node = QStandardItem("[ROOT]")
        self.apply_palette(root_node, GFFFieldType.Struct)
        #root_node.setForeground(QBrush(QColor(0x660000)))
        self.model.appendRow(root_node)

    def selection_changed(self, selected: QItemSelectionRange):
        for proxy_index in selected.indexes():
            source_index = self.proxy_model.mapToSource(proxy_index)
            tree_item = self.model.itemFromIndex(source_index)
            assert tree_item is not None
            self.load_item(tree_item)

    def load_item(self, item: QStandardItem):
        def set_spinbox(minv: int, maxv: int, item: QStandardItem):
            self.ui.pages.setCurrentWidget(self.ui.intPage)
            self.ui.intSpin.setRange(minv, maxv)
            self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))

        if item.data(_TYPE_NODE_ROLE) is None:  # Field-less struct (root or in list)
            self.ui.fieldBox.setEnabled(False)
            set_spinbox(-1, 0xFFFFFFFF, item)
            return
        black_page_layout = self.ui.blankPage.layout()
        if black_page_layout is not None:
            while black_page_layout.count():
                child = black_page_layout.takeAt(0)
                if child is not None and child.widget() is not None:
                    child.widget().deleteLater()

        self.ui.fieldBox.setEnabled(True)
        item_type = cast(GFFFieldType, item.data(_TYPE_NODE_ROLE))
        self.ui.typeCombo.setCurrentText(item_type.name)
        self.ui.labelEdit.setText(item.data(_LABEL_NODE_ROLE))

        if item_type == GFFFieldType.Int8:
            set_spinbox(-0x80, 0x7F, item)
        elif item_type == GFFFieldType.Int16:
            set_spinbox(-0x8000, 0x7FFF, item)
        elif item_type == GFFFieldType.Int32:
            set_spinbox(-0x80000000, 0x7FFFFFFF, item)
        elif item_type == GFFFieldType.Int64:
            set_spinbox(-0x8000000000000000, 0x7FFFFFFFFFFFFFFF, item)
        elif item_type == GFFFieldType.UInt8:
            set_spinbox(0, 0xFF, item)
        elif item_type == GFFFieldType.UInt16:
            set_spinbox(0, 0xFFFF, item)
        elif item_type == GFFFieldType.UInt32:
            set_spinbox(0, 0xFFFFFFFF, item)
        elif item_type == GFFFieldType.UInt64:
            set_spinbox(0, 0xFFFFFFFFFFFFFFFF, item)
        elif item_type in {GFFFieldType.Double, GFFFieldType.Single}:
            self.ui.pages.setCurrentWidget(self.ui.floatPage)
            self.ui.floatSpin.setValue(item.data(_VALUE_NODE_ROLE))
        elif item_type == GFFFieldType.ResRef:
            self.ui.pages.setCurrentWidget(self.ui.linePage)
            self.ui.lineEdit.setText(str(item.data(_VALUE_NODE_ROLE)))
        elif item_type == GFFFieldType.String:
            self.ui.pages.setCurrentWidget(self.ui.textPage)
            self.ui.textEdit.setPlainText(str(item.data(_VALUE_NODE_ROLE)))
        elif item_type == GFFFieldType.Struct:
            set_spinbox(-1, 0xFFFFFFFF, item)
        elif item_type == GFFFieldType.List:
            self.ui.pages.setCurrentWidget(self.ui.blankPage)
        elif item_type == GFFFieldType.Vector3:
            self.ui.pages.setCurrentWidget(self.ui.vector3Page)
            vec3: Vector3 = item.data(_VALUE_NODE_ROLE)
            self.ui.xVec3Spin.setValue(vec3.x)
            self.ui.yVec3Spin.setValue(vec3.y)
            self.ui.zVec3Spin.setValue(vec3.z)
        elif item_type == GFFFieldType.Vector4:
            self.ui.pages.setCurrentWidget(self.ui.vector4Page)
            vec4: Vector4 = item.data(_VALUE_NODE_ROLE)
            self.ui.xVec4Spin.setValue(vec4.x)
            self.ui.yVec4Spin.setValue(vec4.y)
            self.ui.zVec4Spin.setValue(vec4.z)
            self.ui.wVec4Spin.setValue(vec4.w)
        elif item_type == GFFFieldType.Binary:
            binaryData: bytes = item.data(_VALUE_NODE_ROLE)
            self.ui.pages.setCurrentWidget(self.ui.blankPage)
            if self.ui.blankPage.layout() is None:
                layout = QVBoxLayout(self.ui.blankPage)
                self.ui.blankPage.setLayout(layout)
            else:
                while self.ui.blankPage.layout().count():
                    child = self.ui.blankPage.layout().takeAt(0)
                    if child is not None and child.widget() is not None:
                        child.widget().deleteLater()
            hex_data_str = " ".join(f"{b:02X}" for b in binaryData)
            binary_data_label = QLabel(f"{hex_data_str}")
            binary_data_label.setWordWrap(True)
            binary_data_label.setFont(QFont("Courier New", 7))
            binary_data_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            binary_data_label.setMaximumWidth(self.ui.blankPage.width() - 20)  # -20 otherwise the pane grows for some reason.
            self.ui.blankPage.layout().addWidget(binary_data_label)
            copy_button = QPushButton("Copy Binary Data")
            self.ui.blankPage.layout().addWidget(copy_button)
            copy_button.clicked.connect(lambda: QApplication.clipboard().setText(hex_data_str))
        elif item_type == GFFFieldType.LocalizedString:
            locstring: LocalizedString = item.data(_VALUE_NODE_ROLE)
            self.ui.pages.setCurrentWidget(self.ui.substringPage)
            self.ui.substringEdit.setEnabled(False)
            self.ui.stringrefSpin.setValue(locstring.stringref)
            self.ui.substringList.clear()
            for language, gender, text in locstring:
                listItem = QListWidgetItem(f"{language.name.title()}, {gender.name.title()}")
                listItem.setData(_TEXT_SUBSTRING_ROLE, text)
                listItem.setData(_ID_SUBSTRING_ROLE, LocalizedString.substring_id(language, gender))
                self.ui.substringList.addItem(listItem)

    def update_data(self):
        selected_indices = self.ui.treeView.selectedIndexes()
        if not selected_indices:
            return

        proxy_index = selected_indices[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        item: QStandardItem = self.model.itemFromIndex(source_index)
        item_type = cast(GFFFieldType, item.data(_TYPE_NODE_ROLE))

        item.setData(self.ui.labelEdit.text(), _LABEL_NODE_ROLE)

        if item_type in {
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
        elif item_type in {GFFFieldType.Single, GFFFieldType.Double}:
            item.setData(self.ui.floatSpin.value(), _VALUE_NODE_ROLE)
        elif item_type == GFFFieldType.ResRef:
            item.setData(ResRef(self.ui.lineEdit.text()), _VALUE_NODE_ROLE)
        elif item_type == GFFFieldType.String:
            item.setData(self.ui.textEdit.toPlainText(), _VALUE_NODE_ROLE)
        elif item_type == GFFFieldType.Vector3:
            vec3 = Vector3(self.ui.xVec3Spin.value(), self.ui.yVec3Spin.value(), self.ui.zVec3Spin.value())
            item.setData(vec3, _VALUE_NODE_ROLE)
        elif item_type == GFFFieldType.Vector4:
            vec4 = Vector4(self.ui.xVec4Spin.value(), self.ui.yVec4Spin.value(), self.ui.zVec4Spin.value(), self.ui.wVec4Spin.value())
            item.setData(vec4, _VALUE_NODE_ROLE)
        elif item_type == GFFFieldType.LocalizedString:
            value_locstring = cast(LocalizedString, item.data(_VALUE_NODE_ROLE))
            value_locstring.stringref = self.ui.stringrefSpin.value()
        elif item_type == GFFFieldType.Struct or item_type is None:
            item.setData(self.ui.intSpin.value(), _VALUE_NODE_ROLE)
        self.refresh_item_text(item)

    def substringSelected(self):
        selected_substring_items: list[QListWidgetItem] = self.ui.substringList.selectedItems()
        if selected_substring_items:
            for listItem in selected_substring_items:
                self.ui.substringEdit.setEnabled(True)
                self.ui.substringEdit.setPlainText(listItem.data(_TEXT_SUBSTRING_ROLE))
        else:
            self.ui.substringEdit.setEnabled(False)

    def substring_edited(self):
        for item in self.ui.substringList.selectedItems():
            text: str = self.ui.substringEdit.toPlainText()
            item.setData(_TEXT_SUBSTRING_ROLE, text)

            language, gender = LocalizedString.substring_pair(item.data(_ID_SUBSTRING_ROLE))
            proxy_index: QModelIndex = self.ui.treeView.selectedIndexes()[0]
            tree_source_index = self.proxy_model.mapToSource(proxy_index)
            tree_item = self.model.itemFromIndex(tree_source_index)
            locstring: LocalizedString = tree_item.data(_VALUE_NODE_ROLE)
            locstring.set_data(language, gender, text)

    def add_substring(self):
        language = Language(self.ui.substringLangCombo.currentIndex())
        gender = Gender(self.ui.substringGenderCombo.currentIndex())
        substring_id = LocalizedString.substring_id(language, gender)

        for i in range(self.ui.substringList.count()):
            item = self.ui.substringList.item(i)
            if item is None:
                self._logger.warning(f"substringList item at index {i} was None, skipping")
                continue
            if item.data(_ID_SUBSTRING_ROLE) == substring_id:
                self._logger.warning(f"Substring ID '{substring_id}' already exists, exit")
                return

        item = QListWidgetItem(f"{language.name.title()}, {gender.name.title()}")
        item.setData(_ID_SUBSTRING_ROLE, substring_id)
        item.setData(_TEXT_SUBSTRING_ROLE, "")
        self.ui.substringList.addItem(item)

        proxy_index: QModelIndex = self.ui.treeView.selectedIndexes()[0]
        tree_source_index = self.proxy_model.mapToSource(proxy_index)
        tree_item = self.model.itemFromIndex(tree_source_index)
        locstring: LocalizedString = tree_item.data(_VALUE_NODE_ROLE)
        locstring.set_data(language, gender, "")

    def remove_substring(self):
        language = Language(self.ui.substringLangCombo.currentIndex())
        gender = Gender(self.ui.substringGenderCombo.currentIndex())
        substring_id = LocalizedString.substring_id(language, gender)
        for i in range(self.ui.substringList.count())[::-1]:
            item = self.ui.substringList.item(i)
            if item is None:
                self._logger.warning(f"substringList item at index {i} was None, skipping")
                continue
            if item.data(_ID_SUBSTRING_ROLE) == substring_id:
                self.ui.substringList.takeItem(i)

        proxy_index: QModelIndex = self.ui.treeView.selectedIndexes()[0]
        tree_source_index = self.proxy_model.mapToSource(proxy_index)
        tree_item = self.model.itemFromIndex(tree_source_index)
        locstring: LocalizedString = tree_item.data(_VALUE_NODE_ROLE)
        locstring.remove(language, gender)

    def refresh_item_text(self, item: QStandardItem):
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
        self.apply_palette(item, ftype)

        #if ftype == GFFFieldType.Struct or ftype is None:
        #    item.setForeground(QBrush(QColor(0x660000)))
        #elif ftype == GFFFieldType.List:
        #    item.setForeground(QBrush(QColor(0x000088)))
        #else:
        #    item.setForeground(QBrush(QColor(0x000000)))

        item.setText(text)

    def typeChanged(self, ftype_enum_value: int):
        ftype = GFFFieldType(ftype_enum_value)
        proxy_index = self.ui.treeView.selectedIndexes()[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.model.itemFromIndex(source_index)
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
        self.load_item(item)  # type: ignore[]
        self.refresh_item_text(item)

    def insert_node(self, parent: QStandardItem, label: str, ftype: GFFFieldType, value: Any) -> QStandardItem:
        item = QStandardItem("")
        item.setData(label, _LABEL_NODE_ROLE)
        item.setData(ftype, _TYPE_NODE_ROLE)
        item.setData(value, _VALUE_NODE_ROLE)
        parent.appendRow(item)
        self.refresh_item_text(item)
        return item

    def addNode(self, item: QStandardItem):
        def set_spinbox(minv: int, maxv: int, item: QStandardItem):
            self.ui.pages.setCurrentWidget(self.ui.intPage)
            self.ui.intSpin.setRange(minv, maxv)
            self.ui.intSpin.setValue(item.data(_VALUE_NODE_ROLE))

        parent_type = item.data(_TYPE_NODE_ROLE)
        new_value = GFFStruct()
        new_label = "[New Struct]"
        if parent_type == GFFFieldType.List:
            self.ui.fieldBox.setEnabled(False)
            new_value = new_value.struct_id
            new_label = str(item.rowCount())
        new_item = self.insert_node(item, new_label, GFFFieldType.Struct, new_value)
        set_spinbox(-1, 0xFFFFFFFF, new_item)

    def remove_node(self, item: QStandardItem):
        parent_item = item.parent()
        if parent_item is None:
            QMessageBox(QMessageBox.Icon.Critical, "Invalid action attempted", "Cannot remove the top-level [ROOT] item.").exec()
            return
        parent_item.removeRow(item.row())
        self.refresh_item_text(item)

    def remove_selectedNodes(self):
        for proxy_index in self.ui.treeView.selectedIndexes():
            source_index = self.proxy_model.mapToSource(proxy_index)
            item = self.model.itemFromIndex(source_index)
            assert item is not None
            self.remove_node(item)

    def on_context_menu(self, point: QPoint):
        proxy_index = self.ui.treeView.indexAt(point)
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.model.itemFromIndex(source_index)
        if item is None:
            return

        menu = QMenu(self)
        nested_type = item.data(_TYPE_NODE_ROLE)
        if nested_type == GFFFieldType.List:
            menu.addAction("Add Struct").triggered.connect(lambda: self.addNode(item))
        elif nested_type in {GFFFieldType.Struct, None}:
            self._build_context_menu_gff_struct(menu, item)
        menu.addAction("Remove").triggered.connect(lambda: self.remove_node(item))
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
        menu.addAction("Add UInt8").triggered.connect(lambda: self.insert_node(item, "New UInt8", GFFFieldType.UInt8, 0))
        menu.addAction("Add UInt16").triggered.connect(lambda: self.insert_node(item, "New UInt16", GFFFieldType.UInt16, 0))
        menu.addAction("Add UInt32").triggered.connect(lambda: self.insert_node(item, "New UInt32", GFFFieldType.UInt32, 0))
        menu.addAction("Add UInt64").triggered.connect(lambda: self.insert_node(item, "New UInt64", GFFFieldType.UInt64, 0))
        menu.addAction("Add Int8").triggered.connect(lambda: self.insert_node(item, "New Int8", GFFFieldType.Int8, 0))
        menu.addAction("Add Int16").triggered.connect(lambda: self.insert_node(item, "New Int16", GFFFieldType.Int16, 0))
        menu.addAction("Add Int32").triggered.connect(lambda: self.insert_node(item, "New Int32", GFFFieldType.Int32, 0))
        menu.addAction("Add Int64").triggered.connect(lambda: self.insert_node(item, "New Int64", GFFFieldType.Int64, 0))
        menu.addAction("Add Single").triggered.connect(lambda: self.insert_node(item, "New Single", GFFFieldType.Single, 0.0))
        menu.addAction("Add Double").triggered.connect(lambda: self.insert_node(item, "New Double", GFFFieldType.Double, 0.0))
        menu.addAction("Add ResRef").triggered.connect(lambda: self.insert_node(item, "New ResRef", GFFFieldType.ResRef, 0))
        menu.addAction("Add String").triggered.connect(lambda: self.insert_node(item, "New String", GFFFieldType.String, 0))
        menu.addAction("Add LocalizedString").triggered.connect(
            lambda: self.insert_node(
                item,
                "New LocalizedString",
                GFFFieldType.LocalizedString,
                LocalizedString.from_invalid(),
            ),
        )
        menu.addAction("Add Binary").triggered.connect(lambda: self.insert_node(item, "New Binary", GFFFieldType.Binary, b""))
        menu.addAction("Add Vector3").triggered.connect(lambda: self.insert_node(item, "New Vector3", GFFFieldType.Vector3, Vector3.from_null()))
        menu.addAction("Add Vector4").triggered.connect(lambda: self.insert_node(item, "New Vector4", GFFFieldType.Vector4, Vector3.from_null()))
        menu.addSeparator()
        menu.addAction("Add Struct").triggered.connect(lambda: self.insert_node(item, "New Struct", GFFFieldType.Struct, GFFStruct()))
        menu.addAction("Add List").triggered.connect(lambda: self.insert_node(item, "New List", GFFFieldType.List, GFFList()))
        menu.addSeparator()

    def select_talk_table(self):
        """Select a TLK file using a file dialog.

        Args:
        ----
            self: The class instance
        """
        filepath, filter = QFileDialog.getOpenFileName(self, "Select a TLK file", "", "TalkTable (*.tlk)")
        if not filepath:
            return
        self._talktable = TalkTable(filepath)

    def change_locstring_text(self):
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

    def adjustColor(
        self,
        base_color: QColor,
        hue_shift: int = 0,
        saturation_factor: float = 1.0,
        value_factor: float = 1.0,
    ) -> QColor:
        color = base_color if isinstance(base_color, QColor) else QColor(base_color)
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

    def apply_palette(self, item: QStandardItem, ftype: GFFFieldType):
        palette = self.palette()
        #number_base_color = palette.highlight().color()
        field_type_colors = {
            #GFFFieldType.UInt8: self.adjustColor(number_base_color, saturation_factor=1.0, value_factor=1.0),
            #GFFFieldType.Int8: self.adjustColor(number_base_color, saturation_factor=0.8, value_factor=0.9),
            #GFFFieldType.UInt16: self.adjustColor(number_base_color, hue_shift=15, saturation_factor=1.0, value_factor=1.0),
            #GFFFieldType.Int16: self.adjustColor(number_base_color, hue_shift=15, saturation_factor=0.8, value_factor=0.9),
            #GFFFieldType.UInt32: self.adjustColor(number_base_color, hue_shift=30, saturation_factor=1.0, value_factor=1.2),
            #GFFFieldType.Int32: self.adjustColor(number_base_color, hue_shift=30, saturation_factor=0.9, value_factor=1.1),
            #GFFFieldType.UInt64: self.adjustColor(number_base_color, hue_shift=45, saturation_factor=1.0, value_factor=1.0),
            #GFFFieldType.Int64: self.adjustColor(number_base_color, hue_shift=45, saturation_factor=0.8, value_factor=0.9),
            #GFFFieldType.Single: self.adjustColor(number_base_color, hue_shift=60, saturation_factor=1.0, value_factor=1.0),
            #GFFFieldType.Double: self.adjustColor(number_base_color, hue_shift=60, saturation_factor=0.8, value_factor=0.9),
            #GFFFieldType.ResRef: palette.windowText().color(),
            #GFFFieldType.String: palette.text().color(),
            #GFFFieldType.LocalizedString: palette.buttonText().color(),
            #GFFFieldType.Vector3: self.adjustColor(palette.buttonText().color(), hue_shift=90, saturation_factor=0.8, value_factor=1.1),
            #GFFFieldType.Vector4: self.adjustColor(palette.buttonText().color(), hue_shift=90, saturation_factor=0.8, value_factor=1.3),
            GFFFieldType.Struct: QColor("darkGreen"),
            GFFFieldType.List: self.adjustColor(palette.highlight().color(), hue_shift=120, saturation_factor=0.8, value_factor=1.1),
            #GFFFieldType.Binary: palette.midlight().color(),
        }
        if ftype in field_type_colors:
            item.setForeground(QBrush(field_type_colors[ftype]))


class GFFSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        source_model = self.sourceModel()
        assert isinstance(source_model, QStandardItemModel), f"Source model is not a QStandardItemModel, was: {type(source_model).__name__}"
        left_text: str = source_model.itemFromIndex(left).data(_LABEL_NODE_ROLE)
        right_text: str = source_model.itemFromIndex(right).data(_LABEL_NODE_ROLE)

        left_text = left_text or str(source_model.itemFromIndex(left).data(_VALUE_NODE_ROLE))
        right_text = right_text or str(source_model.itemFromIndex(right).data(_VALUE_NODE_ROLE))

        if left_text.isdigit() and right_text.isdigit():
            left_int = int(left_text)
            right_int = int(right_text)
            return left_int < right_int
        return left_text < right_text
