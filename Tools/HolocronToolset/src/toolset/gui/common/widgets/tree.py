from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import (
    QEvent,
    QModelIndex,
    QRect,
    QTimer,
    Qt,
)
from qtpy.QtGui import (
    QStandardItem,
    QStandardItemModel,
)
from qtpy.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTreeView,
)

from toolset.gui.common.style.delegates import HTMLDelegate

if TYPE_CHECKING:

    from qtpy.QtCore import (
        QObject,
    )
    from qtpy.QtGui import (
        QPainter,
        QResizeEvent,
        QWheelEvent,
    )
    from qtpy.QtWidgets import (
        QWidget,
    )
    from typing_extensions import Literal


class RobustTreeView(QTreeView):
    def __init__(self, parent: QWidget | None=None):
        super().__init__(parent)
        self.setUniformRowHeights(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setAnimated(True)
        self.setAutoExpandDelay(2000)
        self.setAutoScroll(False)
        #self.setExpandsOnDoubleClick(True)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.setIndentation(20)
        self.setWordWrap(True)
        self.fix_horizontal_scroll_bar()
        #self.setGraphicsEffect(QGraphicsEffect.)
        self.setAlternatingRowColors(False)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setAutoFillBackground(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.layoutChangedDebounceTimer = QTimer(self)
        self.layoutChangedDebounceTimer.setSingleShot(True)
        self.layoutChangedDebounceTimer.timeout.connect(self.emitLayoutChanged)
        self.branch_connectors_enabled: bool = False
        self.original_stylesheet: str = self.styleSheet()

    def fix_horizontal_scroll_bar(self):
        #self.setColumnWidth(0, 2000)
        header = self.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(self.geometry().width() * 5)
        header.setDefaultSectionSize(self.geometry().width() * 10)
        header.hide()

    def setTextSize(self, size: int):
        delegate = self.itemDelegate()
        if delegate is not None:
            delegate.setTextSize(max(1, size))
            self.debounceLayoutChanged()

    def getTextSize(self) -> int:
        delegate = self.itemDelegate()
        return delegate.text_size if delegate is not None else 12

    def emitLayoutChanged(self):
        model = self.model()
        if model is not None:
            model.layoutChanged.emit()

    def debounceLayoutChanged(self, timeout: int = 100, *, preChangeEmit: bool = False):
        self.viewport().update()
        self.update()
        if self.layoutChangedDebounceTimer.isActive():
            self.layoutChangedDebounceTimer.stop()
        elif preChangeEmit:
            self.model().layoutAboutToBeChanged.emit()
        self.layoutChangedDebounceTimer.start(timeout)

    def drawCircle(self, painter: QPainter, center_x: int, center_y: int, radius: int):
        circle_rect = QRect(center_x - radius, center_y - radius, 2 * radius, 2 * radius)
        painter.setBrush(Qt.GlobalColor.white)  # Fill the circle with white color
        painter.drawEllipse(circle_rect)

        # Draw useful information inside the circle
        random_number = 5
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(circle_rect, Qt.AlignCenter, str(random_number))

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Scroll, QEvent.ScrollPrepare):
            return True  # block automated scroll events
        return super().eventFilter(obj, event)

    def itemDelegate(self, *args) -> HTMLDelegate:
        delegate = super().itemDelegate(*args)
        assert isinstance(delegate, HTMLDelegate)
        return delegate

    def setItemDelegate(self, delegate: HTMLDelegate):
        assert isinstance(delegate, HTMLDelegate)
        super().setItemDelegate(delegate)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.debounceLayoutChanged()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        modifiers = event.modifiers()
        response = None
        if bool(modifiers & Qt.KeyboardModifier.ShiftModifier) and bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            response = self._wheel_changes_item_spacing(event)
        elif bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            response = self._wheel_changes_text_size(event)
        elif bool(modifiers & Qt.KeyboardModifier.ShiftModifier):
            response = self._wheel_changes_horizontal_scroll(event)
        elif bool(modifiers & Qt.KeyboardModifier.AltModifier):
            response = self._wheel_changes_indent_size(event)
        elif not int(modifiers):  # would be zero if there are no modifiers.
            response = self._wheel_changes_vertical_scroll(event)
        if response is not True:
            super().wheelEvent(event)

    def _wheel_changes_text_size(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        self.setTextSize(self.getTextSize() + (1 if delta > 0 else -1))
        return True

    def _wheel_changes_horizontal_scroll(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return True
        if self.horizontalScrollMode() == self.ScrollPerItem:
            delta = self.indentation() * (1 if delta > 0 else -1)
        else:
            delta = -self.getTextSize() if delta > 0 else self.getTextSize()
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta)
        return True

    def _wheel_changes_vertical_scroll(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        #print("wheelVerticalScroll, delta: ", delta)
        if not delta:
            return True
        vertScrollBar = self.verticalScrollBar()
        if self.verticalScrollMode() == self.ScrollPerItem:
            action = vertScrollBar.SliderSingleStepSub if delta > 0 else vertScrollBar.SliderSingleStepAdd
            vertScrollBar.triggerAction(action)
        else:
            scrollStep = -self.getTextSize() if delta > 0 else self.getTextSize()
            vertScrollBar.setValue(vertScrollBar.value() + scrollStep)
        return True

    def scrollSingleStep(self, direction: Literal["up", "down"]):
        """A simple working function that will scroll a single step.

        Determines what a 'single step' is by checking `self.verticalScrollMode()`
        """
        vertScrollBar = self.verticalScrollBar()
        if self.verticalScrollMode() == QAbstractItemView.ScrollPerItem:
            action = vertScrollBar.SliderSingleStepSub if direction == "up" else vertScrollBar.SliderSingleStepAdd
            vertScrollBar.triggerAction(action)
        else:
            scrollStep = -self.getTextSize() if direction == "up" else self.getTextSize()
            vertScrollBar.setValue(vertScrollBar.value() + scrollStep)

    def _wheel_changes_item_spacing(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        if self.itemDelegate() is not None:
            single_step = (1 if delta > 0 else -1)
            newVerticalSpacing = max(0, self.itemDelegate().customVerticalSpacing + single_step)
            self.itemDelegate().setVerticalSpacing(newVerticalSpacing)
            self.emitLayoutChanged()  # Requires immediate update
            return True
        return False

    def _wheel_changes_indent_size(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().x()  # Same as y() in the other funcs but returned in x() due to AltModifier I guess. Not in the documentation.
        #print(f"wheel changes indent delta: {delta}")
        if not delta:
            return False
        if self.itemDelegate() is not None:
            self.setIndentation(max(0, self.indentation() + (1 if delta > 0 else -1)))
            self.debounceLayoutChanged()
            return True
        return False

    def model(self) -> QStandardItemModel | None:
        model = super().model()
        if model is None:
            return None
        assert isinstance(model, QStandardItemModel), f"model was {model} of type {model.__class__.__name__}"
        return model

    def getIdentifyingText(self, indexOrItem: QModelIndex | QStandardItem | None) -> str:
        if indexOrItem is None:
            return "(None)"
        if isinstance(indexOrItem, QStandardItem):
            try:
                indexOrItem = indexOrItem.index()
            except RuntimeError as e: # wrapped C/C++ object of type x has been deleted
                return str(e)
        if not isinstance(indexOrItem, QModelIndex):
            return f"(Unknown index/item: {indexOrItem})"
        if not indexOrItem.isValid():
            return f"(invalid index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"

        item = self.model().itemFromIndex(indexOrItem)
        if item is None:
            return f"(no item associated with index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"

        text = item.text().strip()
        parent_count = 0
        current_index = indexOrItem.parent()
        while current_index.isValid():
            parent_count += 1
            current_index = current_index.parent()

        return f"Item/Index at Row: {indexOrItem.row()}, Column: {indexOrItem.column()}, Ancestors: {parent_count}\nText for above item: {text}\n"

    def branchConnectorsDrawn(self) -> bool:
        return self.branch_connectors_enabled

    def drawConnectors(
        self,
        draw: bool,  # noqa: FBT001, FBT002
    ):
        if not draw:
            self.branch_connectors_enabled = False
            self.setStyleSheet(self.original_stylesheet)
        else:
            self.branch_connectors_enabled = True
            self.setStyleSheet("""
            QTreeView {
                alternate-background-color: yellow;
                show-decoration-selected: 1;
            }

            QTreeView::item {
                border: 1px solid #d9d9d9;
                border-top-color: transparent;
                border-bottom-color: transparent;
            }

            QTreeView::item:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
                border: 1px solid #bfcde4;
            }

            QTreeView::item:selected {
                border: 1px solid #567dbc;
            }

            QTreeView::item:selected:active {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);
            }

            QTreeView::item:selected:!active {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);
            }

            QTreeView::branch {
                background: palette(base);
            }

            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: url(:/images/common/stylesheet-vline.png) 0;
            }

            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url(:/images/common/stylesheet-branch-more.png) 0;
            }

            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(:/images/common/stylesheet-branch-end.png) 0;
            }

            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(:/images/common/stylesheet-branch-closed.png);
            }

            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(:/images/common/stylesheet-branch-open.png);
            }
            """)
