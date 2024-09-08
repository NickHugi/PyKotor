from __future__ import annotations

import json
import multiprocessing

from contextlib import contextmanager
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Callable, Generator, NamedTuple

import qtpy

from loggerplus import RobustLogger, get_log_directory
from qtpy.QtCore import QSettings, QStringListModel, Qt
from qtpy.QtGui import QTextCursor
from qtpy.QtWidgets import (
    QCompleter,
    QDialog,
    QFileSystemModel,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QShortcut,
    QTabBar,
    QTextEdit,
    QToolTip,
    QTreeWidgetItem,
    QVBoxLayout,
)

if __name__ == "__main__":
    import sys

    from pathlib import Path

    def update_path(path: Path):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.append(path_str)

    here = Path(__file__).parent
    some_path = here.parent.parent.parent
    update_path(some_path)


from qtpy.QtWidgets import QWidget

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs.compiler.classes import FunctionDefinition, GlobalVariableDeclaration, StructDefinition
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.gui.common.widgets.code_editor import CodeEditor
from toolset.gui.common.widgets.syntax_highlighter import SyntaxHighlighter
from toolset.gui.dialogs.github_selector import GitHubFileSelector
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from toolset.utils.script import compileScript, decompileScript
from utility.error_handling import universal_simplify_exception
from utility.misc import is_debug_mode
from utility.system.path import Path, PurePath
from utility.updater.github import download_github_file

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QMouseEvent, QWheelEvent

    from pykotor.common.script import ScriptConstant, ScriptFunction
    from toolset.data.installation import HTInstallation


def download_script(
    url: str,
    local_path: str,
    script_relpath: str,
):
    """Downloads a file using `download_github_file` and updates the progress queue."""
    RobustLogger().debug(f"Downloading script @ {url}")
    RobustLogger().debug(f"Saving to {local_path}")
    download_github_file(url, local_path, script_relpath)


class NSSEditor(Editor):
    TAB_SIZE: int = 4
    TAB_AS_SPACE: bool = True

    def __init__(
        self,
        parent: QWidget | None = None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the script editor window.

        Args:
        ----
            parent: QWidget | None: The parent widget
            installation: HTInstallation | None: The installation object
        """
        supported: list[ResourceType] = [ResourceType.NSS, ResourceType.NCS]
        super().__init__(parent, "Script Editor", "script", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._highlighter: SyntaxHighlighter = SyntaxHighlighter(self.ui.codeEdit.document(), self._installation)
        self._is_tsl: bool = installation.tsl if installation else False
        self.bookmarks: list[tuple[int, str]] = []
        self.functions: list[ScriptFunction] = []
        self.constants: list[ScriptConstant] = []
        self.library: dict[str, bytes] = {}

        self.owner: str = "KOTORCommunityPatches"
        self.repo: str = "Vanilla_KOTOR_Script_Source"
        self.sourcerepo_url: str = f"https://github.com/{self.owner}/{self.repo}"
        self.sourcerepo_forks_url: str = f"{self.sourcerepo_url}/forks"

        self._length: int = 0
        self._is_decompiled: bool = False
        self._global_settings: GlobalSettings = GlobalSettings()

        self._setupUI()
        self._update_game_specific_data()
        self._setup_file_explorer()
        self._setup_bookmarks()
        self._setup_stylesheets()

        self.new()

    def _setup_bookmarks(self):
        self.ui.bookmarkTree.setHeaderLabels(["Line", "Description"])
        self.ui.bookmarkTree.itemDoubleClicked.connect(self._goto_bookmark)
        self.ui.addBookmarkButton.clicked.connect(self.add_bookmark)
        self.ui.removeBookmarkButton.clicked.connect(self.delete_bookmark)
        self.load_bookmarks()

    def add_bookmark(self):
        cursor = self.ui.codeEdit.textCursor()
        line_number = cursor.blockNumber() + 1
        default_description = f"Bookmark at line {line_number}"

        item = QTreeWidgetItem(self.ui.bookmarkTree)  # pyright: ignore[reportCallIssue, reportArgumentType]
        item.setText(0, str(line_number))
        item.setText(1, default_description)
        item.setData(0, Qt.ItemDataRole.UserRole, line_number)

        self.ui.bookmarkTree.setCurrentItem(item)  # pyright: ignore[reportCallIssue, reportArgumentType]
        self.ui.bookmarkTree.editItem(item, 1)  # pyright: ignore[reportCallIssue, reportArgumentType]

        # Select the entire text in the editable field
        editor = self.ui.bookmarkTree.itemWidget(item, 1)  # pyright: ignore[reportCallIssue, reportArgumentType]
        if isinstance(editor, QLineEdit):
            editor.selectAll()

        self._save_bookmarks()

    def delete_bookmark(self):
        selected_items = self.ui.bookmarkTree.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            if item is None:
                    continue
            index = self.ui.bookmarkTree.indexOfTopLevelItem(item)  # pyright: ignore[reportCallIssue, reportArgumentType]
            self.ui.bookmarkTree.takeTopLevelItem(index)
        self._save_bookmarks()

    def _goto_bookmark(self, item: QTreeWidgetItem):
        line_number = item.data(0, Qt.ItemDataRole.UserRole)
        self._goto_line(line_number)

    def _goto_line(self, line_number: int):
        block = self.ui.codeEdit.document().findBlockByLineNumber(line_number - 1)
        cursor = QTextCursor(block)
        self.ui.codeEdit.setTextCursor(cursor)
        self.ui.codeEdit.centerCursor()

    def _save_bookmarks(self):
        bookmarks = []
        for i in range(self.ui.bookmarkTree.topLevelItemCount()):
            item = self.ui.bookmarkTree.topLevelItem(i)
            if item is None:
                continue
            bookmarks.append(
                {
                    "line": item.data(0, Qt.ItemDataRole.UserRole),
                    "description": item.text(1),
                }
            )
        settings = QSettings()
        settings.setValue("bookmarks", json.dumps(bookmarks))

    def load_bookmarks(self):
        settings = QSettings()
        bookmarks = json.loads(settings.value("bookmarks", "[]"))
        for bookmark in bookmarks:
            item = QTreeWidgetItem(self.ui.bookmarkTree)  # pyright: ignore[reportCallIssue, reportArgumentType]
            item.setText(0, str(bookmark["line"]))
            item.setText(1, bookmark["description"])
            item.setData(0, Qt.ItemDataRole.UserRole, bookmark["line"])

    def load_snippets(self):
        """TODO: snippet loading into the list widget, and then sending them to the code editor."""

    def _save_snippets(self):
        snippets = []
        for i in range(self.ui.snippetList.count()):
            item = self.ui.snippetList.item(i)  # pyright: ignore[reportCallIssue, reportArgumentType]
            snippets.append(
                {
                    "name": "" if item is None else item.text(),
                    "content": "" if item is None else item.data(Qt.ItemDataRole.UserRole),
                }
            )
        settings = QSettings()
        settings.setValue("snippets", json.dumps(snippets))

    def on_add_snippet(self):
        name, ok = QInputDialog.getText(self, "Add Snippet", "Enter snippet name:")
        if not ok:
            return
        content, ok = QInputDialog.getMultiLineText(self, "Add Snippet", "Enter snippet content:")
        if not ok:
            return
        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, content)
        self.ui.snippetList.addItem(item)  # pyright: ignore[reportCallIssue, reportArgumentType]
        self._save_snippets()

    def on_remove_snippet(self):
        current_item = self.ui.snippetList.currentItem()
        if not current_item:
            return
        self.ui.snippetList.takeItem(self.ui.snippetList.row(current_item))  # pyright: ignore[reportCallIssue, reportArgumentType]
        self._save_snippets()

    def insert_snippet(self, item: QListWidgetItem):
        content = item.data(Qt.ItemDataRole.UserRole)
        cursor = self.ui.codeEdit.textCursor()
        cursor.insertText(content)
        self._save_snippets()

    def _setup_stylesheets(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: palette(window);
                color: palette(windowText);
            }
            QeditorTabs::pane {
                border: none;
                background-color: palette(base);
            }
            QTabBar::tab {
                background-color: palette(dark);
                color: palette(text);
                padding: 8px 12px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: palette(base);
                color: palette(text);
            }
            QTreeView {
                background-color: palette(base);
                color: palette(text);
                border: none;
            }
            QTreeView::item {
                padding: 4px;
            }
            QTreeView::item:selected {
                background-color: palette(highlight);
                color: palette(highlightedText);
            }
            QLineEdit, QTextEdit {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid palette(mid);
                padding: 2px;
            }
            QPushButton {
                background-color: palette(button);
                color: palette(buttonText);
                border: 1px solid palette(mid);
                padding: 4px 8px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QScrollBar:vertical {
                border: none;
                background-color: palette(base);
                width: 14px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background-color: palette(mid);
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _setupUI(self):
        # Snippets
        self.ui.snippetList.itemDoubleClicked.connect(self.insert_snippet)
        self.ui.snippetAddButton.clicked.connect(self.on_add_snippet)
        self.ui.snippetDelButton.clicked.connect(self.on_remove_snippet)
        self.ui.snippetReloadButton.clicked.connect(self.load_snippets)
        self.load_snippets()

        # Bookmarks
        self.ui.bookmarkTree.setHeaderLabels(["Line", "Description"])
        self.ui.bookmarkTree.itemDoubleClicked.connect(self._goto_bookmark)
        self.ui.addBookmarkButton.clicked.connect(self.add_bookmark)
        self.ui.removeBookmarkButton.clicked.connect(self.delete_bookmark)
        self.load_bookmarks()

        # Connect signals for the outline view
        self.ui.outlineView.itemClicked.connect(self.ui.codeEdit.on_outline_item_clicked)
        self.ui.outlineView.itemDoubleClicked.connect(self.ui.codeEdit.on_outline_item_double_clicked)

        # Style the outline view
        self.ui.outlineView.setStyleSheet("""
            QTreeWidget {
                background-color: palette(base);
                color: palette(text);
                border: none;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: palette(highlight);
                color: palette(highlightedText);
            }
        """)

        self.ui.searchBar.setPlaceholderText("Search...")
        self.ui.searchBar.returnPressed.connect(self.ui.codeEdit.search)
        self.ui.codeEdit.textChanged.connect(self.ui.codeEdit.on_text_changed)
        self.ui.codeEdit.textChanged.connect(self._update_outline)
        if self._is_tsl:
            self.ui.actionK1.setChecked(False)  # pyright: ignore[reportCallIssue,reportArgumentType]
            self.ui.actionTSL.setChecked(True)  # pyright: ignore[reportCallIssue,reportArgumentType]
        else:
            self.ui.actionK1.setChecked(True)  # pyright: ignore[reportCallIssue,reportArgumentType]
            self.ui.actionTSL.setChecked(False)  # pyright: ignore[reportCallIssue,reportArgumentType]
        self.ui.actionK1.triggered.connect(self._on_game_changed)
        self.ui.actionTSL.triggered.connect(self._on_game_changed)

        self.completer: QCompleter = QCompleter(self)
        self.completer.setWidget(self.ui.codeEdit)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.ui.codeEdit.setMouseTracking(True)
        self.ui.codeEdit.mouseMoveEvent = self._show_hover_documentation
        self.ui.codeEdit.textChanged.connect(self._update_outline)

        # Add output tab
        self.outputTab: QWidget = QWidget()
        self.ui.editorTabs.addTab(self.ui.outputTab, "Output")  # pyright: ignore[reportCallIssue, reportArgumentType]
        self.outputTextEdit: QTextEdit = QTextEdit(self.ui.outputTab)  # pyright: ignore[reportCallIssue, reportArgumentType]
        self.outputTextEdit.setReadOnly(True)
        self.outputLayout: QVBoxLayout = QVBoxLayout(self.ui.outputTab)  # pyright: ignore[reportCallIssue, reportArgumentType]
        self.outputLayout.addWidget(self.outputTextEdit)

        # Add error badge
        self.errorBadge: QLabel = QLabel(self)
        self.errorBadge.setStyleSheet("""
            background-color: red;
            color: white;
            border-radius: 10px;
            padding: 2px;
        """)
        self.errorBadge.hide()

    def _setup_error_reporting(self):
        self.error_count: int = 0
        tab_bar: QTabBar = self.ui.editorTabs.tabBar()  # pyright: ignore[reportCallIssue, reportAssignmentType]
        if tab_bar is None:
            return
        tab_bar.setTabButton(
            self.ui.editorTabs.indexOf(self.ui.outputTab),  # pyright: ignore[reportCallIssue, reportArgumentType]
            QTabBar.ButtonPosition.RightSide,  # pyright: ignore[reportCallIssue, reportArgumentType]
            QLabel() if self.errorBadge is None else self.errorBadge  # pyright: ignore[reportCallIssue, reportArgumentType]
        )

    def report_error(self, error_message: str):
        self.error_count += 1
        self.errorBadge.setText(str(self.error_count))
        self.errorBadge.show()
        self.outputTextEdit.append(f"Error: {error_message}")
        self.ui.editorTabs.setCurrentWidget(self.ui.outputTab)  # pyright: ignore[reportCallIssue, reportArgumentType]

    def clear_errors(self):
        self.error_count = 0
        self.errorBadge.hide()
        self.outputTextEdit.clear()

    def _on_game_changed(self, index: int):
        self._is_tsl = index == 1
        self._update_game_specific_data()

    def _update_game_specific_data(self):
        # Update constants and functions based on the selected game
        # DO NOT TAKE THESE OUT OF A TYPE CHECKING BLOCK!!! These are so large they straight up crashed my IDE.
        if not TYPE_CHECKING:
            from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_CONSTANTS, TSL_FUNCTIONS
            from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY
            self.constants[:] = sorted(TSL_CONSTANTS if self._is_tsl else KOTOR_CONSTANTS, key=attrgetter("name"))
            self.functions[:] = sorted(TSL_FUNCTIONS if self._is_tsl else KOTOR_FUNCTIONS, key=attrgetter("name"))
            self.library = (TSL_LIBRARY if self._is_tsl else KOTOR_LIBRARY).copy()

        # Clear and repopulate the function and constant lists
        has_error: bool = False
        try:
            self.ui.functionList.clear()
        except RuntimeError:  # wrapped C/C++ object of type 'QListWidget' has been deleted
            RobustLogger().warning("Failed to clear function list", exc_info=True)
            has_error = True
        try:
            self.ui.constantList.clear()
        except RuntimeError:  # wrapped C/C++ object of type 'QListWidget' has been deleted
            RobustLogger().warning("Failed to clear constant list", exc_info=True)
            has_error = True

        for function in self.functions:
            item = QListWidgetItem(function.name)
            item.setData(Qt.ItemDataRole.UserRole, function)
            try:
                self.ui.functionList.addItem(item)  # pyright: ignore[reportCallIssue, reportArgumentType]
            except RuntimeError:  # wrapped C/C++ object of type 'QListWidget' has been deleted
                RobustLogger().warning("Failed to add function to list", exc_info=True)
                has_error = True

        for constant in self.constants:
            item = QListWidgetItem(constant.name)
            item.setData(Qt.ItemDataRole.UserRole, constant)
            try:
                self.ui.constantList.addItem(item)  # pyright: ignore[reportCallIssue, reportArgumentType]
            except RuntimeError:  # wrapped C/C++ object of type 'QListWidget' has been deleted
                RobustLogger().warning("Failed to add constant to list", exc_info=True)
                has_error = True

        if has_error:
            QMessageBox(QMessageBox.Icon.Critical, "Failed to update lists", "Failed to update the function or constant lists.").exec_()

        self._update_completer_model(self.constants, self.functions)
        self._highlighter.update_rules(is_tsl=self._is_tsl)

    def _setupSignals(self):
        """Sets up signals and slots for the GUI.

        Args:
        ----
            self: The class instance.
        """
        self.ui.actionCompile.triggered.connect(self.compile_current_script)
        self.ui.constantList.doubleClicked.connect(self.insert_selected_constant)
        self.ui.functionList.doubleClicked.connect(self.insert_selected_function)
        self.ui.functionSearchEdit.textChanged.connect(self.on_function_search)
        self.ui.constantSearchEdit.textChanged.connect(self.on_constant_search)
        self.ui.codeEdit.textChanged.connect(self.ui.codeEdit.on_text_changed)
        self.ui.codeEdit.customContextMenuRequested.connect(self.ui.codeEdit.show_context_menu)

    def _setup_file_explorer(self):
        self.file_system_model: QFileSystemModel = QFileSystemModel()
        self.file_system_model.setRootPath("")
        self.ui.fileExplorerView.setModel(self.file_system_model)
        self.ui.fileExplorerView.setRootIndex(self.file_system_model.index(""))
        self.ui.fileExplorerView.hideColumn(1)  # Hide size column
        self.ui.fileExplorerView.hideColumn(2)  # Hide type column
        self.ui.fileExplorerView.hideColumn(3)  # Hide date modified column

    def _update_completer_model(self, constants: list[ScriptConstant], functions: list[ScriptFunction]):
        completer_list: list[str] = [*(const.name for const in constants), *(func.name for func in functions)]
        model = QStringListModel(completer_list)
        self.completer.setModel(model)

    def _show_hover_documentation(self, e: QMouseEvent):
        cursor = self.ui.codeEdit.cursorForPosition(e.pos())
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()

        if word:
            doc = self._get_documentation(word)
            if doc:
                global_pos = self.ui.codeEdit.mapToGlobal(e.pos())
                QToolTip.showText(global_pos, doc)
            else:
                QToolTip.hideText()
        else:
            QToolTip.hideText()

        # Call the original mouseMoveEvent
        super(CodeEditor, self.ui.codeEdit).mouseMoveEvent(e)

    def _get_documentation(self, word: str) -> str | None:
        """Get the documentation for a word."""
        for func in self.functions:
            if func.name == word:
                return f"{func.name}\n\n{func.description}"

        for const in self.constants:
            if const.name == word:
                return f"{const.name} = {const.value}"

        return None

    class SavedContext(NamedTuple):
        """A context that can be saved and restored by _snapshotResTypeContext."""
        filepath: Path
        resname: str
        restype: ResourceType
        revert: bytes
        saved_connection: Any  # Specify the actual type here instead of 'any' if possible

    @contextmanager
    def _snapshot_restype_context(
        self,
        saved_file_callback: Callable | None = None,
    ) -> Generator[SavedContext, Any, None]:
        """Snapshots the current _restype and associated state, to restore after a with statement.

        This saves the current _filepath, _resname and _revert data in a context object and restores it when done.
        If saved_file_callback is not None, it will be connected to the savedFile slot during the with statement.
        If a file is successfully saved during that time it will be called with these arguments before the context
        manager restores the original state: (filepath: str, resname: str, restype: ResourceType, data: bytes)

        Usage:

            # self._restype is NSS
            with self._snapshotResTypeContext():
                # Do something that might change self._restype to NCS.
                self.saveAs()
            # after the with statement, self._restype is returned to NSS.
        """
        if saved_file_callback:
            saved_connection = self.savedFile.connect(saved_file_callback)
        else:
            saved_connection = None
        context = NSSEditor.SavedContext(
            self._filepath,
            self._resname,
            self._restype,
            self._revert,
            saved_connection,
        )
        try:
            yield context
        finally:
            if context.saved_connection:
                self.disconnect(context.saved_connection)
            # If _restype changed, unwind all the changes that may have been made.
            if self._restype != context.restype:
                self._filepath = context.filepath
                self._resname = context.resname
                self._restype = context.restype
                self._revert = context.revert
                self.refresh_window_title()

    def determine_script_path(self, resref: str) -> str:
        script_filename = f"{resref}.nss"
        script_filename = script_filename.lower()
        dialog = GitHubFileSelector(self.owner, self.repo, selectedFiles=[script_filename], parent=self)
        if dialog.exec_() != QDialog.Accepted:
            raise ValueError("No script selected.")

        selected_path = dialog.getSelectedPath()
        if not selected_path:
            raise ValueError("No script selected.")
        result = selected_path
        print(f"User selected script path: {result}")
        return result

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)
        self._is_decompiled = False

        if restype is ResourceType.NSS:
            self.ui.codeEdit.setPlainText(data.decode("windows-1252", errors="ignore"))
        elif restype is ResourceType.NCS:
            error_occurred = False
            try:
                self._handle_user_ncs(data, resref)
            except ValueError as e:
                error_occurred = self._handle_exc_debug_mode("Decompilation/Download Failed", e)
            except NoConfigurationSetError as e:
                error_occurred = self._handle_exc_debug_mode("Filepath is not set", e)
            finally:
                if error_occurred:
                    self.new()

    def _handle_exc_debug_mode(self, err_msg: str, e: Exception) -> bool:
        QMessageBox(QMessageBox.Icon.Critical, err_msg, str(universal_simplify_exception(e))).exec_()
        if is_debug_mode():
            raise e
        result = True
        return result

    def _handle_user_ncs(self, data: bytes, resname: str) -> None:
        box = QMessageBox(
            QMessageBox.Icon.Question,
            "Decompile or Download",
            f"Would you like to decompile this script, or download it from <a href='{self.sourcerepo_url}'>Vanilla Source Repository</a>?",
            buttons=QMessageBox.Yes | QMessageBox.Ok | QMessageBox.Cancel,
        )
        box.setDefaultButton(QMessageBox.Cancel)
        box.button(QMessageBox.Yes).setText("Decompile")
        box.button(QMessageBox.Ok).setText("Download")
        choice = box.exec_()
        print(f"User chose '{choice}' in the decompile/download messagebox.")

        if choice == QMessageBox.Yes:
            assert self._installation is not None, "Installation not set, cannot determine path"
            source = decompileScript(data, self._installation.path(), tsl=self._installation.tsl)
        elif choice == QMessageBox.Ok:
            source = self._download_and_load_remote_script(resname)
        else:
            return
        self.ui.codeEdit.setPlainText(source)
        self._is_decompiled = True

    def _download_and_load_remote_script(self, resref: str) -> str:
        script_path: str = self.determine_script_path(resref)
        local_path = CaseAwarePath(get_log_directory(self._global_settings.extractPath), PurePath(script_path).name)
        print(f"Local path: {local_path}")

        download_process = multiprocessing.Process(target=download_script, args=(f"{self.owner}/{self.repo}", str(local_path), script_path))
        download_process.start()
        download_process.join()

        if not local_path.exists():
            raise ValueError(f"Failed to download the script: '{local_path}' did not exist after download completed.")  # noqa: TRY301

        result = BinaryReader.load_file(local_path).decode(encoding="windows-1252")

        return result

    def build(self) -> tuple[bytes | None, bytes]:
        if self._restype is not ResourceType.NCS:
            return self.ui.codeEdit.toPlainText().encode("windows-1252"), b""

        self._logger.debug(f"Compiling script '{self._resname}.{self._restype.extension}' from the NSSEditor...")
        assert self._installation is not None, "Installation not set, cannot determine path"
        compiled_bytes: bytes | None = compileScript(self.ui.codeEdit.toPlainText(), self._installation.path(), tsl=self._installation.tsl)
        if compiled_bytes is None:
            self._logger.debug(f"User cancelled the compilation of '{self._resname}.{self._restype.extension}'.")
            return None, b""
        return compiled_bytes, b""

    def new(self):
        super().new()

        self.ui.codeEdit.setPlainText("\n\nvoid main()\n{\n    \n}\n")

    def compile_current_script(self):
        # _compiledResourceSaved() will show a success message if the file is saved successfully.
        with self._snapshot_restype_context(self._compiled_resource_saved):
            try:
                self._restype = ResourceType.NCS
                filepath: Path = Path.cwd() / "untitled_script.ncs" if self._filepath is None else self._filepath
                if is_any_erf_type_file(filepath.name) or is_rim_file(filepath.name):
                    # Save the NCS resource into the given ERF/RIM.
                    # If this is not allowed save() will find a new path to save at.
                    self._filepath = filepath
                elif not filepath or is_bif_file(filepath.name):
                    assert self._installation is not None
                    self._filepath = self._installation.override_path() / f"{self._resname}.ncs"
                else:
                    self._filepath = filepath.with_suffix(".ncs")

                # Save using the overridden filepath and resource type.
                self.save()
            except ValueError as e:
                QMessageBox(QMessageBox.Icon.Critical, "Failed to compile", str(universal_simplify_exception(e))).exec_()
            except OSError as e:
                QMessageBox(QMessageBox.Icon.Critical, "Failed to save file", str(universal_simplify_exception(e))).exec_()

    def _compiled_resource_saved(
        self,
        filepath: str,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Shows a messagebox after compileCurrentScript successfully saves an NCS resource."""
        savePath = Path(filepath)
        if is_any_erf_type_file(savePath.name) or is_rim_file(savePath.name):
            # Format as /full/path/to/file.mod/resname.ncs
            savePath = savePath / f"{resname}.ncs"
        QMessageBox(
            QMessageBox.Icon.Information,
            "Success",
            f"Compiled script successfully saved to:\n {savePath}.",
        ).exec_()

    def show_auto_complete_menu(self):
        """Show the auto-complete menu."""
        self.completer.setCompletionPrefix(self.ui.codeEdit.textUnderCursor())
        if self.completer.completionCount() > 0:
            rect = self.ui.codeEdit.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)

    def insert_selected_constant(self):
        if self.ui.constantList.selectedItems():
            constant: ScriptConstant = self.ui.constantList.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
            insert = f"{constant.name} = {constant.value}"
            self.ui.codeEdit.insert_text_at_cursor(insert)

    def insert_selected_function(self):
        if self.ui.functionList.selectedItems():
            function: ScriptFunction = self.ui.functionList.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
            insert = f"{function.name}()"
            self.ui.codeEdit.insert_text_at_cursor(insert, insert.index("(") + 1)

    def on_insert_shortcut(self):
        if self.ui.editorTabs.currentIndex() == 0:
            self.insert_selected_function()
        elif self.ui.editorTabs.currentIndex() == 1:
            self.insert_selected_constant()

    def on_function_search(self):
        string = self.ui.functionSearchEdit.text()
        if not string:
            return
        lower_string = string.lower()
        for i in range(self.ui.functionList.count()):
            item = self.ui.functionList.item(i)
            if not item:
                continue
            item.setHidden(lower_string not in item.text().lower())

    def on_constant_search(self):
        string = self.ui.constantSearchEdit.text()
        if not string:
            return
        lower_string = string.lower()
        for i in range(self.ui.constantList.count()):
            item = self.ui.constantList.item(i)
            if not item:
                continue
            item.setHidden(lower_string not in item.text().lower())

    def _update_outline(self):
        self.ui.outlineView.clear()
        text = self.ui.codeEdit.toPlainText()

        lexer = NssLexer()
        parser = NssParser(
            functions=self.functions,
            constants=self.constants,
            library=self.library,
            library_lookup=None if self._filepath is None else self._filepath.parent,
            errorlog=None,
            #            debug=is_debug_mode(),
        )

        try:
            ast = parser.parser.parse(text, lexer=lexer.lexer)
            self._populate_outline(ast)
        except Exception:
            self._logger.exception(f"Failed to update outline for text '{text}'")

    def _populate_outline(self, ast):
        for obj in ast.objects:
            if isinstance(obj, FunctionDefinition):
                item = QTreeWidgetItem(self.ui.outlineView)  # pyright: ignore[reportCallIssue, reportArgumentType]
                item.setText(0, f"Function: {obj.signature.identifier}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)

                for param in obj.signature.parameters:
                    param_item = QTreeWidgetItem(item)
                    param_item.setText(0, f"Param: {param.identifier}")

            elif isinstance(obj, StructDefinition):
                item = QTreeWidgetItem(self.ui.outlineView)  # pyright: ignore[reportCallIssue, reportArgumentType]
                item.setText(0, f"Struct: {obj.identifier}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)

                for member in obj.members:
                    member_item = QTreeWidgetItem(item)
                    member_item.setText(0, f"Member: {member.identifier}")

            elif isinstance(obj, GlobalVariableDeclaration):
                item = QTreeWidgetItem(self.ui.outlineView)  # pyright: ignore[reportCallIssue, reportArgumentType]
                item.setText(0, f"Global: {obj.identifier}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)

    def _setup_shortcuts(self):
        QShortcut("Ctrl+F5", self).activated.connect(self.compile_current_script)
        QShortcut("Ctrl+I", self).activated.connect(self.on_insert_shortcut)
        QShortcut("Ctrl+Shift+I", self).activated.connect(self.insert_selected_constant)
        QShortcut("Ctrl+Shift+F", self).activated.connect(self.insert_selected_function)
        QShortcut("Ctrl+Shift+N", self).activated.connect(self.new)
        QShortcut("Ctrl+Shift+O", self).activated.connect(self.open)
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        QShortcut("Ctrl+Shift+S", self).activated.connect(self.saveAs)
        QShortcut("Ctrl+Shift+W", self).activated.connect(self.close)
        QShortcut("Ctrl+Shift+Z", self).activated.connect(self.ui.codeEdit.undo)  # QUndoCommand
        QShortcut("Ctrl+Y", self).activated.connect(self.ui.codeEdit.redo)  # QRedoCommand
        QShortcut("Ctrl+G", self).activated.connect(self.ui.codeEdit.go_to_line)
        QShortcut("Ctrl+F", self).activated.connect(self.ui.codeEdit.find)  # QTextDocument.find

        # Should show how many matches there are. If the user is not already at the line, the replacement should not happen until the jump first happens.
        QShortcut("Ctrl+H", self).activated.connect(self.ui.codeEdit.replace)

        QShortcut("Ctrl+D", self).activated.connect(self.ui.codeEdit.duplicate_line)  # Duplicate line
        QShortcut("Ctrl+Scroll Up/Down", self).activated.connect(self.ui.codeEdit.change_text_size)  # Change text size
        QShortcut("Shift+Scroll Up/Down", self).activated.connect(self.ui.codeEdit.scroll_horizontally)  # Scroll horizontally
        QShortcut("Ctrl+Shift+Up/Down", self).activated.connect(self.ui.codeEdit.move_line_up_or_down)  # Move line up or down
        QShortcut("Ctrl+Space", self).activated.connect(self.show_auto_complete_menu)  # Show auto-complete menu
        QShortcut("Ctrl+/", self).activated.connect(self.ui.codeEdit.toggle_comment)  # Toggle comment

        # Add new shortcuts for bookmarks and snippets
        QShortcut("Ctrl+B", self).activated.connect(self.ui.codeEdit.add_bookmark)
        QShortcut("Ctrl+Shift+B", self).activated.connect(lambda: self.ui.bookmarksDock.setVisible(not self.ui.bookmarksDock.isVisible()))
        QShortcut("Ctrl+K", self).activated.connect(lambda: self.ui.snippetsDock.setVisible(not self.ui.snippetsDock.isVisible()))

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.ui.codeEdit.change_text_size(increase=True)
            else:
                self.ui.codeEdit.change_text_size(increase=False)
        else:
            super().wheelEvent(event)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    editor = NSSEditor()
    editor.show()
    sys.exit(app.exec())
