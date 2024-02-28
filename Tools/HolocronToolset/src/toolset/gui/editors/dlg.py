from __future__ import annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING

import pyperclip

from PyQt5 import QtCore
from PyQt5.QtCore import QBuffer, QIODevice, QItemSelectionModel
from PyQt5.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QListWidgetItem, QMenu, QMessageBox, QShortcut

from pykotor.common.misc import ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.dlg import (
    DLG,
    DLGAnimation,
    DLGComputerType,
    DLGConversationType,
    DLGEntry,
    DLGLink,
    DLGReply,
    DLGStunt,
    read_dlg,
    write_dlg,
)
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.dialog_animation import EditAnimationDialog
from toolset.gui.dialogs.edit.dialog_model import CutsceneModelDialog
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.utils.misc import QtKey
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    import os

    from PyQt5.QtCore import QItemSelection, QModelIndex, QPoint
    from PyQt5.QtGui import QKeyEvent, QMouseEvent
    from PyQt5.QtWidgets import QPlainTextEdit, QWidget

    from pykotor.common.language import LocalizedString
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.dlg import DLGNode

_LINK_ROLE = QtCore.Qt.UserRole + 1
_COPY_ROLE = QtCore.Qt.UserRole + 2


class DLGEditor(Editor):
    def __init__(self, parent: QWidget | None = None, installation: HTInstallation | None = None):
        """Initializes the Dialog Editor window.

        Args:
        ----
            parent: QWidget | None = None: The parent widget
            installation: HTInstallation | None = None: The installation

        Initializes UI components:
            - Sets up menus
            - Connects signals
            - Sets up installation
            - Initializes model, tree view and selection model
            - Sets buffer and media player
            - Sets boolean to prevent events on programatic updates
            - Sets splitter sizes
            - Calls new() to start with empty dialog.
        """
        supported: list[ResourceType] = [ResourceType.DLG]
        super().__init__(parent, "Dialog Editor", "dialog", supported, supported, installation)

        from toolset.uic.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation:  # will always be None in the unittests.
            self._setupInstallation(installation)

        self._focused: bool = False
        self._dlg: DLG = DLG()
        self._copy: DLGNode | None = None
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

    def _setupSignals(self):
        """Connects UI signals to update node/link on change.

        Args:
        ----
            self: {DLGEditor instance}: Connects UI signals to methods

        Processing Logic:
        ----------------
            - Connects text/value changes of various UI elements to onNodeUpdate method
            - Connects buttons to respective methods like play sound, load tree, add/remove anims
            - Connects delete shortcut to delete node.
        """
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

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Loads a dialogue file.

        Args:
        ----
            filepath: The path to the dialogue file
            resref: The resource reference of the dialogue
            restype: The resource type of the dialogue
            data: The raw data of the dialogue file

        Loads dialogue data:
            - Reads dialogue data from file
            - Loads dialogue data into class
            - Refreshes stunt list
            - Sets UI fields from dialogue data.
        """
        super().load(filepath, resref, restype, data)

        dlg: DLG = read_dlg(data)
        self._loadDLG(dlg)
        self.refreshStuntList()

        self.ui.onAbortEdit.setText(str(dlg.EndConverAbort))
        self.ui.onEndEdit.setText(str(dlg.EndConversation))
        self.ui.voIdEdit.setText(dlg.VO_ID)
        self.ui.ambientTrackEdit.setText(str(dlg.AmbientTrack))
        self.ui.cameraModelEdit.setText(str(dlg.CameraModel))
        self.ui.conversationSelect.setCurrentIndex(dlg.ConversationType.value)
        self.ui.computerSelect.setCurrentIndex(dlg.ComputerType.value)
        self.ui.skippableCheckbox.setChecked(dlg.Skippable)
        self.ui.animatedCutCheckbox.setChecked(bool(dlg.AnimatedCut))
        self.ui.oldHitCheckbox.setChecked(dlg.OldHitCheck)
        self.ui.unequipHandsCheckbox.setChecked(dlg.UnequipHItem)
        self.ui.unequipAllCheckbox.setChecked(dlg.UnequipItems)
        self.ui.entryDelaySpin.setValue(dlg.DelayEntry)
        self.ui.replyDelaySpin.setValue(dlg.DelayReply)

    def _loadDLG(self, dlg: DLG):
        """Loads a dialog tree into the UI view.

        Args:
        ----
            dlg (DLG): The dialog tree to load

        Processing Logic:
        ----------------
            - Clears any existing styling from the dialog tree widget
            - Sets the focused flag to False
            - Sets the internal dlg variable to the passed dlg
            - Clears the model
            - Loops through the starter nodes and loads them recursively into the model.
        """
        self.ui.dialogTree.setStyleSheet("")
        self._focused = False

        self._dlg = dlg
        self.model.clear()
        seenLinks: list[DLGLink] = []
        seenNodes: list[DLGNode] = []
        for start in dlg.StartingList:  # reversed = ascending order
            assert isinstance(start, DLGLink)
            item = QStandardItem()
            self._loadDLGRec(item, start, seenLinks, seenNodes)
            self.model.appendRow(item)

    def _loadDLGRec(
        self,
        item: QStandardItem,
        link: DLGLink,
        seenLinks: list[DLGLink],
        seenNodes: list[DLGNode],
    ):
        """Don't call this function directly.

        Loads a DLG node recursively into the tree model

        Args:
        ----
            item: QStandardItem - The item to load the node into
            link: DLGLink - The link whose node to load
            seenLink: list[DLGLink] - Links already loaded
            seenNode: list[DLGNode] - Nodes already loaded

        Processing Logic:
        ----------------
            - Sets the link on the item
            - Checks if link/node already loaded
            - Marks item as already loaded
            - Refreshes the item
            - Loops through child links and loads recursively if not seen.
        """
        node: DLGNode | None = link._node
        assert node is not None, assert_with_variable_trace(node is not None, "link._node cannot be None.")
        item.setData(link, _LINK_ROLE)

        alreadyListed: bool = link in seenLinks or node in seenNodes
        if link not in seenLinks:
            seenLinks.append(link)
        if node not in seenNodes:
            seenNodes.append(node)

        item.setData(alreadyListed, _COPY_ROLE)
        self.refreshItem(item)

        if alreadyListed:
            return
        for child_link in node._links:
            child_item = QStandardItem()
            self._loadDLGRec(child_item, child_link, seenLinks, seenNodes)
            item.appendRow(child_item)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a dialogue from UI components.

        Args:
        ----
            self: {The class instance}: The class instance whose build method is being called.

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the dialogue data and an empty string

        Processing Logic:
        ----------------
            - Sets dialogue properties from UI components
            - Encodes dialogue data into bytes
            - Returns bytes containing dialogue data and empty string.
        """
        self._dlg.EndConverAbort = ResRef(self.ui.onAbortEdit.text())
        self._dlg.EndConversation = ResRef(self.ui.onEndEdit.text())
        self._dlg.VO_ID = self.ui.voIdEdit.text()
        self._dlg.AmbientTrack = ResRef(self.ui.ambientTrackEdit.text())
        self._dlg.CameraModel = ResRef(self.ui.cameraModelEdit.text())
        self._dlg.ConversationType = DLGConversationType(self.ui.conversationSelect.currentIndex())
        self._dlg.ComputerType = DLGComputerType(self.ui.computerSelect.currentIndex())
        self._dlg.Skippable = self.ui.skippableCheckbox.isChecked()
        self._dlg.AnimatedCut = self.ui.animatedCutCheckbox.isChecked()
        self._dlg.OldHitCheck = self.ui.oldHitCheckbox.isChecked()
        self._dlg.UnequipHItem = self.ui.unequipHandsCheckbox.isChecked()
        self._dlg.UnequipItems = self.ui.unequipAllCheckbox.isChecked()
        self._dlg.DelayEntry = self.ui.entryDelaySpin.value()
        self._dlg.DelayReply = self.ui.replyDelaySpin.value()

        data = bytearray()
        write_dlg(self._dlg, data, self._installation.game())
        return data, b""

    def new(self):
        super().new()
        self._loadDLG(DLG())

    def _setupInstallation(self, installation: HTInstallation):
        """Sets up the installation for the UI.

        Args:
        ----
            installation (HTInstallation): The installation object

        Processing Logic:
        ----------------
            - Sets enabled states of UI elements based on installation.tsl
            - Loads required 2da files if not already loaded
            - Sets up additional definitions if installation.tsl is True
            - Clears and populates camera effect dropdown.
        """
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
        required: list[str] = [
            HTInstallation.TwoDA_EMOTIONS,
            HTInstallation.TwoDA_EXPRESSIONS,
            HTInstallation.TwoDA_VIDEO_EFFECTS,
            HTInstallation.TwoDA_DIALOG_ANIMS,
        ]
        installation.htBatchCache2DA(required)

        if installation.tsl:
            self._setup_tsl_install_defs(installation)
        self.ui.cameraEffectSelect.clear()
        self.ui.cameraEffectSelect.addItem("[None]", None)

        videoEffects: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_VIDEO_EFFECTS)
        for i, label in enumerate(videoEffects.get_column("label")):
            self.ui.cameraEffectSelect.addItem(label.replace("VIDEO_EFFECT_", "").replace("_", " ").title(), i)

    def _setup_tsl_install_defs(self, installation: HTInstallation):
        """Set up UI elements for TSL installation selection.

        TSL has additional properties such as Emotions and Expressions.

        Args:
        ----
            installation: {Installation object to get data from}.

        Processing Logic:
        ----------------
            - Get expression and emotion data from installation object
            - Clear existing items from emotion and expression dropdowns
            - Populate dropdowns with labels from expression and emotion data.
        """
        expressions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_EXPRESSIONS)
        emotions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_EMOTIONS)

        self.ui.emotionSelect.clear()
        for label in emotions.get_column("label"):
            self.ui.emotionSelect.addItem(label.replace("_", " "))

        self.ui.expressionSelect.clear()
        for label in expressions.get_column("label"):
            self.ui.expressionSelect.addItem(label)

    def editText(self, e):
        """Edits the text of the selected dialog node.

        Args:
        ----
            self: The class instance
            e: The triggering event

        Processing Logic:
        ----------------
            1. Gets the selected dialog node item from the dialog tree view.
            2. Gets the DLGLink and DLGNode data from the item.
            3. Opens a localized string dialog with the node's text.
            4. If dialog is accepted and item is not a copy, updates the node's text and item text.
        """
        indexes: list[QModelIndex] = self.ui.dialogTree.selectionModel().selectedIndexes()
        if indexes:
            item: QStandardItem | None = self.model.itemFromIndex(indexes[0])
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            node: DLGNode | None = link._node
            assert_with_variable_trace(node is not None, "node cannot be None")
            dialog = LocalizedStringDialog(self, self._installation, node.Text)
            if dialog.exec_() and not isCopy:
                node.Text = dialog.locstring
                item.setText(self._installation.string(node.Text, "(continue)"))
                self._loadLocstring(self.ui.textEdit, node.Text)

    def _loadLocstring(self, textbox: QPlainTextEdit, locstring: LocalizedString):
        """Load a localized string into a text box.

        Args:
        ----
            textbox (QPlainTextEdit): Text box to load string into
            locstring (LocalizedString): Localized string object

        """
        if locstring.stringref == -1:
            text = str(locstring)
            textbox.setPlainText(text if text != "-1" else "")
            textbox.setStyleSheet("QPlainTextEdit {background-color: white;}")
        else:
            text: str = self._installation.talktable().string(locstring.stringref)
            textbox.setPlainText(text)
            textbox.setStyleSheet("QPlainTextEdit {background-color: #fffded;}")

    def addNode(self, item: QStandardItem | None, node: DLGNode):
        """Adds a node to the dialog tree.

        Args:
        ----
            item: The item to add to the node.
            node: The node to add the item to.

        Processing Logic:
        ----------------
            - Creates a new DLGEntry or DLGReply node based on the type of node passed in
            - Calls _add_node_main to add the new node to the dialog tree
            - Sets the item on the new node
            - Does not return anything, updates dialog tree in place.
        """
        # Update DLG
        newNode: DLGNode = DLGEntry() if isinstance(node, DLGReply) else DLGReply()
        self._add_node_main(newNode, node._links, False, item)

    def addRootNode(self):
        """Adds a root node to the dialog graph.

        Args:
        ----
            self: The dialog manager object.

        Processing Logic:
        ----------------
            - A new DLGEntry node is created to represent the root node
            - A DLGLink is created linking the root node
            - The link is appended to the starters list of the dialog graph
            - A QStandardItem is created and associated with the link
            - The item is added to the model with the link and marked as not a copy
            - The item is refreshed in the view and appended to the model row
        """
        self._add_node_main(DLGEntry(), self._dlg.StartingList, False, self.model)

    def addCopyLink(self, item: QStandardItem | None, target: DLGNode, source: DLGNode):
        self._add_node_main(source, target._links, True, item)

    def _add_node_main(
        self,
        source: DLGNode,
        target_links: list[DLGLink],
        _copy_role_data: bool,
        item: QStandardItem | QStandardItemModel | None
    ):

        newLink = DLGLink(source)
        target_links.append(newLink)
        newItem = QStandardItem()
        newItem.setData(newLink, _LINK_ROLE)
        newItem.setData(_copy_role_data, _COPY_ROLE)
        self.refreshItem(newItem)
        item.appendRow(newItem)

    def addCopy(self, item: QStandardItem, target: DLGNode, source: DLGNode):
        """Adds a copy of a node to a target node.

        Args:
        ----
            item: The item to add the new node to
            target: The target node to add the copy to
            source: The node to copy

        Processing Logic:
        ----------------
            - Makes a deep copy of the source node
            - Creates a new link between the target and copy
            - Creates a new item to hold the copied node
            - Loads the copied node recursively into the new item.
        """
        sourceCopy: DLGNode = deepcopy(source)
        newLink = DLGLink(sourceCopy)
        target._links.append(newLink)

        newItem = QStandardItem()
        self._loadDLGRec(newItem, newLink, [], [])
        item.appendRow(newItem)

    def copyNode(self, node: DLGNode):
        self._copy = node
        self.copyPath(node)

    def copyPath(self, node: DLGNode):
        path: str = ""
        if isinstance(node, DLGEntry):
            path = f"EntryList\\{node.list_index}"
        elif isinstance(node, DLGReply):
            path = f"ReplyList\\{node.list_index}"
        if path:
            pyperclip.copy(path)

    def deleteNode(self, item: QStandardItem | None):
        """Deletes a node from the diagram.

        Args:
        ----
            item: QStandardItem - The item to delete
            link: DLGLink - The link associated with the item
            node: DLGNode - The node associated with the link

        Processing Logic:
        ----------------
            - Get the link and node associated with the item
            - If item has no parent, remove link from starters list and row from model
            - Else, get parent item and associated link/node
            - Remove link from parent's links and row from parent.
        """
        link: DLGLink = item.data(_LINK_ROLE)
        node: DLGNode = link._node
        parent: QStandardItem | None = item.parent()

        if parent is None:
            for link in copy(self._dlg.StartingList):  # type: ignore[reportAssignmentType]
                if link._node is node:
                    self._dlg.StartingList.remove(link)  # type: ignore[reportAssignmentType]
            self.model.removeRow(item.row())
        else:
            parentLink: DLGLink = parent.data(_LINK_ROLE)
            parentNode: DLGNode = parentLink._node

            for link in copy(parentNode._links):
                if link._node is node:
                    parentNode._links.remove(link)
            parent.removeRow(item.row())

    def deleteSelectedNode(self):
        """Deletes the currently selected node from the tree.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Check if any node is selected in the tree
            - Get the index of the selected node
            - Get the item object from the model using the index
            - Call the deleteNode method to remove the item from the model.
        """
        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            self.deleteNode(item)

    def expandToRoot(self, item: QStandardItem):
        parent: QStandardItem | None = item.parent()
        while parent is not None:
            self.ui.dialogTree.expand(parent.index())
            parent = parent.parent()

    def jumpToOriginal(self, sourceItem: QStandardItem):
        """Jumps to the original node of a copied item.

        Args:
        ----
            sourceItem: The copied item to find the original of.

        Processing Logic:
        ----------------
            - Get the copied node from the source item
            - Iterate through all items in the tree
            - Check if the item's node matches the copied node and it is not a copy
            - If a match is found, expand the tree to that item and select it
            - If no match is found, print a failure message.
        """
        copiedLink: DLGLink = sourceItem.data(_LINK_ROLE)
        copiedNode: DLGNode = copiedLink._node

        items: list[QStandardItem | None] = [self.model.item(i, 0) for i in range(self.model.rowCount())]
        while items:
            item: QStandardItem | None = items.pop()
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            if link._node is copiedNode and not isCopy:
                self.expandToRoot(item)
                self.ui.dialogTree.setCurrentIndex(item.index())
                break
            items.extend([item.child(i, 0) for i in range(item.rowCount())])
        else:
            print("Failed to find original")

    def refreshItem(self, item: QStandardItem):
        """Refreshes the item text and formatting based on the node data.

        Refreshes the item in-place

        Args:
        ----
            item: QStandardItem - The item to refresh

        Processing Logic:
        ----------------
            - Sets the item text to the node text translated by the installation
            - Appends "[End Dialog]" if the node has no links
            - Sets the item foreground color based on the node and copy type
            - Blue for replies, red for entries, lighter if it is a copy.
        """
        node: DLGNode = item.data(_LINK_ROLE)._node
        isCopy: bool = item.data(_COPY_ROLE)
        color: QColor | None = None
        if isinstance(node, DLGEntry):
            color = QColor(210, 90, 90) if isCopy else QColor(255, 0, 0)
            prefix = "E"
        elif isinstance(node, DLGReply):
            color = QColor(90, 90, 210) if isCopy else QColor(0, 0, 255)
            prefix = "R"
        else:
            prefix = "N"

        list_prefix: str = f"{prefix}{node.list_index}: "
        if not node._links:
            item.setText(f"{list_prefix}[End Dialog]")
        else:
            text: str = self._installation.string(node.text, "(continue)")
            if node.list_index != -1:
                text = f"{list_prefix}{text}"
            item.setText(text)

        if color is not None:
            item.setForeground(QBrush(color))

    def playSound(self, resname: str):
        """Plays a sound resource.

        Args:
        ----
            resname: The name of the sound resource to play.

        Processing Logic:
        ----------------
            - Stops any currently playing sound.
            - Searches for the sound resource in multiple locations and loads the data if found.
            - Creates a buffer with the sound data and sets it as the media for a player.
            - Starts playback of the sound using a single shot timer to avoid blocking.
            - Displays an error message if the sound resource is not found.
        """
        self.player.stop()

        data: bytes | None = self._installation.sound(
            resname,
            [
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN
            ],
        )

        if data:
            self.buffer = QBuffer(self)
            self.buffer.setData(data)
            self.buffer.open(QIODevice.ReadOnly)
            self.player.setMedia(QMediaContent(), self.buffer)
            QtCore.QTimer.singleShot(0, self.player.play)
        elif data is None:
            QMessageBox(
                QMessageBox.Critical,
                "Could not find audio file",
                f"Could not find audio resource '{resname}'.",
            )
        else:
            QMessageBox(
                QMessageBox.Critical,
                "Corrupted/blank audio file",
                f"Could not load audio resource '{resname}'.",
            )

    def focusOnNode(self, link: DLGLink) -> QStandardItem:
        """Focuses the dialog tree on a specific link node.

        Args:
        ----
            link: The DLGLink to focus on.

        Returns:
        -------
            item (QStandardItem): The new subtree

        Processes the link node:
            - Sets the dialog tree style sheet to highlight the background
            - Clears any existing model data
            - Sets an internal flag to track the focused state
            - Creates a root item for the new focused subtree
            - Loads the DLG recursively from the given link into the item/model
            - Returns it to be optionally used by the main tree
        """
        self.ui.dialogTree.setStyleSheet("QTreeView { background: #FFFFEE; }")
        self.model.clear()
        self._focused = True

        item = QStandardItem()
        self._loadDLGRec(item, link, [], [])
        self.model.appendRow(item)
        return item

    def shiftItem(self, item: QStandardItem, amount: int):
        """Shifts an item in the tree by a given amount.

        Args:
        ----
            item: The item to shift.
            amount: The number of rows to shift by.

        Processing Logic:
        ----------------
            - Remove the item from its current row.
            - Insert the item into the new row calculated by adding the amount to the original row.
            - Update the selection in the tree view.
            - Sync the changes to the underlying DLG data structure by moving the corresponding link.
        """
        oldRow: int = item.row()
        parent = self.model if item.parent() is None else item.parent()
        newRow: int = oldRow + amount

        if newRow >= parent.rowCount() or newRow < 0:
            return  # Already at the start/end of the branch

        item = parent.takeRow(oldRow)[0]
        parent.insertRow(newRow, item)
        self.ui.dialogTree.selectionModel().select(item.index(), QItemSelectionModel.ClearAndSelect)

        # Sync DLG to tree changes
        links = (
            self._dlg.StartingList
            if item.parent() is None
            else item.parent().data(_LINK_ROLE)._node._links
        )
        link: DLGLink = links._structs.pop(oldRow)
        links._structs.insert(newRow, link)

    def onTreeContextMenu(self, point: QPoint):
        """Displays context menu for tree items.

        Args:
        ----
            point (QPoint): Mouse position for context menu

        Processing Logic:
        ----------------
            - Checks if mouse position is over a tree item
            - Gets the item from tree model if mouse is over an item
            - Sets context menu actions based on the item
            - Shows default add entry menu if mouse not over item.
        """
        index: QModelIndex = self.ui.dialogTree.indexAt(point)
        item: QStandardItem = self.model.itemFromIndex(index)

        if item is not None:
            self._set_context_menu_actions(item, point)
        elif not self._focused:
            menu = QMenu(self)

            menu.addAction("Add Entry").triggered.connect(self.addRootNode)

            menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def _set_context_menu_actions(self, item: QStandardItem, point: QPoint):
        """Sets context menu actions for a dialog tree item.

        Args:
        ----
            item: {The QTreeWidgetItem being right clicked}
            point: {The position of the mouse click}.

        Processing Logic:
        ----------------
            - Gets link and node data from item
            - Creates a QMenu
            - Adds actions like Focus, etc
            - Adds separator
            - Adds additional actions based on node type
            - Adds Copy/Delete actions if entry or reply
            - Displays menu at mouse position.
        """
        link: DLGLink = item.data(_LINK_ROLE)
        isCopy: bool = item.data(_COPY_ROLE)
        node: DLGNode = link._node

        menu = QMenu(self)

        menu.addAction("Focus").triggered.connect(lambda: self.focusOnNode(link))
        menu.addSeparator()
        # REMOVEME: moving nodes is a horrible idea. It's currently broken anyway.
        #menu.addAction("Move Up").triggered.connect(lambda: self.shiftItem(item, -1))
        #menu.addAction("Move Down").triggered.connect(lambda: self.shiftItem(item, 1))
        menu.addSeparator()

        if isCopy:
            menu.addAction("Jump to Original").triggered.connect(lambda: self.jumpToOriginal(item))

        elif isinstance(node, DLGReply):
            menu.addAction("Add Entry").triggered.connect(lambda: self.addNode(item, node))
            if isinstance(self._copy, DLGEntry):
                menu.addAction("Paste Entry as Link").triggered.connect(lambda: self.addCopyLink(item, node, self._copy))
                menu.addAction("Paste Entry as New").triggered.connect(lambda: self.addCopy(item, node, self._copy))
        elif isinstance(node, DLGEntry):
            menu.addAction("Add Reply").triggered.connect(lambda: self.addNode(item, node))
            if isinstance(self._copy, DLGReply):
                menu.addAction("Paste Reply as Link").triggered.connect(lambda: self.addCopyLink(item, node, self._copy))
                menu.addAction("Paste Reply as New").triggered.connect(lambda: self.addCopy(item, node, self._copy))

        if isinstance(node, DLGReply):
            menu.addAction("Copy Reply").triggered.connect(lambda: self.copyNode(node))
            menu.addAction("Delete Reply").triggered.connect(lambda: self.deleteNode(item))
        elif isinstance(node, DLGEntry):
            menu.addAction("Copy Entry").triggered.connect(lambda: self.copyNode(node))
            menu.addAction("Delete Entry").triggered.connect(lambda: self.deleteNode(item))

        menu.addAction("Copy GFF Path").triggered.connect(lambda: self.copyPath(node))

        menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def keyPressEvent(self, event: QKeyEvent | None):
        if not event:
            return
        if event.key() in {QtKey.Key_Enter, QtKey.Key_Return}:
            selectedItem: QModelIndex = self.ui.dialogTree.currentIndex()
            if selectedItem.isValid():
                item: QStandardItem | None = self.model.itemFromIndex(selectedItem)
                link = item.data(_LINK_ROLE)
                if link:
                    self.focusOnNode(link)
        super().keyPressEvent(event)  # Call the base class method to ensure default behavior

    def mouseDoubleClickEvent(self, event: QMouseEvent | None):
        selectedItem: QModelIndex = self.ui.dialogTree.currentIndex()
        if selectedItem.isValid():
            item: QStandardItem | None = self.model.itemFromIndex(selectedItem)
            link = item.data(_LINK_ROLE)
            if link:
                self.focusOnNode(link)
        super().mouseDoubleClickEvent(event)

    def onSelectionChanged(self, selection: QItemSelection):
        """Updates UI fields based on selected dialog node.

        Args:
        ----
            selection: QItemSelection - The current selection

        Processing Logic:
        ----------------
            - Disable updates to prevent recursion
            - Get selected item and link/node data
            - Populate various UI fields like text, scripts, conditions from node data
            - Refresh anim list
            - Enable updates.
        """
        self.acceptUpdates = False
        if selection.indexes():
            item: QStandardItem | None = self.model.itemFromIndex(selection.indexes()[0])
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            node: DLGNode | None = link.node

            if isinstance(node, DLGEntry):
                self.ui.speakerEdit.setEnabled(True)
                self.ui.speakerEdit.setText(node.Speaker)
            elif isinstance(node, DLGReply):
                self.ui.speakerEdit.setEnabled(False)
                self.ui.speakerEdit.setText("")
            assert node is not None, "onSelectionChanged, node cannot be None"

            self.ui.textEdit.setEnabled(not isCopy)

            self.ui.listenerEdit.setText(node.Listener)
            self._loadLocstring(self.ui.textEdit, node.Text)

            self.ui.script1ResrefEdit.setText(str(node.Script))
            self.ui.script1Param1Spin.setValue(node.ActionParam1)
            self.ui.script1Param2Spin.setValue(node.ActionParam2)
            self.ui.script1Param3Spin.setValue(node.ActionParam3)
            self.ui.script1Param4Spin.setValue(node.ActionParam4)
            self.ui.script1Param5Spin.setValue(node.ActionParam5)
            self.ui.script1Param6Edit.setText(node.ActionParamStrA)

            self.ui.script2ResrefEdit.setText(str(node.Script2))
            self.ui.script2Param1Spin.setValue(node.ActionParam1b)
            self.ui.script2Param2Spin.setValue(node.ActionParam2b)
            self.ui.script2Param3Spin.setValue(node.ActionParam3b)
            self.ui.script2Param4Spin.setValue(node.ActionParam4b)
            self.ui.script2Param5Spin.setValue(node.ActionParam5b)
            self.ui.script2Param6Edit.setText(node.ActionParamStrB)

            assert isinstance(link, DLGLink)
            self.ui.condition1ResrefEdit.setText(str(link.Active))
            self.ui.condition1Param1Spin.setValue(link.Param1)
            self.ui.condition1Param2Spin.setValue(link.Param2)
            self.ui.condition1Param3Spin.setValue(link.Param3)
            self.ui.condition1Param4Spin.setValue(link.Param4)
            self.ui.condition1Param5Spin.setValue(link.Param5)
            self.ui.condition1Param6Edit.setText(link.ParamStrA)
            self.ui.condition1NotCheckbox.setChecked(link.Not)

            self.ui.condition2ResrefEdit.setText(str(link.Active2))
            self.ui.condition2Param1Spin.setValue(link.Param1b)
            self.ui.condition2Param2Spin.setValue(link.Param2b)
            self.ui.condition2Param3Spin.setValue(link.Param3b)
            self.ui.condition2Param4Spin.setValue(link.Param4b)
            self.ui.condition2Param5Spin.setValue(link.Param5b)
            self.ui.condition2Param6Edit.setText(link.ParamStrB)
            self.ui.condition2NotCheckbox.setChecked(link.Not2)

            self.refreshAnimList()
            self.ui.emotionSelect.setCurrentIndex(node.Emotion)
            self.ui.expressionSelect.setCurrentIndex(node.FacialAnim)
            self.ui.soundEdit.setText(node.Sound.get())
            self.ui.soundCheckbox.setChecked(node.SoundExists)
            self.ui.voiceEdit.setText(node.VO_ResRef.get())

            self.ui.plotIndexSpin.setValue(node.PlotIndex)
            self.ui.plotXpSpin.setValue(node.PlotXPPercentage)
            self.ui.questEdit.setText(node.Quest)
            self.ui.questEntrySpin.setValue(node.QuestEntry)

            self.ui.cameraIdSpin.setValue(node.CameraID if node.CameraID is not None else -1)
            self.ui.cameraAnimSpin.setValue(node.CameraAnimation if node.CameraAnimation is not None else -1)
            self.ui.cameraAngleSelect.setCurrentIndex(node.CameraAnimation if node.CameraAnimation is not None else 0)
            self.ui.cameraEffectSelect.setCurrentIndex(node.CamVidEffect+1 if node.CamVidEffect is not None else 0)

            self.ui.nodeUnskippableCheckbox.setChecked(node.NodeUnskippable)
            self.ui.nodeIdSpin.setValue(node.NodeID)
            self.ui.alienRaceNodeSpin.setValue(node.AlienRaceNode)
            self.ui.postProcSpin.setValue(node.PostProcNode)
            delay = -1 if node.Delay == 4294967295 else node.Delay
            self.ui.delaySpin.setValue(delay)
            self.ui.logicSpin.setValue(link.Logic)
            self.ui.waitFlagSpin.setValue(node.WaitFlags)
            self.ui.fadeTypeSpin.setValue(node.FadeType)

            self.ui.commentsEdit.setPlainText(node.Comment)
        self.acceptUpdates = True

    def onNodeUpdate(self):
        """Updates node properties based on UI selections.

        Args:
        ----
            self: The class instance

        Updates node properties:
            - Sets listener, speaker and scripts based on UI selections
            - Sets conditions and parameters based on UI selections
            - Sets animations, journal, camera and other properties based on UI
            - Sets comment text from UI text edit.
        """
        if not self.ui.dialogTree.selectedIndexes() or not self.acceptUpdates:
            return
        index = self.ui.dialogTree.selectedIndexes()[0]
        item = self.model.itemFromIndex(index)

        link: DLGLink = item.data(_LINK_ROLE)
        node: DLGNode = link._node

        node.Listener = self.ui.listenerEdit.text()
        if isinstance(node, DLGEntry):
            node.Speaker = self.ui.speakerEdit.text()

        # Scripts
        node.Script = ResRef(self.ui.script1ResrefEdit.text())
        node.ActionParam1 = self.ui.script1Param1Spin.value()
        node.ActionParam2 = self.ui.script1Param2Spin.value()
        node.ActionParam3 = self.ui.script1Param3Spin.value()
        node.ActionParam4 = self.ui.script1Param4Spin.value()
        node.ActionParam5 = self.ui.script1Param5Spin.value()
        node.ActionParamStrA = self.ui.script1Param6Edit.text()
        node.Script2 = ResRef(self.ui.script2ResrefEdit.text())
        node.ActionParam1b = self.ui.script2Param1Spin.value()
        node.ActionParam2b = self.ui.script2Param2Spin.value()
        node.ActionParam3b = self.ui.script2Param3Spin.value()
        node.ActionParam4b = self.ui.script2Param4Spin.value()
        node.ActionParam5b = self.ui.script2Param5Spin.value()
        node.ActionParamStrB = self.ui.script2Param6Edit.text()

        link.Active = ResRef(self.ui.condition1ResrefEdit.text())
        link.Param1 = self.ui.condition1Param1Spin.value()
        link.Param2 = self.ui.condition1Param2Spin.value()
        link.Param3 = self.ui.condition1Param3Spin.value()
        link.Param4 = self.ui.condition1Param4Spin.value()
        link.Param5 = self.ui.condition1Param5Spin.value()
        link.ParamStrA = self.ui.condition1Param6Edit.text()
        link.Not = self.ui.condition1NotCheckbox.isChecked()
        link.Active2 = ResRef(self.ui.condition2ResrefEdit.text())
        link.Param1b = self.ui.condition2Param1Spin.value()
        link.Param2b = self.ui.condition2Param2Spin.value()
        link.Param3b = self.ui.condition2Param3Spin.value()
        link.Param4b = self.ui.condition2Param4Spin.value()
        link.Param5b = self.ui.condition2Param5Spin.value()
        link.ParamStrB = self.ui.condition2Param6Edit.text()
        link.Not2 = self.ui.condition2NotCheckbox.isChecked()

        # Animations
        node.Emotion = self.ui.emotionSelect.currentIndex()
        node.FacialAnim = self.ui.expressionSelect.currentIndex()
        node.Sound = ResRef(self.ui.soundEdit.text())
        node.SoundExists = self.ui.soundCheckbox.isChecked()
        node.VO_ResRef = ResRef(self.ui.voiceEdit.text())

        # Journal
        node.PlotIndex = self.ui.plotIndexSpin.value()
        node.PlotXPPercentage = self.ui.plotXpSpin.value()
        node.Quest = self.ui.questEdit.text()
        node.QuestEntry = self.ui.questEntrySpin.value()

        # Camera
        node.CameraID = self.ui.cameraIdSpin.value()
        node.CameraAnimation = self.ui.cameraAnimSpin.value()
        node.CameraAngle = self.ui.cameraAngleSelect.currentIndex()
        node.CamVidEffect = self.ui.cameraEffectSelect.currentData()
        if node.CameraID >= 0 and self.ui.cameraAngleSelect.currentIndex() == 0:
            self.ui.cameraAngleSelect.setCurrentIndex(6)
        elif node.CameraID == -1 and self.ui.cameraAngleSelect.currentIndex() == 6:
            self.ui.cameraAngleSelect.setCurrentIndex(0)

        # Other
        node.NodeUnskippable = self.ui.nodeUnskippableCheckbox.isChecked()
        node.NodeID = self.ui.nodeIdSpin.value()
        node.AlienRaceNode = self.ui.alienRaceNodeSpin.value()
        node.PostProcNode = self.ui.postProcSpin.value()
        node.Delay = self.ui.delaySpin.value()
        link.Logic = self.ui.logicSpin.value()
        node.WaitFlags = self.ui.waitFlagSpin.value()
        node.FadeType = self.ui.fadeTypeSpin.value()

        # Comments
        node.Comment = self.ui.commentsEdit.toPlainText()

    def onAddStuntClicked(self):
        dialog = CutsceneModelDialog(self)
        if dialog.exec_():
            self._dlg.StuntList._structs.append(dialog.stunt())
            self.refreshStuntList()

    def onRemoveStuntClicked(self):
        if self.ui.stuntList.selectedItems():
            item: QListWidgetItem = self.ui.stuntList.selectedItems()[0]
            stunt: DLGStunt = item.data(QtCore.Qt.UserRole)
            self._dlg.StuntList.remove(stunt)
            self.refreshStuntList()

    def onEditStuntClicked(self):
        if self.ui.stuntList.selectedItems():
            item: QListWidgetItem = self.ui.stuntList.selectedItems()[0]
            stunt: DLGStunt = item.data(QtCore.Qt.UserRole)
            dialog = CutsceneModelDialog(self, stunt)
            if dialog.exec_():
                stunt.StuntModel = dialog.stunt().StuntModel
                stunt.Participant = dialog.stunt().Participant
                self.refreshStuntList()

    def refreshStuntList(self):
        self.ui.stuntList.clear()
        for stunt in self._dlg.StuntList:
            assert isinstance(stunt, DLGStunt)
            text = f"{stunt.StuntModel} ({stunt.Participant})"
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, stunt)
            self.ui.stuntList.addItem(item)

    def onAddAnimClicked(self):
        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem = self.model.itemFromIndex(index)
            node: DLGNode = item.data(_LINK_ROLE)._node

            dialog = EditAnimationDialog(self, self._installation)
            if dialog.exec_():
                node.AnimList._structs.append(dialog.animation())
                self.refreshAnimList()

    def onRemoveAnimClicked(self):
        if self.ui.animsList.selectedItems():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            node: DLGNode = item.data(_LINK_ROLE)._node

            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(QtCore.Qt.UserRole)
            node.AnimList.remove(anim)
            self.refreshAnimList()

    def onEditAnimClicked(self):
        if self.ui.animsList.selectedItems():
            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(QtCore.Qt.UserRole)
            dialog = EditAnimationDialog(self, self._installation, anim)
            if dialog.exec_():
                anim.Animation = dialog.animation().Animation
                anim.Participant = dialog.animation().Participant
                self.refreshAnimList()

    def refreshAnimList(self):
        """Refreshes the animations list.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Clears the existing animations list
            - Gets the selected dialog node from the tree view
            - Loops through the animations on the node
            - Looks up the animation name from the TwoDA cache
            - Adds each animation as a item to the list with the name and participant.
        """
        self.ui.animsList.clear()

        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            link: DLGLink = item.data(_LINK_ROLE)
            node: DLGNode = link._node

            animations_2da: TwoDA = self._installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
            for anim in node.AnimList:
                assert isinstance(anim, DLGAnimation)
                name: str = str(anim.animation_id)
                if animations_2da.get_height() > anim.Animation:
                    name = animations_2da.get_cell(anim.Animation, "name")
                text: str = f"{name} ({anim.Participant})"
                item = QListWidgetItem(text)
                item.setData(QtCore.Qt.UserRole, anim)
                self.ui.animsList.addItem(item)


