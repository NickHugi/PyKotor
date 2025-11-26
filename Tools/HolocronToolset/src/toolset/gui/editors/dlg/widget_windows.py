from __future__ import annotations

import weakref

from typing import TYPE_CHECKING, ClassVar

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QTextDocument
from qtpy.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidgetItem, QPushButton, QStyle, QStyleOptionViewItem, QVBoxLayout

from pykotor.resource.generics.dlg import DLGLink
from toolset.gui.editors.dlg.list_widget_base import DLGListWidget, DLGListWidgetItem
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if TYPE_CHECKING:
    import weakref

    from qtpy.QtCore import QObject

    from pykotor.resource.generics.dlg import DLGLink
    from toolset.gui.editors.dlg.editor import DLGEditor
    from toolset.gui.editors.dlg.list_widget_base import QAbstractItemDelegate


class ReferenceChooserDialog(QDialog):
    item_chosen: ClassVar[Signal] = Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        references: list[weakref.ref[DLGLink]],
        parent: DLGEditor,
        item_text: str,
    ):
        from toolset.gui.editors.dlg.editor import DLGEditor

        assert isinstance(parent, DLGEditor)
        super().__init__(parent)
        qt_constructor: type[Qt.WindowFlags | Qt.WindowType] = Qt.WindowFlags if qtpy.QT5 else Qt.WindowType  # pyright: ignore[reportAttributeAccessIssue]
        self.setWindowFlags(Qt.WindowType.Dialog | qt_constructor(Qt.WindowType.WindowCloseButtonHint & ~Qt.WindowType.WindowContextHelpButtonHint))  # pyright: ignore[reportAttributeAccessIssue]
        self.setWindowTitle("Node References")

        layout = QVBoxLayout(self)
        self.label = QLabel()
        self.editor: DLGEditor = parent
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.list_widget: DLGListWidget = DLGListWidget(parent)  # HACK(th3w1zard1): fix later (set editor attr properly in listWidget)
        self.list_widget.use_hover_text = True
        self.list_widget.setParent(self)
        self.list_widget.setItemDelegate(HTMLDelegate(self.list_widget))
        layout.addWidget(self.list_widget)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        max_width = 0
        for linkref in references:
            link: DLGLink | None = linkref()
            if link is None:
                continue
            item = DLGListWidgetItem(link=link, ref=linkref)
            # Build the HTML display
            self.list_widget.update_item(item)
            self.list_widget.addItem(item)
            max_width = max(max_width, self.calculate_html_width(item.data(Qt.ItemDataRole.DisplayRole)))

        button_layout = QHBoxLayout()
        self.back_button: QPushButton = QPushButton()
        self.back_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))  # pyright: ignore[reportOptionalMemberAccess]
        self.forward_button: QPushButton = QPushButton()
        self.forward_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))  # pyright: ignore[reportOptionalMemberAccess]
        ok_button: QPushButton = QPushButton("OK")
        cancel_button: QPushButton = QPushButton("Cancel")
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.forward_button)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)

        self.setStyleSheet("""
        .link-container:hover .link-hover-text {
            display: block;
        }
        .link-container:hover .link-text {
            display: none;
        }
        .link-hover-text {
            display: none;
        }
        """)
        self.adjustSize()
        self.setMinimumSize(self.height(), self.width() + 50)
        self.forward_button.setEnabled(False)
        self.update_item_sizes()
        self.update_references(references, item_text)

    def parent(self) -> DLGEditor:
        from toolset.gui.editors.dlg.editor import DLGEditor

        parent: QObject | None = super().parent()
        assert isinstance(parent, DLGEditor)
        return parent

    def update_item_sizes(self):
        item_delegate: HTMLDelegate | QAbstractItemDelegate | None = self.list_widget.itemDelegate()
        if item_delegate is None:
            return
        for i in range(self.list_widget.count()):
            item: QListWidgetItem | None = self.list_widget.item(i)
            if not isinstance(item, QListWidgetItem):
                RobustLogger().warning(f"ReferenceChooser.update_item_sizes({i}): Item was None unexpectedly.")
                continue
            if qtpy.QT5:
                options: QStyleOptionViewItem = self.list_widget.viewOptions()  # pyright: ignore[reportAttributeAccessIssue]
            else:
                options: QStyleOptionViewItem = QStyleOptionViewItem()
                self.list_widget.initViewItemOption(options)
            item.setSizeHint(item_delegate.sizeHint(options, self.list_widget.indexFromItem(item)))

    def calculate_html_width(
        self,
        html: str,
    ) -> int:
        doc: QTextDocument = QTextDocument()
        doc.setHtml(html)
        return int(doc.idealWidth())

    def get_stylesheet(self) -> str:
        font_size = 12
        return f"""
        QListWidget {{
            font-size: {font_size}pt;
            margin: 10px;
        }}
        QPushButton {{
            font-size: {font_size}pt;
            padding: 5px 10px;
        }}
        QDialog {{
            background-color: #f0f0f0;
        }}
        .link-container:hover .link-hover-text {{
            display: block;
        }}
        .link-container:hover .link-text {{
            display: none;
        }}
        .link-hover-text {{
            display: none;
        }}
        """

    def accept(self):
        sel_item: QListWidgetItem | None = self.list_widget.currentItem()
        if isinstance(sel_item, DLGListWidgetItem):
            self.item_chosen.emit(sel_item)
        super().accept()

    def go_back(self):
        self.parent().navigate_back()
        self.update_button_states()

    def go_forward(self):
        self.parent().navigate_forward()
        self.update_button_states()

    def update_references(
        self,
        referenceItems: list[weakref.ref[DLGLink]],
        item_text: str,
    ):
        self.label.setText(item_text)
        self.list_widget.clear()
        node_path: str = ""
        for linkref in referenceItems:
            link: DLGLink | None = linkref()
            if link is None:
                continue
            listItem = DLGListWidgetItem(link=link, ref=linkref)
            self.list_widget.update_item(listItem)
            self.list_widget.addItem(listItem)
        self.update_item_sizes()
        self.adjustSize()
        self.setWindowTitle(f"Node References: {node_path}")
        self.update_button_states()

    def update_button_states(self):
        parent: DLGEditor = self.parent()
        self.back_button.setEnabled(parent.current_reference_index > 0)
        self.forward_button.setEnabled(parent.current_reference_index < len(parent.reference_history) - 1)
