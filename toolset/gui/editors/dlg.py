from copy import deepcopy, copy
from typing import Optional, List, Tuple

from PyQt5 import QtCore
from PyQt5.QtCore import QItemSelection, QBuffer, QIODevice, QPoint, QItemSelectionModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QWidget, QListWidgetItem, QPlainTextEdit, QMenu, QMessageBox, QShortcut, QDialog

from gui.dialogs.locstring import LocalizedStringDialog
from gui.editor import Editor
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import DLG, DLGLink, DLGNode, DLGReply, DLGEntry, dismantle_dlg, \
    DLGConversationType, DLGComputerType, DLGAnimation, DLGStunt, read_dlg
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation


_LINK_ROLE = QtCore.Qt.UserRole + 1
_COPY_ROLE = QtCore.Qt.UserRole + 2


class DLGEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[HTInstallation] = None):
        supported = [ResourceType.DLG]
        super().__init__(parent, "Dialog Editor", "dialog", supported, supported, installation)

        from toolset.uic.editors.dlg import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self._focused: bool = False
        self._dlg: DLG = DLG()
        self._copy: Optional[DLGNode] = None
        self.model: QStandardItemModel = QStandardItemModel(self)
        self.ui.dialogTree.setModel(self.model)

        self.ui.dialogTree.customContextMenuRequested.connect(self.onTreeContextMenu)
        self.ui.dialogTree.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        self.ui.textEdit.mouseDoubleClickEvent = self.editText

        self.buffer: QBuffer = QBuffer()
        self.player: QMediaPlayer = QMediaPlayer(self)

        # This boolean is used to prevent events firing onNodeUpdate() when values are changed programatically
        self.acceptUpdates: bool = False

        # Make the bottom panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setupSignals(self) -> None:
        # Events to update link/nodes connected to its respective tree view item
        self.ui.speakerEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.listenerEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.script1ResrefEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.script1Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.script2ResrefEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.script2Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition1ResrefEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition1Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition2ResrefEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition1NotCheckbox.stateChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition2NotCheckbox.stateChanged.connect(self.onNodeUpdate)
        self.ui.emotionSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.expressionSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.soundEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.voiceEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.soundCheckbox.toggled.connect(self.onNodeUpdate)
        self.ui.plotIndexSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.plotXpSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.questEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.questEntrySpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.cameraIdSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.cameraAngleSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.cameraEffectSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.nodeUnskippableCheckbox.toggled.connect(self.onNodeUpdate)
        self.ui.nodeIdSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.alienRaceNodeSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.postProcSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.delaySpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.logicSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.waitFlagSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.fadeTypeSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.commentsEdit.textChanged.connect(self.onNodeUpdate)

        self.ui.soundButton.clicked.connect(lambda: self.playSound(self.ui.soundEdit.text()))
        self.ui.voiceButton.clicked.connect(lambda: self.playSound(self.ui.voiceEdit.text()))

        self.ui.actionReloadTree.triggered.connect(lambda: self._loadDLG(self._dlg))

        self.ui.addStuntButton.clicked.connect(self.onAddStuntClicked)
        self.ui.removeStuntButton.clicked.connect(self.onRemoveStuntClicked)
        self.ui.editStuntButton.clicked.connect(self.onEditStuntClicked)

        self.ui.addAnimButton.clicked.connect(self.onAddAnimClicked)
        self.ui.removeAnimButton.clicked.connect(self.onRemoveAnimClicked)
        self.ui.editAnimButton.clicked.connect(self.onEditAnimClicked)

        QShortcut("Del", self).activated.connect(self.deleteSelectedNode)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        dlg = read_dlg(data)
        self._loadDLG(dlg)
        self.refreshStuntList()

        self.ui.onAbortEdit.setText(dlg.on_abort.get())
        self.ui.onEndEdit.setText(dlg.on_end.get())
        self.ui.voIdEdit.setText(dlg.vo_id)
        self.ui.ambientTrackEdit.setText(dlg.ambient_track.get())
        self.ui.cameraModelEdit.setText(dlg.camera_model.get())
        self.ui.conversationSelect.setCurrentIndex(dlg.conversation_type.value)
        self.ui.computerSelect.setCurrentIndex(dlg.computer_type.value)
        self.ui.skippableCheckbox.setChecked(dlg.skippable)
        self.ui.animatedCutCheckbox.setChecked(dlg.animated_cut)
        self.ui.oldHitCheckbox.setChecked(dlg.old_hit_check)
        self.ui.unequipHandsCheckbox.setChecked(dlg.unequip_hands)
        self.ui.unequipAllCheckbox.setChecked(dlg.unequip_items)
        self.ui.entryDelaySpin.setValue(dlg.delay_entry)
        self.ui.replyDelaySpin.setValue(dlg.delay_reply)

    def _loadDLG(self, dlg: DLG):
        self.ui.dialogTree.setStyleSheet("")
        self._focused = False

        self._dlg = dlg
        self.model.clear()
        seenLink = []
        seenNode = []
        for start in dlg.starters:
            item = QStandardItem()
            self._loadDLGRec(item, start, seenLink, seenNode)
            self.model.appendRow(item)

    def _loadDLGRec(self, item: QStandardItem, link: DLGLink, seenLink: List[DLGLink], seenNode: List[DLGNode]):
        node = link.node
        item.setData(link, _LINK_ROLE)

        alreadyListed = link in seenLink or node in seenNode
        if not link in seenLink:
            seenLink.append(link)
        if not node in seenNode:
            seenNode.append(node)

        item.setData(alreadyListed, _COPY_ROLE)
        self.refreshItem(item)

        if not alreadyListed:
            for child_link in node.links:
                child_item = QStandardItem()
                self._loadDLGRec(child_item, child_link, seenLink, seenNode)
                item.appendRow(child_item)

    def build(self) -> Tuple[bytes, bytes]:
        self._dlg.on_abort = ResRef(self.ui.onAbortEdit.text())
        self._dlg.on_end = ResRef(self.ui.onEndEdit.text())
        self._dlg.vo_id = self.ui.voIdEdit.text()
        self._dlg.ambient_track = ResRef(self.ui.ambientTrackEdit.text())
        self._dlg.camera_model = ResRef(self.ui.cameraModelEdit.text())
        self._dlg.conversation_type = DLGConversationType(self.ui.conversationSelect.currentIndex())
        self._dlg.computer_type = DLGComputerType(self.ui.computerSelect.currentIndex())
        self._dlg.skippable = self.ui.skippableCheckbox.isChecked()
        self._dlg.animated_cut = self.ui.animatedCutCheckbox.isChecked()
        self._dlg.old_hit_check = self.ui.oldHitCheckbox.isChecked()
        self._dlg.unequip_hands = self.ui.unequipHandsCheckbox.isChecked()
        self._dlg.unequip_items = self.ui.unequipAllCheckbox.isChecked()
        self._dlg.delay_entry = self.ui.entryDelaySpin.value()
        self._dlg.delay_reply = self.ui.replyDelaySpin.value()

        data = bytearray()
        write_gff(dismantle_dlg(self._dlg), data)
        return data, b''

    def new(self) -> None:
        super().new()
        self._loadDLG(DLG())

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation

        self.ui.script1Param1Spin.setEnabled(installation.tsl)
        self.ui.script1Param2Spin.setEnabled(installation.tsl)
        self.ui.script1Param3Spin.setEnabled(installation.tsl)
        self.ui.script1Param4Spin.setEnabled(installation.tsl)
        self.ui.script1Param5Spin.setEnabled(installation.tsl)
        self.ui.script1Param6Edit.setEnabled(installation.tsl)

        self.ui.script2ResrefEdit.setEnabled(installation.tsl)
        self.ui.script2Param1Spin.setEnabled(installation.tsl)
        self.ui.script2Param2Spin.setEnabled(installation.tsl)
        self.ui.script2Param3Spin.setEnabled(installation.tsl)
        self.ui.script2Param4Spin.setEnabled(installation.tsl)
        self.ui.script2Param5Spin.setEnabled(installation.tsl)
        self.ui.script2Param6Edit.setEnabled(installation.tsl)

        self.ui.condition1Param1Spin.setEnabled(installation.tsl)
        self.ui.condition1Param2Spin.setEnabled(installation.tsl)
        self.ui.condition1Param3Spin.setEnabled(installation.tsl)
        self.ui.condition1Param4Spin.setEnabled(installation.tsl)
        self.ui.condition1Param5Spin.setEnabled(installation.tsl)
        self.ui.condition1Param6Edit.setEnabled(installation.tsl)
        self.ui.condition1NotCheckbox.setEnabled(installation.tsl)

        self.ui.condition2ResrefEdit.setEnabled(installation.tsl)
        self.ui.condition2Param1Spin.setEnabled(installation.tsl)
        self.ui.condition2Param2Spin.setEnabled(installation.tsl)
        self.ui.condition2Param3Spin.setEnabled(installation.tsl)
        self.ui.condition2Param4Spin.setEnabled(installation.tsl)
        self.ui.condition2Param5Spin.setEnabled(installation.tsl)
        self.ui.condition2Param6Edit.setEnabled(installation.tsl)
        self.ui.condition2NotCheckbox.setEnabled(installation.tsl)

        self.ui.emotionSelect.setEnabled(installation.tsl)
        self.ui.expressionSelect.setEnabled(installation.tsl)

        self.ui.nodeUnskippableCheckbox.setEnabled(installation.tsl)
        self.ui.nodeIdSpin.setEnabled(installation.tsl)
        self.ui.alienRaceNodeSpin.setEnabled(installation.tsl)
        self.ui.postProcSpin.setEnabled(installation.tsl)
        self.ui.logicSpin.setEnabled(installation.tsl)

        # Load required 2da files if they have not been loaded already
        required = [HTInstallation.TwoDA_EMOTIONS, HTInstallation.TwoDA_EXPRESSIONS, HTInstallation.TwoDA_VIDEO_EFFECTS,
                    HTInstallation.TwoDA_DIALOG_ANIMS]
        installation.htBatchCache2DA(required)

        videoEffects = installation.htGetCache2DA(HTInstallation.TwoDA_VIDEO_EFFECTS)

        if installation.tsl:
            expressions = installation.htGetCache2DA(HTInstallation.TwoDA_EXPRESSIONS)
            emotions = installation.htGetCache2DA(HTInstallation.TwoDA_EMOTIONS)

            self.ui.emotionSelect.clear()
            [self.ui.emotionSelect.addItem(label.replace("_", " ")) for label in emotions.get_column("label")]

            self.ui.expressionSelect.clear()
            [self.ui.expressionSelect.addItem(label) for label in expressions.get_column("label")]

        self.ui.cameraEffectSelect.clear()
        self.ui.cameraEffectSelect.addItem("[None]", None)
        for i, label in enumerate(videoEffects.get_column("label")):
            self.ui.cameraEffectSelect.addItem(label.replace("VIDEO_EFFECT_", "").replace("_" , " ").title(), i)

    def editText(self, e) -> None:
        indexes = self.ui.dialogTree.selectionModel().selectedIndexes()
        if indexes:
            item = self.model.itemFromIndex(indexes[0])
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            node: DLGNode = link.node
            dialog = LocalizedStringDialog(self, self._installation, node.text)
            if dialog.exec_() and not isCopy:
                node.text = dialog.locstring
                item.setText(self._installation.string(node.text, "(continue"))
                self._loadLocstring(self.ui.textEdit, node.text)

    def _loadLocstring(self, textbox: QPlainTextEdit, locstring: LocalizedString) -> None:
        if locstring.stringref == -1:
            text = str(locstring)
            textbox.setPlainText(text if text != "-1" else "")
            textbox.setStyleSheet("QPlainTextEdit {background-color: white;}")
        else:
            text = self._installation.talktable().string(locstring.stringref)
            textbox.setPlainText(text)
            textbox.setStyleSheet("QPlainTextEdit {background-color: #fffded;}")

    def addNode(self, item: Optional[QStandardItem], node: DLGNode) -> None:
        # Update DLG
        newNode = DLGEntry() if isinstance(node, DLGReply) else DLGReply()
        newLink = DLGLink(newNode)
        node.links.append(newLink)

        # Sync TreeView with DLG
        newItem = QStandardItem()
        newItem.setData(newLink, _LINK_ROLE)
        newItem.setData(False, _COPY_ROLE)

        self.refreshItem(newItem)
        item.appendRow(newItem)

    def addRootNode(self) -> None:
        newNode = DLGEntry()
        newLink = DLGLink(newNode)
        self._dlg.starters.append(newLink)

        newItem = QStandardItem()
        newItem.setData(newLink, _LINK_ROLE)
        newItem.setData(False, _COPY_ROLE)

        self.refreshItem(newItem)
        self.model.appendRow(newItem)

    def addCopyLink(self, item: QStandardItem, target: DLGNode, source: DLGNode):
        newLink = DLGLink(source)
        target.links.append(newLink)

        newItem = QStandardItem()
        newItem.setData(newLink, _LINK_ROLE)
        newItem.setData(True, _COPY_ROLE)

        self.refreshItem(newItem)
        item.appendRow(newItem)

    def addCopy(self, item: QStandardItem, target: DLGNode, source: DLGNode):
        sourceCopy = deepcopy(source)
        newLink = DLGLink(sourceCopy)
        target.links.append(newLink)

        newItem = QStandardItem()
        self._loadDLGRec(newItem, newLink, [], [])
        item.appendRow(newItem)

    def copyNode(self, node: DLGNode):
        self._copy = node

    def deleteNode(self, item: QStandardItem) -> None:
        link: DLGLink = item.data(_LINK_ROLE)
        node: DLGNode = link.node

        if item.parent() is None:
            for link in copy(self._dlg.starters):
                if link.node is node:
                    self._dlg.starters.remove(link)
            self.model.removeRow(item.row())
        else:
            parentItem = item.parent()
            parentLink: DLGLink = parentItem.data(_LINK_ROLE)
            parentNode: DLGNode = parentLink.node

            for link in copy(parentNode.links):
                if link.node is node:
                    parentNode.links.remove(link)
            parentItem.removeRow(item.row())

    def deleteSelectedNode(self) -> None:
        if self.ui.dialogTree.selectedIndexes():
            index = self.ui.dialogTree.selectedIndexes()[0]
            item = self.model.itemFromIndex(index)
            self.deleteNode(item)

    def expandToRoot(self, item: QStandardItem):
        parent = item.parent()
        while parent is not None:
            self.ui.dialogTree.expand(parent.index())
            parent = parent.parent()

    def jumpToOriginal(self, sourceItem: QStandardItem):
        copiedLink: DLGLink = sourceItem.data(_LINK_ROLE)
        copiedNode: DLGNode = copiedLink.node

        items = [self.model.item(i, 0) for i in range(self.model.rowCount())]
        while items:
            item = items.pop()
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            if link.node is copiedNode and not isCopy:
                self.expandToRoot(item)
                self.ui.dialogTree.setCurrentIndex(item.index())
                break
            items.extend([item.child(i, 0) for i in range(item.rowCount())])
        else:
            print("Failed to find original")

    def refreshItem(self, item: QStandardItem):
        node: DLGNode = item.data(_LINK_ROLE).node
        isCopy: bool = item.data(_COPY_ROLE)
        text = self._installation.string(node.text, "(continue)")
        item.setText(text)

        if not node.links:
            item.setText(item.text() + " [End Dialog]")

        if isinstance(node, DLGReply):
            color = QColor(90, 90, 210) if isCopy else QColor(0, 0, 255)
            item.setForeground(QBrush(color))
        elif isinstance(node, DLGEntry):
            color = QColor(210, 90, 90) if isCopy else QColor(255, 0, 0)
            item.setForeground(QBrush(color))

    def playSound(self, resname: str) -> None:
        self.player.stop()

        data = self._installation.sound(resname, [SearchLocation.VOICE, SearchLocation.SOUND, SearchLocation.OVERRIDE,
                                                  SearchLocation.CHITIN])

        if data:
            self.buffer = QBuffer(self)
            self.buffer.setData(data)
            self.buffer.open(QIODevice.ReadOnly)
            self.player.setMedia(QMediaContent(), self.buffer)
            QtCore.QTimer.singleShot(0, self.player.play)
        else:
            QMessageBox(QMessageBox.Critical, "Could not find audio file", "Could not find audio resource '{}'.".format(resname))

    def focusOnNode(self, link: DLGLink) -> None:
        self.ui.dialogTree.setStyleSheet("QTreeView { background: #FFFFEE; }")
        self.model.clear()
        self._focused = True

        item = QStandardItem()
        self._loadDLGRec(item, link, [], [])
        self.model.appendRow(item)

    def shiftItem(self, item: QStandardItem, amount: int) -> None:
        oldRow = item.row()
        parent = self.model if item.parent() is None else item.parent()
        newRow = oldRow + amount

        if newRow >= parent.rowCount() or newRow < 0:
            return  # Already at the start/end of the branch

        item = parent.takeRow(oldRow)[0]
        parent.insertRow(newRow, item)
        self.ui.dialogTree.selectionModel().select(item.index(), QItemSelectionModel.ClearAndSelect)

        # Sync DLG to tree changes
        links = self._dlg.starters if item.parent() is None else item.parent().data(_LINK_ROLE).node.links
        link = links.pop(oldRow)
        links.insert(newRow, link)

    def onTreeContextMenu(self, point: QPoint):
        index = self.ui.dialogTree.indexAt(point)
        item = self.model.itemFromIndex(index)

        if item is not None:
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            node: DLGNode = link.node

            menu = QMenu(self)

            menu.addAction("Focus").triggered.connect(lambda: self.focusOnNode(link))
            menu.addSeparator()
            menu.addAction("Move Up").triggered.connect(lambda: self.shiftItem(item, -1))
            menu.addAction("Move Down").triggered.connect(lambda: self.shiftItem(item, 1))
            menu.addSeparator()

            if not isCopy:
                if isinstance(node, DLGReply):
                    menu.addAction("Add Entry").triggered.connect(lambda: self.addNode(item, node))
                    if isinstance(self._copy, DLGEntry):
                        menu.addAction("Paste Entry as Link").triggered.connect(lambda: self.addCopyLink(item, node, self._copy))
                        menu.addAction("Paste Entry as New").triggered.connect(lambda: self.addCopy(item, node, self._copy))
                elif isinstance(node, DLGEntry):
                    menu.addAction("Add Reply").triggered.connect(lambda: self.addNode(item, node))
                    if isinstance(self._copy, DLGReply):
                        menu.addAction("Paste Reply as Link").triggered.connect(lambda: self.addCopyLink(item, node, self._copy))
                        menu.addAction("Paste Reply as New").triggered.connect(lambda: self.addCopy(item, node, self._copy))
                else:
                    ...
            else:
                menu.addAction("Jump to Original").triggered.connect(lambda: self.jumpToOriginal(item))

            if isinstance(node, DLGReply):
                menu.addAction("Copy Reply").triggered.connect(lambda: self.copyNode(node))
                menu.addAction("Delete Reply").triggered.connect(lambda: self.deleteNode(item))
            elif isinstance(node, DLGEntry):
                menu.addAction("Copy Entry").triggered.connect(lambda: self.copyNode(node))
                menu.addAction("Delete Entry").triggered.connect(lambda: self.deleteNode(item))

            menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))
        elif not self._focused:
            menu = QMenu(self)

            menu.addAction("Add Entry").triggered.connect(lambda: self.addRootNode())

            menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def onSelectionChanged(self, selection: QItemSelection) -> None:
        self.acceptUpdates = False
        if selection.indexes():
            item = self.model.itemFromIndex(selection.indexes()[0])
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            node: DLGNode = link.node

            if isinstance(node, DLGEntry):
                self.ui.speakerEdit.setEnabled(True)
                self.ui.speakerEdit.setText(node.speaker)
            elif isinstance(node, DLGReply):
                self.ui.speakerEdit.setEnabled(False)
                self.ui.speakerEdit.setText("")

            self.ui.textEdit.setEnabled(not isCopy)

            self.ui.listenerEdit.setText(node.listener)
            self._loadLocstring(self.ui.textEdit, node.text)

            self.ui.script1ResrefEdit.setText(node.script1.get())
            self.ui.script1Param1Spin.setValue(node.script1_param1)
            self.ui.script1Param2Spin.setValue(node.script1_param2)
            self.ui.script1Param3Spin.setValue(node.script1_param3)
            self.ui.script1Param4Spin.setValue(node.script1_param4)
            self.ui.script1Param5Spin.setValue(node.script1_param5)
            self.ui.script1Param6Edit.setText(node.script1_param6)

            self.ui.script2ResrefEdit.setText(node.script2.get())
            self.ui.script2Param1Spin.setValue(node.script2_param1)
            self.ui.script2Param2Spin.setValue(node.script2_param2)
            self.ui.script2Param3Spin.setValue(node.script2_param3)
            self.ui.script2Param4Spin.setValue(node.script2_param4)
            self.ui.script2Param5Spin.setValue(node.script2_param5)
            self.ui.script2Param6Edit.setText(node.script2_param6)

            self.ui.condition1ResrefEdit.setText(link.active1.get())
            self.ui.condition1Param1Spin.setValue(link.active1_param1)
            self.ui.condition1Param2Spin.setValue(link.active1_param2)
            self.ui.condition1Param3Spin.setValue(link.active1_param3)
            self.ui.condition1Param4Spin.setValue(link.active1_param4)
            self.ui.condition1Param5Spin.setValue(link.active1_param5)
            self.ui.condition1Param6Edit.setText(link.active1_param6)
            self.ui.condition1NotCheckbox.setChecked(link.active1_not)

            self.ui.condition2ResrefEdit.setText(link.active2.get())
            self.ui.condition2Param1Spin.setValue(link.active2_param1)
            self.ui.condition2Param2Spin.setValue(link.active2_param2)
            self.ui.condition2Param3Spin.setValue(link.active2_param3)
            self.ui.condition2Param4Spin.setValue(link.active2_param4)
            self.ui.condition2Param5Spin.setValue(link.active2_param5)
            self.ui.condition2Param6Edit.setText(link.active2_param6)
            self.ui.condition2NotCheckbox.setChecked(link.active2_not)

            self.refreshAnimList()
            self.ui.emotionSelect.setCurrentIndex(node.emotion_id)
            self.ui.expressionSelect.setCurrentIndex(node.facial_id)
            self.ui.soundEdit.setText(node.sound.get())
            self.ui.soundCheckbox.setChecked(node.sound_exists)
            self.ui.voiceEdit.setText(node.vo_resref.get())

            self.ui.plotIndexSpin.setValue(node.plot_index)
            self.ui.plotXpSpin.setValue(node.plot_xp_percentage)
            self.ui.questEdit.setText(node.quest)
            self.ui.questEntrySpin.setValue(node.quest_entry)

            self.ui.cameraIdSpin.setValue(node.camera_id if node.camera_id is not None else -1)
            self.ui.cameraAnimSpin.setValue(node.camera_anim if node.camera_anim is not None else -1)
            self.ui.cameraAngleSelect.setCurrentIndex(node.camera_angle if node.camera_angle is not None else 0)
            self.ui.cameraEffectSelect.setCurrentIndex(node.camera_effect+1 if node.camera_effect is not None else 0)

            self.ui.nodeUnskippableCheckbox.setChecked(node.unskippable)
            self.ui.nodeIdSpin.setValue(node.node_id)
            self.ui.alienRaceNodeSpin.setValue(node.alien_race_node)
            self.ui.postProcSpin.setValue(node.post_proc_node)
            self.ui.delaySpin.setValue(node.delay)
            self.ui.logicSpin.setValue(link.logic)
            self.ui.waitFlagSpin.setValue(node.wait_flags)
            self.ui.fadeTypeSpin.setValue(node.fade_type)

            self.ui.commentsEdit.setPlainText(node.comment)
        self.acceptUpdates = True

    def onNodeUpdate(self) -> None:
        if self.ui.dialogTree.selectedIndexes() and self.acceptUpdates:
            index = self.ui.dialogTree.selectedIndexes()[0]
            item = self.model.itemFromIndex(index)

            link: DLGLink = item.data(_LINK_ROLE)
            node: DLGNode = link.node

            node.listener = self.ui.listenerEdit.text()
            if isinstance(node, DLGEntry):
                node.speaker = self.ui.speakerEdit.text()

            # Scripts
            node.script1 = ResRef(self.ui.script1ResrefEdit.text())
            node.script1_param1 = self.ui.script1Param1Spin.value()
            node.script1_param2 = self.ui.script1Param2Spin.value()
            node.script1_param3 = self.ui.script1Param3Spin.value()
            node.script1_param4 = self.ui.script1Param4Spin.value()
            node.script1_param5 = self.ui.script1Param5Spin.value()
            node.script1_param6 = self.ui.script1Param6Edit.text()
            node.script2 = ResRef(self.ui.script2ResrefEdit.text())
            node.script2_param1 = self.ui.script2Param1Spin.value()
            node.script2_param2 = self.ui.script2Param2Spin.value()
            node.script2_param3 = self.ui.script2Param3Spin.value()
            node.script2_param4 = self.ui.script2Param4Spin.value()
            node.script2_param5 = self.ui.script2Param5Spin.value()
            node.script2_param6 = self.ui.script2Param6Edit.text()

            link.active1 = ResRef(self.ui.condition1ResrefEdit.text())
            link.active1_param1 = self.ui.condition1Param1Spin.value()
            link.active1_param2 = self.ui.condition1Param2Spin.value()
            link.active1_param3 = self.ui.condition1Param3Spin.value()
            link.active1_param4 = self.ui.condition1Param4Spin.value()
            link.active1_param5 = self.ui.condition1Param5Spin.value()
            link.active1_param6 = self.ui.condition1Param6Edit.text()
            link.active1_not = self.ui.condition1NotCheckbox.isChecked()
            link.active2 = ResRef(self.ui.condition2ResrefEdit.text())
            link.active2_param1 = self.ui.condition2Param1Spin.value()
            link.active2_param2 = self.ui.condition2Param2Spin.value()
            link.active2_param3 = self.ui.condition2Param3Spin.value()
            link.active2_param4 = self.ui.condition2Param4Spin.value()
            link.active2_param5 = self.ui.condition2Param5Spin.value()
            link.active2_param6 = self.ui.condition2Param6Edit.text()
            link.active2_not = self.ui.condition2NotCheckbox.isChecked()

            # Animations
            node.emotion_id = self.ui.emotionSelect.currentIndex()
            node.facial_id = self.ui.expressionSelect.currentIndex()
            node.sound = ResRef(self.ui.soundEdit.text())
            node.sound_exists = self.ui.soundCheckbox.isChecked()
            node.vo_resref = ResRef(self.ui.voiceEdit.text())

            # Journal
            node.plot_index = self.ui.plotIndexSpin.value()
            node.plot_xp_percentage = self.ui.plotXpSpin.value()
            node.quest = self.ui.questEdit.text()
            node.quest_entry = self.ui.questEntrySpin.value()

            # Camera
            node.camera_id = self.ui.cameraIdSpin.value()
            node.camera_anim = self.ui.cameraAnimSpin.value()
            node.camera_angle = self.ui.cameraAngleSelect.currentIndex()
            node.camera_effect = self.ui.cameraEffectSelect.currentData()
            if node.camera_id >= 0 and self.ui.cameraAngleSelect.currentIndex() == 0:
                self.ui.cameraAngleSelect.setCurrentIndex(6)
            elif node.camera_id == -1 and self.ui.cameraAngleSelect.currentIndex() == 6:
                self.ui.cameraAngleSelect.setCurrentIndex(0)

            # Other
            node.unskippable = self.ui.nodeUnskippableCheckbox.isChecked()
            node.node_id = self.ui.nodeIdSpin.value()
            node.alien_race_node = self.ui.alienRaceNodeSpin.value()
            node.post_proc_node = self.ui.postProcSpin.value()
            node.delay = self.ui.delaySpin.value()
            link.logic = self.ui.logicSpin.value()
            node.wait_flags = self.ui.waitFlagSpin.value()
            node.fade_type = self.ui.fadeTypeSpin.value()

            # Comments
            node.comment = self.ui.commentsEdit.toPlainText()

    def onAddStuntClicked(self) -> None:
        dialog = CutsceneModelDialog(self)
        if dialog.exec_():
            self._dlg.stunts.append(dialog.stunt())
            self.refreshStuntList()

    def onRemoveStuntClicked(self) -> None:
        if self.ui.stuntList.selectedItems():
            item = self.ui.stuntList.selectedItems()[0]
            stunt = item.data(QtCore.Qt.UserRole)
            self._dlg.stunts.remove(stunt)
            self.refreshStuntList()

    def onEditStuntClicked(self) -> None:
        if self.ui.stuntList.selectedItems():
            item = self.ui.stuntList.selectedItems()[0]
            stunt = item.data(QtCore.Qt.UserRole)
            dialog = CutsceneModelDialog(self, stunt)
            if dialog.exec_():
                stunt.stunt_model = dialog.stunt().stunt_model
                stunt.participant = dialog.stunt().participant
                self.refreshStuntList()

    def refreshStuntList(self) -> None:
        self.ui.stuntList.clear()
        for stunt in self._dlg.stunts:
            text = "{} ({})".format(stunt.stunt_model, stunt.participant)
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, stunt)
            self.ui.stuntList.addItem(item)

    def onAddAnimClicked(self) -> None:
        if self.ui.dialogTree.selectedIndexes():
            index = self.ui.dialogTree.selectedIndexes()[0]
            item = self.model.itemFromIndex(index)
            node: DLGNode = item.data(_LINK_ROLE).node

            dialog = EditAnimationDialog(self, self._installation)
            if dialog.exec_():
                node.animations.append(dialog.animation())
                self.refreshAnimList()

    def onRemoveAnimClicked(self) -> None:
        if self.ui.animsList.selectedItems():
            index = self.ui.dialogTree.selectedIndexes()[0]
            item = self.model.itemFromIndex(index)
            node: DLGNode = item.data(_LINK_ROLE).node

            animItem = self.ui.animsList.selectedItems()[0]
            anim = animItem.data(QtCore.Qt.UserRole)
            node.animations.remove(anim)
            self.refreshAnimList()

    def onEditAnimClicked(self) -> None:
        if self.ui.animsList.selectedItems():
            animItem = self.ui.animsList.selectedItems()[0]
            anim = animItem.data(QtCore.Qt.UserRole)
            dialog = EditAnimationDialog(self, self._installation, anim)
            if dialog.exec_():
                anim.animation_id = dialog.animation().animation_id
                anim.participant = dialog.animation().participant
                self.refreshAnimList()

    def refreshAnimList(self) -> None:
        self.ui.animsList.clear()

        if self.ui.dialogTree.selectedIndexes():
            index = self.ui.dialogTree.selectedIndexes()[0]
            item = self.model.itemFromIndex(index)
            link: DLGLink = item.data(_LINK_ROLE)
            node: DLGNode = link.node

            animations_list = self._installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
            for anim in node.animations:
                if animations_list.get_height() > anim.animation_id:
                    name = animations_list.get_cell(anim.animation_id, "name")
                else:
                    name = str(anim.animation_id)
                text = "{} ({})".format(name, anim.participant)
                item = QListWidgetItem(text)
                item.setData(QtCore.Qt.UserRole, anim)
                self.ui.animsList.addItem(item)


class EditAnimationDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, animation: DLGAnimation = DLGAnimation()):
        super().__init__(parent)

        from toolset.uic.dialogs.edit_animation import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        animations_list = installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
        for row in animations_list:
            if row.get_string("name") != "":
                self.ui.animationSelect.addItem(row.get_string("name"), row.label())

        animationIndex = self._getAnimationIndex(animation.animation_id)
        if animationIndex is not None:
            self.ui.animationSelect.setCurrentIndex(animationIndex)
        else:
            self.ui.animationSelect.addItem("[Unknown Animation ID: {}".format(animation.animation_id), animation.animation_id)
            self.ui.animationSelect.setCurrentIndex(self.ui.animationSelect.count() - 1)

        self.ui.participantEdit.setText(animation.participant)

    def _getAnimationIndex(self, animation_id: int):
        for i in range(self.ui.animationSelect.count()):
            if self.ui.animationSelect.itemData(i) == animation_id:
                return i
        return None

    def animation(self) -> DLGAnimation:
        animation = DLGAnimation()
        animation_id = self.ui.animationSelect.itemData(self.ui.animationSelect.currentIndex())
        animation.animation_id = 6 if animation_id is None else int(animation_id) #apparently it doesn't save anims because it saves ids as strs
        animation.participant = self.ui.participantEdit.text()
        return animation


class CutsceneModelDialog(QDialog):
    def __init__(self, parent: QWidget, stunt: DLGStunt = DLGStunt()):
        super().__init__(parent)

        from toolset.uic.dialogs.edit_model import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.participantEdit.setText(stunt.participant)
        self.ui.stuntEdit.setText(stunt.stunt_model.get())

    def stunt(self) -> DLGStunt:
        stunt = DLGStunt()
        stunt.participant = self.ui.participantEdit.text()
        stunt.stunt_model = ResRef(self.ui.stuntEdit.text())
        return stunt
