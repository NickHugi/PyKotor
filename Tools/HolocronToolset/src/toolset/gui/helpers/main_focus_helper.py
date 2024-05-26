from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QEvent, QObject, Qt, Signal
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import QTreeView

from toolset.gui.widgets.main_widgets import ResourceList, TextureList

if TYPE_CHECKING:
    from qtpy.QtWidgets import QLineEdit, QWidget

    from toolset.gui.windows.main import ToolWindow


class MainFocusHandler(QObject):
    tabNavigated = Signal()

    def __init__(self, mainWindow: ToolWindow):
        super().__init__(mainWindow)
        self.mainWindow: ToolWindow = mainWindow
        self.curFocusIndex: int = 0
        self.focuseableWidgets: list[QWidget] = [
            self.mainWindow.ui.gameCombo,
            self.mainWindow.ui.coreWidget,
            self.mainWindow.ui.savesWidget,
            self.mainWindow.ui.modulesWidget,
            self.mainWindow.ui.overrideWidget,
            self.mainWindow.ui.texturesWidget,
            self.mainWindow.ui.openButton,
            self.mainWindow.ui.extractButton,
            self.mainWindow.ui.tpcDecompileCheckbox,
            self.mainWindow.ui.tpcTxiCheckbox,
            self.mainWindow.ui.mdlDecompileCheckbox,
            self.mainWindow.ui.mdlTexturesCheckbox,
        ]

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:  # KeyPress event type is 51
            #self.mainWindow.log.debug(f"MainFocusHandler: obj={obj.objectName()}, event.type()={event.type()}")
            assert isinstance(event, QKeyEvent)
            qKey: Qt.Key = Qt.Key(event.key())
            curWidget = self.mainWindow.getActiveResourceWidget()
            searchEdit = curWidget.ui.searchEdit if isinstance(curWidget, (ResourceList, TextureList)) else None
            if searchEdit is None:
                return super().eventFilter(obj, event)
            #self.mainWindow.log.debug(f"MainFocusHandler: curWidget={curWidget.objectName()}, searchEdit={searchEdit.objectName()}")

            if qKey in [Qt.Key_Tab, Qt.Key_Backtab]:
                #self.mainWindow.log.debug(f"MainFocusHandler: qKey ({qKey}) in [Qt.Key_Tab ({Qt.Key_Tab}), Qt.KeyBacktab ({Qt.Key_Backtab})]")
                self.handleTabNavigation(event)
                return True

            if searchEdit and (
                Qt.Key_Space <= qKey <= Qt.Key_AsciiTilde
                or qKey in [Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Escape, Qt.Key_Left, Qt.Key_Right]
            ):
                #self.mainWindow.log.debug(f"MainFocusHandler: qKey ({qKey}) in [Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Escape, Qt.Key_Left, Qt.Key_Right]")
                self.handleSearchBoxKeyEvent(searchEdit, qKey, event)
                return True

            if qKey in [Qt.Key_Enter, Qt.Key_Return]:
                curWidget.requestOpenResource.emit(curWidget.selectedResources(), True)

            if isinstance(curWidget, QTreeView) and qKey in [Qt.Key_Left, Qt.Key_Right]:
                #self.mainWindow.log.debug("MainFocusHandler: curWidget is QTreeView, left/right arrow key pressed")
                self.handleTreeViewKeyEvent(curWidget, qKey)
                return True

        return super().eventFilter(obj, event)

    def handleTabNavigation(self, event: QKeyEvent):
        # TODO(th3w1zard1)
        shift_pressed = event.key() == Qt.Key_Backtab
        if shift_pressed:
            #self.mainWindow.log.debug("MainFocusHandler.handleTabNavigation: shift_pressed!")
            self.curFocusIndex -= 1
            if self.curFocusIndex < 0:
                self.curFocusIndex = len(self.focuseableWidgets) - 1
        else:
            #self.mainWindow.log.debug("MainFocusHandler.handleTabNavigation: NOT shift_pressed!")
            self.curFocusIndex += 1
            if self.curFocusIndex >= len(self.focuseableWidgets):
                self.curFocusIndex = 0

        self.focuseableWidgets[self.curFocusIndex].setFocus()
        self.tabNavigated.emit()

    def handleSearchBoxKeyEvent(
        self,
        searchEdit: QLineEdit,
        qKey: Qt.Key,
        event: QKeyEvent,
    ):  # sourcery skip: extract-method
        if qKey == Qt.Key_Escape:
            #self.mainWindow.log.debug("MainFocusHandler.handleSearchBoxKeyEvent: qKey == Qt.Key_Escape")
            searchEdit.clear()

        elif qKey == Qt.Key_Backspace:
            #self.mainWindow.log.debug("MainFocusHandler.handleSearchBoxKeyEvent: qKey == Qt.Key_Backspace")
            cursorPos = searchEdit.cursorPosition()
            currentText = searchEdit.text()
            if cursorPos > 0:
                searchEdit.setText(currentText[: cursorPos - 1] + currentText[cursorPos:])
                searchEdit.setCursorPosition(cursorPos - 1)

        elif qKey == Qt.Key_Delete:
            #self.mainWindow.log.debug("MainFocusHandler.handleSearchBoxKeyEvent: qKey == Qt.Key_Delete")
            cursorPos = searchEdit.cursorPosition()
            currentText = searchEdit.text()
            if cursorPos < len(currentText):
                searchEdit.setText(currentText[:cursorPos] + currentText[cursorPos + 1 :])
                searchEdit.setCursorPosition(cursorPos)

        elif qKey in [Qt.Key_Left, Qt.Key_Right]:
            #self.mainWindow.log.debug("MainFocusHandler.handleSearchBoxKeyEvent: qKey in [Qt.Key_Left, Qt.Key_Right]")
            searchEdit.setFocus()  # Ensure the search box has focus for cursor movement
            searchEdit.event(event)  # Send the event to the search box

        else:
            cursorPos = searchEdit.cursorPosition()
            currentText = searchEdit.text()
            eventText = event.text()
            #self.mainWindow.log.debug(f"MainFocusHandler.handleSearchBoxKeyEvent else blc: cursor_pos={cursorPos}, current_text={currentText}, appending event text: {eventText}")
            searchEdit.setText(currentText[:cursorPos] + eventText + currentText[cursorPos:])
            searchEdit.setCursorPosition(cursorPos + 1)

        searchEdit.textEdited.emit(None)

    def handleTreeViewKeyEvent(self, treeView: QTreeView, qKey: Qt.Key):
        #self.mainWindow.log.debug(f"MainFocusHandler.handleTreeViewKeyEvent qKey={qKey}")
        index = treeView.currentIndex()
        if qKey == Qt.Key_Left:
            #self.mainWindow.log.debug("MainFocusHandler.handleTreeViewKeyEvent qKey == Qt.Key_Left")
            treeView.setExpanded(index, False)
        elif qKey == Qt.Key_Right:
            #self.mainWindow.log.debug("MainFocusHandler.handleTreeViewKeyEvent qKey == Qt.Key_Right")
            treeView.setExpanded(index, True)
