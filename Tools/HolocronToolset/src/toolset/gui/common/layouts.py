from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QLayout, QMainWindow, QSizePolicy, QWidget
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QCheckBox, QComboBox, QDateEdit, QLineEdit, QProgressBar, QPushButton, QRadioButton, QScrollArea, QSlider, QSpinBox

if TYPE_CHECKING:
    from qtpy.QtWidgets import QLayoutItem


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hSpacing=-1, vSpacing=-1):
        super().__init__(parent)
        self.itemList: list[QLayoutItem] = []
        self.m_hSpace = hSpacing
        self.m_vSpace = vSpacing
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.rearrangeItems(rect)

    def sizeHint(self):
        return self.calculateSize()

    def minimumSize(self):
        return self.calculateSize()

    def calculateSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def rearrangeItems(self, rect: QRect):
        left, top, right, bottom = self.getContentsMargins()
        effectiveRect = rect.adjusted(left, top, -right, -bottom)
        x, y = effectiveRect.x(), effectiveRect.y()
        lineHeight = 0
        maxWidth = effectiveRect.width()
        maxHeight = effectiveRect.height()

        currentLine = []

        def layoutCurrentLine():
            nonlocal x, y, lineHeight
            if not currentLine:
                return
            totalWidth = sum(item.sizeHint().width() for item in currentLine)
            spaceBetween = (maxWidth - totalWidth) / (len(currentLine) - 1) if len(currentLine) > 1 else 0
            x = effectiveRect.x()
            for item in currentLine:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                x += item.sizeHint().width() + spaceBetween
            y += lineHeight + spaceY
            lineHeight = 0
            currentLine.clear()

        for item in self.itemList:
            widget = item.widget()
            itemWidth = item.sizeHint().width()
            itemHeight = item.sizeHint().height()
            spaceX = self.m_hSpace if self.m_hSpace >= 0 else widget.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.m_vSpace if self.m_vSpace >= 0 else widget.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)

            if x + itemWidth > effectiveRect.right():
                layoutCurrentLine()

            if y + itemHeight + lineHeight + spaceY > effectiveRect.bottom():
                spaceY = 0

            currentLine.append(item)
            x += itemWidth + spaceX
            lineHeight = max(lineHeight, itemHeight)

        layoutCurrentLine()

class ExampleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowLayout Example")

        # Scrollable Area Setup
        scrollArea = QScrollArea(self)  # Create a scroll area that will contain the central widget
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setCentralWidget(scrollArea)

        # Central Widget which will contain the layout
        centralWidget = QWidget()
        scrollArea.setWidget(centralWidget)  # Set the central widget of the scroll area

        # Flow Layout Setup
        flowLayout = FlowLayout(centralWidget)
        centralWidget.setLayout(flowLayout)

        # Adding various widgets to the flow layout
        flowLayout.addWidget(QLabel("Label"))
        flowLayout.addWidget(QPushButton("Button"))
        flowLayout.addWidget(QLineEdit("Edit me"))
        flowLayout.addWidget(QCheckBox("Check me"))
        flowLayout.addWidget(QRadioButton("Choose me"))

        combo = QComboBox()
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        flowLayout.addWidget(combo)

        flowLayout.addWidget(QSlider(Qt.Horizontal))
        spinBox = QSpinBox()
        spinBox.setRange(0, 100)
        flowLayout.addWidget(spinBox)

        progressBar = QProgressBar()
        progressBar.setValue(50)
        flowLayout.addWidget(progressBar)

        flowLayout.addWidget(QDateEdit())

        # Styling the widgets
        self.applyStyles(centralWidget)

    def applyStyles(self, widget: QWidget):
        # Apply some color to distinguish widget areas
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))  # Light gray background
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
