from time import sleep
from typing import List, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel, QThread, QItemSelection
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PyQt5.QtWidgets import QShortcut, QDialog, QProgressBar, QVBoxLayout, QWidget
from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk import read_tlk, TLK, TLKEntry, write_tlk
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.editor import Editor


class TLKEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.TLK, ResourceType.TLK_XML, ResourceType.TLK_JSON]
        super().__init__(parent, "TLK Editor", "none", supported, supported, installation)

        from editors.tlk import tlk_editor_ui
        self.ui = tlk_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ui.searchBox.setVisible(False)
        self.ui.jumpBox.setVisible(False)

        self.model = QStandardItemModel(self)
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        self.ui.talkTable.setModel(self.proxyModel)

        # Make the bottom panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setupSignals(self) -> None:
        self.ui.actionGoTo.triggered.connect(self.toggleGotoBox)
        self.ui.jumpButton.clicked.connect(lambda: self.gotoLine(self.ui.jumpSpinbox.value()))
        self.ui.actionFind.triggered.connect(self.toggleFilterBox)
        self.ui.searchButton.clicked.connect(lambda: self.doFilter(self.ui.searchEdit.text()))
        self.ui.actionInsert.triggered.connect(self.insert)

        self.ui.talkTable.clicked.connect(self.selectionChanged)
        self.ui.textEdit.textChanged.connect(self.updateEntry)
        self.ui.soundEdit.textChanged.connect(self.updateEntry)

        QShortcut("Ctrl+F", self).activated.connect(self.toggleFilterBox)
        QShortcut("Ctrl+G", self).activated.connect(self.toggleGotoBox)
        QShortcut("Ctrl+I", self).activated.connect(self.insert)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        self.model.clear()
        self.model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)

        dialog = LoaderDialog(self, data, self.model)
        dialog.exec_()
        self.model = dialog.model
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        self.ui.talkTable.setModel(self.proxyModel)
        self.ui.talkTable.selectionModel().selectionChanged.connect(self.selectionChanged)

        self.ui.jumpSpinbox.setMaximum(self.model.rowCount())

    def new(self) -> None:
        super().new()

        self.model.clear()
        self.model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)

        self.ui.textEdit.setEnabled(False)
        self.ui.soundEdit.setEnabled(False)

    def build(self) -> bytes:
        tlk = TLK()

        for i in range(self.model.rowCount()):
            text = self.model.item(i, 0).text()
            sound = ResRef(self.model.item(i, 1).text())
            tlk.entries.append(TLKEntry(text, sound))

        data = bytearray()
        write_tlk(tlk, data, self._restype)
        return data

    def insert(self) -> None:
        self.model.appendRow([QStandardItem(""), QStandardItem("")])

    def doFilter(self, text: str) -> None:
        self.proxyModel.setFilterFixedString(text)

    def toggleFilterBox(self) -> None:
        self.ui.searchBox.setVisible(not self.ui.searchBox.isVisible())

    def gotoLine(self, line: int) -> None:
        index = self.model.index(line, 0)
        proxyIndex = self.proxyModel.mapFromSource(index)
        self.ui.talkTable.scrollTo(proxyIndex)
        self.ui.talkTable.setCurrentIndex(proxyIndex)

    def toggleGotoBox(self) -> None:
        self.ui.jumpBox.setVisible(not self.ui.jumpBox.isVisible())

    def selectionChanged(self) -> None:
        selected = self.ui.talkTable.selectionModel().selection()

        if len(selected.indexes()) == 0:
            self.ui.textEdit.setEnabled(False)
            self.ui.soundEdit.setEnabled(False)
            return

        self.ui.textEdit.setEnabled(True)
        self.ui.soundEdit.setEnabled(True)

        proxyIndex = selected.indexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item = self.model.itemFromIndex(sourceIndex)

        text = item.text()
        sound = self.model.item(sourceIndex.row(), 1).text()

        self.ui.textEdit.setPlainText(text)
        self.ui.soundEdit.setText(sound)

    def updateEntry(self) -> None:
        proxyIndex = self.ui.talkTable.selectedIndexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)

        self.model.item(sourceIndex.row(), 0).setText(self.ui.textEdit.toPlainText())
        self.model.item(sourceIndex.row(), 1).setText(self.ui.soundEdit.text())


class LoaderDialog(QDialog):
    def __init__(self, parent, fileData, model):
        super().__init__(parent)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMinimum(0)
        self._progressBar.setMaximum(0)
        self._progressBar.setTextVisible(False)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)

        self.setWindowTitle("Loading...")
        self.setFixedSize(200, 40)

        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        self.model = QStandardItemModel()
        self.model.setColumnCount(2)

        self.worker = LoaderWorker(fileData, model)
        self.worker.entryCount.connect(self.onEntryCount)
        self.worker.batch.connect(self.onBatch)
        self.worker.loaded.connect(self.onLoaded)
        self.worker.start()

    def onEntryCount(self, count: int):
        self._progressBar.setMaximum(count)

    def onBatch(self, batch: List[QStandardItem]):
        for row in batch:
            self.model.appendRow(row)
            index = self.model.rowCount() - 1
            self.model.setVerticalHeaderItem(index, QStandardItem(str(index)))
        self._progressBar.setValue(self.model.rowCount())

    def onLoaded(self):
        self.close()


class LoaderWorker(QThread):
    batch = QtCore.pyqtSignal(object)
    entryCount = QtCore.pyqtSignal(object)
    loaded = QtCore.pyqtSignal()

    def __init__(self, fileData, model):
        super().__init__()
        self._fileData: bytes = fileData
        self._model: QStandardItemModel = model

    def run(self):
        tlk = read_tlk(self._fileData)

        self.entryCount.emit(len(tlk))

        batch = []
        for stringref, entry in tlk:
            batch.append([QStandardItem(entry.text), QStandardItem(entry.voiceover.get())])
            if len(batch) > 200:
                self.batch.emit(batch)
                batch = []
                sleep(0.001)
        self.batch.emit(batch)

        self.loaded.emit()
