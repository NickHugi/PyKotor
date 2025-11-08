from __future__ import annotations

import io
import json
import multiprocessing
import sys
import traceback

from contextlib import contextmanager
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Callable, Generator, NamedTuple
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generator, NamedTuple

from loggerplus import RobustLogger, get_log_directory
from qtpy.QtCore import QSettings, QStringListModel, Qt
from qtpy.QtGui import QKeySequence, QTextCursor
from qtpy.QtWidgets import (
    QCompleter,
    QDialog,
    QFileSystemModel,  # pyright: ignore[reportPrivateImportUsage]
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMenu,
    QMessageBox,  # pyright: ignore[reportPrivateImportUsage]
    QTabBar,
    QTextEdit,
    QToolTip,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

if __name__ == "__main__":
    import sys

    from pathlib import Path

    def update_path(path: Path):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.append(path_str)

    update_path(Path(__file__).parent.parent.parent.parent)


from pykotor.extract.file import FileResource  # pyright: ignore[reportPrivateImportUsage]
from pykotor.resource.formats.ncs.compiler.classes import FunctionDefinition, GlobalVariableDeclaration, StructDefinition  # pyright: ignore[reportPrivateImportUsage]
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer  # pyright: ignore[reportPrivateImportUsage]
from pykotor.resource.formats.ncs.compiler.parser import NssParser  # pyright: ignore[reportPrivateImportUsage]
from pykotor.resource.type import ResourceType  # pyright: ignore[reportPrivateImportUsage]
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_rim_file  # pyright: ignore[reportPrivateImportUsage]
from pykotor.tools.path import CaseAwarePath  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.code_editor import CodeEditor  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.syntax_highlighter import SyntaxHighlighter  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.dialogs.github_selector import GitHubFileSelector  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.editor import Editor  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError  # pyright: ignore[reportPrivateImportUsage]
from toolset.utils.script import ht_compile_script, ht_decompile_script  # pyright: ignore[reportPrivateImportUsage]
from toolset.utils.window import open_resource_editor  # pyright: ignore[reportPrivateImportUsage]
from utility.error_handling import universal_simplify_exception  # pyright: ignore[reportPrivateImportUsage]
from utility.misc import is_debug_mode  # pyright: ignore[reportPrivateImportUsage]
from utility.updater.github import download_github_file  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    import os

    from types import TracebackType

    from qtpy.QtCore import QPoint  # pyright: ignore[reportPrivateImportUsage, reportAttributeAccessIssue]
    from qtpy.QtGui import (
        QAction,  # pyright: ignore[reportPrivateImportUsage]
        QMouseEvent,
        QWheelEvent,
    )

    from pykotor.common.script import ScriptConstant, ScriptFunction  # pyright: ignore[reportPrivateImportUsage]
    from pykotor.resource.formats.ncs.compiler.classes import CodeRoot  # pyright: ignore[reportPrivateImportUsage]
    from toolset.data.installation import HTInstallation  # pyright: ignore[reportPrivateImportUsage]
    KOTOR_CONSTANTS: list[ScriptConstant] = []  # pyright: ignore[reportPrivateImportUsage]
    KOTOR_FUNCTIONS: list[ScriptFunction] = []  # pyright: ignore[reportPrivateImportUsage]
    TSL_CONSTANTS: list[ScriptConstant] = []  # pyright: ignore[reportPrivateImportUsage]
    TSL_FUNCTIONS: list[ScriptFunction] = []  # pyright: ignore[reportPrivateImportUsage]
else:
    from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_CONSTANTS, TSL_FUNCTIONS  # pyright: ignore[reportPrivateImportUsage]


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

        from toolset.uic.qtpy.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()

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

        item = QTreeWidgetItem(self.ui.bookmarkTree)
        item.setText(0, str(line_number))
        item.setText(1, default_description)
        item.setData(0, Qt.ItemDataRole.UserRole, line_number)

        self.ui.bookmarkTree.setCurrentItem(item)
        self.ui.bookmarkTree.editItem(item, 1)

        # Select the entire text in the editable field
        editor = self.ui.bookmarkTree.itemWidget(item, 1)
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
            index = self.ui.bookmarkTree.indexOfTopLevelItem(item)
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
        bookmarks = json.loads(settings.value("bookmarks", "[]"))  # type: ignore[arg-type]
        for bookmark in bookmarks:
            item = QTreeWidgetItem(self.ui.bookmarkTree)
            item.setText(0, str(bookmark["line"]))
            item.setText(1, bookmark["description"])
            item.setData(0, Qt.ItemDataRole.UserRole, bookmark["line"])

    def load_snippets(self):
        """TODO: snippet loading into the list widget, and then sending them to the code editor."""

    def _save_snippets(self):
        snippets = []
        for i in range(self.ui.snippetList.count()):
            item = self.ui.snippetList.item(i)
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
        self.ui.snippetList.addItem(item)
        self._save_snippets()

    def on_remove_snippet(self):
        current_item = self.ui.snippetList.currentItem()
        if not current_item:
            return
        self.ui.snippetList.takeItem(self.ui.snippetList.row(current_item))
        self._save_snippets()

    def insert_snippet(self, item: QListWidgetItem):
        content = item.data(Qt.ItemDataRole.UserRole)
        cursor = self.ui.codeEdit.textCursor()
        cursor.insertText(content)
        self._save_snippets()

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
        self.ui.codeEdit.textChanged.connect(self.ui.codeEdit.on_text_changed)
        self.ui.codeEdit.textChanged.connect(self._update_outline)
        if self._is_tsl:
            self.ui.actionK1.setChecked(False)
            self.ui.actionTSL.setChecked(True)
        else:
            self.ui.actionK1.setChecked(True)
            self.ui.actionTSL.setChecked(False)
        self.ui.actionK1.triggered.connect(self._on_game_changed)
        self.ui.actionTSL.triggered.connect(self._on_game_changed)

        self.ui.mainSplitter.setSizes([999999, 1])

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
        self.ui.panelTabs.addTab(self.ui.outputTab, "Output")
        self.output_text_edit: QTextEdit = QTextEdit(self.ui.outputTab)
        self.output_text_edit.setReadOnly(True)
        self.outputLayout: QVBoxLayout = QVBoxLayout(self.ui.outputTab)
        self.outputLayout.addWidget(self.output_text_edit)

        # Add error badge
        self.error_badge: QLabel = QLabel(self)
        self.error_badge.setStyleSheet("""
            background-color: red;
            color: white;
            border-radius: 10px;
            padding: 2px;
        """)
        self.error_badge.hide()
        self._setup_shortcuts()

    def _setup_error_reporting(self):
        self.error_count: int = 0
        tab_bar: QTabBar = self.ui.panelTabs.tabBar()  # pyright: ignore[reportCallIssue, reportAssignmentType]
        if tab_bar is None:
            return
        tab_bar.setTabButton(
            self.ui.panelTabs.indexOf(self.ui.outputTab),
            QTabBar.ButtonPosition.RightSide,
            QLabel() if self.error_badge is None else self.error_badge,
        )
        self.error_stream: io.StringIO = io.StringIO()
        sys.stderr = self.error_stream

    def handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ):
        tb_list: list[str] = traceback.format_exception(exc_type, exc_value, exc_traceback)
        self.report_error("".join(tb_list))

    def report_error(self, error_message: str):
        self.error_count += 1
        self.error_badge.setText(str(self.error_count))
        self.error_badge.show()
        self.output_text_edit.append(f"Error: {error_message}")
        self.ui.panelTabs.setCurrentWidget(self.ui.outputTab)
        self.output_text_edit.append(self.error_stream.getvalue())
        self.error_stream.truncate(0)
        self.error_stream.seek(0)

    def clear_errors(self):
        self.error_count = 0
        self.error_badge.hide()
        self.output_text_edit.clear()

    def _on_game_changed(self, index: int):
        self._is_tsl = index == 1
        self._update_game_specific_data()

    def _update_game_specific_data(self):
        # Update constants and functions based on the selected game
        # Don't take these out of a type checking block. These are so large they'll lag out your language server in your IDE.
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
                self.ui.functionList.addItem(item)
            except RuntimeError:  # wrapped C/C++ object of type 'QListWidget' has been deleted
                RobustLogger().warning("Failed to add function to list", exc_info=True)
                has_error = True

        for constant in self.constants:
            item = QListWidgetItem(constant.name)
            item.setData(Qt.ItemDataRole.UserRole, constant)
            try:
                self.ui.constantList.addItem(item)
            except RuntimeError:  # wrapped C/C++ object of type 'QListWidget' has been deleted
                RobustLogger().warning("Failed to add constant to list", exc_info=True)
                has_error = True

        if has_error:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Failed to update lists",
                "Failed to update the function or constant lists.",
            ).exec_()

        self._update_completer_model(self.constants, self.functions)
        self._highlighter.update_rules(is_tsl=self._is_tsl)

    def _setup_signals(self):
        self.ui.actionCompile.triggered.connect(self.compile_current_script)
        self.ui.constantList.doubleClicked.connect(self.insert_selected_constant)
        self.ui.functionList.doubleClicked.connect(self.insert_selected_function)
        self.ui.functionSearchEdit.textChanged.connect(self.on_function_search)
        self.ui.constantSearchEdit.textChanged.connect(self.on_constant_search)
        self.ui.codeEdit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.codeEdit.customContextMenuRequested.connect(self.editor_context_menu)
        self.ui.codeEdit.textChanged.connect(self.ui.codeEdit.on_text_changed)

    def editor_context_menu(self, pos: QPoint):
        menu: QMenu = self.ui.codeEdit.createStandardContextMenu()

        # Navigation
        menu.addSeparator()
        action_go_to_definition: QAction = menu.addAction("Go to Definition")
        action_go_to_definition.setShortcut(Qt.Key.Key_F12)
        action_go_to_definition.triggered.connect(self.go_to_definition)
        menu.addSeparator()

        # Snippets
        snippet_menu = QMenu("Snippets", self)
        for trigger, content in self.ui.codeEdit.snippets.items():
            snippet_menu.addAction(trigger).triggered.connect(lambda _checked, content=content: self.ui.codeEdit.insertPlainText(content))
        snippet_menu.addAction("Add Snippet").triggered.connect(self.on_add_snippet)
        snippet_menu.addAction("Remove Snippet").triggered.connect(self.on_remove_snippet)
        menu.addMenu(snippet_menu)

        # Editing
        menu.addSeparator()
        action_add_bookmark: QAction = menu.addAction("Add Bookmark")
        action_add_bookmark.setShortcut(QKeySequence("Ctrl+B"))
        action_add_bookmark.triggered.connect(self.add_bookmark)

        action_duplicate_line: QAction = menu.addAction("Duplicate Line")
        action_duplicate_line.setShortcut(QKeySequence("Ctrl+D"))
        action_duplicate_line.triggered.connect(self.ui.codeEdit.duplicate_line)

        action_toggle_comment: QAction = menu.addAction("Toggle Comment")
        action_toggle_comment.setShortcut(QKeySequence("Ctrl+/"))
        action_toggle_comment.triggered.connect(self.ui.codeEdit.toggle_comment)
        action_insert_constant: QAction = menu.addAction("Insert Constant")
        action_insert_constant.setShortcut(QKeySequence("Ctrl+Shift+I"))
        action_insert_constant.triggered.connect(self.insert_selected_constant)
        action_insert_function: QAction = menu.addAction("Insert Function")
        action_insert_function.setShortcut(QKeySequence("Ctrl+Shift+F"))
        action_insert_function.triggered.connect(self.insert_selected_function)

        # Line Movement
        move_line_menu: QMenu = menu.addMenu("Move Line")
        action_move_line_up: QAction = move_line_menu.addAction("Up")
        action_move_line_up.setShortcut(QKeySequence("Ctrl+Shift+Up"))
        action_move_line_up.triggered.connect(lambda: self.ui.codeEdit.move_line_up_or_down("up"))
        action_move_line_down: QAction = move_line_menu.addAction("Down")
        action_move_line_down.setShortcut(QKeySequence("Ctrl+Shift+Down"))
        action_move_line_down.triggered.connect(lambda: self.ui.codeEdit.move_line_up_or_down("down"))

        # Auto-complete
        action_show_auto_complete_menu: QAction = menu.addAction("Show Auto-Complete Menu")
        action_show_auto_complete_menu.setShortcut(QKeySequence("Ctrl+Space"))
        action_show_auto_complete_menu.triggered.connect(self.ui.codeEdit.show_auto_complete_menu)

        # View
        menu.addSeparator()
        change_text_size_menu: QMenu = menu.addMenu("Text Size")
        action_increase_text_size: QAction = change_text_size_menu.addAction("Increase")
        action_increase_text_size.setShortcut(QKeySequence("Ctrl++"))
        action_increase_text_size.triggered.connect(lambda: self.ui.codeEdit.change_text_size(increase=True))
        action_decrease_text_size: QAction = change_text_size_menu.addAction("Decrease")
        action_decrease_text_size.setShortcut(QKeySequence("Ctrl+-"))
        action_decrease_text_size.triggered.connect(lambda: self.ui.codeEdit.change_text_size(increase=False))

        menu.exec(self.ui.codeEdit.mapToGlobal(pos))

    def go_to_definition(self):
        cursor: QTextCursor = self.ui.codeEdit.textCursor()
        word: str = cursor.selectedText()
        if not word or not word.strip():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()

        if not word or not word.strip():
            return

        for obj in self.ui.outlineView.findItems(word, Qt.MatchFlag.MatchRecursive):  # pyright: ignore[reportArgumentType]
            if not obj.data(0, Qt.ItemDataRole.UserRole):
                continue
            self.ui.codeEdit.on_outline_item_double_clicked(obj, 0)  # pyright: ignore[reportArgumentType]
            break

    def _setup_file_explorer(self):
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath("")
        self.ui.fileExplorerView.setModel(self.file_system_model)
        self.ui.fileExplorerView.setRootIndex(self.file_system_model.index(""))
        self.ui.fileExplorerView.hideColumn(1)
        self.ui.fileExplorerView.hideColumn(2)
        self.ui.fileExplorerView.hideColumn(3)
        self.ui.fileExplorerView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.fileExplorerView.customContextMenuRequested.connect(self._show_file_explorer_context_menu)
        self.ui.fileExplorerView.doubleClicked.connect(self._open_file_from_explorer)

        if self._filepath:
            index = self.file_system_model.index(str(self._filepath))
            self.ui.fileExplorerView.setCurrentIndex(index)
            self.ui.fileExplorerView.scrollTo(index)
            self.ui.fileExplorerView.expand(index.parent())

    def _show_file_explorer_context_menu(self, position):
        index = self.ui.fileExplorerView.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()
        menu.addAction("Open").triggered.connect(lambda: self._open_file_from_explorer(index))
        menu.exec_(self.ui.fileExplorerView.viewport().mapToGlobal(position))

    def _open_file_from_explorer(self, index):
        file_path = self.file_system_model.filePath(index)
        fileres = FileResource.from_path(file_path)
        open_resource_editor(fileres)

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
            saved_connection = self.sig_saved_file.connect(saved_file_callback)
        else:
            saved_connection = None
        assert self._filepath is not None
        assert self._resname is not None
        assert self._restype is not None
        assert self._revert is not None
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
        script_filename = f"{resref.lower()}.nss"
        dialog = GitHubFileSelector(self.owner, self.repo, selected_files=[script_filename], parent=self)
        if dialog.exec_() != QDialog.DialogCode.Accepted:
            raise ValueError("No script selected.")

        selected_path: str | None = dialog.selected_path
        if selected_path is None or not selected_path.strip():
            raise ValueError("No script selected.")
        print(f"User selected script path: {selected_path}")
        return str(selected_path)

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
        return True

    def _handle_user_ncs(self, data: bytes, resname: str) -> None:
        box = QMessageBox(
            QMessageBox.Icon.Question,
            "Decompile or Download",
            f"Would you like to decompile this script, or download it from <a href='{self.sourcerepo_url}'>Vanilla Source Repository</a>?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        box.button(QMessageBox.StandardButton.Yes).setText("Decompile")
        box.button(QMessageBox.StandardButton.Ok).setText("Download")
        choice = box.exec_()
        print(f"User chose '{choice}' in the decompile/download messagebox.")

        if choice == QMessageBox.StandardButton.Yes:
            assert self._installation is not None, "Installation not set, cannot determine path"
            source = ht_decompile_script(data, self._installation.path(), tsl=self._installation.tsl)
        elif choice == QMessageBox.StandardButton.Ok:
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

        return local_path.read_text(encoding="windows-1252")

    def build(self) -> tuple[bytes | bytearray, bytes]:
        if self._restype is not ResourceType.NCS:
            return self.ui.codeEdit.toPlainText().encode("windows-1252"), b""

        RobustLogger().debug(f"Compiling script '{self._resname}.{self._restype.extension}' from the NSSEditor...")
        assert self._installation is not None, "Installation not set, cannot determine path"
        compiled_bytes: bytes | None = ht_compile_script(
            self.ui.codeEdit.toPlainText(),
            self._installation.path(),
            tsl=self._installation.game().is_k2()  # Determine whether this is a TSL installation (K2/TSL/2)
        )
        if compiled_bytes is None:
            self._logger.debug(f"User cancelled the compilation of '{self._resname}.{self._restype.extension}'.")
            return bytearray(), b""
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
        """Shows a messagebox after compile_current_script successfully saves an NCS resource."""
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
        self.completer.setCompletionPrefix(self.ui.codeEdit.text_under_cursor())
        if self.completer.completionCount() > 0:
            rect = self.ui.codeEdit.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)

    def insert_selected_constant(self):
        selected_items: list[QListWidgetItem] = self.ui.constantList.selectedItems()
        if selected_items:
            constant: ScriptConstant = selected_items[0].data(Qt.ItemDataRole.UserRole)
            insert = f"{constant.name} = {constant.value}"
            self.ui.codeEdit.insert_text_at_cursor(insert)

    def insert_selected_function(self):
        selected_items: list[QListWidgetItem] = self.ui.functionList.selectedItems()
        if selected_items:
            function: ScriptFunction = selected_items[0].data(Qt.ItemDataRole.UserRole)
            insert = f"{function.name}()"
            self.ui.codeEdit.insert_text_at_cursor(insert, insert.index("(") + 1)

    def on_function_search(self):
        string = self.ui.functionSearchEdit.text()
        if not string or not string.strip():
            return
        lower_string = string.lower()
        for i in range(self.ui.functionList.count()):
            item = self.ui.functionList.item(i)
            if not item:
                continue
            item.setHidden(lower_string not in item.text().lower())

    def on_constant_search(self):
        string = self.ui.constantSearchEdit.text()
        if not string or not string.strip():
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

        ast: CodeRoot = parser.parser.parse(text, lexer=lexer.lexer)
        self._populate_outline(ast)
        self.ui.outlineView.expandAll()

    def _populate_outline(self, ast: CodeRoot):
        for obj in ast.objects:
            if isinstance(obj, FunctionDefinition):
                item = QTreeWidgetItem(self.ui.outlineView)
                item.setText(0, f"Function: {obj.identifier}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)

                for param in obj.parameters:
                    param_item = QTreeWidgetItem(item)
                    param_item.setText(0, f"Param: {param.identifier}")

            elif isinstance(obj, StructDefinition):
                item = QTreeWidgetItem(self.ui.outlineView)
                item.setText(0, f"Struct: {obj.identifier}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)

                for member in obj.members:
                    member_item = QTreeWidgetItem(item)
                    member_item.setText(0, f"Member: {member.identifier}")

            elif isinstance(obj, GlobalVariableDeclaration):
                item = QTreeWidgetItem(self.ui.outlineView)
                item.setText(0, f"Global: {obj.identifier}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)

    def _setup_shortcuts(self):
        self.ui.actionCompile.setShortcut(Qt.Key.Key_F5)
        self.ui.actionCompile.triggered.connect(self.compile_current_script)
        self.ui.actionNew.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_N))
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_O))
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_S))
        self.ui.actionSave_As.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_S))
        self.ui.actionClose.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_W))

        # Add new shortcuts for bookmarks and snippets
        self.ui.actionReset_Zoom.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_0))
        self.ui.actionUndo.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Z))
        self.ui.actionUndo.triggered.connect(self.ui.codeEdit.undo)  # QUndoCommand
        self.ui.actionRedo.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Y))
        self.ui.actionRedo.triggered.connect(self.ui.codeEdit.redo)  # QRedoCommand
        self.ui.actionGo_to_Line.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_G))
        self.ui.actionGo_to_Line.triggered.connect(self.ui.codeEdit.go_to_line)
        self.ui.actionFind.setShortcut(QKeySequence(Qt.Key.Key_Control + Qt.Key.Key_F))
        self.ui.actionFind.triggered.connect(self.ui.codeEdit.find_and_replace_dialog)
        self.ui.actionReplace.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_H))
        self.ui.actionReplace.triggered.connect(self.ui.codeEdit.find_and_replace_dialog)

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
