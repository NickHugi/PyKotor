from __future__ import annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING

import pyperclip

from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice, QItemSelectionModel, QTimer
from qtpy.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel
from qtpy.QtMultimedia import QMediaContent, QMediaPlayer
from qtpy.QtWidgets import QListWidgetItem, QMenu, QShortcut

from pykotor.common.misc import ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.dlg import (
    DLG,
    DLGComputerType,
    DLGConversationType,
    DLGEntry,
    DLGLink,
    DLGReply,
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

    from qtpy.QtCore import QItemSelection, QModelIndex, QPoint
    from qtpy.QtGui import QKeyEvent, QMouseEvent
    from qtpy.QtWidgets import QPlainTextEdit, QWidget

    from pykotor.common.language import LocalizedString
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.dlg import (
        DLGAnimation,
        DLGNode,
        DLGStunt,
    )

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

        from toolset.uic.pyqt5.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
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

        self.ui.onAbortEdit.setText(str(dlg.on_abort))
        self.ui.onEndEdit.setText(str(dlg.on_end))
        self.ui.voIdEdit.setText(dlg.vo_id)
        self.ui.ambientTrackEdit.setText(str(dlg.ambient_track))
        self.ui.cameraModelEdit.setText(str(dlg.camera_model))
        self.ui.conversationSelect.setCurrentIndex(dlg.conversation_type.value)
        self.ui.computerSelect.setCurrentIndex(dlg.computer_type.value)
        self.ui.skippableCheckbox.setChecked(dlg.skippable)
        self.ui.animatedCutCheckbox.setChecked(bool(dlg.animated_cut))
        self.ui.oldHitCheckbox.setChecked(dlg.old_hit_check)
        self.ui.unequipHandsCheckbox.setChecked(dlg.unequip_hands)
        self.ui.unequipAllCheckbox.setChecked(dlg.unequip_items)
        self.ui.entryDelaySpin.setValue(dlg.delay_entry)
        self.ui.replyDelaySpin.setValue(dlg.delay_reply)

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
        for start in reversed(dlg.starters):  # reversed = ascending order
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
            item (QStandardItem): The item to load the node into
            link (DLGLink): The link whose node to load
            seenLink (list[DLGLink]): Links already loaded
            seenNode (list[DLGNode]): Nodes already loaded

        Processing Logic:
        ----------------
            - Sets the link on the item
            - Checks if link/node already loaded
            - Marks item as already loaded
            - Refreshes the item
            - Loops through child links and loads recursively if not seen.
        """
        node: DLGNode | None = link.node
        assert_with_variable_trace(node is not None, "link.node cannot be None.")
        assert node is not None
        item.setData(link, _LINK_ROLE)

        alreadyListed: bool = link in seenLinks or node in seenNodes
        if link not in seenLinks:
            seenLinks.append(link)
        if node not in seenNodes:
            seenNodes.append(node)

        item.setData(alreadyListed, _COPY_ROLE)
        self.refreshItem(item)

        if not alreadyListed:
            for child_link in reversed(node.links):  # reversed = ascending order
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
            node: DLGNode | None = link.node
            assert_with_variable_trace(node is not None, "node cannot be None")
            dialog = LocalizedStringDialog(self, self._installation, node.text)
            if dialog.exec_() and not isCopy:
                node.text = dialog.locstring
                item.setText(self._installation.string(node.text, "(continue)"))
                self._loadLocstring(self.ui.textEdit, node.text)

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
        self._add_node_main(newNode, node.links, False, item)

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
        self._add_node_main(DLGEntry(), self._dlg.starters, False, self.model)

    def addCopyLink(self, item: QStandardItem | None, target: DLGNode, source: DLGNode):
        self._add_node_main(source, target.links, True, item)

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
        target.links.append(newLink)

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
        node: DLGNode = link.node
        parent: QStandardItem | None = item.parent()

        if parent is None:
            for link in copy(self._dlg.starters):
                if link.node is node:
                    self._dlg.starters.remove(link)
            self.model.removeRow(item.row())
        else:
            parentItem: QStandardItem | None = parent
            parentLink: DLGLink = parentItem.data(_LINK_ROLE)
            parentNode: DLGNode = parentLink.node

            for link in copy(parentNode.links):
                if link.node is node:
                    parentNode.links.remove(link)
            parentItem.removeRow(item.row())

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
        copiedNode: DLGNode = copiedLink.node

        items: list[QStandardItem | None] = [self.model.item(i, 0) for i in range(self.model.rowCount())]
        while items:
            item: QStandardItem | None = items.pop()
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
        """Refreshes the item text and formatting based on the node data.  Refreshes the item in-place.

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
        node: DLGNode = item.data(_LINK_ROLE).node
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
        if not node.links:
            item.setText(f"{list_prefix}[End Dialog]")
        else:
            text: str = self._installation.string(node.text, "(continue)")
            if node.list_index != -1:
                text = f"{list_prefix}{text}"
            item.setText(text)

        if color is not None:
            item.setForeground(QBrush(color))

    def blinkWindow(self):
        self.setWindowOpacity(0.7)
        QTimer.singleShot(125, lambda: self.setWindowOpacity(1))

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
        else:
            self.blinkWindow()

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
            - It removes the item from its current row.
            - It inserts the item into the new row calculated by adding the amount to the original row.
            - It updates the selection in the tree view.
            - It syncs the changes to the underlying DLG data structure by moving the corresponding link.
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
        links: list[DLGLink] = (
            self._dlg.starters
            if item.parent() is None
            else item.parent().data(_LINK_ROLE).node.links
        )
        link: DLGLink = links.pop(oldRow)
        links.insert(newRow, link)

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
        item: QStandardItem | None = self.model.itemFromIndex(index)

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
        node: DLGNode = link.node

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

    def keyPressEvent(self, event: QKeyEvent):
        selectedItem: QModelIndex = self.ui.dialogTree.currentIndex()
        if not selectedItem.isValid():
            return
        if event.key() in {QtKey.Key_Enter, QtKey.Key_Return}:
            item: QStandardItem | None = self.model.itemFromIndex(selectedItem)
            link = item.data(_LINK_ROLE)
            if link:
                self.focusOnNode(link)
        if event.key() in {QtKey.Key_P}:
            self.ui.soundButton.clicked.connect(lambda: self.playSound(self.ui.soundEdit.text()))
            self.ui.voiceButton.clicked.connect(lambda: self.playSound(self.ui.voiceEdit.text()))
        super().keyPressEvent(event)  # Call the base class method to ensure default behavior

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        selectedItem: QModelIndex = self.ui.dialogTree.currentIndex()
        if not selectedItem.isValid():
            return
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
                self.ui.speakerEdit.setText(node.speaker)
            elif isinstance(node, DLGReply):
                self.ui.speakerEdit.setEnabled(False)
                self.ui.speakerEdit.setText("")
            assert node is not None, "onSelectionChanged, node cannot be None"

            self.ui.textEdit.setEnabled(not isCopy)

            self.ui.listenerEdit.setText(node.listener)
            self._loadLocstring(self.ui.textEdit, node.text)

            self.ui.script1ResrefEdit.setText(str(node.script1))
            self.ui.script1Param1Spin.setValue(node.script1_param1)
            self.ui.script1Param2Spin.setValue(node.script1_param2)
            self.ui.script1Param3Spin.setValue(node.script1_param3)
            self.ui.script1Param4Spin.setValue(node.script1_param4)
            self.ui.script1Param5Spin.setValue(node.script1_param5)
            self.ui.script1Param6Edit.setText(node.script1_param6)

            self.ui.script2ResrefEdit.setText(str(node.script2))
            self.ui.script2Param1Spin.setValue(node.script2_param1)
            self.ui.script2Param2Spin.setValue(node.script2_param2)
            self.ui.script2Param3Spin.setValue(node.script2_param3)
            self.ui.script2Param4Spin.setValue(node.script2_param4)
            self.ui.script2Param5Spin.setValue(node.script2_param5)
            self.ui.script2Param6Edit.setText(node.script2_param6)

            self.ui.condition1ResrefEdit.setText(str(link.active1))
            self.ui.condition1Param1Spin.setValue(link.active1_param1)
            self.ui.condition1Param2Spin.setValue(link.active1_param2)
            self.ui.condition1Param3Spin.setValue(link.active1_param3)
            self.ui.condition1Param4Spin.setValue(link.active1_param4)
            self.ui.condition1Param5Spin.setValue(link.active1_param5)
            self.ui.condition1Param6Edit.setText(link.active1_param6)
            self.ui.condition1NotCheckbox.setChecked(link.active1_not)

            self.ui.condition2ResrefEdit.setText(str(link.active2))
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
            self.ui.soundEdit.setText(str(node.sound))
            self.ui.soundCheckbox.setChecked(node.sound_exists)
            self.ui.voiceEdit.setText(str(node.vo_resref))

            self.ui.plotIndexSpin.setValue(node.plot_index)
            self.ui.plotXpSpin.setValue(node.plot_xp_percentage)
            self.ui.questEdit.setText(node.quest)
            self.ui.questEntrySpin.setValue(node.quest_entry or 0)

            self.ui.cameraIdSpin.setValue(node.camera_id if node.camera_id is not None else -1)
            self.ui.cameraAnimSpin.setValue(node.camera_anim if node.camera_anim is not None else -1)
            self.ui.cameraAngleSelect.setCurrentIndex(node.camera_angle if node.camera_angle is not None else 0)
            self.ui.cameraEffectSelect.setCurrentIndex(node.camera_effect + 1 if node.camera_effect is not None else 0)

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
        index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
        item: QStandardItem | None = self.model.itemFromIndex(index)

        link: DLGLink = item.data(_LINK_ROLE)
        node: DLGNode | None = link.node
        assert node is not None

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
        link.logic = bool(self.ui.logicSpin.value())
        node.wait_flags = self.ui.waitFlagSpin.value()
        node.fade_type = self.ui.fadeTypeSpin.value()

        # Comments
        node.comment = self.ui.commentsEdit.toPlainText()

    def onAddStuntClicked(self):
        dialog = CutsceneModelDialog(self)
        if dialog.exec_():
            self._dlg.stunts.append(dialog.stunt())
            self.refreshStuntList()

    def onRemoveStuntClicked(self):
        if self.ui.stuntList.selectedItems():
            item: QListWidgetItem = self.ui.stuntList.selectedItems()[0]
            stunt: DLGStunt = item.data(QtCore.Qt.UserRole)
            self._dlg.stunts.remove(stunt)
            self.refreshStuntList()

    def onEditStuntClicked(self):
        if self.ui.stuntList.selectedItems():
            item: QListWidgetItem = self.ui.stuntList.selectedItems()[0]
            stunt: DLGStunt = item.data(QtCore.Qt.UserRole)
            dialog = CutsceneModelDialog(self, stunt)
            if dialog.exec_():
                stunt.stunt_model = dialog.stunt().stunt_model
                stunt.participant = dialog.stunt().participant
                self.refreshStuntList()

    def refreshStuntList(self):
        self.ui.stuntList.clear()
        for stunt in self._dlg.stunts:
            text = f"{stunt.stunt_model} ({stunt.participant})"
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, stunt)
            self.ui.stuntList.addItem(item)

    def onAddAnimClicked(self):
        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            node: DLGNode = item.data(_LINK_ROLE).node

            dialog = EditAnimationDialog(self, self._installation)
            if dialog.exec_():
                node.animations.append(dialog.animation())
                self.refreshAnimList()

    def onRemoveAnimClicked(self):
        if self.ui.animsList.selectedItems():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            node: DLGNode = item.data(_LINK_ROLE).node

            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(QtCore.Qt.UserRole)
            node.animations.remove(anim)
            self.refreshAnimList()

    def onEditAnimClicked(self):
        if self.ui.animsList.selectedItems():
            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(QtCore.Qt.UserRole)
            dialog = EditAnimationDialog(self, self._installation, anim)
            if dialog.exec_():
                anim.animation_id = dialog.animation().animation_id
                anim.participant = dialog.animation().participant
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
            node: DLGNode = link.node

            animations_2da: TwoDA = self._installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
            for anim in node.animations:
                name: str = str(anim.animation_id)
                if animations_2da.get_height() > anim.animation_id:
                    name = animations_2da.get_cell(anim.animation_id, "name")
                text: str = f"{name} ({anim.participant})"
                item = QListWidgetItem(text)
                item.setData(QtCore.Qt.UserRole, anim)
                self.ui.animsList.addItem(item)


