from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel, QThread
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QAction, QDialog, QProgressBar, QShortcut, QVBoxLayout, QWidget

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk import TLK, TLKEntry, read_tlk, write_tlk
from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from toolset.data.installation import HTInstallation


class TLKEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation | None = None):
        """Initialize the TLK Editor.

        Args:
        ----
            parent: QWidget - Parent widget
            installation: HTInstallation | None - Installation object
        Returns:
            None
        Processing Logic:
            - Set up the UI from the designer file
            - Connect menu and signal handlers
            - Hide search/jump boxes
            - Set up the data model and proxy model for the table view
            - Make bottom panel take minimal space
            - Create a new empty TLK file.
        """
        supported = [ResourceType.TLK, ResourceType.TLK_XML, ResourceType.TLK_JSON]
        super().__init__(parent, "TLK Editor", "none", supported, supported, installation)

        from toolset.uic.editors.tlk import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ui.searchBox.setVisible(False)
        self.ui.jumpBox.setVisible(False)

        self.language = Language.ENGLISH

        self.model = QStandardItemModel(self)
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        self.ui.talkTable.setModel(self.proxyModel)

        # Make the bottom panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setupSignals(self) -> None:
        """Set up signal connections for UI actions and widgets.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None
        Processing Logic:
            - Connect action triggers to slot functions
            - Connect button clicks to slot functions
            - Connect table and text edits to update functions
            - Set up keyboard shortcuts to trigger actions.
        """
        self.ui.actionGoTo.triggered.connect(self.toggleGotoBox)
        self.ui.jumpButton.clicked.connect(lambda: self.gotoLine(self.ui.jumpSpinbox.value()))
        self.ui.actionFind.triggered.connect(self.toggleFilterBox)
        self.ui.searchButton.clicked.connect(lambda: self.doFilter(self.ui.searchEdit.text()))
        self.ui.actionInsert.triggered.connect(self.insert)
        #self.ui.actionAuto_detect_slower.triggered.connect()

        self.ui.talkTable.clicked.connect(self.selectionChanged)
        self.ui.textEdit.textChanged.connect(self.updateEntry)
        self.ui.soundEdit.textChanged.connect(self.updateEntry)

        self.populateLanguageMenu()

        QShortcut("Ctrl+F", self).activated.connect(self.toggleFilterBox)
        QShortcut("Ctrl+G", self).activated.connect(self.toggleGotoBox)
        QShortcut("Ctrl+I", self).activated.connect(self.insert)

    def populateLanguageMenu(self):
        self.ui.menuLanguage.clear()

        # Add 'Auto_Detect_slower' action first
        autoDetectAction = QAction("Auto_detect_slower", self)
        autoDetectAction.triggered.connect(lambda: self.onLanguageSelected("auto_detect"))
        self.ui.menuLanguage.addAction(autoDetectAction)

        # Separator
        self.ui.menuLanguage.addSeparator()

        # Add languages from the enum
        for language in Language:
            action = QAction(language.name.replace("_", " "), self)
            action.triggered.connect(lambda _checked, lang=language: self.onLanguageSelected(lang))
            self.ui.menuLanguage.addAction(action)

    def onLanguageSelected(self, language) -> None:
        if isinstance(language, Language):
            print(f"Language selected: {language.name}")
            self.change_language(language)
        else:
            print("Auto detect selected")
            self.change_language(Language.UNKNOWN)

    def change_language(self, language: Language):
        encoding = language.get_encoding()  # Assuming get_encoding() returns the correct encoding string

        for i in range(self.model.rowCount()):
            # Retrieve the current text from the model
            current_text_item = self.model.item(i, 0)  # Assuming column 0 has the text
            if current_text_item is not None:
                current_text = current_text_item.text()

                # Re-encode the text
                try:
                    text_bytes = current_text.encode(self.language.get_encoding())
                    decoded_text = text_bytes.decode(encoding) if encoding else decode_bytes_with_fallbacks(text_bytes)
                except UnicodeEncodeError:
                    print("could not encode, attempting encode as utf-8...")
                    # Handle encoding errors, maybe log or set a default value
                    try:
                        text_bytes = current_text.encode()
                        decoded_text = text_bytes.decode(encoding) if encoding else decode_bytes_with_fallbacks(text_bytes)
                    except UnicodeDecodeError:
                        print("could not encode or decode, using utf-8 for both")
                        text_bytes = current_text.encode()
                        decoded_text = text_bytes.decode()
                except UnicodeDecodeError:
                    print("could not decode but encoding works, decoding as utf-8")
                    text_bytes = current_text.encode(self.language.get_encoding())
                    decoded_text = text_bytes.decode()

                # Update the model with the new text
                self.model.setItem(i, 0, QStandardItem(decoded_text))

        # Update UI components if necessary, like the table view
        self.ui.talkTable.setModel(self.proxyModel)
        self.language = language

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Loads data into the resource from a file.

        Args:
        ----
            filepath: The path to the file to load from.
            resref: The resource reference.
            restype: The resource type.
            data: The raw data bytes.

        Returns:
        -------
            None
        Processing Logic:
            - Clears existing model data
            - Sets column count to 2 and hides second column
            - Opens dialog to process loading data
            - Sets loaded data as model
            - Sets sorting proxy model
            - Connects selection changed signal
            - Sets max rows in spinbox.
        """
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

    def build(self) -> tuple[bytes, bytes]:
        """Builds a TLK file from the model data.

        Args:
        ----
            self: The object instance
        Returns:
            tuple[bytes, bytes]: A tuple containing the TLK data and an empty bytes object
        - Iterate through each row in the model
        - Extract the text and sound from each item
        - Add an entry to the TLK object with the text and sound
        - Write the TLK object to a byte array
        - Return the byte array and an empty bytes object as a tuple.
        """
        tlk = TLK()

        for i in range(self.model.rowCount()):
            text = self.model.item(i, 0).text()
            sound = ResRef(self.model.item(i, 1).text())
            tlk.entries.append(TLKEntry(text, sound))

        data = bytearray()
        write_tlk(tlk, data, self._restype)
        return data, b""

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
        """Handle selection changes in the talk table.

        Args:
        ----
            self: The class instance
        Returns:
            None: Does not return anything
        - Check if any rows are selected in the talk table
        - If no rows selected, disable text and sound editors
        - If rows selected, enable text and sound editors
        - Get selected row data from model
        - Populate text and sound editors with data from selected row.
        """
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
        """Initializes the loading dialog.

        Args:
        ----
            parent: {The parent widget of the dialog}
            fileData: {The data to load}
            model: {The model to populate}.

        Returns:
        -------
            None: {Does not return anything}
        Processing Logic:
            - Creates a progress bar to display loading progress
            - Sets up the dialog layout and adds progress bar
            - Starts a worker thread to load the data in the background
            - Connects signals from worker to update progress bar.
        """
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
        self.worker.language.connect(self.setupLanguage)
        self.worker.start()

    def onEntryCount(self, count: int):
        self._progressBar.setMaximum(count)

    def onBatch(self, batch: list[QStandardItem]):
        for row in batch:
            self.model.appendRow(row)
            index = self.model.rowCount() - 1
            self.model.setVerticalHeaderItem(index, QStandardItem(str(index)))
        self._progressBar.setValue(self.model.rowCount())

    def setupLanguage(self, language: Language):
        self.language = language

    def onLoaded(self):
        self.close()


class LoaderWorker(QThread):
    batch = QtCore.pyqtSignal(object)
    entryCount = QtCore.pyqtSignal(object)
    loaded = QtCore.pyqtSignal()
    language = QtCore.pyqtSignal(object)

    def __init__(self, fileData, model) -> None:
        super().__init__()
        self._fileData: bytes = fileData
        self._model: QStandardItemModel = model

    def load_data(self):
        """Load tlk data from file."""
        tlk = read_tlk(self._fileData)
        self.entryCount.emit(len(tlk))
        self.language.emit(tlk.language)

        batch = []
        for _stringref, entry in tlk:
            batch.append([QStandardItem(entry.text), QStandardItem(entry.voiceover.get())])
            if len(batch) > 200:
                self.batch.emit(batch)
                batch = []
                sleep(0.001)
        self.batch.emit(batch)
        self.loaded.emit()

    def run(self):
        """Load tlk data from file in batches
        Args:
            self: The class instance
        Returns:
            None: Load data and emit signals
        Processes tlk data:
            - Reads timeline data from file
            - Counts number of entries and emits count
            - Loops through entries and batches data into lists of 200
            - Emits batches and sleeps to allow UI to update
            - Emits final batch
            - Signals loading is complete.
        """
        self.load_data()
