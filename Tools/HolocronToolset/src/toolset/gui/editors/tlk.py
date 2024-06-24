from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QSortFilterProxyModel, QThread, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAction, QDialog, QMenu, QMessageBox, QProgressBar, QShortcut, QSpinBox, QVBoxLayout

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk import TLK, TLKEntry, bytes_tlk, read_tlk, write_tlk
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.search import FileResults
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import addWindow, openResourceEditor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QModelIndex
    from qtpy.QtGui import QKeyEvent
    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal

    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class EnterSpinBox(QSpinBox):
    # Custom signal that you can emit when Enter is pressed
    enterPressed = QtCore.Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Emit the custom signal when Enter or Return is pressed
            self.enterPressed.emit()
        else:
            # Otherwise, proceed with the default behavior
            super().keyPressEvent(event)


class TLKEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the TLK Editor.

        Args:
        ----
            parent: QWidget - Parent widget
            installation: HTInstallation | None - Installation object

        Processing Logic:
        ----------------
            - Set up the UI from the designer file
            - Connect menu and signal handlers
            - Hide search/jump boxes
            - Set up the data model and proxy model for the table view
            - Make bottom panel take minimal space
            - Create a new empty TLK file.
        """
        supported: list[ResourceType] = [ResourceType.TLK, ResourceType.TLK_XML, ResourceType.TLK_JSON]
        super().__init__(parent, "TLK Editor", "none", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.tlk import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.tlk import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.tlk import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.tlk import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ui.searchBox.setVisible(False)
        self.ui.jumpBox.setVisible(False)

        self.language: Language = Language.ENGLISH

        self.model = QStandardItemModel(self)
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        self.ui.talkTable.setModel(self.proxyModel)

        # Make the bottom panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setupSignals(self):
        """Set up signal connections for UI actions and widgets.

        Processing Logic:
        ----------------
            - Connect action triggers to slot functions
            - Connect button clicks to slot functions
            - Connect table and text edits to update functions
            - Set up keyboard shortcuts to trigger actions.
        """
        self.ui.actionGoTo.triggered.connect(self.toggleGotoBox)
        self.ui.jumpButton.clicked.connect(lambda: self.gotoLine(self.ui.jumpSpinbox.value()))
        #self.ui.jumpSpinbox.editingFinished.connect(lambda: self.gotoLine(self.ui.jumpSpinbox.value()))
        self.ui.jumpSpinbox.__class__ = EnterSpinBox
        assert isinstance(self.ui.jumpSpinbox, EnterSpinBox)
        self.ui.jumpSpinbox.enterPressed.connect(lambda: self.gotoLine(self.ui.jumpSpinbox.value()))
        self.ui.actionFind.triggered.connect(self.toggleFilterBox)
        self.ui.searchButton.clicked.connect(lambda: self.doFilter(self.ui.searchEdit.text()))
        self.ui.actionInsert.triggered.connect(self.insert)
        # self.ui.actionAuto_detect_slower.triggered.connect()

        self.ui.talkTable.clicked.connect(self.selectionChanged)
        self.ui.textEdit.textChanged.connect(self.updateEntry)
        self.ui.soundEdit.textChanged.connect(self.updateEntry)
        self.ui.talkTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.talkTable.customContextMenuRequested.connect(self.showContextMenu)

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
            action.triggered.connect(lambda _checked=None, lang=language: self.onLanguageSelected(lang))
            self.ui.menuLanguage.addAction(action)

    def onLanguageSelected(
        self,
        language: Language | Literal["auto_detect"],
    ):
        if isinstance(language, Language):
            print(f"Language selected: {language.name}")
            self.change_language(language)
        else:
            print("Auto detect selected")
            self.change_language(Language.UNKNOWN)

    def change_language(
        self,
        language: Language,
    ):  # sourcery skip: class-extract-method
        self.language = language
        if not self._revert:
            return
        tlk: TLK = read_tlk(self._revert, language=language)
        self.model.clear()
        self.model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)
        dialog = LoaderDialog(self, bytes_tlk(tlk), self.model)
        self._init_model_dialog(dialog)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Loads data into the resource from a file.

        Args:
        ----
            filepath: The path to the file to load from.
            resref: The resource reference.
            restype: The resource type.
            data: The raw data bytes.

        Processing Logic:
        ----------------
            - Clears existing model data
            - Sets column count to 2 and hides second column
            - Opens dialog to process loading data
            - Sets loaded data as model
            - Sets sorting proxy model
            - Connects selection changed signal
            - Sets max rows in spinbox.
        """
        super().load(filepath, resref, restype, data)  # sourcery skip: class-extract-method
        self.model.clear()
        self.model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)
        dialog = LoaderDialog(self, data, self.model)
        self._init_model_dialog(dialog)

    def _init_model_dialog(
        self,
        dialog: LoaderDialog,
    ):
        dialog.exec_()
        self.model = dialog.model
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        self.ui.talkTable.setModel(self.proxyModel)
        self.ui.talkTable.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.ui.jumpSpinbox.setMaximum(self.model.rowCount())

    def showContextMenu(self, position):
        # Map the point to index to determine which item is under the cursor
        index = self.ui.talkTable.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()

        # Add 'Find References' action
        findAction = QAction("Find LocalizedString references", self)
        findAction.triggered.connect(lambda: self.findReferences(index))
        menu.addAction(findAction)

        # Add more actions as needed
        #otherAction = QAction("Other Action", self)
        # Connect otherAction to its slot here

        #menu.addAction(otherAction)

        # Show the menu at the current position
        menu.exec_(self.ui.talkTable.viewport().mapToGlobal(position))

    def findReferences(
        self,
        index: QModelIndex,
    ):
        # Implement the logic to find references based on the provided index
        stringref = index.row()
        print(f"Finding references to stringref: {stringref}")
        loader = AsyncLoader(
            self,
            f"Looking for stringref '{stringref}' in {self._installation.path()}...",
            lambda: self._installation.find_tlk_entry_references(stringref),
            errorTitle="An unexpected error occurred searching the installation.",
            startImmediately=False,
        )
        loader.setModal(False)
        loader.show()
        loader.optionalFinishHook.connect(
            lambda results: self.handleSearchCompleted(
                stringref, results, self._installation
            )
        )
        loader.startWorker()
        addWindow(loader)

    def handleSearchCompleted(
        self,
        stringref: int,
        results_list: list[FileResource] | set[FileResource],
        searchedInstallation: HTInstallation,
    ):
        if not results_list:
            QMessageBox(
                QMessageBox.Icon.Information,
                "No resources found",
                f"There are no GFFs that reference this tlk entry (stringref {stringref})",
                parent=self,
            ).exec_()
            return
        resultsDialog = FileResults(self, results_list, searchedInstallation)
        resultsDialog.setModal(False)  # Make the dialog non-modal
        resultsDialog.show()  # Show the dialog without blocking
        resultsDialog.setWindowTitle(f"{len(results_list)} results for stringref '{stringref}' in {self._installation.path()}")
        addWindow(resultsDialog)
        resultsDialog.selectionSignal.connect(self.handleResultsSelection)

    def handleResultsSelection(
        self,
        selection: FileResource,
    ):
        # Open relevant tab then select resource in the tree
        filepath, editor = openResourceEditor(
            selection.filepath(),
            selection.resname(),
            selection.restype(),
            selection.data(),
            self._installation,
            self,
            gff_specialized=GlobalSettings().gff_specializedEditors,
        )

    def new(self):
        super().new()

        self.model.clear()  # sourcery skip: class-extract-method
        self.model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)
        self.ui.textEdit.setEnabled(False)
        self.ui.soundEdit.setEnabled(False)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a TLK file from the model data.

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the TLK data and an empty bytes object

        Processing Logic:
        ----------------
            - Iterate through each row in the model
            - Extract the text and sound from each item
            - Add an entry to the TLK object with the text and sound
            - Write the TLK object to a byte array
            - Return the byte array and an empty bytes object as a tuple.
        """
        tlk = TLK()
        tlk.language = self.language

        for i in range(self.model.rowCount()):
            text = self.model.item(i, 0).text()
            sound = ResRef(self.model.item(i, 1).text())
            tlk.entries.append(TLKEntry(text, sound))

        data = bytearray()
        write_tlk(tlk, data, self._restype or ResourceType.TLK)
        return data, b""

    def insert(self):
        self.model.appendRow([QStandardItem(""), QStandardItem("")])

    def doFilter(self, text: str):
        self.proxyModel.setFilterFixedString(text)

    def toggleFilterBox(self):
        isVisible: bool = self.ui.searchBox.isVisible()
        self.ui.searchBox.setVisible(not isVisible)
        if not isVisible:  # If the jump box was not visible before and now is
            self.ui.searchEdit.setFocus()  # Activate the spinbox for immediate typing
            self.ui.searchEdit.selectAll()

    def gotoLine(self, line: int):
        index = self.model.index(line, 0)
        proxyIndex = self.proxyModel.mapFromSource(index)
        self.ui.talkTable.scrollTo(proxyIndex)
        self.ui.talkTable.setCurrentIndex(proxyIndex)

    def toggleGotoBox(self):
        isVisible: bool = self.ui.jumpBox.isVisible()
        self.ui.jumpBox.setVisible(not isVisible)
        if not isVisible:  # If the jump box was not visible before and now is
            self.ui.jumpSpinbox.setFocus()  # Activate the spinbox for immediate typing
            self.ui.jumpSpinbox.selectAll()

    def selectionChanged(self):
        """Handle selection changes in the talk table.

        Processing Logic:
        ----------------
            - Check if any rows are selected in the talk table
            - If no rows selected, disable text and sound editors
            - If rows selected, enable text and sound editors
            - Get selected row data from model
            - Populate text and sound editors with data from selected row.
        """
        selected = self.ui.talkTable.selectionModel().selection()

        if not selected.indexes():
            self.ui.textEdit.setEnabled(False)
            self.ui.soundEdit.setEnabled(False)
            return

        self.ui.textEdit.setEnabled(True)
        self.ui.soundEdit.setEnabled(True)

        proxyIndex = selected.indexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)
        item: QStandardItem | None = self.model.itemFromIndex(sourceIndex)

        text: str = item.text()
        sound: str = self.model.item(sourceIndex.row(), 1).text()

        self.ui.textEdit.setPlainText(text)
        self.ui.soundEdit.setText(sound)

    def updateEntry(self):
        proxyIndex = self.ui.talkTable.selectedIndexes()[0]
        sourceIndex = self.proxyModel.mapToSource(proxyIndex)

        self.model.item(sourceIndex.row(), 0).setText(self.ui.textEdit.toPlainText())
        self.model.item(sourceIndex.row(), 1).setText(self.ui.soundEdit.text())


class LoaderDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        fileData: bytes,
        model: QStandardItemModel,
    ):
        """Initializes the loading dialog.

        Args:
        ----
            parent: {The parent widget of the dialog}
            fileData: {The data to load}
            model: {The model to populate}.

        Processing Logic:
        ----------------
            - Creates a progress bar to display loading progress
            - Sets up the dialog layout and adds progress bar
            - Starts a worker thread to load the data in the background
            - Connects signals from worker to update progress bar.
        """
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMinimum(0)
        self._progressBar.setMaximum(0)
        self._progressBar.setTextVisible(False)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)

        self.setWindowTitle("Loading...")
        self.setFixedSize(200, 40)

        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self.model = QStandardItemModel()
        self.model.setColumnCount(2)

        self.worker = LoaderWorker(fileData, model)
        self.worker.entryCount.connect(self.onEntryCount)
        self.worker.batch.connect(self.onBatch)
        self.worker.loaded.connect(self.onLoaded)
        self.worker.language.connect(self.setupLanguage)
        self.worker.start()

    def onEntryCount(
        self,
        count: int,
    ):
        self._progressBar.setMaximum(count)

    def onBatch(
        self,
        batch: list[QStandardItem],
    ):
        for row in batch:
            self.model.appendRow(row)
            index: int = self.model.rowCount() - 1
            self.model.setVerticalHeaderItem(index, QStandardItem(str(index)))
        self._progressBar.setValue(self.model.rowCount())

    def setupLanguage(
        self,
        language: Language,
    ):
        self.language = language

    def onLoaded(self):
        self.close()


class LoaderWorker(QThread):
    batch = QtCore.Signal(object)
    entryCount = QtCore.Signal(object)
    loaded = QtCore.Signal()
    language = QtCore.Signal(object)

    def __init__(self, fileData: bytes, model: QStandardItemModel):
        super().__init__()
        self._fileData: bytes = fileData
        self._model: QStandardItemModel = model

    def load_data(self):
        """Load tlk data from file."""
        tlk: TLK = read_tlk(self._fileData)
        self.entryCount.emit(len(tlk))
        self.language.emit(tlk.language)

        batch: list[list[QStandardItem]] = []
        for _stringref, entry in tlk:
            batch.append([QStandardItem(entry.text), QStandardItem(str(entry.voiceover))])
            large_amount = 200
            if len(batch) > large_amount:
                self.batch.emit(batch)
                batch = []
                sleep(0.001)
        self.batch.emit(batch)
        self.loaded.emit()

    def run(self):
        """Load tlk data from file in batches.

        Processing Logic:
        ----------------
            - Reads timeline data from file
            - Counts number of entries and emits count
            - Loops through entries and batches data into lists of 200
            - Emits batches and sleeps to allow UI to update
            - Emits final batch
            - Signals loading is complete.
        """
        self.load_data()
