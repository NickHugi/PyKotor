#!/usr/bin/env python3
from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING, Callable

from qtpy.QtCore import (
    QModelIndex,
    QSortFilterProxyModel,
    QThread,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QDialog,
    QMenu,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
)

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.extract.file import FileResource
from pykotor.resource.formats.tlk import TLK, TLKEntry, bytes_tlk, read_tlk, write_tlk
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.search import FileResults
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import add_window, open_resource_editor
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import (
        QAbstractItemModel,
        QItemSelection,
        QItemSelectionModel,  # pyright: ignore[reportPrivateImportUsage]
        QModelIndex,
        QPoint,
    )
    from qtpy.QtGui import QKeyEvent
    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class TLKEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.TLK, ResourceType.TLK_XML, ResourceType.TLK_JSON]
        super().__init__(parent, "TLK Editor", "none", supported, supported, installation)

        from toolset.uic.qtpy.editors.tlk import Ui_MainWindow

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()

        self.ui.searchBox.setVisible(False)
        self.ui.jumpBox.setVisible(False)

        self.language: Language = Language.ENGLISH

        self.source_model: QStandardItemModel = QStandardItemModel(self)
        self.proxy_model: QSortFilterProxyModel = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.talkTable.setModel(self.proxy_model)

        # Make the bottom panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()
        self.show()

    def _setup_signals(self):
        def _on_jump_spinbox_goto(*args, **kwargs):
            table_view: RobustTableView = self.ui.talkTable
            assert isinstance(table_view, RobustTableView)
            proxy_table_model: QAbstractItemModel | None = table_view.model()
            assert isinstance(proxy_table_model, QSortFilterProxyModel)
            proxy_index: QModelIndex = proxy_table_model.index(self.ui.jumpSpinbox.value(), 0)
            self.ui.talkTable.scrollTo(proxy_index)
            self.ui.talkTable.setCurrentIndex(proxy_index)

        def _on_search_button_clicked(*args, **kwargs):
            self.do_filter(self.ui.searchEdit.text())

        self.ui.actionGoTo.triggered.connect(self.toggle_goto_box)
        self.ui.actionGoTo.setShortcut("Ctrl+G")
        self.ui.jumpButton.clicked.connect(_on_jump_spinbox_goto)

        orig_key_press_event: Callable[[QKeyEvent], None] = self.ui.jumpSpinbox.keyPressEvent

        def keyPressEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
            event: QKeyEvent,
        ):
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                _on_jump_spinbox_goto()
            orig_key_press_event(event)

        self.ui.jumpSpinbox.keyPressEvent = keyPressEvent  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.jumpSpinbox.valueChanged.connect(_on_jump_spinbox_goto)
        self.ui.actionFind.triggered.connect(self.toggle_filter_box)
        self.ui.actionFind.setShortcut("Ctrl+F")
        self.ui.searchButton.clicked.connect(_on_search_button_clicked)
        self.ui.actionInsert.triggered.connect(self.insert)
        self.ui.actionInsert.setShortcut("Ctrl+I")
        # self.ui.actionDelete.triggered.connect(self.delete)
        # self.ui.actionDelete.setShortcut("Ctrl+D")

        self.ui.talkTable.clicked.connect(self.selection_changed)
        self.ui.textEdit.textChanged.connect(self.update_entry)
        self.ui.soundEdit.textChanged.connect(self.update_entry)
        self.ui.talkTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.talkTable.customContextMenuRequested.connect(self.on_context_menu)

        self.populate_language_menu()

    def populate_language_menu(self):
        self.ui.menuLanguage.clear()

        # Separator
        self.ui.menuLanguage.addSeparator()

        # Add languages from the enum
        for language in Language:
            action = QAction(language.name.replace("_", " "), self)
            action.triggered.connect(lambda _checked=None, lang=language: self.on_language_selected(lang))
            self.ui.menuLanguage.addAction(action)

    def on_language_selected(
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
        self.source_model: QStandardItemModel = dialog.source_model
        self.proxy_model: QSortFilterProxyModel = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.talkTable.setModel(self.proxy_model)
        sel_model: QItemSelectionModel | None = self.ui.talkTable.selectionModel()
        assert sel_model is not None
        sel_model.selectionChanged.connect(self.selection_changed)
        self.ui.jumpSpinbox.setMaximum(self.source_model.rowCount())

    def on_context_menu(
        self,
        position: QPoint,
    ):
        index: QModelIndex = self.ui.talkTable.indexAt(position)
        menu = QMenu()
        findAction = QAction("Find LocalizedString references", self)
        findAction.triggered.connect(lambda: self.find_references(index))
        menu.addAction(findAction)
        viewport: QWidget | None = self.ui.talkTable.viewport()
        assert viewport is not None
        menu.exec(viewport.mapToGlobal(position))

    def find_references(
        self,
        index: QModelIndex,
    ):
        # Implement the logic to find references based on the provided index
        stringref: int = index.row()
        print(f"Finding references to stringref: {stringref}")
        from pykotor.tools.reference_cache import find_tlk_entry_references  # noqa: PLC0415

        assert self._installation is not None

        def search_fn() -> set[FileResource]:
            assert self._installation is not None
            return find_tlk_entry_references(self._installation, stringref)

        loader = AsyncLoader(
            self,
            f"Looking for stringref '{stringref}' in {self._installation.path()}...",
            search_fn,
            error_title="An unexpected error occurred searching the installation.",
            start_immediately=False,
        )
        loader.setModal(False)
        loader.show()

        def handle_search_completed(
            results_list: list[FileResource] | set[FileResource],
        ):
            if not results_list:
                QMessageBox(
                    QMessageBox.Icon.Information,
                    "No resources found",
                    f"There are no GFFs that reference this tlk entry (stringref {stringref})",
                    parent=self,
                ).exec()
                return
            assert self._installation is not None
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
        _filepath, _editor = open_resource_editor(
            selection.filepath(),
            selection.resname(),
            selection.restype(),
            selection.data(),
            self._installation,
            self,
            gff_specialized=GlobalSettings().gffSpecializedEditors,
        )

    def new(self):
        super().new()

        self.source_model.clear()  # sourcery skip: class-extract-method
        self.source_model.setColumnCount(2)
        self.ui.talkTable.hideColumn(1)
        self.ui.textEdit.setEnabled(False)
        self.ui.soundEdit.setEnabled(False)

    def build(self) -> tuple[bytes | bytearray, bytes]:
        tlk = TLK()
        tlk.language = self.language

        for i in range(self.source_model.rowCount()):
            col_zero_cell: QStandardItem | None = self.source_model.item(i, 0)
            col_one_cell: QStandardItem | None = self.source_model.item(i, 1)
            if col_zero_cell is None or col_one_cell is None:
                continue
            text: str = col_zero_cell.text()
            sound: ResRef = ResRef(col_one_cell.text())
            tlk.entries.append(TLKEntry(text, sound))

        data = bytearray()
        write_tlk(tlk, data, self._restype or ResourceType.TLK)
        return data, b""

    def insert(self):
        self.source_model.appendRow([QStandardItem(""), QStandardItem("")])

    def do_filter(
        self,
        text: str,
    ):
        self.proxy_model.setFilterFixedString(text)

    def toggle_filter_box(self):
        is_visible: bool = self.ui.searchBox.isVisible()
        self.ui.searchBox.setVisible(not is_visible)
        if not is_visible:  # If the jump box was not visible before and now is
            self.ui.searchEdit.setFocus()  # Activate the spinbox for immediate typing
            self.ui.searchEdit.selectAll()

    def toggle_goto_box(self):
        is_visible: bool = self.ui.jumpBox.isVisible()
        self.ui.jumpBox.setVisible(not is_visible)
        if not is_visible:  # If the jump box was not visible before and now is
            self.ui.jumpSpinbox.setFocus()  # Activate the spinbox for immediate typing
            self.ui.jumpSpinbox.selectAll()

    def selection_changed(self):
        sel_model: QItemSelectionModel | None = self.ui.talkTable.selectionModel()
        if sel_model is None:
            return
        selected: QItemSelection | None = sel_model.selection()

        if selected is None or not selected.indexes():
            self.ui.textEdit.setEnabled(False)
            self.ui.soundEdit.setEnabled(False)
            return

        self.ui.textEdit.setEnabled(True)
        self.ui.soundEdit.setEnabled(True)

        proxy_index: QModelIndex = selected.indexes()[0]
        source_index: QModelIndex = self.proxy_model.mapToSource(proxy_index)
        item: QStandardItem | None = self.source_model.itemFromIndex(source_index)
        if item is None:
            return
        text: str = item.text()
        col_one_cell: QStandardItem | None = self.source_model.item(source_index.row(), 1)
        if col_one_cell is None:
            return
        sound: str = col_one_cell.text()

        self.ui.textEdit.setPlainText(text)
        self.ui.soundEdit.setText(sound)

    def update_entry(self):
        proxy_index: QModelIndex = self.ui.talkTable.selectedIndexes()[0]
        source_index: QModelIndex = self.proxy_model.mapToSource(proxy_index)

        col_zero_cell: QStandardItem | None = self.source_model.item(source_index.row(), 0)
        if col_zero_cell is None:
            return
        col_zero_cell.setText(self.ui.textEdit.toPlainText())

        col_one_cell: QStandardItem | None = self.source_model.item(source_index.row(), 1)
        if col_one_cell is None:
            return
        col_one_cell.setText(self.ui.soundEdit.text())


class LoaderDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        file_data: bytes,
        model: QStandardItemModel,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint & ~Qt.WindowType.WindowContextHelpButtonHint & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        self._progress_bar: QProgressBar = QProgressBar(self)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)
        self._progress_bar.setTextVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self._progress_bar)
        self.setLayout(layout)

        self.setWindowTitle("Loading...")
        self.setFixedSize(200, 40)

        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self.source_model: QStandardItemModel = QStandardItemModel()
        self.source_model.setColumnCount(2)

        self.worker: LoaderWorker = LoaderWorker(file_data, model)
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
        self.language: Language = language

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
        self.load_data()
