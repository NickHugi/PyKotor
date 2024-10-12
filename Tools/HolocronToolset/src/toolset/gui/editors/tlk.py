#!/usr/bin/env python3
from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from qtpy.QtCore import (
    QSortFilterProxyModel,
    QThread,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
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
from toolset.utils.window import add_window, open_resource_editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QModelIndex
    from qtpy.QtGui import QKeyEvent
    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal

    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class EnterSpinBox(QSpinBox):
    sig_enter_key_pressed: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]

    def keyPressEvent(self, event: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.sig_enter_key_pressed.emit()
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

        from toolset.uic.qtpy.editors.tlk import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()

        self.ui.searchBox.setVisible(False)
        self.ui.jumpBox.setVisible(False)

        self.language: Language = Language.ENGLISH

        self.source_model = QStandardItemModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.talkTable.setModel(self.proxy_model)

        # Make the bottom panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setup_signals(self):
        """Set up signal connections for UI actions and widgets.

        Processing Logic:
        ----------------
            - Connect action triggers to slot functions
            - Connect button clicks to slot functions
            - Connect table and text edits to update functions
            - Set up keyboard shortcuts to trigger actions.
        """
        self.ui.actionGoTo.triggered.connect(self.toggle_goto_box)
        self.ui.jumpButton.clicked.connect(lambda: self.goto_line(self.ui.jumpSpinbox.value()))
        #self.ui.jumpSpinbox.editingFinished.connect(lambda: self.goto_line(self.ui.jumpSpinbox.value()))
        self.ui.jumpSpinbox.__class__ = EnterSpinBox
        assert isinstance(self.ui.jumpSpinbox, EnterSpinBox)
        self.ui.jumpSpinbox.sig_enter_key_pressed.connect(lambda: self.goto_line(self.ui.jumpSpinbox.value()))
        self.ui.actionFind.triggered.connect(self.toggle_filter_box)
        self.ui.searchButton.clicked.connect(lambda: self.do_filter(self.ui.searchEdit.text()))
        self.ui.actionInsert.triggered.connect(self.insert)
        # self.ui.actionAuto_detect_slower.triggered.connect()

        self.ui.talkTable.clicked.connect(self.selection_changed)
        self.ui.textEdit.textChanged.connect(self.updateEntry)
        self.ui.soundEdit.textChanged.connect(self.updateEntry)
        self.ui.talkTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.talkTable.customContextMenuRequested.connect(self.showContextMenu)

        self.populateLanguageMenu()

        QShortcut("Ctrl+F", self).activated.connect(self.toggle_filter_box)
        QShortcut("Ctrl+G", self).activated.connect(self.toggle_goto_box)
        QShortcut("Ctrl+I", self).activated.connect(self.insert)

    def populateLanguageMenu(self):
        self.ui.menuLanguage.clear()

        # Add 'Auto_Detect_slower' action first
        auto_detect_action = QAction("Auto_detect_slower", self)
        auto_detect_action.triggered.connect(lambda: self.onLanguageSelected("auto_detect"))
        self.ui.menuLanguage.addAction(auto_detect_action)

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
        self.source_model.clear()
        self.source_model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)
        dialog = LoaderDialog(self, bytes_tlk(tlk), self.source_model)
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
        self.source_model.clear()
        self.source_model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)
        dialog = LoaderDialog(self, data, self.source_model)
        self._init_model_dialog(dialog)

    def _init_model_dialog(
        self,
        dialog: LoaderDialog,
    ):
        dialog.exec()
        self.source_model = dialog.source_model
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.talkTable.setModel(self.proxy_model)
        self.ui.talkTable.selectionModel().selectionChanged.connect(self.selection_changed)
        self.ui.jumpSpinbox.setMaximum(self.source_model.rowCount())

    def showContextMenu(self, position):
        index = self.ui.talkTable.indexAt(position)
        if not index.isValid():
            return
        menu = QMenu()
        findAction = QAction("Find LocalizedString references", self)
        findAction.triggered.connect(lambda: self.findReferences(index))
        menu.addAction(findAction)
        menu.exec(self.ui.talkTable.viewport().mapToGlobal(position))

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
            error_title="An unexpected error occurred searching the installation.",
            start_immediately=False,
        )
        loader.setModal(False)
        loader.show()
        def handle_search_completed(results_list: list[FileResource] | set[FileResource]):
            if not results_list:
                QMessageBox(
                    QMessageBox.Icon.Information,
                    "No resources found",
                    f"There are no GFFs that reference this tlk entry (stringref {stringref})",
                    parent=self,
                ).exec()
                return
            results_dialog = FileResults(self, results_list, self._installation)
            results_dialog.show()
            results_dialog.activateWindow()
            results_dialog.setWindowTitle(f"{len(results_list)} results for stringref '{stringref}' in {self._installation.path()}")
            add_window(results_dialog)
            results_dialog.sig_searchresults_selected.connect(self.handle_results_selection)

        loader.optional_finish_hook.connect(handle_search_completed)
        loader.start_worker()
        add_window(loader)

    def handle_results_selection(
        self,
        selection: FileResource,
    ):
        # Open relevant tab then select resource in the tree
        filepath, editor = open_resource_editor(
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

        self.source_model.clear()  # sourcery skip: class-extract-method
        self.source_model.setColumnCount(2)
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

        for i in range(self.source_model.rowCount()):
            text = self.source_model.item(i, 0).text()
            sound = ResRef(self.source_model.item(i, 1).text())
            tlk.entries.append(TLKEntry(text, sound))

        data = bytearray()
        write_tlk(tlk, data, self._restype or ResourceType.TLK)
        return data, b""

    def insert(self):
        self.source_model.appendRow([QStandardItem(""), QStandardItem("")])

    def do_filter(self, text: str):
        self.proxy_model.setFilterFixedString(text)

    def toggle_filter_box(self):
        is_visible: bool = self.ui.searchBox.isVisible()
        self.ui.searchBox.setVisible(not is_visible)
        if not is_visible:  # If the jump box was not visible before and now is
            self.ui.searchEdit.setFocus()  # Activate the spinbox for immediate typing
            self.ui.searchEdit.selectAll()

    def goto_line(self, line: int):
        index = self.source_model.index(line, 0)
        proxy_index: QModelIndex = self.proxy_model.mapFromSource(index)
        self.ui.talkTable.scrollTo(proxy_index)
        self.ui.talkTable.setCurrentIndex(proxy_index)

    def toggle_goto_box(self):
        is_visible: bool = self.ui.jumpBox.isVisible()
        self.ui.jumpBox.setVisible(not is_visible)
        if not is_visible:  # If the jump box was not visible before and now is
            self.ui.jumpSpinbox.setFocus()  # Activate the spinbox for immediate typing
            self.ui.jumpSpinbox.selectAll()

    def selection_changed(self):
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

        proxy_index = selected.indexes()[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        item: QStandardItem | None = self.source_model.itemFromIndex(source_index)

        text: str = item.text()
        sound: str = self.source_model.item(source_index.row(), 1).text()

        self.ui.textEdit.setPlainText(text)
        self.ui.soundEdit.setText(sound)

    def updateEntry(self):
        proxy_index = self.ui.talkTable.selectedIndexes()[0]
        source_index = self.proxy_model.mapToSource(proxy_index)

        self.source_model.item(source_index.row(), 0).setText(self.ui.textEdit.toPlainText())
        self.source_model.item(source_index.row(), 1).setText(self.ui.soundEdit.text())


class LoaderDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        file_data: bytes,
        model: QStandardItemModel,
    ):
        """Initializes the loading dialog.

        Args:
        ----
            parent: {The parent widget of the dialog}
            file_data: {The data to load}
            model: {The model to populate}.

        Processing Logic:
        ----------------
            - Creates a progress bar to display loading progress
            - Sets up the dialog layout and adds progress bar
            - Starts a worker thread to load the data in the background
            - Connects signals from worker to update progress bar.
        """
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)
        self._progress_bar.setTextVisible(False)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progress_bar)

        self.setWindowTitle("Loading...")
        self.setFixedSize(200, 40)

        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self.source_model: QStandardItemModel = QStandardItemModel()
        self.source_model.setColumnCount(2)

        self.worker = LoaderWorker(file_data, model)
        self.worker.entryCount.connect(self.on_entry_count)
        self.worker.batch.connect(self.on_batch)
        self.worker.loaded.connect(self.on_loaded)
        self.worker.language.connect(self.setup_language)
        self.worker.start()

    def on_entry_count(
        self,
        count: int,
    ):
        self._progress_bar.setMaximum(count)

    def on_batch(
        self,
        batch: list[QStandardItem],
    ):
        for row in batch:
            self.source_model.appendRow(row)
            index: int = self.source_model.rowCount() - 1
            self.source_model.setVerticalHeaderItem(index, QStandardItem(str(index)))
        self._progress_bar.setValue(self.source_model.rowCount())

    def setup_language(
        self,
        language: Language,
    ):
        self.language = language

    def on_loaded(self):
        self.close()


class LoaderWorker(QThread):
    batch: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    entryCount: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    loaded: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]
    language: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, file_data: bytes, model: QStandardItemModel):
        super().__init__()
        self._fileData: bytes = file_data
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
