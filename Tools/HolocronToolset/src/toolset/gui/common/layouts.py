from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QPoint, QRect, QSize, Qt
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QLabel,
    QLayout,
    QLayoutItem,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QWidget,
)

if TYPE_CHECKING:
    from qtpy.QtCore import QMargins
    from qtpy.QtWidgets import QLayoutItem, QStyle


class FlowLayout(QLayout):
    def __init__(
        self,
        parent: QWidget | None = None,
        margin: int = -1,
        h_spacing: int = -1,
        v_spacing: int = -1,
    ):
        super().__init__(parent)
        self.item_list: list[QLayoutItem] = []
        self.m_h_space: int = h_spacing
        self.m_v_space: int = v_spacing
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def addItem(
        self,
        item: QLayoutItem,
    ):
        self.item_list.append(item)

    def count(self) -> int:
        return len(self.item_list)

    def itemAt(
        self,
        index: int,
    ) -> QLayoutItem | None:
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(
        self,
        index: int,
    ) -> QLayoutItem | None:
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self.rearrangeItems(rect)

    def sizeHint(self) -> QSize:
        return self.calculateSize()

    def minimumSize(self) -> QSize:
        return self.calculateSize()

    def calculateSize(self) -> QSize:
        size: QSize = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margins: QMargins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def rearrangeItems(self, rect: QRect):
        contents_margin: QMargins = self.contentsMargins()
        left: int = contents_margin.left()
        top: int = contents_margin.top()
        right: int = contents_margin.right()
        bottom: int = contents_margin.bottom()
        effective_rect: QRect = rect.adjusted(left, top, -right, -bottom)
        x: float = effective_rect.x()
        y: float = effective_rect.y()
        line_height: int = 0
        max_width: int = effective_rect.width()
        max_height: int = effective_rect.height()

        current_line: list[QLayoutItem] = []

        def layout_current_line():
            nonlocal x, y, line_height
            if not current_line:
                return
            total_width: int = sum(item.sizeHint().width() for item in current_line)
            space_between: float = (
                (max_width - total_width) / (len(current_line) - 1)
                if len(current_line) > 1
                else 0
            )
            x = effective_rect.x()
            for item in current_line:
                item_size_hint: QSize = item.sizeHint()
                item.setGeometry(QRect(QPoint(int(x), int(y)), item_size_hint))
                x += item_size_hint.width() + space_between
            y += line_height + space_y
            line_height = 0
            current_line.clear()

        for item in self.item_list:
            widget: QWidget | None = item.widget()
            if widget is None:
                continue
            item_size_hint: QSize = item.sizeHint()
            item_width: int = item_size_hint.width()
            item_height: int = item_size_hint.height()
            widget_style: QStyle | None = widget.style()
            if widget_style is None:
                continue
            space_x: int = (
                self.m_h_space
                if self.m_h_space >= 0
                else widget_style.layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal,
                )
            )
            space_y: int = (
                self.m_v_space
                if self.m_v_space >= 0
                else widget_style.layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical,
                )
            )

            if x + item_width > effective_rect.right():
                layout_current_line()

            if y + item_height + line_height + space_y > effective_rect.bottom():
                space_y = 0

            current_line.append(item)
            x += item_width + space_x
            line_height = max(line_height, item_height)

        layout_current_line()

class ExampleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowLayout Example")

        # Scrollable Area Setup
        scroll_area = QScrollArea(self)  # Create a scroll area that will contain the central widget
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setCentralWidget(scroll_area)

        # Central Widget which will contain the layout
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)  # Set the central widget of the scroll area

        # Flow Layout Setup
        flow_layout = FlowLayout(central_widget)
        central_widget.setLayout(flow_layout)

        # Adding various widgets to the flow layout
        flow_layout.addWidget(QLabel("Label"))
        flow_layout.addWidget(QPushButton("Button"))
        flow_layout.addWidget(QLineEdit("Edit me"))
        flow_layout.addWidget(QCheckBox("Check me"))
        flow_layout.addWidget(QRadioButton("Choose me"))

        combo = QComboBox()
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        flow_layout.addWidget(combo)

        flow_layout.addWidget(QSlider(Qt.Orientation.Horizontal))
        spin_box = QSpinBox()
        spin_box.setRange(0, 100)
        flow_layout.addWidget(spin_box)

        progress_bar = QProgressBar()
        progress_bar.setValue(50)
        flow_layout.addWidget(progress_bar)

        flow_layout.addWidget(QDateEdit())

        # Styling the widgets
        self.applyStyles(central_widget)

    def applyStyles(
        self,
        widget: QWidget,
    ):
        # Apply some color to distinguish widget areas
        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window,
            QColor(240, 240, 240),
        )  # Light gray background
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
