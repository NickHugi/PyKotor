from __future__ import annotations

import json
import tempfile

from collections import deque
from typing import TYPE_CHECKING, cast

import qtpy

from qtpy import QtMultimedia
from qtpy.QtCore import QBuffer, QIODevice, QItemSelectionModel, QModelIndex, QPoint, QTimer, QUrl, Qt
from qtpy.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QKeySequence,
    QPainter,
    QPixmap,
    QRadialGradient,
    QStandardItem,
    QStandardItemModel,
)
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import QApplication, QFormLayout, QHBoxLayout, QLabel, QListWidgetItem, QMenu, QSpinBox, QTreeView, QWidget, QWidgetAction

from pykotor.common.misc import ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.dlg import (
    DLG,
    DLGComputerType,
    DLGConversationType,
    DLGEntry,
    DLGLink,
    DLGNode,
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
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.misc import QtKey, getQtKeyString
from utility.error_handling import assert_with_variable_trace
from utility.system.os_helper import remove_any

if TYPE_CHECKING:

    import os

    from qtpy.QtCore import QItemSelection, QTemporaryFile
    from qtpy.QtGui import (
        QDragEnterEvent,
        QDragMoveEvent,
        QDropEvent,
        QFocusEvent,
        QKeyEvent,
        QMouseEvent,
    )
    from qtpy.QtWidgets import QPlainTextEdit

    from pykotor.common.language import LocalizedString
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.dlg import (
        DLGAnimation,
        DLGStunt,
    )

_LINK_ROLE = Qt.ItemDataRole.UserRole + 1
_COPY_ROLE = Qt.ItemDataRole.UserRole + 2
_FUTURE_EXPAND_ROLE = Qt.ItemDataRole.UserRole + 3


class GFFFieldSpinBox(QSpinBox):
    def __init__(
        self,
        *args,
        min_value: int = 1200,
        max_value: int = 65534,
        **kwargs,
    ):
        self._no_validate: bool = False
        super().__init__(*args, **kwargs)
        self.specialValueTextMapping: dict[int, str] = {0: "0", -1: "-1"}
        self.min_value: int = min_value
        self.max_value: int = max_value
        self.setSpecialValueText(self.specialValueTextMapping[-1])

    def fixup(self, text: str):
        if text.isdigit() or (text and text[0] == "-" and text[1:].isdigit()):
            value = int(text)
            if value < self.min_value:
                self.setValue(self.min_value)
            elif value > self.max_value:
                self.setValue(self.max_value)
        else:
            self.setValue(self.value())

    def stepBy(self, steps: int):
        current_value = self.value()
        if current_value in self.specialValueTextMapping and steps > 0:
            self.setValue(self.min_value)
        elif current_value == self.min_value and steps < 0:
            self.setValue(max(self.specialValueTextMapping.keys()))
        else:
            next_value = current_value + steps
            if self.min_value <= next_value <= self.max_value:
                super().stepBy(steps)
            elif next_value < self.min_value:
                self.setValue(-1)
            else:
                self.setValue(self.max_value)

    @classmethod
    def from_spinbox(
        cls,
        originalSpin: QSpinBox,
        min_value: int = 0,
        max_value: int = 100,
    ) -> GFFFieldSpinBox:
        """Is not perfect at realigning, but attempts to initialize a GFFFieldSpinBox from a pre-existing QSpinBox."""
        if not isinstance(originalSpin, QSpinBox):
            raise TypeError("The provided widget is not a QSpinBox.")

        layout = originalSpin.parentWidget().layout()
        row, role = None, None

        if isinstance(layout, QFormLayout):
            for r in range(layout.rowCount()):
                if layout.itemAt(r, QFormLayout.ItemRole.FieldRole) and layout.itemAt(r, QFormLayout.ItemRole.FieldRole).widget() == originalSpin:
                    row, role = r, QFormLayout.ItemRole.FieldRole
                    break
                if layout.itemAt(r, QFormLayout.ItemRole.LabelRole) and layout.itemAt(r, QFormLayout.ItemRole.LabelRole).widget() == originalSpin:
                    row, role = r, QFormLayout.ItemRole.LabelRole
                    break

        parent = originalSpin.parent()
        customSpin = cls(parent, min_value=min_value, max_value=max_value)

        for i in range(originalSpin.metaObject().propertyCount()):
            prop = originalSpin.metaObject().property(i)
            if prop.isReadable() and prop.isWritable():
                value = originalSpin.property(prop.name())
                customSpin.setProperty(prop.name(), value)

        if row is not None and role is not None:
            layout.setWidget(row, role, customSpin)

        originalSpin.deleteLater()

        return customSpin


class DraggableTreeView(QTreeView):
    def __init__(self, parent: DLGEditor):
        super().__init__(parent)
        self.startPos: QPoint = QPoint()
        self.editor: DLGEditor | None = None
        self.highlighted_index: QModelIndex | None = None
        self.previous_highlighted_index: QModelIndex | None = None
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)

    def keyReleaseEvent(self, event: QKeyEvent):
        super().keyReleaseEvent(event)
        key = event.key()
        #self.editor._logger.debug(f"{self.__class__.__name__}.keyReleaseEvent, calling keyReleaseEvent in DLGEditor")
        if key in self.editor._keysDown:
              # This happens because super().keyReleaseEvent doesn't call DLGEditor.keyReleaseEvent, which itself
              # happens because DLGEditor.ui.dialogTree is, unintuitively, not a child of DLGEditor.
              # Attempting to set it as such with things like `self.ui.dialogTree.setParent`` breaks sizing and other ui stylings.
            self.editor.keyReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        key = event.key()
        #self.editor._logger.debug(f"{self.__class__.__name__}.keyPressEvent, calling keyPressEvent in DLGEditor")
        if key not in self.editor._keysDown:
              # This happens because super().keyPressEvent doesn't call DLGEditor.keyPressEvent, which itself
              # happens because DLGEditor.ui.dialogTree is, unintuitively, not a child of DLGEditor.
              # Attempting to set it as such with things like `self.ui.dialogTree.setParent`` breaks sizing and other ui stylings.
            self.editor.keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        self.startPos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if (event.buttons() & Qt.LeftButton) and (event.pos() - self.startPos).manhattanLength() > QApplication.startDragDistance():
            self.performDrag(event)

    def performDrag(self, event: QMouseEvent):
        index = self.indexAt(self.startPos)
        if not index.isValid():
            return

        itemModel: QStandardItemModel = self.model()
        dragged_item = itemModel.itemFromIndex(index)
        if not dragged_item:
            return

        link: DLGLink = dragged_item.data(_LINK_ROLE)
        node: DLGNode = link.node
        num_links, num_unique_nodes = self.calculate_links_and_nodes(node)

        drag = QDrag(self)
        mimeData = itemModel.mimeData([index])
        drag.setMimeData(mimeData)

        # Create a transparent pixmap with shiny circles
        pixmap = QPixmap(100, 50)  # Set an appropriate size for the pixmap
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Draw shiny circles
        def draw_shiny_circle(painter: QPainter, center: QPoint, radius: int, color: QColor):
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0, QColor(255, 255, 255, 150))
            gradient.setColorAt(0.5, color.lighter())
            gradient.setColorAt(1, color)
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

        link_center = QPoint(20, 25)
        nodes_center = QPoint(70, 25)
        draw_shiny_circle(painter, link_center, 10, QColor(255, 0, 0))
        draw_shiny_circle(painter, nodes_center, 10, QColor(0, 0, 255))

        painter.setPen(QColor(0, 0, 0))
        painter.drawText(link_center - QPoint(5, -4), f"{num_links}")
        painter.drawText(nodes_center - QPoint(5, -4), f"{num_unique_nodes}")
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos() - self.visualRect(index).topLeft())
        drag.exec_(Qt.MoveAction)

    def calculate_links_and_nodes(self, root_node: DLGNode) -> tuple[int, int]:
        queue = deque([root_node])
        seen_nodes = set()
        num_links = 0

        while queue:
            node = queue.popleft()
            if node in seen_nodes:
                continue
            seen_nodes.add(node)
            num_links += len(node.links)
            for link in node.links:
                queue.append(link.node)

        return num_links, len(seen_nodes)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (event.buttons() & Qt.LeftButton) and (event.pos() - self.startPos).manhattanLength() > QApplication.startDragDistance():
            self.performDrag(event)

    def performDrag(self, event: QMouseEvent):
        index = self.indexAt(self.startPos)
        if not index.isValid():
            return

        itemModel: QStandardItemModel = self.model()
        dragged_item = itemModel.itemFromIndex(index)
        if not dragged_item:
            return

        link: DLGLink = dragged_item.data(_LINK_ROLE)
        node: DLGNode = link.node
        num_links, num_unique_nodes = self.calculate_links_and_nodes(node)

        drag = QDrag(self)
        mimeData = itemModel.mimeData([index])
        drag.setMimeData(mimeData)

        # Create a transparent pixmap with shiny circles
        pixmap = QPixmap(100, 50)  # Set an appropriate size for the pixmap
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Draw shiny circles
        def draw_shiny_circle(painter: QPainter, center: QPoint, radius: int, color: QColor):
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0, QColor(255, 255, 255, 150))
            gradient.setColorAt(0.5, color.lighter())
            gradient.setColorAt(1, color)
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

        link_center = QPoint(20, 25)
        nodes_center = QPoint(70, 25)
        draw_shiny_circle(painter, link_center, 10, QColor(255, 0, 0))
        draw_shiny_circle(painter, nodes_center, 10, QColor(0, 0, 255))

        painter.setPen(QColor(0, 0, 0))
        painter.drawText(link_center - QPoint(5, -4), f"{num_links}")
        painter.drawText(nodes_center - QPoint(5, -4), f"{num_unique_nodes}")
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos() - self.visualRect(index).topLeft())
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if not event.mimeData().hasFormat(
            "application/x-qabstractitemmodeldatalist"
        ):
            return
        index = self.indexAt(event.pos())
        if index.isValid() and index != self.highlighted_index:
            # Unhighlight the previous item
            if self.previous_highlighted_index is not None:
                previous_item = self.model().itemFromIndex(self.previous_highlighted_index)
                if previous_item is not None:
                    previous_item.setBackground(QBrush())

            # Highlight the new item
            item = self.model().itemFromIndex(index)
            if item is not None:
                item.setBackground(QBrush(QColor(173, 216, 230)))
                self.highlighted_index = index
                self.previous_highlighted_index = index
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            return
        itemModel: QStandardItemModel = self.model()

        # Clear the highlighting
        if self.highlighted_index is not None:
            item = itemModel.itemFromIndex(self.highlighted_index)
            if item is not None:
                item.setBackground(QBrush())
            self.highlighted_index = None
            self.previous_highlighted_index = None

        event.acceptProposedAction()

        index = self.indexAt(event.pos())
        target_item = itemModel.itemFromIndex(index)

        # Get the node associated with the dragged item
        dragged_index = self.currentIndex()
        dragged_item = itemModel.itemFromIndex(dragged_index)
        if not dragged_item:
            return  # Invalid drop, do nothing
        link: DLGLink = dragged_item.data(_LINK_ROLE)
        dragged_node: DLGNode = link.node
        node_dict = dragged_node.to_dict()
        self.editor._copy = DLGNode.from_dict(node_dict)

        # Validate drop
        if target_item:
            target_link: DLGLink = target_item.data(_LINK_ROLE)
            target_node: DLGNode = target_link.node
            if (
                isinstance(dragged_node, DLGReply)
                and isinstance(target_node, DLGReply)
            ) or (
                isinstance(dragged_node, DLGEntry)
                and isinstance(target_node, DLGEntry)
            ):
                return  # Invalid drop, do nothing
            self.editor.pasteItem(target_item, asNewBranches=False)
        else:
            self.editor.pasteItem(self.editor.model, asNewBranches=False)
        super().dropEvent(event)


class DLGEditor(Editor):
    def __init__(self, parent: QWidget | None = None, installation: HTInstallation | None = None):
        """Initializes the Dialog Editor window."""
        supported: list[ResourceType] = [ResourceType.DLG]
        super().__init__(parent, "Dialog Editor", "dialog", supported, supported, installation)
        self._installation: HTInstallation

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation:
            self._setupInstallation(installation)

        self._focused: bool = False
        self._dlg: DLG = DLG()
        self._copy: DLGNode | None = None
        self.model: QStandardItemModel = QStandardItemModel(self)

        self.ui.dialogTree.editor = self
        self.ui.dialogTree.setModel(self.model)
        self.ui.dialogTree.customContextMenuRequested.connect(self.onTreeContextMenu)
        self.ui.dialogTree.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        self.ui.dialogTree.doubleClicked.connect(self.mouseDoubleClickEvent)

        self.ui.textEdit.mouseDoubleClickEvent = self.editText
        if GlobalSettings().selectedTheme != "Default (Light)":
            self.ui.textEdit.setStyleSheet(f"{self.ui.textEdit.styleSheet()} QPlainTextEdit {{color: black;}}")

        self.buffer: QBuffer = QBuffer()
        self.player: QMediaPlayer = QMediaPlayer(self)
        self.acceptUpdates: bool = False
        self.tempFile: QTemporaryFile | None = None
        self.ui.splitter.setSizes([99999999, 1])
        self.new()
        self._keysDown: set[int] = set()
        self.installEventFilter(self)

    def _setupSignals(self):
        """Connects UI signals to update node/link on change."""
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
        self.ui.dialogTree.expanded.connect(self.onItemExpanded)

        self.ui.soundButton.clicked.connect(lambda: self.playSound(self.ui.soundEdit.text()) and None or None)
        self.ui.voiceButton.clicked.connect(lambda: self.playSound(self.ui.voiceEdit.text()) and None or None)

        self.ui.actionReloadTree.triggered.connect(lambda: self._loadDLG(self._dlg))

        self.ui.addStuntButton.clicked.connect(self.onAddStuntClicked)
        self.ui.removeStuntButton.clicked.connect(self.onRemoveStuntClicked)
        self.ui.editStuntButton.clicked.connect(self.onEditStuntClicked)

        self.ui.addAnimButton.clicked.connect(self.onAddAnimClicked)
        self.ui.removeAnimButton.clicked.connect(self.onRemoveAnimClicked)
        self.ui.editAnimButton.clicked.connect(self.onEditAnimClicked)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Loads a dialogue file."""
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
        """Loads a dialog tree into the UI view."""
        if GlobalSettings().selectedTheme == "Default (Light)":
            self.ui.dialogTree.setStyleSheet("")
        self._focused = False

        self._dlg = dlg
        self.model.clear()
        seenLinks: list[DLGLink] = []
        seenNodes: list[DLGNode] = []
        for start in dlg.starters:  # descending order - matches what the game does.
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
            for child_link in node.links:
                child_item = QStandardItem()
                self._loadDLGRec(child_item, child_link, seenLinks, seenNodes)
                item.appendRow(child_item)
        else:
            return  # Implement once we can correctly update the model for other instances.
            # Add a dummy child item to show the expander
            dummy_child = QStandardItem("Loading...")
            item.appendRow(dummy_child)
            item.setData(True, _FUTURE_EXPAND_ROLE)  # Custom role to indicate it's a placeholder

    def build(self) -> tuple[bytes, bytes]:
        """Builds a dialogue from UI components."""
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
        #dismantle_dlg(self._dlg).compare(read_gff(data), log_func=self._logger.debug)
        return data, b""

    def new(self):
        super().new()
        self._loadDLG(DLG())

    def _setupInstallation(self, installation: HTInstallation):
        """Sets up the installation for the UI."""
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

        if installation.game().is_k1():
            required: list[str] = [
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS
            ]
        else:
            required = [
                HTInstallation.TwoDA_EMOTIONS,
                HTInstallation.TwoDA_EXPRESSIONS,
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS,
            ]
        installation.htBatchCache2DA(required)

        if installation.tsl:
            self._setupTslInstallDefs(installation)
        self.ui.cameraEffectSelect.clear()
        self.ui.cameraEffectSelect.addItem("[None]", None)

        videoEffects: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_VIDEO_EFFECTS)
        for i, label in enumerate(videoEffects.get_column("label")):
            self.ui.cameraEffectSelect.addItem(label.replace("VIDEO_EFFECT_", "").replace("_", " ").title(), i)

    def _setupTslInstallDefs(self, installation: HTInstallation):
        """Set up UI elements for TSL installation selection."""
        expressions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_EXPRESSIONS)
        emotions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_EMOTIONS)

        self.ui.emotionSelect.clear()
        for label in emotions.get_column("label"):
            self.ui.emotionSelect.addItem(label.replace("_", " "))

        self.ui.expressionSelect.clear()
        for label in expressions.get_column("label"):
            self.ui.expressionSelect.addItem(label)

    def editText(self, e: QMouseEvent):
        """Edits the text of the selected dialog node."""
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
        """Load a localized string into a text box."""
        if locstring.stringref == -1:
            text = str(locstring)
            textbox.setPlainText(text if text != "-1" else "")
            textbox.setStyleSheet(f"{textbox.styleSheet()} QPlainTextEdit {{background-color: white;}}")
        else:
            textbox.setPlainText(self._installation.talktable().string(locstring.stringref))
            textbox.setStyleSheet(f"{textbox.styleSheet()} QPlainTextEdit {{background-color: #fffded; color: black;}}")

    def addNode(self, item: QStandardItem | None, node: DLGNode):
        """Adds a node to the dialog tree."""
        newNode: DLGNode = DLGEntry() if isinstance(node, DLGReply) else DLGReply()
        self._coreAddNode(newNode, node.links, item)

    def addRootNode(self):
        """Adds a root node to the dialog graph."""
        self._coreAddNode(DLGEntry(), self._dlg.starters, self.model)

    def _coreAddNode(
        self,
        source: DLGNode,
        targetLinks: list[DLGLink],
        item: QStandardItem | QStandardItemModel,
    ):
        newLink = DLGLink(source)
        targetLinks.append(newLink)
        self._addLinkToItem(item, newLink)

    def _addLinkToItem(self, item: QStandardItem, link: DLGLink):
        """Helper method to update the UI with the new link."""
        new_item = QStandardItem()
        new_item.setData(link, _LINK_ROLE)
        self.refreshItem(new_item)
        item.appendRow(new_item)

    def _createLinkBetweenNodes(self, childNode: DLGNode, parentNode: DLGNode) -> QStandardItem:
        newLink = DLGLink(childNode)
        parentNode.links.append(newLink)
        result = QStandardItem()
        self._loadDLGRec(result, newLink, [], [])
        return result

    def _addNodeToTarget(self, target: DLGNode, source: DLGNode) -> DLGLink:
        """Helper method to add a source node to a target node."""
        new_link = DLGLink(source)
        target.links.append(new_link)
        return new_link

    def copyNode(self, node: DLGNode):
        node_dict_str = json.dumps(node.to_dict())
        QApplication.clipboard().setText(node_dict_str)

    def pasteItem(
        self,
        parentItem: QStandardItem,
        *,
        asNewBranches: bool = True,
    ):
        """Paste a node from the clipboard to the parent node."""
        link: DLGLink = parentItem.data(_LINK_ROLE)
        parentNode: DLGNode = link.node
        pastedNode: DLGNode = self._copy

        if asNewBranches:
            self._reindexChildNodes(pastedNode)
        else:
            self._integrateChildNodes(pastedNode)

        newLink = DLGLink(pastedNode)
        newLink.link_index = len(parentNode.links)
        parentNode.links.append(newLink)

        # Update the model
        newItem = QStandardItem()
        newItem.setData(newLink, _LINK_ROLE)
        self.refreshItem(newItem)

        # Add placeholder child if the new node has children
        if pastedNode.links:
            childPlaceholder = QStandardItem("Loading...")
            newItem.appendRow(childPlaceholder)
            newItem.setData(True, _FUTURE_EXPAND_ROLE)

        parentItem.appendRow(newItem)
        self.ui.dialogTree.expand(parentItem.index())
        if pastedNode.links:  # Optional
            self.ui.dialogTree.expand(newItem.index())

    def _reindexChildNodes(
        self,
        rootNode: DLGNode,
    ):
        """Reindex nodes to maintain unique indices and update links in a single pass."""
        entryIndices, replyIndices = self._getAllIndices()
        queue = [rootNode]
        visited = set()

        while queue:
            curNode = queue.pop(0)
            nodeHash = hash(curNode)
            if nodeHash in visited:
                continue
            visited.add(nodeHash)
            curNode.list_index = self._get_new_index(curNode, entryIndices, replyIndices)

            queue.extend([link.node for link in curNode.links if hash(link.node) not in visited])

    def _integrateChildNodes(
        self,
        rootNode: DLGNode,
    ):
        """Integrate links from the copied node into the parent node, reindexing as necessary."""
        entryIndices, replyIndices = self._getAllIndices()
        queue = [rootNode]
        visited = set()

        while queue:
            curNode = queue.pop(0)
            nodeHash = hash(curNode)
            if nodeHash in visited:
                continue
            visited.add(nodeHash)

            if (
                isinstance(curNode, DLGEntry) and curNode.list_index in entryIndices
                or isinstance(curNode, DLGReply) and curNode.list_index in replyIndices
            ):
                item = self.findItemForNode(curNode)
                if item is None:
                    curNode.list_index = self._get_new_index(curNode, entryIndices, replyIndices)
                else:
                    item.setData(True, _COPY_ROLE)
            else:
                curNode.list_index = self._get_new_index(curNode, entryIndices, replyIndices)

            queue.extend([link.node for link in curNode.links if hash(link.node) not in visited])


    def _get_new_index(
        self,
        node: DLGNode,
        entryIndices: set[int] | None = None,
        replyIndices: set[int] | None = None,
    ) -> int:
        """Generate a new unique index for the node."""
        if isinstance(node, DLGEntry):
            return self._nextNodeListIndex({entry.list_index for entry in self._dlg.all_entries()} if entryIndices is None else entryIndices)
        if isinstance(node, DLGReply):
            return self._nextNodeListIndex({reply.list_index for reply in self._dlg.all_replies()} if replyIndices is None else replyIndices)
        raise ValueError(node)

    def _nextNodeListIndex(self, indices: set[int]) -> int:
        new_index = max(indices, default=-1) + 1
        while new_index in indices:
            new_index += 1
        indices.add(new_index)
        return new_index

    def _getAllIndices(self) -> tuple[set[int], set[int]]:
        """Get all indices for entries and replies."""
        entryIndices = {entry.list_index for entry in self._dlg.all_entries()}
        replyIndices = {reply.list_index for reply in self._dlg.all_replies()}
        return entryIndices, replyIndices

    def copyPath(self, node_or_link: DLGNode | DLGLink):
        """Copies the node path to the user's clipboard."""
        path: str = ""
        if isinstance(node_or_link, DLGEntry):
            path = f"EntryList\\{node_or_link.list_index}"
        elif isinstance(node_or_link, DLGReply):
            path = f"ReplyList\\{node_or_link.list_index}"
        elif isinstance(node_or_link, DLGLink):
            if isinstance(node_or_link.node, DLGReply):
                path = f"EntryList\\{node_or_link.node.list_index}\\RepliesList\\{node_or_link.link_index}"
            elif isinstance(node_or_link.node, DLGEntry):
                path = f"ReplyList\\{node_or_link.node.list_index}\\EntriesList\\{node_or_link.link_index}"
        if path:
            QApplication.clipboard().setText(path)

    def findItemForNode(self, node: DLGNode) -> QStandardItem:
        """Find the QStandardItem in the model, given a DLGNode argument.

        Will raise an AttributeError when the node is not connected.
        """
        itemsToCheck = [self.model.item(i, 0) for i in range(self.model.rowCount())]
        while itemsToCheck:
            item = itemsToCheck.pop(0)
            lookupNode = self._getNodeFromLinkItem(item)
            if lookupNode == node:
                return item
            itemsToCheck.extend([item.child(i, 0) for i in range(item.rowCount())])
        return None

    def _checkClipboardForJsonNode(self):
        clipboard_text = QApplication.clipboard().text()
        try:
            node_data = json.loads(clipboard_text)
            if isinstance(node_data, dict) and "type" in node_data:
                self._copy = DLGNode.from_dict(node_data)
        except json.JSONDecodeError:
            ...
        except Exception:
            self._logger.exception("Invalid JSON node on clipboard.")

    def deleteNodeEverywhere(self, node: DLGNode):
        """Removes all occurrences of a node and all links to it from the model and self._dlg."""

        def removeNodeRecursive(item: QStandardItem, node_to_remove: DLGNode):
            for i in range(item.rowCount() - 1, -1, -1):
                child_item = item.child(i)
                if child_item is not None:
                    child_node = self._getNodeFromLinkItem(child_item)
                    if child_node is node_to_remove:
                        item.removeRow(i)
                    else:
                        removeNodeRecursive(child_item, node_to_remove)

        def removeNodeFromModel(model: QStandardItemModel, node_to_remove: DLGNode):
            for i in range(model.rowCount() - 1, -1, -1):
                item = model.item(i)
                if item is not None:
                    lookupNode = self._getNodeFromLinkItem(item)
                    if lookupNode == node_to_remove:
                        model.removeRow(i)
                    else:
                        removeNodeRecursive(item, node_to_remove)

        def removeLinksToNode(model: QStandardItemModel, node_to_remove: DLGNode):
            for i in range(model.rowCount()):
                item = model.item(i)
                removeLinksRecursive(item, node_to_remove)

        def removeLinksRecursive(item: QStandardItem, node_to_remove: DLGNode):
            for i in range(item.rowCount()):
                child_item = item.child(i)
                if child_item is not None:
                    link: DLGLink = child_item.data(_LINK_ROLE)
                    if link.node is node_to_remove:
                        item.removeRow(i)
                    removeLinksRecursive(child_item, node_to_remove)

        removeNodeFromModel(self.model, node)
        removeLinksToNode(self.model, node)

        # Remove the node and any links to it from the _dlg.starters list
        self._dlg.starters = [link for link in self._dlg.starters if link.node is not node]
        for link in self._dlg.starters:
            link.node.links = [child_link for child_link in link.node.links if child_link.node is not node]

        # Ensure all other links to this node are removed
        for dlg_node in self._dlg.all_entries() + self._dlg.all_replies():
            dlg_node.links = [child_link for child_link in dlg_node.links if child_link.node is not node]

    def deleteNode(self, item: QStandardItem):
        """Deletes a node from the DLG and ui tree model."""
        node = self._getNodeFromLinkItem(item)
        parent: QStandardItem | None = item.parent()

        if parent is None:
            for link in self._dlg.starters.copy():
                if link.node is node:
                    self._dlg.starters.remove(link)
            self.model.removeRow(item.row())
        else:
            parentItem: QStandardItem | None = parent
            parentNode = self._getNodeFromLinkItem(parentItem)
            for link in parentNode.links.copy():
                if link.node is node:
                    parentNode.links.remove(link)
            parentItem.removeRow(item.row())

    def _getNodeFromLinkItem(self, item: QStandardItem) -> DLGNode:
        link: DLGLink = item.data(_LINK_ROLE)
        result: DLGNode | None = link.node
        assert result is not None

        return result

    def deleteSelectedNode(self):
        """Deletes the currently selected node from the tree."""
        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]  # type: ignore[arg-type]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            assert item is not None
            self.deleteNode(item)

    def expandToRoot(self, item: QStandardItem):
        parent: QStandardItem | None = item.parent()
        while parent is not None:
            self.ui.dialogTree.expand(parent.index())  # type: ignore[arg-type]
            parent = parent.parent()

    def jumpToOriginal(self, sourceItem: QStandardItem):
        """Jumps to the original node of a copied item."""
        copiedNode: DLGNode = self._getNodeFromLinkItem(sourceItem)

        items: list[QStandardItem | None] = [self.model.item(i, 0) for i in range(self.model.rowCount())]
        while items:
            item: QStandardItem | None = items.pop()
            assert item is not None
            link: DLGLink = item.data(_LINK_ROLE)
            isCopy: bool = item.data(_COPY_ROLE)
            if link.node is copiedNode and not isCopy:
                self.expandToRoot(item)
                self.ui.dialogTree.setCurrentIndex(item.index())
                break
            items.extend([item.child(i, 0) for i in range(item.rowCount())])
        else:
            self._logger.error(f"Failed to find original node: {copiedNode!r}")

    def refreshItem(self, item: QStandardItem):
        """Refreshes the item text and formatting based on the node data."""
        node: DLGNode = self._getNodeFromLinkItem(item)
        isCopy: bool = item.data(_COPY_ROLE)
        color: QColor | None = None

        if GlobalSettings().selectedTheme == "Default (Light)":
            if isinstance(node, DLGEntry):
                color = QColor(210, 90, 90) if isCopy else QColor(255, 0, 0)
                prefix = "E"
            elif isinstance(node, DLGReply):
                color = QColor(90, 90, 210) if isCopy else QColor(0, 0, 255)
                prefix = "R"
            else:
                prefix = "N"

        elif isinstance(node, DLGEntry):
            color = QColor(255, 128, 128) if isCopy else QColor(255, 64, 64)
            prefix = "E"
        elif isinstance(node, DLGReply):
            color = QColor(128, 200, 255) if isCopy else QColor(64, 180, 255)
            prefix = "R"
        else:
            prefix = "N"
        list_prefix: str = f"{prefix}{node.list_index}: "
        text: str = self._installation.string(node.text, "")
        if not node.links:
            item.setText(f"{list_prefix}{text}[End Dialog]")
        else:
            if node.list_index != -1:
                text = f"{list_prefix}{text if text.strip() else '(continue)'}"
            item.setText(text)

        if color is not None:
            item.setForeground(QBrush(color))

    def blinkWindow(self):
        self.setWindowOpacity(0.7)
        QTimer.singleShot(125, lambda: self.setWindowOpacity(1))

    def playSound(self, resname: str) -> bool:
        """Plays a sound resource."""
        if qtpy.API_NAME in ["PyQt5", "PySide2"]:
            from qtpy.QtMultimedia import QMediaContent

            def set_media(data: bytes | None):
                if data:
                    self.buffer = QBuffer(self)
                    self.buffer.setData(data)
                    self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                    self.player.setMedia(QMediaContent(), self.buffer)
                    QTimer.singleShot(0, self.player.play)
                else:
                    self.blinkWindow()
                    return False
                return True

        elif qtpy.API_NAME in ["PyQt6", "PySide6"]:
            def set_media(data: bytes | None):
                if data:
                    tempFile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                    tempFile.write(data)
                    tempFile.flush()
                    tempFile.seek(0)
                    tempFile.close()

                    audioOutput = QtMultimedia.QAudioOutput(self)
                    self.player.setAudioOutput(audioOutput)
                    self.player.setSource(QUrl.fromLocalFile(tempFile.name))
                    audioOutput.setVolume(1)
                    self.player.play()
                    self.player.mediaStatusChanged.connect(lambda status, file_name=tempFile.name: self.removeTempAudioFile(status, file_name))
                else:
                    self.blinkWindow()
                    return False
                return True
        else:
            raise ValueError(f"Unsupported QT_API value: {qtpy.API_NAME}")

        self.player.stop()

        data: bytes | None = self._installation.sound(
            resname,
            [
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
            ],
        )
        return set_media(data)

    def removeTempAudioFile(
        self,
        status: QtMultimedia.QMediaPlayer.MediaStatus,
        filePathStr: str,
    ):
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            try:
                self.player.stop()
                QTimer.singleShot(33, lambda: remove_any(filePathStr))
            except OSError:
                self._logger.exception(f"Error removing temporary file {filePathStr}")

    def focusOnNode(self, link: DLGLink) -> QStandardItem:
        """Focuses the dialog tree on a specific link node."""
        if GlobalSettings().selectedTheme == "Default (Light)":
            self.ui.dialogTree.setStyleSheet("QTreeView { background: #FFFFEE; }")
        self.model.clear()
        self._focused = True

        item = QStandardItem()
        self._loadDLGRec(item, link, [], [])
        self.model.appendRow(item)
        return item

    def shiftItem(self, item: QStandardItem, amount: int):
        """Shifts an item in the tree by a given amount."""
        itemText = item.text()
        oldRow: int = item.row()
        itemParent = item.parent()
        parent = self.model if item.parent() is None else itemParent
        assert parent is not None
        newRow: int = oldRow + amount
        itemParentText = "" if itemParent is None else itemParent.text()

        self._logger.debug("Received item: '%s', row shift amount %s", itemText, amount)
        self._logger.debug("Attempting to change row index for '%s' from %s to %s", itemParentText, oldRow, newRow)

        if newRow >= parent.rowCount() or newRow < 0:
            self._logger.info("New row index '%s' out of bounds. Already at the start/end of the branch. Cancelling operation.", newRow)
            return

        itemToMove = parent.takeRow(oldRow)[0]
        self._logger.debug("itemToMove '%s' taken from old position: '%s', moving to '%s'", itemToMove.text(), oldRow, newRow)
        parent.insertRow(newRow, itemToMove)
        selectionModel = self.ui.dialogTree.selectionModel()
        if selectionModel is not None:
            selectionModel.select(itemToMove.index(), QItemSelectionModel.ClearAndSelect)
            self._logger.debug("Selection updated to new index")

        itemParent = itemToMove.parent()
        self._logger.debug("Item new parent after move: '%s'", itemParent.text() if itemParent else "Root")
        itemParentNode: DLGEntry | DLGReply | None = None if itemParent is None else itemParent.data(_LINK_ROLE).node
        links: list[DLGLink] = self._dlg.starters if itemParentNode is None else itemParentNode.links
        self._logger.debug("Links list length before removal: %s", len(links))
        link: DLGLink = links.pop(oldRow)
        links.insert(newRow, link)
        self._logger.info("Moved link from %s to %s", oldRow, newRow)

    def onTreeContextMenu(self, point: QPoint):
        """Displays context menu for tree items."""
        index: QModelIndex = self.ui.dialogTree.indexAt(point)
        item: QStandardItem | None = self.model.itemFromIndex(index)

        if item is not None:
            self._setContextMenuActions(item, point)
        elif not self._focused:
            menu = QMenu(self)
            menu.addAction("Add Entry").triggered.connect(self.addRootNode)
            menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def _setContextMenuActions(self, item: QStandardItem, point: QPoint):
        """Sets context menu actions for a dialog tree item."""
        self._checkClipboardForJsonNode()
        link: DLGLink = item.data(_LINK_ROLE)
        isCopy: bool = item.data(_COPY_ROLE)
        node: DLGNode = link.node
        node_type = "Entry" if isinstance(node, DLGEntry) else "Reply"

        menu = QMenu(self)

        # Jump/Focus Actions
        if isCopy:
            jumpToOriginalAction = menu.addAction("Jump to Original")
            jumpToOriginalAction.triggered.connect(lambda: self.jumpToOriginal(item))
            jumpToOriginalAction.setShortcut(QKeySequence(Qt.ControlModifier | QtKey.Key_Enter | QtKey.Key_Return))
        focusAction = menu.addAction("Focus")
        focusAction.triggered.connect(lambda: self.focusOnNode(link))
        focusAction.setShortcut(QKeySequence(QtKey.Key_Enter | QtKey.Key_Return))
        if not node.links:
            focusAction.setEnabled(False)
        menu.addSeparator()

        # Play Actions
        playMenu = menu.addMenu("Play")
        playAnyAction = playMenu.addAction("Any")
        playAnyAction.triggered.connect(lambda: self._playNodeSound(node))
        playAnyAction.setShortcut(QtKey.Key_P)
        playSoundAction = playMenu.addAction("Play Sound")
        playSoundAction.triggered.connect(lambda: self.playSound(str(node.sound)) and None or None)
        playVoiceAction = playMenu.addAction("Play Voice")
        playVoiceAction.triggered.connect(lambda: self.playSound(str(node.vo_resref)) and None or None)
        if not self.ui.soundEdit.text().strip():
            playSoundAction.setEnabled(False)
        if not self.ui.voiceEdit.text().strip():
            playVoiceAction.setEnabled(False)
        if not self.ui.soundEdit.text().strip() and not self.ui.voiceEdit.text().strip():
            playAnyAction.setEnabled(False)
        menu.addSeparator()

        # Copy Actions
        copyNodeAction = menu.addAction(f"Copy {node_type} to Clipboard")
        copyNodeAction.triggered.connect(lambda: self.copyNode(node))
        copyNodeAction.setShortcut(QKeySequence(Qt.ControlModifier | QtKey.Key_C))
        copyGffPathAction = menu.addAction("Copy GFF Path")
        copyGffPathAction.triggered.connect(lambda: self.copyPath(node))
        copyGffPathAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.AltModifier | QtKey.Key_C))
        menu.addSeparator()

        # Paste Actions
        pasteLinkAction = menu.addAction("Paste from Clipboard as Link")
        pasteNewAction = menu.addAction("Paste from Clipboard as Deep Copy")
        if isinstance(self._copy, DLGEntry) and isinstance(node, DLGReply):
            pasteLinkAction.setText("Paste Entry from Clipboard as Link")
            pasteNewAction.setText("Paste Entry from Clipboard as Deep Copy")
        elif isinstance(self._copy, DLGReply) and isinstance(node, DLGEntry):
            pasteLinkAction.setText("Paste Reply from Clipboard as Link")
            pasteNewAction.setText("Paste Reply from Clipboard as Deep Copy")
        else:
            pasteLinkAction.setEnabled(False)
            pasteNewAction.setEnabled(False)
        pasteLinkAction.setShortcut(QKeySequence(Qt.ControlModifier | QtKey.Key_V))
        pasteLinkAction.triggered.connect(lambda: self.pasteItem(item, asNewBranches=False))
        pasteNewAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.ShiftModifier | QtKey.Key_V))
        pasteNewAction.triggered.connect(lambda: self.pasteItem(item, asNewBranches=True))
        menu.addSeparator()

        # Add/Insert Actions
        addNodeAction = menu.addAction(f"Add {node_type}")
        addNodeAction.triggered.connect(lambda: self._addLinkToItem(item))
        addNodeAction.setShortcut(QtKey.Key_Insert)
        menu.addSeparator()
        moveUpAction = menu.addAction("Move Up")
        moveUpAction.triggered.connect(lambda: self.shiftItem(item, -1))
        moveUpAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Up))
        moveDownAction = menu.addAction("Move Down")
        moveDownAction.triggered.connect(lambda: self.shiftItem(item, 1))
        moveDownAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Down))
        menu.addSeparator()

        # Remove/Delete Actions
        removeLinkAction = menu.addAction(f"Remove Simple Link to {node_type}")
        removeLinkAction.setShortcut(QtKey.Key_Delete)
        removeLinkAction.triggered.connect(lambda: self.removeLink(item))
        deleteItemAction = menu.addAction("Delete Selected")
        deleteItemAction.triggered.connect(lambda: self.deleteNode(item))
        deleteItemAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Delete))
        menu.addSeparator()

        # Create a custom styled action for "Delete ALL References"
        deleteAllReferencesAction = QWidgetAction(self)
        deleteAllReferencesWidget = QWidget()
        layout = QHBoxLayout()
        deleteAllReferencesLabel = QLabel(f"Delete ALL References to {node_type}")
        deleteAllReferencesLabel.setStyleSheet("""
            QLabel {
                color: red;
                font-weight: bold;
                padding: 4px;
                text-align: center;
            }
            QLabel:hover {
                background-color: #d3d3d3;
            }
        """)
        layout.addWidget(deleteAllReferencesLabel)
        layout.setContentsMargins(0, 0, 0, 0)
        deleteAllReferencesWidget.setLayout(layout)
        deleteAllReferencesAction.setDefaultWidget(deleteAllReferencesWidget)
        deleteAllReferencesAction.triggered.connect(lambda: self.deleteNodeEverywhere(node))
        deleteAllReferencesAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.ShiftModifier | Qt.Key_Delete))
        menu.addAction(deleteAllReferencesAction)

        menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def removeLink(self, item: QStandardItem):
        """Removes the link from the parent node."""
        parent = item.parent()
        item_row = item.row()
        if parent is None:
            self.model.removeRow(item_row)
            self._dlg.starters.pop(item_row)
        else:
            parent.removeRow(item_row)
            parent_node = self._getNodeFromLinkItem(parent)
            parent_node.links.pop(item_row)

    def _playNodeSound(self, node: DLGEntry | DLGReply):
        if str(node.sound).strip():
            self.playSound(str(node.sound).strip())
        elif str(node.vo_resref).strip():
            self.playSound(str(node.vo_resref).strip())
        else:
            self.blinkWindow()

    # region Events
    def focusOutEvent(self, e: QFocusEvent):
        self._keysDown.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        #self._logger.debug("dlgedit.focusOutEvent: clearing all keys/buttons held down.")

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        key = event.key()
        if event.isAutoRepeat() or key in self._keysDown:
            return  # Ignore auto-repeat events and prevent multiple executions on single key
        selectedItem: QModelIndex = self.ui.dialogTree.currentIndex()
        if not selectedItem.isValid():
            return

        item: QStandardItem | None = self.model.itemFromIndex(selectedItem)
        if item is None:
            if key == QtKey.Key_Insert:
                self.addRootNode()
            return
        node = self._getNodeFromLinkItem(item)
        if node is None:
            return

        self._logger.debug(f"DLGEditor.keyPressEvent: {getQtKeyString(key)}")
        if not self._keysDown:
            self._keysDown.add(key)
            if key in (QtKey.Key_Delete, QtKey.Key_Backspace):
                self.removeLink(item)
            elif key in (QtKey.Key_Enter, QtKey.Key_Return):
                self.focusOnNode(node)
            elif key == QtKey.Key_Insert:
                self._addLinkToItem(item)
            elif key == QtKey.Key_P:
                if self.ui.soundEdit.text().strip():
                    self.playSound(self.ui.soundEdit.text().strip())
                elif self.ui.voiceEdit.text().strip():
                    self.playSound(self.ui.voiceEdit.text().strip())
                else:
                    self.blinkWindow()
            return

        self._keysDown.add(key)
        if {QtKey.Key_Shift, QtKey.Key_Up} == self._keysDown:
            self.shiftItem(item, -1)
        elif {QtKey.Key_Shift, QtKey.Key_Down} == self._keysDown:
            self.shiftItem(item, 1)
        elif QtKey.Key_Control in self._keysDown:
            if QtKey.Key_C in self._keysDown:
                if QtKey.Key_Alt in self._keysDown:
                    self.copyPath(node)
                else:
                    self.copyNode(node)
            elif QtKey.Key_V in self._keysDown:
                if QtKey.Key_Alt in self._keysDown:
                    self.pasteItem(item, asNewBranches=True)
                else:
                    self.pasteItem(item, asNewBranches=False)
            elif QtKey.Key_Delete in self._keysDown:
                if QtKey.Key_Shift in self._keysDown:
                    self.deleteNodeEverywhere(node)
                else:
                    self.deleteSelectedNode()

    def keyReleaseEvent(self, event: QKeyEvent):
        super().keyReleaseEvent(event)
        key = event.key()
        if key in self._keysDown:
            self._keysDown.remove(key)
        self._logger.debug(f"DLGEditor.keyReleaseEvent: {getQtKeyString(key)}")

    def mouseDoubleClickEvent(self, event: QMouseEvent | QModelIndex):
        if not self.ui.dialogTree.underMouse():
            return
        index: QModelIndex = event if isinstance(event, QModelIndex) else self.ui.dialogTree.indexAt(event.pos())
        if index.isValid():
            item: QStandardItem | None = self.model.itemFromIndex(index)
            link = item.data(_LINK_ROLE)
            if link:
                self.focusOnNode(link)

    def onSelectionChanged(self, selection: QItemSelection):
        """Updates UI fields based on selected dialog node."""
        self.acceptUpdates = False
        selectionIndices = selection.indexes()
        if selectionIndices:
            item: QStandardItem | None = self.model.itemFromIndex(selectionIndices[0])
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

            self.ui.cameraIdSpin.setValue(-1 if node.camera_id is None else node.camera_id)

            self.ui.cameraAnimSpin.__class__ = GFFFieldSpinBox
            spinBox: GFFFieldSpinBox = cast(GFFFieldSpinBox, self.ui.cameraAnimSpin)
            spinBox.min_value = 1200
            spinBox.max_value = 65534
            spinBox.specialValueTextMapping = {0: "0", -1: "-1"}
            spinBox.setMinimum(-1)
            spinBox.setMaximum(65534)
            spinBox.setValue(-1 if node.camera_anim is None else node.camera_anim)

            self.ui.cameraAngleSelect.setCurrentIndex(0 if node.camera_angle is None else node.camera_angle)
            self.ui.cameraEffectSelect.setCurrentIndex(0 if node.camera_effect is None else int(node.camera_effect) + 1)

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
        """Updates node properties based on UI selections."""
        selectedIndices = self.ui.dialogTree.selectedIndexes()
        if not selectedIndices:
            return
        if not self.acceptUpdates:
            return
        index: QModelIndex = selectedIndices[0]
        item: QStandardItem | None = self.model.itemFromIndex(index)

        link: DLGLink = item.data(_LINK_ROLE)
        assert isinstance(link, DLGLink)
        node: DLGNode | None = link.node
        assert isinstance(node, DLGNode)

        node.listener = self.ui.listenerEdit.text()
        if isinstance(node, DLGEntry):
            node.speaker = self.ui.speakerEdit.text()

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
        link.logic = bool(self.ui.logicSpin.value())

        node.emotion_id = self.ui.emotionSelect.currentIndex()
        node.facial_id = self.ui.expressionSelect.currentIndex()
        node.sound = ResRef(self.ui.soundEdit.text())
        node.sound_exists = self.ui.soundCheckbox.isChecked()
        node.vo_resref = ResRef(self.ui.voiceEdit.text())

        node.plot_index = self.ui.plotIndexSpin.value()
        node.plot_xp_percentage = self.ui.plotXpSpin.value()
        node.quest = self.ui.questEdit.text()
        node.quest_entry = self.ui.questEntrySpin.value()

        node.camera_id = self.ui.cameraIdSpin.value()
        node.camera_anim = self.ui.cameraAnimSpin.value()
        node.camera_angle = self.ui.cameraAngleSelect.currentIndex()
        node.camera_effect = self.ui.cameraEffectSelect.currentData()
        if node.camera_id >= 0 and node.camera_angle == 0:
            self.ui.cameraAngleSelect.setCurrentIndex(6)
        elif node.camera_id == -1 and node.camera_angle == 7:
            self.ui.cameraAngleSelect.setCurrentIndex(0)

        node.unskippable = self.ui.nodeUnskippableCheckbox.isChecked()
        node.node_id = self.ui.nodeIdSpin.value()
        node.alien_race_node = self.ui.alienRaceNodeSpin.value()
        node.post_proc_node = self.ui.postProcSpin.value()
        node.delay = self.ui.delaySpin.value()
        node.wait_flags = self.ui.waitFlagSpin.value()
        node.fade_type = self.ui.fadeTypeSpin.value()

        node.comment = self.ui.commentsEdit.toPlainText()

    def onItemExpanded(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        if item.data(_FUTURE_EXPAND_ROLE):  # Check if it's a placeholder
            item.removeRow(0)  # Remove the placeholder
            link: DLGLink = item.data(_LINK_ROLE)
            node: DLGNode = link.node
            for child_link in node.links:
                child_item = QStandardItem()
                self._loadDLGRec(child_item, child_link, [], [])
                item.appendRow(child_item)
            item.setData(False, _FUTURE_EXPAND_ROLE)  # Remove the placeholder flag

    def onAddStuntClicked(self):
        dialog = CutsceneModelDialog(self)
        if dialog.exec_():
            self._dlg.stunts.append(dialog.stunt())
            self.refreshStuntList()

    def onRemoveStuntClicked(self):
        selected = self.ui.stuntList.selectedItems()
        if selected:
            item: QListWidgetItem = selected[0]
            stunt: DLGStunt = item.data(Qt.ItemDataRole.UserRole)
            self._dlg.stunts.remove(stunt)
            self.refreshStuntList()

    def onEditStuntClicked(self):
        selected = self.ui.stuntList.selectedItems()
        if selected:
            item: QListWidgetItem = selected[0]
            stunt: DLGStunt = item.data(Qt.ItemDataRole.UserRole)
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
            item.setData(Qt.ItemDataRole.UserRole, stunt)
            self.ui.stuntList.addItem(item)

    def onAddAnimClicked(self):
        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            node: DLGNode = cast(DLGLink, item.data(_LINK_ROLE)).node

            dialog = EditAnimationDialog(self, self._installation)
            if dialog.exec_():
                node.animations.append(dialog.animation())
                self.refreshAnimList()

    def onRemoveAnimClicked(self):
        if self.ui.animsList.selectedItems():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            item: QStandardItem | None = self.model.itemFromIndex(index)
            node: DLGNode = cast(DLGLink, item.data(_LINK_ROLE)).node

            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(Qt.ItemDataRole.UserRole)
            node.animations.remove(anim)
            self.refreshAnimList()

    def onEditAnimClicked(self):
        if self.ui.animsList.selectedItems():
            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(Qt.ItemDataRole.UserRole)
            dialog = EditAnimationDialog(self, self._installation, anim)
            if dialog.exec_():
                anim.animation_id = dialog.animation().animation_id
                anim.participant = dialog.animation().participant
                self.refreshAnimList()

    def refreshAnimList(self):
        """Refreshes the animations list."""
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
                item.setData(Qt.ItemDataRole.UserRole, anim)
                self.ui.animsList.addItem(item)
