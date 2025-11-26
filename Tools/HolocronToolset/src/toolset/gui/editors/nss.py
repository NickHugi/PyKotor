from __future__ import annotations

import io
import json
import multiprocessing
import os
import sys
import traceback
from contextlib import contextmanager
from operator import attrgetter
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable, Generator, NamedTuple, Sequence, cast

from loggerplus import RobustLogger, get_log_directory  # type: ignore[import-untyped]
from qtpy.QtCore import QDir, QModelIndex, QRect, QSettings, QStringListModel, Qt  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QFont, QKeySequence, QShortcut, QTextBlock, QTextCursor, QTextDocument
from qtpy.QtWidgets import (
    QApplication,
    QCompleter,
    QDialog,
    QFileDialog,
    QFileSystemModel,  # pyright: ignore[reportPrivateImportUsage]
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMenu,
    QMessageBox,  # pyright: ignore[reportPrivateImportUsage]
    QPlainTextDocumentLayout,
    QPlainTextEdit,
    QTabBar,
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
from toolset.gui.common.debugger import Debugger, DebuggerState  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.breadcrumbs_widget import BreadcrumbsWidget  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.command_palette import CommandPalette  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.debug_callstack_widget import DebugCallStackWidget  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.debug_variables_widget import DebugVariablesWidget  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.debug_watch_widget import DebugWatchWidget  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.find_replace_widget import FindReplaceWidget  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.test_config_widget import TestConfigDialog  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.common.widgets.syntax_highlighter import SyntaxHighlighter  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.dialogs.github_selector import GitHubFileSelector  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.editor import Editor  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError  # pyright: ignore[reportPrivateImportUsage]
from toolset.gui.widgets.terminal_widget import TerminalWidget  # pyright: ignore[reportPrivateImportUsage]
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
        self._add_help_action()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        self._setup_signals()

        # Create document with QPlainTextDocumentLayout for QPlainTextEdit compatibility
        # QPlainTextEdit requires QPlainTextDocumentLayout, not the default QTextDocumentLayout
        document: QTextDocument = QTextDocument(self)
        layout: QPlainTextDocumentLayout = QPlainTextDocumentLayout(document)
        document.setDocumentLayout(layout)
        self._highlighter: SyntaxHighlighter = SyntaxHighlighter(document, self._installation)
        self.ui.codeEdit.setDocument(document)
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
        self._error_count: int = 0
        self._find_results: list[dict[str, Any]] = []
        self._find_replace_widget: FindReplaceWidget | None = None
        self._current_find_text: str = ""
        self._current_find_flags: dict[str, bool] = {}
        self._completion_map: dict[str, Any] = {}  # Map completion strings to functions/constants
        self._error_lines: set[int] = set()  # Line numbers with errors (1-indexed)
        self._warning_lines: set[int] = set()  # Line numbers with warnings (1-indexed)
        
        # Debugger state
        self._debugger: Debugger | None = None
        self._breakpoint_lines: set[int] = set()  # Line numbers with breakpoints (1-indexed)
        self._current_debug_line: int | None = None  # Current line being debugged
        self._line_to_instruction_map: dict[int, list[int]] = {}  # Map source lines to instruction indices

        self._setupUI()
        self._update_game_specific_data()
        self._setup_file_explorer()
        self._setup_bookmarks()
        self._setup_statusbar()
        self._setup_error_reporting()
        self._setup_find_replace_widget()
        self._setup_breadcrumbs()

        # Connect game selector
        self.ui.gameSelector.currentIndexChanged.connect(self._on_game_selector_changed)

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
        self._update_bookmark_visualization()

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
        self._update_bookmark_visualization()

    def _goto_bookmark(self, item: QTreeWidgetItem):
        line_number = item.data(0, Qt.ItemDataRole.UserRole)
        self._goto_line(line_number)

    def _goto_line(self, line_number: int):
        document: QTextDocument | None = self.ui.codeEdit.document()
        if document is None:
            return
        block: QTextBlock | None = document.findBlockByLineNumber(line_number - 1)
        if block is None:
            return
        cursor = QTextCursor(block)
        self.ui.codeEdit.setTextCursor(cursor)
        self.ui.codeEdit.centerCursor()

    def _save_bookmarks(self):
        """Save bookmarks to QSettings, keyed by file path."""
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
        # Save bookmarks per-file for better persistence
        file_key = f"nss_editor/bookmarks/{self._resname}" if self._resname else "nss_editor/bookmarks/untitled"
        settings.setValue(file_key, json.dumps(bookmarks))

    def load_bookmarks(self):
        """Load bookmarks from QSettings, keyed by file path."""
        settings = QSettings()
        # Load bookmarks per-file
        file_key = f"nss_editor/bookmarks/{self._resname}" if self._resname else "nss_editor/bookmarks/untitled"
        bookmarks_json = settings.value(file_key, "[]")
        if isinstance(bookmarks_json, str):
            try:
                bookmarks = json.loads(bookmarks_json)
            except json.JSONDecodeError:
                bookmarks = []
        else:
            bookmarks = bookmarks_json if isinstance(bookmarks_json, list) else []
        
        self.ui.bookmarkTree.clear()
        for bookmark in bookmarks:
            if isinstance(bookmark, dict) and "line" in bookmark:
                item = QTreeWidgetItem(self.ui.bookmarkTree)
                item.setText(0, str(bookmark["line"]))
                item.setText(1, bookmark.get("description", ""))
                item.setData(0, Qt.ItemDataRole.UserRole, bookmark["line"])

    def load_snippets(self):
        """Load snippets from QSettings into the list widget."""
        settings = QSettings()
        snippets_json = settings.value("nss_editor/snippets", "[]")
        if isinstance(snippets_json, str):
            try:
                snippets = json.loads(snippets_json)
            except json.JSONDecodeError:
                snippets = []
        else:
            snippets = snippets_json if isinstance(snippets_json, list) else []

        self.ui.snippetList.clear()
        for snippet in snippets:
            if isinstance(snippet, dict) and "name" in snippet and "content" in snippet:
                item = QListWidgetItem(snippet["name"])
                item.setData(Qt.ItemDataRole.UserRole, snippet["content"])
                self.ui.snippetList.addItem(item)

        # Also update snippet search
        self._filter_snippets()

    def _save_snippets(self):
        """Save snippets to QSettings."""
        snippets = []
        for i in range(self.ui.snippetList.count()):
            item = self.ui.snippetList.item(i)
            if item is not None:
                name = item.text() or ""
                content = item.data(Qt.ItemDataRole.UserRole) or ""
                snippets.append({"name": name, "content": content})
        settings = QSettings()
        settings.setValue("nss_editor/snippets", json.dumps(snippets))

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
        """Insert a snippet into the editor at cursor position."""
        content = item.data(Qt.ItemDataRole.UserRole)
        if content:
            cursor = self.ui.codeEdit.textCursor()
            # If there's a selection, replace it
            if cursor.hasSelection():
                cursor.removeSelectedText()
            # Insert the snippet
            cursor.insertText(content)
            # Move cursor to end of inserted text
            self.ui.codeEdit.setTextCursor(cursor)
            self._save_snippets()
    
    def _filter_snippets(self):
        """Filter snippets based on search text."""
        search_text = self.ui.snippetSearchEdit.text().lower()
        for i in range(self.ui.snippetList.count()):
            item = self.ui.snippetList.item(i)
            if item is not None:
                item.setHidden(search_text not in item.text().lower())

    def _setupUI(self):
        # Snippets
        self.ui.snippetList.itemDoubleClicked.connect(self.insert_snippet)
        self.ui.snippetAddButton.clicked.connect(self.on_add_snippet)
        self.ui.snippetDelButton.clicked.connect(self.on_remove_snippet)
        self.ui.snippetReloadButton.clicked.connect(self.load_snippets)
        self.ui.snippetSearchEdit.textChanged.connect(self._filter_snippets)
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

        # Style the outline view with VS Code-like appearance
        self.ui.outlineView.setStyleSheet("""
            QTreeWidget {
                background-color: palette(base);
                color: palette(text);
                border: none;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 3px 4px;
                border: none;
            }
            QTreeWidget::item:hover {
                background-color: palette(alternate-base);
            }
            QTreeWidget::item:selected {
                background-color: palette(highlight);
                color: palette(highlightedText);
            }
            QTreeWidget::branch {
                background-color: palette(base);
            }
            QTreeWidget::branch:has-siblings:!adjoins-item {
                border-image: none;
                border: none;
            }
        """)
        
        # Enable sorting and better navigation
        self.ui.outlineView.setSortingEnabled(False)  # Keep manual order by line number
        self.ui.outlineView.setRootIsDecorated(True)
        self.ui.outlineView.setHeaderHidden(True)
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
        self.ui.codeEdit.mouseMoveEvent = self._show_hover_documentation  # type: ignore[assignment]
        self.ui.codeEdit.textChanged.connect(self._update_outline)

        # Use the existing outputEdit widget from UI file with proper encoding
        self.output_text_edit = self.ui.outputEdit
        self.output_text_edit.setReadOnly(True)
        # Set proper font for output
        output_font = QFont("Consolas" if sys.platform == "win32" else "Monaco", 10)
        output_font.setStyleHint(QFont.StyleHint.Monospace)
        self.output_text_edit.setFont(output_font)

        # Initialize the terminal widget
        self._setup_terminal()

        # Initialize test/debug widgets (hidden by default - only shown during test runs)
        self._setup_debug_widgets()
        self._hide_test_ui()

        # Add error badge (will be set up in _setup_error_reporting)
        self.error_badge: QLabel | None = None
        self._setup_shortcuts()
        
        # Connect panel toggle actions
        self.ui.actionToggleFileExplorer.triggered.connect(self._toggle_file_explorer)
        self.ui.actionToggleTerminal.triggered.connect(self._toggle_terminal_panel)
        self.ui.actionToggle_Output_Panel.triggered.connect(self._toggle_output_panel)
        
        # Connect text change to update status bar
        self.ui.codeEdit.textChanged.connect(self._update_status_bar)
        self.ui.codeEdit.cursorPositionChanged.connect(self._update_status_bar)
        # Also update bookmarks when text changes (for line number updates)
        self.ui.codeEdit.textChanged.connect(self._validate_bookmarks)
        # Update bookmark visualization when bookmarks change
        self.ui.codeEdit.textChanged.connect(self._update_bookmark_visualization)
        
        # Connect outline view error handling
        self.ui.outlineView.setHeaderLabels(["Symbols"])
        
        # Enhanced auto-completion with IntelliSense-style hints
        self._setup_enhanced_completer()
        
        # Connect compilation errors to error visualization
        self.ui.codeEdit.textChanged.connect(self._update_error_diagnostics)
    
    def _validate_bookmarks(self):
        """Validate and update bookmark line numbers when text changes."""
        document = self.ui.codeEdit.document()
        assert document is not None, "Document should not be None"
        max_lines = document.blockCount()
        items_to_remove = []
        
        for i in range(self.ui.bookmarkTree.topLevelItemCount()):
            item = self.ui.bookmarkTree.topLevelItem(i)
            if item is None:
                continue
            line_number = item.data(0, Qt.ItemDataRole.UserRole)
            if line_number > max_lines:
                items_to_remove.append(i)
        
        # Remove invalid bookmarks (lines that no longer exist)
        for index in reversed(items_to_remove):
            self.ui.bookmarkTree.takeTopLevelItem(index)
        
        if items_to_remove:
            self._save_bookmarks()
        self._update_bookmark_visualization()
        self._update_bookmark_visualization()
    
    def _update_bookmark_visualization(self):
        """Update bookmark visualization in the gutter."""
        bookmark_lines = set()
        for i in range(self.ui.bookmarkTree.topLevelItemCount()):
            item = self.ui.bookmarkTree.topLevelItem(i)
            if item:
                line = item.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(line, int):
                    bookmark_lines.add(line)
        self.ui.codeEdit.set_bookmark_lines(bookmark_lines)

    def _setup_debug_widgets(self):
        """Set up debug UI widgets (variables, call stack, watch)."""
        # Create debug widgets
        self._debug_variables_widget = DebugVariablesWidget(self)
        self._debug_callstack_widget = DebugCallStackWidget(self)
        self._debug_watch_widget = DebugWatchWidget(self)
        
        # Replace the simple debug table with a tabbed interface
        # Check if debugTab exists and has a layout
        if hasattr(self.ui, 'debugTab') and hasattr(self.ui, 'debugTable'):
            # Get the existing layout
            debug_layout = self.ui.debugTab.layout()
            if debug_layout is not None:
                # Remove the old table
                old_table = self.ui.debugTable
                if old_table is not None:
                    old_table.setParent(None)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
                    old_table.deleteLater()
                
                # Create tab widget for debug panels
                from qtpy.QtWidgets import QTabWidget
                debug_tabs = QTabWidget(self.ui.debugTab)
                debug_tabs.addTab(self._debug_variables_widget, "Variables")
                debug_tabs.addTab(self._debug_callstack_widget, "Call Stack")
                debug_tabs.addTab(self._debug_watch_widget, "Watch")
                
                debug_layout.addWidget(debug_tabs)
        
        # Initially clear widgets
        self._debug_variables_widget.clear()
        self._debug_callstack_widget.clear()
        self._debug_watch_widget.clear()
    
    def _hide_test_ui(self):
        """Hide test/debug UI by default - only show during test runs."""
        # Hide debug tab
        if hasattr(self.ui, 'debugTab') and hasattr(self.ui, 'panelTabs'):
            debug_tab_index = self.ui.panelTabs.indexOf(self.ui.debugTab)
            if debug_tab_index >= 0:
                self.ui.panelTabs.removeTab(debug_tab_index)
    
    def _show_test_ui(self):
        """Show test/debug UI during a test run."""
        if hasattr(self.ui, 'debugTab') and hasattr(self.ui, 'panelTabs'):
            # Check if tab already exists
            debug_tab_index = self.ui.panelTabs.indexOf(self.ui.debugTab)
            if debug_tab_index < 0:
                # Add debug tab back
                debug_tab_index = self.ui.panelTabs.addTab(self.ui.debugTab, "Test")
            self.ui.panelTabs.setCurrentIndex(debug_tab_index)
    
    def _setup_command_palette(self):
        """Set up the command palette with all available commands."""
        commands = [
            # File operations
            {"id": "file.new", "label": "New File", "category": "File"},
            {"id": "file.open", "label": "Open File...", "category": "File"},
            {"id": "file.save", "label": "Save", "category": "File"},
            {"id": "file.saveAs", "label": "Save As...", "category": "File"},
            {"id": "file.saveAll", "label": "Save All", "category": "File"},
            {"id": "file.close", "label": "Close", "category": "File"},
            {"id": "file.closeAll", "label": "Close All", "category": "File"},
            
            # Edit operations
            {"id": "edit.undo", "label": "Undo", "category": "Edit"},
            {"id": "edit.redo", "label": "Redo", "category": "Edit"},
            {"id": "edit.cut", "label": "Cut", "category": "Edit"},
            {"id": "edit.copy", "label": "Copy", "category": "Edit"},
            {"id": "edit.paste", "label": "Paste", "category": "Edit"},
            {"id": "edit.find", "label": "Find", "category": "Edit"},
            {"id": "edit.replace", "label": "Replace", "category": "Edit"},
            {"id": "edit.toggleComment", "label": "Toggle Line Comment", "category": "Edit"},
            {"id": "edit.duplicateLine", "label": "Duplicate Line", "category": "Edit"},
            {"id": "edit.deleteLine", "label": "Delete Line", "category": "Edit"},
            {"id": "edit.moveLineUp", "label": "Move Line Up", "category": "Edit"},
            {"id": "edit.moveLineDown", "label": "Move Line Down", "category": "Edit"},
            
            # View operations
            {"id": "view.toggleExplorer", "label": "Toggle Explorer", "category": "View"},
            {"id": "view.toggleTerminal", "label": "Toggle Terminal", "category": "View"},
            {"id": "view.toggleOutput", "label": "Toggle Output Panel", "category": "View"},
            {"id": "view.zoomIn", "label": "Zoom In", "category": "View"},
            {"id": "view.zoomOut", "label": "Zoom Out", "category": "View"},
            {"id": "view.resetZoom", "label": "Reset Zoom", "category": "View"},
            {"id": "view.toggleWordWrap", "label": "Toggle Word Wrap", "category": "View"},
            
            # Navigation
            {"id": "navigate.gotoLine", "label": "Go to Line...", "category": "Navigation"},
            {"id": "navigate.gotoDefinition", "label": "Go to Definition", "category": "Navigation"},
            {"id": "navigate.findReferences", "label": "Find All References", "category": "Navigation"},
            
            # Code operations
            {"id": "code.format", "label": "Format Document", "category": "Code"},
            {"id": "code.compile", "label": "Compile Script", "category": "Code"},
            {"id": "code.analyze", "label": "Analyze Code", "category": "Code"},
            
            # Bookmarks
            {"id": "bookmark.toggle", "label": "Toggle Bookmark", "category": "Bookmarks"},
            {"id": "bookmark.next", "label": "Next Bookmark", "category": "Bookmarks"},
            {"id": "bookmark.previous", "label": "Previous Bookmark", "category": "Bookmarks"},
            
            # Help
            {"id": "help.documentation", "label": "Show Documentation", "category": "Help"},
            {"id": "help.shortcuts", "label": "Show Keyboard Shortcuts", "category": "Help"},
        ]
        
        # Register commands with callbacks
        command_map = {
            "file.new": self.new,
            "file.open": self.open,
            "file.save": self.save,
            "file.saveAs": self.save_as,
            "file.close": self.close,
            "edit.undo": lambda: self.ui.codeEdit.undo(),
            "edit.redo": lambda: self.ui.codeEdit.redo(),
            "edit.cut": lambda: self.ui.codeEdit.cut(),
            "edit.copy": lambda: self.ui.codeEdit.copy(),
            "edit.paste": lambda: self.ui.codeEdit.paste(),
            "edit.find": self._show_find,
            "edit.replace": self._show_replace,
            "edit.toggleComment": lambda: self.ui.codeEdit.toggle_comment(),
            "edit.duplicateLine": lambda: self.ui.codeEdit.duplicate_line(),
            "edit.deleteLine": self._delete_line,
            "edit.moveLineUp": lambda: self.ui.codeEdit.move_line_up_or_down("up"),
            "edit.moveLineDown": lambda: self.ui.codeEdit.move_line_up_or_down("down"),
            "view.toggleExplorer": lambda: self.ui.actionToggleFileExplorer.trigger(),
            "view.toggleTerminal": lambda: self.ui.actionToggleTerminal.trigger(),
            "view.toggleOutput": lambda: self.ui.actionToggle_Output_Panel.trigger(),
            "view.zoomIn": lambda: self.ui.codeEdit.change_text_size(increase=True),
            "view.zoomOut": lambda: self.ui.codeEdit.change_text_size(increase=False),
            "view.resetZoom": self._reset_zoom,
            "view.toggleWordWrap": self._toggle_word_wrap,
            "navigate.gotoLine": lambda: self.ui.codeEdit.go_to_line(),
            "navigate.gotoDefinition": self.go_to_definition,
            "navigate.findReferences": self._find_all_references_at_cursor,
            "code.format": self._format_code,
            "code.compile": self.compile_current_script,
            "code.analyze": self._analyze_code,
            "bookmark.toggle": self._toggle_bookmark_at_cursor,
            "bookmark.next": self._goto_next_bookmark,
            "bookmark.previous": self._goto_previous_bookmark,
            "help.documentation": self._show_documentation,
            "help.shortcuts": self._show_keyboard_shortcuts,
        }
        
        # Register all commands
        for cmd in commands:
            callback = command_map.get(cmd["id"])
            self._command_palette.register_command(
                cmd["id"],
                cmd["label"],
                cmd.get("category", ""),
                callback
            )
    
    def _show_command_palette(self):
        """Show the command palette."""
        self._command_palette.show_palette()
    
    def _detect_entry_point(self, source: str) -> str:
        """Detect the entry point type from source code.
        
        Args:
        ----
            source: str: Source code to analyze
            
        Returns:
        -------
            str: "main" or "StartingConditional" or "unknown"
        """
        import re
        # Check for void main()
        main_pattern = r'\bvoid\s+main\s*\('
        if re.search(main_pattern, source, re.IGNORECASE):
            return "main"
        
        # Check for int StartingConditional()
        conditional_pattern = r'\bint\s+StartingConditional\s*\('
        if re.search(conditional_pattern, source, re.IGNORECASE):
            return "StartingConditional"
        
        return "unknown"
    
    def _setup_terminal(self):
        """Set up the integrated terminal widget."""
        # Clear existing layout if any
        old_layout = self.ui.terminalWidget.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item and item.widget():
                    item_widget = item.widget()
                    assert item_widget is not None, "Widget should not be None"
                    item_widget.deleteLater()
            QWidget().setLayout(old_layout)  # Delete old layout

        # Create and add terminal widget
        terminal_layout = QVBoxLayout(self.ui.terminalWidget)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)

        self.terminal = TerminalWidget(self.ui.terminalWidget)
        terminal_layout.addWidget(self.terminal)

        # Connect terminal signals
        self.terminal.command_executed.connect(self._on_terminal_command)
        
        # Set up terminal with useful defaults
        # Terminal widget should handle its own initialization
        # But we can set the working directory to the current file's directory if available
        if self._filepath and self._filepath.exists():
            try:
                # Try to set working directory to file's parent
                if hasattr(self.terminal, 'set_working_directory'):
                    self.terminal.set_working_directory(str(self._filepath.parent))
            except Exception:
                # Terminal might not support this, that's okay
                pass

    def _on_terminal_command(self, command: str):
        """Handle commands executed in the terminal.

        Args:
        ----
            command: str: The command that was executed
        """
        # Log command to output if needed
        self._log_to_output(f"Terminal: {command}")
        
        # Handle special commands that interact with the editor
        if command.strip().startswith("compile") or command.strip() == "build":
            # Auto-compile when user types 'compile' or 'build' in terminal
            self.compile_current_script()
        elif command.strip().startswith("open "):
            # Try to open a file
            file_path = command.strip()[5:].strip()
            if file_path:
                try:
                    path = Path(file_path)
                    if path.exists():
                        fileres = FileResource.from_path(path)
                        open_resource_editor(fileres)
                    else:
                        self._log_to_output(f"File not found: {file_path}")
                except Exception as e:
                    self._log_to_output(f"Error opening file: {e}")

    def _log_to_output(self, message: str):
        """Log a message to the output panel with proper encoding.

        Args:
        ----
            message: str: The message to log
        """
        try:
            # Ensure proper text encoding
            if isinstance(message, bytes):
                message = message.decode('utf-8', errors='replace')
            self.output_text_edit.appendPlainText(message)
        except Exception:
            # Fallback if there's any encoding issue
            self.output_text_edit.appendPlainText(str(message))

    def _setup_error_reporting(self):
        """Set up error badge on output tab."""
        self._error_count  = 0
        self.error_badge = QLabel("0")
        # Use palette colors instead of hardcoded colors
        self.error_badge.setStyleSheet("""
            QLabel {
                background-color: palette(windowText);
                color: palette(window);
                border-radius: 10px;
                padding: 2px 6px;
                font-weight: bold;
                min-width: 18px;
                text-align: center;
            }
        """)
        self.error_badge.hide()
        
        tab_bar: QTabBar | None = self.ui.panelTabs.tabBar()  # pyright: ignore[reportCallIssue, reportAssignmentType]
        if tab_bar is not None:
            output_tab_index = self.ui.panelTabs.indexOf(self.ui.outputTab)
            if output_tab_index >= 0:
                tab_bar.setTabButton(
                    output_tab_index,
                    QTabBar.ButtonPosition.RightSide,
                    self.error_badge,
                )
        
        self.error_stream: io.StringIO = io.StringIO()
        # Don't redirect stderr globally - only log errors explicitly

    def handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ):
        tb_list: list[str] = traceback.format_exception(exc_type, exc_value, exc_traceback)
        self.report_error("".join(tb_list))

    def report_error(self, error_message: str):
        """Report an error and update the error badge."""
        self._error_count += 1
        if self.error_badge is not None:
            self.error_badge.setText(str(self._error_count))
            self.error_badge.show()

        # Log error with proper encoding
        try:
            if isinstance(error_message, bytes):
                error_message = error_message.decode('utf-8', errors='replace')
            self.output_text_edit.appendPlainText(f"Error: {error_message}")
        except Exception:
            self.output_text_edit.appendPlainText(f"Error: {str(error_message)}")

        self.ui.panelTabs.setCurrentWidget(self.ui.outputTab)

        # Append error stream content with proper encoding
        error_content = self.error_stream.getvalue()
        if error_content:
            try:
                self.output_text_edit.appendPlainText(error_content)
            except Exception:
                self.output_text_edit.appendPlainText(str(error_content))

        self.error_stream.truncate(0)
        self.error_stream.seek(0)

    def clear_errors(self):
        """Clear all errors and reset the error badge."""
        self._error_count = 0
        if self.error_badge is not None:
            self.error_badge.hide()
        self.output_text_edit.clear()

    def _on_game_changed(self, index: int):
        """Handle game change from action menu."""
        self._is_tsl = index == 1
        self._update_game_specific_data()
        
    def _on_game_selector_changed(self, index: int):
        """Handle game change from dropdown selector."""
        self._is_tsl = index == 1
        self._update_game_specific_data()
        # Update action check states
        self.ui.actionK1.setChecked(not self._is_tsl)
        self.ui.actionTSL.setChecked(self._is_tsl)

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
            ).exec()

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
        """Enhanced context menu with VS Code-like organization."""
        menu: QMenu | None = self.ui.codeEdit.createStandardContextMenu()
        assert menu is not None, "Menu should not be None"
        
        # Get word under cursor for context-aware actions
        cursor: QTextCursor = self.ui.codeEdit.cursorForPosition(pos)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word_under_cursor: str = cursor.selectedText().strip()

        # Navigation section
        menu.addSeparator()
        if word_under_cursor and word_under_cursor.strip():
            action_go_to_definition: QAction | None = menu.addAction("Go to Definition")
            assert action_go_to_definition is not None, "Go to definition action should not be None"
            action_go_to_definition.setShortcut(QKeySequence("F12"))
            action_go_to_definition.triggered.connect(self.go_to_definition)
            
            action_find_all_refs: QAction | None = menu.addAction("Find All References")
            assert action_find_all_refs is not None, "Find all references action should not be None"
            action_find_all_refs.setShortcut(QKeySequence("Shift+F12"))
            action_find_all_refs.triggered.connect(lambda: self._find_all_references(word_under_cursor))
        
        action_go_to_line: QAction | None = menu.addAction("Go to Line...")
        assert action_go_to_line is not None, "Go to line action should not be None"
        action_go_to_line.setShortcut(QKeySequence("Ctrl+G"))
        action_go_to_line.triggered.connect(self.ui.codeEdit.go_to_line)
        menu.addSeparator()

        # Editing section
        action_cut: QAction | None = menu.addAction("Cut")
        assert action_cut is not None, "Cut action should not be None"
        action_cut.setShortcut(QKeySequence("Ctrl+X"))
        action_cut.triggered.connect(self.ui.codeEdit.cut)
        
        action_copy: QAction | None = menu.addAction("Copy")
        assert action_copy is not None, "Copy action should not be None"
        action_copy.setShortcut(QKeySequence("Ctrl+C"))
        action_copy.triggered.connect(self.ui.codeEdit.copy)
        
        action_paste: QAction | None = menu.addAction("Paste")
        assert action_paste is not None, "Paste action should not be None"
        action_paste.setShortcut(QKeySequence("Ctrl+V"))
        action_paste.triggered.connect(self.ui.codeEdit.paste)
        
        menu.addSeparator()
        
        action_duplicate_line: QAction | None = menu.addAction("Duplicate Line")
        assert action_duplicate_line is not None, "Duplicate line action should not be None"
        action_duplicate_line.setShortcut(QKeySequence("Ctrl+D"))
        action_duplicate_line.triggered.connect(self.ui.codeEdit.duplicate_line)
        
        action_delete_line: QAction | None = menu.addAction("Delete Line")
        assert action_delete_line is not None, "Delete line action should not be None"
        action_delete_line.setShortcut(QKeySequence("Ctrl+Shift+K"))
        action_delete_line.triggered.connect(self._delete_line)

        # Line Movement
        move_line_menu: QMenu | None = menu.addMenu("Move Line")
        assert move_line_menu is not None, "Move line menu should not be None"
        action_move_line_up: QAction | None = move_line_menu.addAction("Move Line Up")
        assert action_move_line_up is not None, "Move line up action should not be None"
        action_move_line_up.setShortcut(QKeySequence("Alt+Up"))
        action_move_line_up.triggered.connect(lambda: self.ui.codeEdit.move_line_up_or_down("up"))
        action_move_line_down: QAction | None = move_line_menu.addAction("Move Line Down")
        assert action_move_line_down is not None, "Move line down action should not be None"
        action_move_line_down.setShortcut(QKeySequence("Alt+Down"))
        action_move_line_down.triggered.connect(lambda: self.ui.codeEdit.move_line_up_or_down("down"))

        menu.addSeparator()
        
        # Code actions
        action_toggle_comment: QAction | None = menu.addAction("Toggle Line Comment")
        assert action_toggle_comment is not None, "Toggle line comment action should not be None"
        action_toggle_comment.setShortcut(QKeySequence("Ctrl+/"))
        action_toggle_comment.triggered.connect(self.ui.codeEdit.toggle_comment)
        
        indent_menu: QMenu | None = menu.addMenu("Indentation")
        assert indent_menu is not None, "Indentation menu should not be None"
        action_indent: QAction | None = indent_menu.addAction("Indent Line")
        assert action_indent is not None, "Indent line action should not be None"
        action_indent.setShortcut(QKeySequence("Ctrl+]"))
        action_indent.triggered.connect(self._indent_selection)
        action_unindent: QAction | None = indent_menu.addAction("Outdent Line")
        assert action_unindent is not None, "Outdent line action should not be None"
        action_unindent.setShortcut(QKeySequence("Ctrl+["))
        action_unindent.triggered.connect(self._unindent_selection)

        menu.addSeparator()
        
        # Bookmarks
        current_line = self.ui.codeEdit.textCursor().blockNumber() + 1
        has_bookmark = self._has_bookmark_at_line(current_line)
        
        if has_bookmark:
            action_remove_bookmark: QAction | None = menu.addAction("Remove Bookmark")
            assert action_remove_bookmark is not None, "Remove bookmark action should not be None"
            action_remove_bookmark.setShortcut(QKeySequence("Ctrl+K, Ctrl+B"))
            action_remove_bookmark.triggered.connect(lambda: self._remove_bookmark_at_line(current_line))
        else:
            action_add_bookmark: QAction | None = menu.addAction("Toggle Bookmark")
            assert action_add_bookmark is not None, "Toggle bookmark action should not be None"
            action_add_bookmark.setShortcut(QKeySequence("Ctrl+K, Ctrl+B"))
            action_add_bookmark.triggered.connect(self.add_bookmark)
        
        action_next_bookmark: QAction | None = menu.addAction("Next Bookmark")
        assert action_next_bookmark is not None, "Next bookmark action should not be None"
        action_next_bookmark.setShortcut(QKeySequence("Ctrl+K, Ctrl+N"))
        action_next_bookmark.triggered.connect(self._goto_next_bookmark)
        
        action_prev_bookmark: QAction | None = menu.addAction("Previous Bookmark")
        assert action_prev_bookmark is not None, "Previous bookmark action should not be None"
        action_prev_bookmark.setShortcut(QKeySequence("Ctrl+K, Ctrl+P"))
        action_prev_bookmark.triggered.connect(self._goto_previous_bookmark)

        # Snippets
        menu.addSeparator()
        snippet_menu = QMenu("Snippets", self)
        if self.ui.codeEdit.snippets:
            for trigger, content in self.ui.codeEdit.snippets.items():
                action = snippet_menu.addAction(trigger)
                assert action is not None, "Snippet action should not be None"
                action.triggered.connect(
                    lambda _checked, c=content: self.ui.codeEdit.insertPlainText(c)
                )
            snippet_menu.addSeparator()
        action = snippet_menu.addAction("Insert Snippet...")
        assert action is not None, "Insert snippet action should not be None"
        action.triggered.connect(self._insert_snippet_dialog)
        action = snippet_menu.addAction("Configure Snippets...")
        assert action is not None, "Configure snippets action should not be None"
        action.triggered.connect(self._manage_snippets)
        menu.addMenu(snippet_menu)

        # Insert
        menu.addSeparator()
        insert_menu: QMenu | None = menu.addMenu("Insert")
        assert insert_menu is not None, "Insert menu should not be None"
        action_insert_constant: QAction | None = insert_menu.addAction("Insert Constant...")
        assert action_insert_constant is not None, "Insert constant action should not be None"
        action_insert_constant.setShortcut(QKeySequence("Ctrl+Shift+I"))
        action_insert_constant.triggered.connect(self.insert_selected_constant)
        action_insert_function: QAction | None = insert_menu.addAction("Insert Function...")
        assert action_insert_function is not None, "Insert function action should not be None"
        action_insert_function.setShortcut(QKeySequence("Ctrl+Shift+F"))
        action_insert_function.triggered.connect(self.insert_selected_function)

        # Auto-complete
        menu.addSeparator()
        action_show_auto_complete_menu: QAction | None = menu.addAction("Trigger Suggest")
        assert action_show_auto_complete_menu is not None, "Trigger suggest action should not be None"
        action_show_auto_complete_menu.setShortcut(QKeySequence("Ctrl+Space"))
        action_show_auto_complete_menu.triggered.connect(self.ui.codeEdit.show_auto_complete_menu)

        menu.exec(self.ui.codeEdit.mapToGlobal(pos))
    
    def _has_bookmark_at_line(self, line_number: int) -> bool:
        """Check if a bookmark exists at the given line."""
        for i in range(self.ui.bookmarkTree.topLevelItemCount()):
            item = self.ui.bookmarkTree.topLevelItem(i)
            if item and item.data(0, Qt.ItemDataRole.UserRole) == line_number:
                return True
        return False
    
    def _remove_bookmark_at_line(self, line_number: int):
        """Remove bookmark at the given line."""
        for i in range(self.ui.bookmarkTree.topLevelItemCount()):
            item = self.ui.bookmarkTree.topLevelItem(i)
            if item and item.data(0, Qt.ItemDataRole.UserRole) == line_number:
                self.ui.bookmarkTree.takeTopLevelItem(i)
                self._save_bookmarks()
                self._update_bookmark_visualization()
                break
    
    def _goto_next_bookmark(self):
        """Go to next bookmark after current line."""
        cursor = self.ui.codeEdit.textCursor()
        current_line = cursor.blockNumber() + 1
        
        bookmarks = []
        for i in range(self.ui.bookmarkTree.topLevelItemCount()):
            item = self.ui.bookmarkTree.topLevelItem(i)
            if item:
                line = item.data(0, Qt.ItemDataRole.UserRole)
                if line > current_line:
                    bookmarks.append(line)
        
        if bookmarks:
            self._goto_line(min(bookmarks))
        else:
            # Wrap around to first bookmark
            for i in range(self.ui.bookmarkTree.topLevelItemCount()):
                item = self.ui.bookmarkTree.topLevelItem(i)
                if item:
                    self._goto_line(item.data(0, Qt.ItemDataRole.UserRole))
                    break
    
    def _goto_previous_bookmark(self):
        """Go to previous bookmark before current line."""
        cursor = self.ui.codeEdit.textCursor()
        current_line = cursor.blockNumber() + 1
        
        bookmarks = []
        for i in range(self.ui.bookmarkTree.topLevelItemCount()):
            item = self.ui.bookmarkTree.topLevelItem(i)
            if item:
                line = item.data(0, Qt.ItemDataRole.UserRole)
                if line < current_line:
                    bookmarks.append(line)
        
        if bookmarks:
            self._goto_line(max(bookmarks))
        else:
            # Wrap around to last bookmark
            last_line = None
            for i in range(self.ui.bookmarkTree.topLevelItemCount()):
                item = self.ui.bookmarkTree.topLevelItem(i)
                if item:
                    last_line = item.data(0, Qt.ItemDataRole.UserRole)
            if last_line:
                self._goto_line(last_line)
    
    def _find_all_references(self, word: str):
        """Find all references to a symbol in the current file."""
        if not word or not word.strip():
            return
        
        # Clear previous results
        self.ui.findResultsTree.clear()
        self._find_results = []
        
        # Search in current file
        text = self.ui.codeEdit.toPlainText()
        lines = text.split("\n")
        
        for line_num, line in enumerate(lines, 1):
            # Simple word boundary matching
            import re
            pattern = r'\b' + re.escape(word) + r'\b'
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                self._find_results.append({
                    "file": str(self._filepath) if self._filepath else "Untitled",
                    "line": line_num,
                    "content": line.strip()[:100],
                    "column": match.start() + 1
                })
        
        # Populate results
        self._populate_find_results()
        
        # Show results panel
        self.ui.panelTabs.setCurrentWidget(self.ui.findResultsTab)
        
        if not self._find_results:
            QMessageBox.information(
                self,
                "Find All References",
                f"No references to '{word}' found in current file."
            )
        else:
            self._log_to_output(f"Found {len(self._find_results)} reference(s) to '{word}'")
    
    def _insert_snippet_dialog(self):
        """Open dialog to select and insert a snippet."""
        # Show snippet panel if available
        self.ui.snippetsDock.setVisible(True)
        self.ui.snippetsDock.raise_()
    
    def _insert_snippet_content(self, content: str):
        """Insert snippet content at cursor."""
        cursor = self.ui.codeEdit.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        cursor.insertText(content)
        self.ui.codeEdit.setTextCursor(cursor)

    def go_to_definition(self):
        """Go to definition of symbol under cursor."""
        cursor: QTextCursor = self.ui.codeEdit.textCursor()
        word: str = cursor.selectedText()
        if not word or not word.strip():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()

        if not word or not word.strip():
            QMessageBox.information(self, "Go to Definition", "No symbol selected.")
            return

        # First try to find in outline (functions, structs, globals)
        found = False
        for i in range(self.ui.outlineView.topLevelItemCount()):
            tree_item: QTreeWidgetItem | None = self.ui.outlineView.topLevelItem(i)
            if tree_item is None:
                continue
            item_text: str = tree_item.text(0)
            # Extract identifier from item text (e.g., "Function: main" -> "main")
            if ":" in item_text:
                identifier = item_text.split(":", 1)[1].strip()
            else:
                identifier = item_text.strip()
            
            if identifier.lower() == word.lower():
                obj: Any = tree_item.data(0, Qt.ItemDataRole.UserRole)
                if obj:
                    self.ui.codeEdit.on_outline_item_double_clicked(tree_item, 0)  # pyright: ignore[reportArgumentType]
                    found = True
                    break
            
            # Also check children (parameters, members)
            for j in range(tree_item.childCount()):
                child = tree_item.child(j)
                if child is None:
                    continue
                child_text = child.text(0)
                if ":" in child_text:
                    child_identifier = child_text.split(":", 1)[1].strip()
                else:
                    child_identifier = child_text.strip()
                if child_identifier.lower() == word.lower():
                    # Go to parent definition
                    self.ui.codeEdit.on_outline_item_double_clicked(item, 0)  # pyright: ignore[reportArgumentType]
                    found = True
                    break
            if found:
                break
        
        # If not found in outline, check if it's a function or constant
        if not found:
            # Check functions
            for func in self.functions:
                if func.name.lower() == word.lower():
                    # Show in constants/learn tab
                    self.ui.panelTabs.setCurrentWidget(self.ui.learnTab)
                    # Try to find and select in function list
                    for i in range(self.ui.functionList.count()):
                        list_item: QListWidgetItem | None = self.ui.functionList.item(i)
                        if list_item and list_item.text().lower() == word.lower():
                            self.ui.functionList.setCurrentItem(list_item)
                            self.ui.functionList.scrollToItem(list_item)
                            QMessageBox.information(
                                self,
                                "Go to Definition",
                                f"Function '{word}' is a built-in function.\n\n"
                                f"Return type: {getattr(func, 'return_type', 'void')}\n"
                                f"See the Constants tab for more information."
                            )
                            return
            
            # Check constants
            for const in self.constants:
                if const.name.lower() == word.lower():
                    self.ui.panelTabs.setCurrentWidget(self.ui.learnTab)
                    for i in range(self.ui.constantList.count()):
                        list_item = self.ui.constantList.item(i)
                        if list_item and list_item.text().lower() == word.lower():
                            self.ui.constantList.setCurrentItem(list_item)
                            self.ui.constantList.scrollToItem(list_item)
                            QMessageBox.information(
                                self,
                                "Go to Definition",
                                f"Constant '{word}' is a built-in constant.\n"
                                f"See the Constants tab for more information."
                            )
                            return
            
            QMessageBox.information(
                self,
                "Go to Definition",
                f"Definition for '{word}' not found in current file."
            )

    def _setup_file_explorer(self):
        """Set up the file explorer with filtering and navigation."""
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath("")
        # Filter to show files and directories
        self.file_system_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        
        self.ui.fileExplorerView.setModel(self.file_system_model)
        
        # Start with current file's directory or home directory
        if self._filepath and self._filepath.exists():
            root_path = str(self._filepath.parent)
        else:
            root_path = str(Path.home())
        
        root_index = self.file_system_model.index(root_path)
        self.ui.fileExplorerView.setRootIndex(root_index)
        self.ui.fileExplorerView.setColumnWidth(0, 250)
        
        # Hide size, type, and date columns
        self.ui.fileExplorerView.hideColumn(1)
        self.ui.fileExplorerView.hideColumn(2)
        self.ui.fileExplorerView.hideColumn(3)
        
        self.ui.fileExplorerView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.fileExplorerView.customContextMenuRequested.connect(self._show_file_explorer_context_menu)
        self.ui.fileExplorerView.doubleClicked.connect(self._open_file_from_explorer)
        
        # Connect address bar
        self.ui.lineEdit.returnPressed.connect(self._on_address_bar_changed)
        self.ui.lineEdit.setText(root_path)
        
        # Connect file search
        self.ui.fileSearchEdit.textChanged.connect(self._filter_file_explorer)
        
        # Connect refresh button
        self.ui.refreshFileExplorerButton.clicked.connect(self._refresh_file_explorer)
        
        # Set current file if available
        if self._filepath and self._filepath.exists():
            index = self.file_system_model.index(str(self._filepath))
            self.ui.fileExplorerView.setCurrentIndex(index)
            self.ui.fileExplorerView.scrollTo(index)
            parent_index = index.parent()
            while parent_index.isValid():
                self.ui.fileExplorerView.expand(parent_index)
                parent_index = parent_index.parent()
    
    def _on_address_bar_changed(self):
        """Handle address bar path change."""
        path_text = self.ui.lineEdit.text()
        path = Path(path_text)
        if path.exists() and path.is_dir():
            root_index = self.file_system_model.index(str(path))
            self.ui.fileExplorerView.setRootIndex(root_index)
        else:
            QMessageBox.warning(self, "Invalid Path", f"The path '{path_text}' does not exist or is not a directory.")
            # Reset to current root
            current_root = self.file_system_model.rootPath()
            self.ui.lineEdit.setText(current_root)
    
    def _filter_file_explorer(self):
        """Filter files in the explorer based on search text."""
        search_text: str = self.ui.fileSearchEdit.text().lower()
        if not search_text:
            # Show all files when search is empty
            model = self.ui.fileExplorerView.model()
            assert model is not None, "Model should not be None"
            for i in range(model.rowCount(self.ui.fileExplorerView.rootIndex())):
                index = model.index(i, 0, self.ui.fileExplorerView.rootIndex())
                if index.isValid():
                    self.ui.fileExplorerView.setRowHidden(i, self.ui.fileExplorerView.rootIndex(), False)
            return
        
        # Filter files matching search text
        def filter_recursive(parent_index):
            for i in range(self.file_system_model.rowCount(parent_index)):
                index = self.file_system_model.index(i, 0, parent_index)
                if not index.isValid():
                    continue
                
                file_name: str = self.file_system_model.fileName(index).lower()
                file_path: str = self.file_system_model.filePath(index).lower()
                
                # Check if this item or any child matches
                matches: bool = search_text in file_name or search_text in file_path
                
                # Check children
                if self.file_system_model.isDir(index):
                    child_matches = filter_recursive(index)
                    matches = matches or child_matches
                
                # Hide if no match
                view_index = self.ui.fileExplorerView.model().index(i, 0, parent_index)
                if view_index.isValid():
                    self.ui.fileExplorerView.setRowHidden(i, parent_index, not matches)
                
                return matches if matches else False
        
        filter_recursive(self.ui.fileExplorerView.rootIndex())
    
    def _refresh_file_explorer(self):
        """Refresh the file explorer view."""
        current_root: str = self.file_system_model.rootPath()
        self.file_system_model.setRootPath("")  # Reset model
        root_index: QModelIndex = self.file_system_model.index(current_root)
        self.ui.fileExplorerView.setRootIndex(root_index)
        self.ui.lineEdit.setText(current_root)

    def _show_file_explorer_context_menu(self, position):
        """Show context menu for file explorer items."""
        index: QModelIndex = self.ui.fileExplorerView.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()
        
        file_path = Path(self.file_system_model.filePath(index))
        is_dir = file_path.is_dir()
        
        if not is_dir:
            open_action = menu.addAction("Open")
            assert open_action is not None, "Open action should not be None"
            open_action.triggered.connect(lambda: self._open_file_from_explorer(index))
            menu.addSeparator()
        
        reveal_action = menu.addAction("Reveal in File Explorer")
        assert reveal_action is not None, "Reveal action should not be None"
        reveal_action.triggered.connect(lambda: self._reveal_in_explorer(file_path))
        
        if is_dir:
            menu.addSeparator()
            set_root_action = menu.addAction("Set as Root")
            assert set_root_action is not None, "Set root action should not be None"
            set_root_action.triggered.connect(lambda: self._set_explorer_root(file_path))
        
        menu.exec_(self.ui.fileExplorerView.viewport().mapToGlobal(position))
    
    def _reveal_in_explorer(self, file_path: Path):
        """Open the file's location in the system file explorer."""
        if sys.platform == "win32":
            os.startfile(file_path.parent if file_path.is_file() else file_path)  # noqa: S606
        elif sys.platform == "darwin":
            os.system(f'open "{file_path.parent if file_path.is_file() else file_path}"')  # noqa: S605
        else:
            os.system(f'xdg-open "{file_path.parent if file_path.is_file() else file_path}"')  # noqa: S605
    
    def _set_explorer_root(self, dir_path: Path):
        """Set the directory as the root of the file explorer."""
        if dir_path.is_dir():
            root_index = self.file_system_model.index(str(dir_path))
            self.ui.fileExplorerView.setRootIndex(root_index)
            self.ui.lineEdit.setText(str(dir_path))

    def _open_file_from_explorer(self, index):
        """Open a file from the file explorer."""
        file_path_str: str = self.file_system_model.filePath(index)
        file_path: Path = Path(file_path_str)
        
        # Don't open directories
        if file_path.is_dir():
            # Toggle expansion instead
            self.ui.fileExplorerView.setExpanded(index, not self.ui.fileExplorerView.isExpanded(index))
            return
        
        try:
            fileres: FileResource = FileResource.from_path(file_path)
            open_resource_editor(fileres)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Failed to Open File",
                f"Could not open file '{file_path_str}':\n{universal_simplify_exception(e)}",
            )

    def _update_completer_model(
        self,
        constants: list[ScriptConstant],
        functions: list[ScriptFunction],
    ):
        """Update completer model with enhanced information for IntelliSense-style hints."""
        # Create enriched completion strings with type hints
        completer_list: list[str] = []
        
        # Add functions with return type hints and parameter info
        for func in functions:
            return_type: str = getattr(func, 'return_type', 'void')
            # Try to get parameter info
            params: list[dict[str, Any]] = getattr(func, 'parameters', [])
            if params:
                param_str = ", ".join([f"{p.get('type', '')} {p.get('name', '')}" if isinstance(p, dict) else str(p) for p in params[:3]])
                if len(params) > 3:
                    param_str += "..."
                completer_list.append(f"{func.name}({param_str}) → {return_type}")
            else:
                completer_list.append(f"{func.name}(...) → {return_type}")
        
        # Add constants with type hints
        for const in constants:
            const_type: str = getattr(const, 'type', '')
            const_value: str = getattr(const, 'value', '')
            if const_type and const_value:
                completer_list.append(f"{const.name} ({const_type} = {const_value})")
            elif const_type:
                completer_list.append(f"{const.name} ({const_type})")
            elif const_value:
                completer_list.append(f"{const.name} = {const_value}")
            else:
                completer_list.append(const.name)
        
        # Also add keywords
        keywords: list[str] = [
            "void", "int", "float", "string", "object", "vector", "location", "effect", "event",
            "if", "else", "for", "while", "do", "switch", "case", "default", "break", "continue",
            "return", "struct", "const", "include", "define"
        ]
        completer_list.extend(keywords)
        
        model = QStringListModel(completer_list)
        self.completer.setModel(model)
        
        # Store mapping for quick lookup
        self._completion_map.clear()
        for func in functions:
            self._completion_map[func.name] = func
            # Also map with parentheses for function calls
            self._completion_map[f"{func.name}("] = func
        for const in constants:
            self._completion_map[const.name] = const
    
    def _setup_enhanced_completer(self):
        """Set up enhanced auto-completion with better presentation."""
        # Set completer to show more items
        popup: QWidget | None = self.completer.popup()
        if popup is not None:
            popup.setMaximumHeight(300)
            popup.setAlternatingRowColors(True)
        
        # Connect to show documentation in tooltip when hovering over completions
        if hasattr(self.completer, 'highlighted'):
            assert self.completer.highlighted is not None, "Highlighted should not be None"
            self.completer.highlighted.connect(self._on_completion_highlighted)
    
    def _on_completion_highlighted(self, text: str):
        """Show documentation tooltip when hovering over completion items."""
        # This would show a tooltip with function/constant documentation
        # Implementation can be enhanced further if needed
        pass
    
    def _update_error_diagnostics(self):
        """Update error/warning indicators in the gutter based on compilation errors."""
        text: str = self.ui.codeEdit.toPlainText()
        if not text.strip():
            self._error_lines.clear()
            self._warning_lines.clear()
            self.ui.codeEdit.set_error_lines(self._error_lines)
            self.ui.codeEdit.set_warning_lines(self._warning_lines)
            return
        
        error_lines: set[int] = set()
        warning_lines: set[int] = set()
        
        try:
            # Try to parse the code to detect syntax errors
            lexer = NssLexer()
            library_lookup = None if self._filepath is None else [str(self._filepath.parent)]
            
            # Use None for errorlog - we'll catch exceptions instead
            parser = NssParser(
                functions=self.functions,
                constants=self.constants,
                library=self.library,
                library_lookup=library_lookup,
                errorlog=None,
            )
            
            try:
                parser.parser.parse(text, lexer=lexer.lexer)
            except Exception as parse_exc:
                # Extract line number from error message if possible
                error_msg = str(parse_exc)
                import re
                line_match = re.search(r'line (\d+)', error_msg, re.IGNORECASE)
                if line_match:
                    line_num = int(line_match.group(1))
                    error_lines.add(line_num)
                else:
                    # If we can't extract line number, mark current line
                    cursor = self.ui.codeEdit.textCursor()
                    error_lines.add(cursor.blockNumber() + 1)
                
                # Log the error
                RobustLogger().debug(f"Parse error: {parse_exc}")
        except Exception:
            # If parsing completely fails, try to find obvious syntax errors
            lines: list[str] = text.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # Check for common syntax issues
                if stripped.endswith(';') and not stripped.startswith('//'):
                    # Check for double semicolons
                    if ';;' in stripped:
                        warning_lines.add(i)
                # Check for missing semicolons on statements (heuristic)
                if stripped and not stripped.startswith('//') and not stripped.endswith((';', '{', '}', ':')):
                    # This is a warning, not an error
                    if any(keyword in stripped for keyword in ['if', 'while', 'for', 'return']):
                        # These might need semicolons depending on context
                        pass
        
        self._error_lines = error_lines
        self._warning_lines = warning_lines
        self.ui.codeEdit.set_error_lines(error_lines)
        self.ui.codeEdit.set_warning_lines(warning_lines)

    def _show_hover_documentation(self, e: QMouseEvent):
        """Show rich tooltip documentation on hover."""
        cursor: QTextCursor = self.ui.codeEdit.cursorForPosition(e.pos())
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word: str = cursor.selectedText()

        if word and word.strip():
            doc: str | None = self._get_documentation(word.strip())
            if doc and doc.strip():
                global_pos: QPoint = self.ui.codeEdit.mapToGlobal(e.pos())
                # Use rich text tooltip with proper formatting
                QToolTip.showText(global_pos, doc, self.ui.codeEdit, QRect(), 5000)
            else:
                QToolTip.hideText()
        else:
            QToolTip.hideText()

        # Call the original mouseMoveEvent properly
        QPlainTextEdit.mouseMoveEvent(self.ui.codeEdit, e)

    def _get_documentation(self, word: str) -> str | None:
        """Get the documentation for a word with rich formatting."""
        word_lower: str = word.lower().strip()
        
        # Get palette colors for theme-aware tooltips
        app: QApplication | None = QApplication.instance()
        if app is None:
            # Fallback colors if no application instance
            text_color = "#000000"
            highlight_color = "#0066CC"
            link_color = "#0066CC"
            base_color = "#FFFFFF"
            bright_text = "#666666"
            desc_color = "#333333"
        else:
            palette = app.palette()
            text_color = palette.color(palette.ColorRole.ToolTipText).name()
            highlight_color = palette.color(palette.ColorRole.Highlight).name()
            link_color = palette.color(palette.ColorRole.Link).name()
            base_color = palette.color(palette.ColorRole.ToolTipBase).name()
            # Use bright text for secondary elements if available
            bright_text = palette.color(palette.ColorRole.BrightText).name()
            # Use window text for descriptions
            desc_color = palette.color(palette.ColorRole.WindowText).name()
        
        # Search functions
        for func in self.functions:
            if func.name.lower() == word_lower:
                # Build rich documentation string with theme-aware colors
                doc_parts = [f"<b style='color: {highlight_color}; font-size: 14px;'>{func.name}</b>"]
                
                # Build signature
                signature_parts: list[str] = []
                if hasattr(func, 'return_type') and func.return_type is not None:
                    return_type: str = getattr(func, 'return_type', 'unknown')
                    signature_parts.append(f"<span style='color: {link_color};'>{return_type}</span>")
                signature_parts.append(f"<b style='color: {highlight_color};'>{func.name}</b>")
                
                # Add parameters if available
                params: list[str] = []
                if hasattr(func, 'parameters') and func.parameters is not None:
                    for param in func.parameters:
                        param_type: str = getattr(param, 'type', 'unknown')
                        param_name: str = getattr(param, 'name', 'unknown')
                        params.append(f"<span style='color: {bright_text};'>{param_name}</span>: <span style='color: {link_color};'>{param_type}</span>")
                    signature_parts.append(f"({', '.join(params)})")
                else:
                    signature_parts.append("()")
                
                doc_parts.append(" ".join(signature_parts))
                
                # Add description
                if hasattr(func, 'description') and func.description:
                    doc_parts.append(f"<p style='margin-top: 6px; color: {desc_color}; line-height: 1.4;'>{func.description}</p>")
                
                # Improved font styling with better readability
                return f"""<div style='font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif; font-size: 13px; line-height: 1.5; color: {text_color}; padding: 2px;'>""" + "<br>".join(doc_parts) + "</div>"

        # Search constants
        for const in self.constants:
            if const.name.lower() == word_lower:
                const_value: str = getattr(const, 'value', 'unknown')
                const_type: str = getattr(const, 'type', '')
                doc_parts: list[str] = [f"<b style='color: {highlight_color}; font-size: 14px;'>{const.name}</b>"]
                
                if const_type:
                    doc_parts.append(f"<span style='color: {link_color};'>({const_type})</span>")
                
                doc_parts.append(f"<br><span style='color: {bright_text};'>Value: {const_value}</span>")
                
                if hasattr(const, 'description') and const.description:
                    doc_parts.append(f"<p style='margin-top: 6px; color: {desc_color}; line-height: 1.4;'>{const.description}</p>")
                
                # Improved font styling with better readability
                return f"""<div style='font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif; font-size: 13px; line-height: 1.5; color: {text_color}; padding: 2px;'>""" + " ".join(doc_parts) + "</div>"

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
        
        # Save old bookmarks before loading new file
        if hasattr(self, '_resname') and self._resname:
            self._save_bookmarks()
        self._update_bookmark_visualization()

        if restype is ResourceType.NSS:
            # Try multiple encodings to properly decode the text
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = data.decode("windows-1252", errors="replace")
                except UnicodeDecodeError:
                    text = data.decode("latin-1", errors="replace")
            self.ui.codeEdit.setPlainText(text)
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
        
        # Load bookmarks for the new file
        self.load_bookmarks()
        # Update file explorer if path changed
        if self._filepath:
            self._setup_file_explorer()

    def _handle_exc_debug_mode(self, err_msg: str, e: Exception) -> bool:
        QMessageBox(QMessageBox.Icon.Critical, err_msg, str(universal_simplify_exception(e))).exec_()
        if is_debug_mode():
            raise e
        return True

    def _handle_user_ncs(self, data: bytes, resname: str) -> None:
        from toolset.gui.common.localization import translate as tr, trf
        box = QMessageBox(
            QMessageBox.Icon.Question,
            tr("Decompile or Download"),
            trf("Would you like to decompile this script, or download it from <a href='{url}'>Vanilla Source Repository</a>?", url=self.sourcerepo_url),
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        box.button(QMessageBox.StandardButton.Yes).setText(tr("Decompile"))
        box.button(QMessageBox.StandardButton.Ok).setText(tr("Download"))
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

        # Try multiple encodings
        try:
            return local_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return local_path.read_text(encoding="windows-1252")
            except UnicodeDecodeError:
                return local_path.read_text(encoding="latin-1", errors="replace")

    def build(self) -> tuple[bytes | bytearray, bytes]:
        if self._restype is not ResourceType.NCS:
            # Encode with proper error handling
            text = self.ui.codeEdit.toPlainText()
            try:
                return text.encode("utf-8"), b""
            except UnicodeEncodeError:
                try:
                    return text.encode("windows-1252", errors="replace"), b""
                except UnicodeEncodeError:
                    return text.encode("latin-1", errors="replace"), b""

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
                QMessageBox(QMessageBox.Icon.Critical, "Failed to compile", str(universal_simplify_exception(e))).exec()
            except OSError as e:
                QMessageBox(QMessageBox.Icon.Critical, "Failed to save file", str(universal_simplify_exception(e))).exec()

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
        ).exec()

    def show_auto_complete_menu(self):
        """Show the auto-complete menu."""
        self.completer.setCompletionPrefix(self.ui.codeEdit.text_under_cursor())
        if self.completer.completionCount() > 0:
            rect = self.ui.codeEdit.cursorRect()
            popup = self.completer.popup()
            assert popup is not None, "Popup should not be None"
            rect.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
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
        string: str = self.ui.constantSearchEdit.text()
        if not string or not string.strip():
            return
        lower_string: str = string.lower()
        for i in range(self.ui.constantList.count()):
            item = self.ui.constantList.item(i)
            if not item:
                continue
            item.setHidden(lower_string not in item.text().lower())

    def _update_outline(self):
        """Update the outline view with better error handling."""
        self.ui.outlineView.clear()
        text: str = self.ui.codeEdit.toPlainText()
        
        if not text.strip():
            return

        try:
            lexer = NssLexer()
            library_lookup: list[str] | None = None if self._filepath is None else [str(self._filepath.parent)]
            parser = NssParser(
                functions=self.functions,
                constants=self.constants,
                library=self.library,
                library_lookup=library_lookup,
                errorlog=None,
            )

            ast: CodeRoot = parser.parser.parse(text, lexer=lexer.lexer)
            self._populate_outline(ast)
            self.ui.outlineView.expandAll()
        except Exception as exc:
            # Silently fail - outline is not critical
            RobustLogger().debug(f"Failed to update outline: {exc}")

    def _populate_outline(self, ast: CodeRoot):
        """Populate outline view with symbols from AST."""
        # Clear existing items
        self.ui.outlineView.clear()
        
        # Sort objects by line number for better organization
        sorted_objects: Sequence[ScriptFunction | ScriptConstant | StructDefinition | GlobalVariableDeclaration | None] = sorted(ast.objects, key=lambda o: getattr(o, 'line_num', 0) if hasattr(o, 'line_num') else 0)  # type: ignore[arg-type]
        
        for obj in sorted_objects:
            if isinstance(obj, FunctionDefinition):
                item = QTreeWidgetItem(self.ui.outlineView)
                # Get return type if available
                return_type: str = getattr(obj, 'return_type', 'void')
                # Get parameter count
                param_count: int = len(getattr(obj, 'parameters', []))
                item.setText(0, f"🔷 {obj.identifier}({param_count}) → {return_type}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)
                item.setToolTip(0, f"Function: {obj.identifier}\nReturn type: {return_type}\nParameters: {param_count}")
                
                # Add parameters as children
                for param in getattr(obj, 'parameters', []):
                    param_item = QTreeWidgetItem(item)
                    param_type = getattr(param, 'type', 'unknown')
                    param_name = getattr(param, 'identifier', 'unknown')
                    param_item.setText(0, f"  📝 {param_name}: {param_type}")
                    param_item.setToolTip(0, f"Parameter: {param_name}\nType: {param_type}")

            elif isinstance(obj, StructDefinition):
                item = QTreeWidgetItem(self.ui.outlineView)
                member_count: int = len(getattr(obj, 'members', []))
                item.setText(0, f"📦 {obj.identifier} ({member_count} members)")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)
                item.setToolTip(0, f"Struct: {obj.identifier}\nMembers: {member_count}")

                # Add members as children
                for member in getattr(obj, 'members', []):
                    member_item = QTreeWidgetItem(item)
                    member_type: str = getattr(member, 'type', 'unknown')
                    member_name: str = getattr(member, 'identifier', 'unknown')
                    member_item.setText(0, f"  • {member_name}: {member_type}")
                    member_item.setToolTip(0, f"Member: {member_name}\nType: {member_type}")

            elif isinstance(obj, GlobalVariableDeclaration):
                item = QTreeWidgetItem(self.ui.outlineView)
                var_type: str = getattr(obj, 'type', 'unknown')
                item.setText(0, f"🌐 {obj.identifier}: {var_type}")
                item.setData(0, Qt.ItemDataRole.UserRole, obj)
                item.setToolTip(0, f"Global variable: {obj.identifier}\nType: {var_type}")
        
        # Expand all by default for better visibility
        self.ui.outlineView.expandAll()
        
        # Set column width to fit content
        self.ui.outlineView.resizeColumnToContents(0)

    def _setup_shortcuts(self):
        """Set up all keyboard shortcuts with VS Code-like behavior."""
        # File operations
        self.ui.actionNew.setShortcut(QKeySequence("Ctrl+N"))
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.setShortcut(QKeySequence("Ctrl+O"))
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.setShortcut(QKeySequence("Ctrl+S"))
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSave_As.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.ui.actionSave_As.triggered.connect(self.save_as)
        self.ui.actionSave_All.setShortcut(QKeySequence("Ctrl+K, S"))  # VS Code style
        self.ui.actionClose.setShortcut(QKeySequence("Ctrl+W"))
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionClose_All.setShortcut(QKeySequence("Ctrl+K, W"))
        self.ui.actionExit.setShortcut(QKeySequence("Ctrl+Q"))
        self.ui.actionExit.triggered.connect(self.close)
        
        # Compile
        self.ui.actionCompile.setShortcut(QKeySequence("F5"))  # Changed from Ctrl+Shift+B to F5 (VS Code style)
        self.ui.actionCompile.triggered.connect(self.compile_current_script)
        
        # Edit operations - VS Code style
        self.ui.actionUndo.setShortcut(QKeySequence("Ctrl+Z"))
        self.ui.actionUndo.triggered.connect(self.ui.codeEdit.undo)
        # VS Code uses Ctrl+Shift+Z for redo, but Ctrl+Y also works
        self.ui.actionRedo.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        self.ui.actionRedo.triggered.connect(self.ui.codeEdit.redo)
        # Also add Ctrl+Y as alternative
        redo_alt = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_alt.activated.connect(self.ui.codeEdit.redo)
        self.ui.actionCut.setShortcut(QKeySequence("Ctrl+X"))
        self.ui.actionCut.triggered.connect(lambda: self.ui.codeEdit.cut())
        self.ui.actionCopy.setShortcut(QKeySequence("Ctrl+C"))
        self.ui.actionCopy.triggered.connect(lambda: self.ui.codeEdit.copy())
        self.ui.actionPaste.setShortcut(QKeySequence("Ctrl+V"))
        self.ui.actionPaste.triggered.connect(lambda: self.ui.codeEdit.paste())
        
        # Find/Replace - Use inline widget instead of dialog
        self.ui.actionFind.setShortcut(QKeySequence("Ctrl+F"))
        self.ui.actionFind.triggered.connect(self._show_find)
        self.ui.actionReplace.setShortcut(QKeySequence("Ctrl+H"))
        self.ui.actionReplace.triggered.connect(self._show_replace)
        
        # Add F3 and Shift+F3 for find next/previous (VS Code style)
        find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        find_next_shortcut.activated.connect(self._on_find_next_requested)
        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
        find_prev_shortcut.activated.connect(self._on_find_previous_requested)
        self.ui.actionFind_in_Files.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.ui.actionFind_in_Files.triggered.connect(self._find_in_files)
        
        # Navigation
        self.ui.actionGo_to_Line.setShortcut(QKeySequence("Ctrl+G"))
        self.ui.actionGo_to_Line.triggered.connect(self.ui.codeEdit.go_to_line)
        
        # Code editing - VS Code style shortcuts
        self.ui.actionToggle_Comment.setShortcut(QKeySequence("Ctrl+/"))
        self.ui.actionToggle_Comment.triggered.connect(self.ui.codeEdit.toggle_comment)
        
        # Indent/Unindent - VS Code uses Tab/Shift+Tab when no selection, Ctrl+]/[ for selection
        self.ui.actionIndent.setShortcut(QKeySequence("Ctrl+]"))
        self.ui.actionIndent.triggered.connect(self._indent_selection)
        self.ui.actionUnindent.setShortcut(QKeySequence("Ctrl+["))
        self.ui.actionUnindent.triggered.connect(self._unindent_selection)
        
        # Add select next occurrence shortcut (Ctrl+D in VS Code - selects next occurrence of word)
        select_next_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        select_next_shortcut.activated.connect(self.ui.codeEdit.select_next_occurrence)
        
        # Add select all occurrences shortcut (Alt+F3 in VS Code alternative since Ctrl+Shift+L is used for line numbers)
        select_all_shortcut = QShortcut(QKeySequence("Alt+F3"), self)
        select_all_shortcut.activated.connect(self.ui.codeEdit.select_all_occurrences)
        
        # Add select line shortcut (Ctrl+L in VS Code)
        select_line_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        select_line_shortcut.activated.connect(self.ui.codeEdit.select_line)
        
        # Add duplicate line shortcut (Ctrl+Shift+D in VS Code alternative, or we can use Alt+Shift+Down)
        duplicate_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        duplicate_shortcut.activated.connect(self.ui.codeEdit.duplicate_line)
        
        # Code folding shortcuts
        fold_shortcut = QShortcut(QKeySequence("Ctrl+Shift+["), self)
        fold_shortcut.activated.connect(self.ui.codeEdit.fold_region)
        unfold_shortcut = QShortcut(QKeySequence("Ctrl+Shift+]"), self)
        unfold_shortcut.activated.connect(self.ui.codeEdit.unfold_region)
        fold_all_shortcut = QShortcut(QKeySequence("Ctrl+K, Ctrl+0"), self)
        fold_all_shortcut.activated.connect(self.ui.codeEdit.fold_all)
        unfold_all_shortcut = QShortcut(QKeySequence("Ctrl+K, Ctrl+J"), self)
        unfold_all_shortcut.activated.connect(self.ui.codeEdit.unfold_all)
        
        # Add delete line shortcut (Ctrl+Shift+K in VS Code)
        delete_line_shortcut = QShortcut(QKeySequence("Ctrl+Shift+K"), self)
        delete_line_shortcut.activated.connect(self._delete_line)
        
        # Add move line shortcuts (Alt+Up/Down in VS Code)
        move_line_up_shortcut = QShortcut(QKeySequence("Alt+Up"), self)
        move_line_up_shortcut.activated.connect(lambda: self.ui.codeEdit.move_line_up_or_down("up"))
        move_line_down_shortcut = QShortcut(QKeySequence("Alt+Down"), self)
        move_line_down_shortcut.activated.connect(lambda: self.ui.codeEdit.move_line_up_or_down("down"))
        
        # Add bookmark shortcuts (Ctrl+K, Ctrl+B/N/P in VS Code)
        toggle_bookmark_shortcut = QShortcut(QKeySequence("Ctrl+K, Ctrl+B"), self)
        toggle_bookmark_shortcut.activated.connect(self._toggle_bookmark_at_cursor)
        next_bookmark_shortcut = QShortcut(QKeySequence("Ctrl+K, Ctrl+N"), self)
        next_bookmark_shortcut.activated.connect(self._goto_next_bookmark)
        prev_bookmark_shortcut = QShortcut(QKeySequence("Ctrl+K, Ctrl+P"), self)
        prev_bookmark_shortcut.activated.connect(self._goto_previous_bookmark)
        
        # Add go to definition and find references shortcuts
        go_to_def_shortcut = QShortcut(QKeySequence("F12"), self)
        go_to_def_shortcut.activated.connect(self.go_to_definition)
        find_refs_shortcut = QShortcut(QKeySequence("Shift+F12"), self)
        find_refs_shortcut.activated.connect(self._find_all_references_at_cursor)
        
        # Add trigger suggest shortcut (Ctrl+Space in VS Code)
        trigger_suggest_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        trigger_suggest_shortcut.activated.connect(self.ui.codeEdit.show_auto_complete_menu)
        
        # Add go to line shortcut (already set but ensure it's correct)
        self.ui.actionGo_to_Line.setShortcut(QKeySequence("Ctrl+G"))
        
        # View operations
        self.ui.actionZoom_In.setShortcut(QKeySequence("Ctrl+="))
        self.ui.actionZoom_In.triggered.connect(lambda: self.ui.codeEdit.change_text_size(increase=True))
        self.ui.actionZoom_Out.setShortcut(QKeySequence("Ctrl+-"))
        self.ui.actionZoom_Out.triggered.connect(lambda: self.ui.codeEdit.change_text_size(increase=False))
        self.ui.actionReset_Zoom.setShortcut(QKeySequence("Ctrl+0"))
        self.ui.actionReset_Zoom.triggered.connect(self._reset_zoom)
        self.ui.actionToggle_Line_Numbers.setShortcut(QKeySequence("Ctrl+Shift+L"))
        self.ui.actionToggle_Line_Numbers.triggered.connect(self._toggle_line_numbers)
        self.ui.actionToggle_Wrap_Lines.setShortcut(QKeySequence("Alt+Z"))
        self.ui.actionToggle_Wrap_Lines.triggered.connect(self._toggle_word_wrap)
        
        # Minimap toggle (if action exists)
        if hasattr(self.ui, 'actionToggle_Minimap'):
            assert self.ui.actionToggle_Minimap is not None, "Toggle minimap action should not be None"
            self.ui.actionToggle_Minimap.setShortcut(QKeySequence("Ctrl+Shift+M"))
            self.ui.actionToggle_Minimap.triggered.connect(self._toggle_minimap)
        
        # Command Palette (VS Code Ctrl+Shift+P)
        self._command_palette = CommandPalette(self)
        self._setup_command_palette()
        command_palette_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        command_palette_shortcut.activated.connect(self._show_command_palette)
        
        # Quick Open (VS Code Ctrl+P) - for now just show command palette
        quick_open_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        quick_open_shortcut.activated.connect(self._show_command_palette)
        
        # Panel toggles
        self.ui.actionToggleFileExplorer.setShortcut(QKeySequence("Ctrl+B"))
        self.ui.actionToggleTerminal.setShortcut(QKeySequence("Ctrl+`"))
        self.ui.actionToggle_Output_Panel.setShortcut(QKeySequence("Ctrl+Shift+U"))  # VS Code uses Ctrl+Shift+U for output
        
        # Tools
        self.ui.actionFormat_Code.setShortcut(QKeySequence("Shift+Alt+F"))
        self.ui.actionFormat_Code.triggered.connect(self._format_code)
        self.ui.actionManage_Snippets.triggered.connect(self._manage_snippets)
        
        # Connect Analyze Code action if it exists
        if hasattr(self.ui, 'actionAnalyze_Code'):
            assert self.ui.actionAnalyze_Code is not None, "Analyze code action should not be None"
            self.ui.actionAnalyze_Code.triggered.connect(self._analyze_code)
        
        # Help
        self.ui.actionDocumentation.setShortcut(QKeySequence("F1"))
        self.ui.actionDocumentation.triggered.connect(self._show_documentation)
        self.ui.actionKeyboard_Shortcuts.setShortcut(QKeySequence("Ctrl+K, Ctrl+H"))
        self.ui.actionKeyboard_Shortcuts.triggered.connect(self._show_keyboard_shortcuts)
        if hasattr(self.ui, 'actionAbout'):
            assert self.ui.actionAbout is not None, "About action should not be None"
            self.ui.actionAbout.triggered.connect(self._show_about)
        if hasattr(self.ui, 'actionCheck_for_Updates'):
            assert self.ui.actionCheck_for_Updates is not None, "Check for updates action should not be None"
            self.ui.actionCheck_for_Updates.triggered.connect(self._check_for_updates)
        
        # Debug menu actions (placeholders for future implementation)
        if hasattr(self.ui, 'actionStart_Debugging'):
            assert self.ui.actionStart_Debugging is not None, "Start debugging action should not be None"
            self.ui.actionStart_Debugging.triggered.connect(self._start_debugging)
        if hasattr(self.ui, 'actionStop_Debugging'):
            assert self.ui.actionStop_Debugging is not None, "Stop debugging action should not be None"
            self.ui.actionStop_Debugging.triggered.connect(self._stop_debugging)
        if hasattr(self.ui, 'actionToggle_Breakpoint'):
            assert self.ui.actionToggle_Breakpoint is not None, "Toggle breakpoint action should not be None"
            self.ui.actionToggle_Breakpoint.triggered.connect(self._toggle_breakpoint)
        if hasattr(self.ui, 'actionClear_All_Breakpoints'):
            assert self.ui.actionClear_All_Breakpoints is not None, "Clear all breakpoints action should not be None"
            self.ui.actionClear_All_Breakpoints.triggered.connect(self._clear_all_breakpoints)
        
        # Game type toggle
        self.ui.actionK1.triggered.connect(lambda: self._on_game_changed(0))
        self.ui.actionTSL.triggered.connect(lambda: self._on_game_changed(1))

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for zooming."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.ui.codeEdit.change_text_size(increase=True)
            else:
                self.ui.codeEdit.change_text_size(increase=False)
        else:
            super().wheelEvent(event)
    
    def _setup_statusbar(self):
        """Set up status bar with cursor position and file info."""
        self.status_label = QLabel("Line 1, Column 1")
        self.ui.statusbar.addWidget(self.status_label)
        
        # Add encoding, line ending, and indentation info
        self.encoding_label = QLabel("UTF-8")
        self.line_ending_label = QLabel("LF")
        self.indent_label = QLabel("Spaces: 4")
        
        self.ui.statusbar.addPermanentWidget(self.indent_label)
        self.ui.statusbar.addPermanentWidget(self.line_ending_label)
        self.ui.statusbar.addPermanentWidget(self.encoding_label)
    
    def _setup_breadcrumbs(self):
        """Set up breadcrumbs navigation widget above the code editor."""
        from qtpy.QtWidgets import QVBoxLayout, QWidget
        
        # Create breadcrumbs widget
        self._breadcrumbs = BreadcrumbsWidget(self)
        self._breadcrumbs.item_clicked.connect(self._on_breadcrumb_clicked)
        
        # Insert breadcrumbs above the code editor in the splitter
        # We need to wrap the code editor without deleting it
        splitter = self.ui.mainSplitter
        code_edit_index = splitter.indexOf(self.ui.codeEdit)
        
        if code_edit_index >= 0:
            # Get the code editor widget (it's already in the splitter)
            code_editor = self.ui.codeEdit
            
            # Create a container widget
            code_editor_container = QWidget()
            editor_layout = QVBoxLayout(code_editor_container)
            editor_layout.setContentsMargins(0, 0, 0, 0)
            editor_layout.setSpacing(0)
            
            # Add breadcrumbs
            editor_layout.addWidget(self._breadcrumbs)
            
            # Add the code editor (will automatically remove from splitter)
            editor_layout.addWidget(code_editor)
            
            # Replace the code editor in splitter with the container
            # First, temporarily store sizes
            sizes = splitter.sizes()
            
            # Remove code editor from splitter (it's now in the container)
            # Insert container at the same position
            splitter.insertWidget(code_edit_index, code_editor_container)
            
            # Restore sizes
            if len(sizes) >= 2:
                splitter.setSizes(sizes)
            
            # Store reference
            self._code_editor_container = code_editor_container
        
        # Connect cursor position changes to update breadcrumbs
        self.ui.codeEdit.cursorPositionChanged.connect(self._update_breadcrumbs)
        
        # Initially clear breadcrumbs
        self._breadcrumbs.clear()
    
    def _update_breadcrumbs(self):
        """Update breadcrumbs based on current cursor position."""
        cursor = self.ui.codeEdit.textCursor()
        current_line = cursor.blockNumber() + 1
        
        # Try to find context (function, struct, etc.) from outline
        breadcrumb_path: list[str] = []
        
        # Get filename if available
        if self._filepath:
            breadcrumb_path.append(self._filepath.name)
        else:
            breadcrumb_path.append("Untitled")
        
        # Try to find current function/scope from outline
        text = self.ui.codeEdit.toPlainText()
        if text.strip():
            try:
                from pykotor.resource.formats.ncs.compiler.parser import NssParser
                from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
                
                lexer = NssLexer()
                library_lookup: list[str] | None = None if self._filepath is None else [str(self._filepath.parent)]
                parser = NssParser(
                    functions=self.functions,
                    constants=self.constants,
                    library=self.library,
                    library_lookup=library_lookup,
                    errorlog=None,
                )
                
                ast = parser.parser.parse(text, lexer=lexer.lexer)
                
                # Find function/struct containing current line
                for obj in ast.objects:
                    obj_line = getattr(obj, 'line_num', -1)
                    if obj_line > 0 and obj_line <= current_line:
                        if hasattr(obj, 'identifier'):
                            if isinstance(obj, FunctionDefinition):
                                breadcrumb_path.append(f"Function: {obj.identifier}")
                            elif hasattr(obj, 'members'):  # StructDefinition
                                breadcrumb_path.append(f"Struct: {obj.identifier}")
                            elif hasattr(obj, 'type'):  # GlobalVariableDeclaration
                                breadcrumb_path.append(f"Variable: {obj.identifier}")
            except Exception:
                # Silently fail - breadcrumbs are not critical
                pass
        
        self._breadcrumbs.set_path(breadcrumb_path)
    
    def _on_breadcrumb_clicked(self, segment: str):
        """Handle breadcrumb segment click - navigate to that context."""
        # If clicking on filename, do nothing (already there)
        # If clicking on function/struct, navigate to it
        if segment.startswith("Function: "):
            func_name = segment.replace("Function: ", "")
            self._navigate_to_symbol(func_name)
        elif segment.startswith("Struct: "):
            struct_name = segment.replace("Struct: ", "")
            self._navigate_to_symbol(struct_name)
        elif segment.startswith("Variable: "):
            var_name = segment.replace("Variable: ", "")
            self._navigate_to_symbol(var_name)
    
    def _navigate_to_symbol(self, symbol_name: str):
        """Navigate to a symbol (function, struct, variable) by name."""
        text = self.ui.codeEdit.toPlainText()
        lines = text.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Look for function definition
            if f"void {symbol_name}(" in line or f"int {symbol_name}(" in line or f"float {symbol_name}(" in line:
                self._goto_line(i)
                return
            # Look for struct definition
            if f"struct {symbol_name}" in line:
                self._goto_line(i)
                return
            # Look for variable declaration
            if f"{symbol_name}" in line and ("=" in line or ";" in line):
                # More specific check needed
                if any(keyword in line for keyword in ["int ", "float ", "string ", "object ", "void "]):
                    self._goto_line(i)
                    return
    
    def _update_status_bar(self):
        """Update status bar with current cursor position and selection info."""
        # Check if status bar is initialized (may be called during initialization)
        if not hasattr(self, 'status_label') or self.status_label is None:
            return
        
        cursor: QTextCursor = self.ui.codeEdit.textCursor()
        line: int = cursor.blockNumber() + 1
        col: int = cursor.columnNumber() + 1
        document: QTextDocument | None = self.ui.codeEdit.document()
        total_lines: int = 0 if document is None else document.blockCount()
        
        selection: str = cursor.selectedText()
        selected_count: int = len(selection) if selection else 0
        
        # Format like VS Code: "Ln 1, Col 1" or "Ln 1, Col 1 (5 selected)"
        if selected_count > 0:
            # Count lines in selection
            selection_lines: int = len(selection.split('\u2029'))  # Unicode paragraph separator
            if selection_lines > 1:
                self.status_label.setText(f"Ln {line}, Col {col} ({selected_count} chars in {selection_lines} lines) | {total_lines} lines")
            else:
                self.status_label.setText(f"Ln {line}, Col {col} ({selected_count} selected) | {total_lines} lines")
        else:
            self.status_label.setText(f"Ln {line}, Col {col} | {total_lines} lines")
        
        # Update indent info
        if hasattr(self, 'indent_label') and self.indent_label is not None:
            indent_type: str = "Spaces" if self.TAB_AS_SPACE else "Tabs"
            indent_size: str = str(self.TAB_SIZE) if self.TAB_AS_SPACE else "1"
            self.indent_label.setText(f"{indent_type}: {indent_size}")
    
    def _toggle_file_explorer(self):
        """Toggle file explorer dock visibility."""
        self.ui.fileExplorerDock.setVisible(not self.ui.fileExplorerDock.isVisible())
    
    def _toggle_terminal_panel(self):
        """Toggle terminal/bookmarks/snippets dock visibility."""
        is_visible: bool = self.ui.bookmarksDock.isVisible()
        self.ui.bookmarksDock.setVisible(not is_visible)
        self.ui.snippetsDock.setVisible(not is_visible)
    
    def _toggle_output_panel(self):
        """Toggle output panel visibility."""
        if self.ui.panelTabs.isVisible():
            # Hide panel if visible
            self.ui.mainSplitter.setSizes([999999, 0])
        else:
            # Show panel
            sizes: list[int] = self.ui.mainSplitter.sizes()
            if sizes[1] == 0:
                self.ui.mainSplitter.setSizes([sizes[0] - 200, 200])
            self.ui.panelTabs.setVisible(True)
    
    def _reset_zoom(self):
        """Reset editor font size to default."""
        default_font: QFont = QFont("Consolas" if sys.platform == "win32" else "Monaco", 12)
        self.ui.codeEdit.setFont(default_font)
    
    def _toggle_line_numbers(self):
        """Toggle line numbers visibility."""
        # Line numbers are always visible in CodeEditor, but we can toggle the width
        # This is a visual toggle - line numbers are always shown but can be made narrower
        current_width: int = self.ui.codeEdit.line_number_area_width()
        if current_width > 40:
            # Hide by making very narrow (but still functional)
            # Actually, we can't really hide them without modifying CodeEditor
            # So we'll just acknowledge the action
            pass
        # Line numbers are always visible in this implementation
    
    def _toggle_word_wrap(self):
        """Toggle word wrap mode."""
        current_mode: QPlainTextEdit.LineWrapMode = self.ui.codeEdit.lineWrapMode()
        if current_mode == QPlainTextEdit.LineWrapMode.NoWrap:
            self.ui.codeEdit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            self.ui.actionToggle_Wrap_Lines.setChecked(True)
            self._log_to_output("Word wrap: ON")
        else:
            self.ui.codeEdit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            self.ui.actionToggle_Wrap_Lines.setChecked(False)
            self._log_to_output("Word wrap: OFF")
    
    def _toggle_minimap(self):
        """Toggle minimap visibility (placeholder for future implementation)."""
        # Minimap is a complex feature that would require significant changes to CodeEditor
        # For now, we'll just acknowledge the action
        QMessageBox.information(
            self,
            "Minimap",
            "Minimap feature is planned for a future release.\n\n"
            "This will show a small overview of your code on the right side of the editor, "
            "similar to VS Code's minimap feature."
        )
    
    def _indent_selection(self):
        """Indent selected lines."""
        cursor: QTextCursor = self.ui.codeEdit.textCursor()
        if not cursor.hasSelection():
            # Just insert tab or spaces at cursor
            indent: str = " " * self.TAB_SIZE if self.TAB_AS_SPACE else "\t"
            cursor.insertText(indent)
            return
        
        start: int = cursor.selectionStart()
        end: int = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        
        indent = " " * self.TAB_SIZE if self.TAB_AS_SPACE else "\t"
        
        cursor.beginEditBlock()
        while cursor.position() <= end:
            cursor.insertText(indent)
            if not cursor.movePosition(QTextCursor.MoveOperation.NextBlock):
                break
            end += len(indent)
        cursor.endEditBlock()
    
    def _unindent_selection(self):
        """Unindent selected lines."""
        cursor: QTextCursor = self.ui.codeEdit.textCursor()
        if not cursor.hasSelection():
            # Just remove tab or spaces at start of line
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            block: QTextBlock = cursor.block()
            text: str = block.text()
            if text.startswith("\t"):
                cursor.deleteChar()
            elif text.startswith(" "):
                spaces_to_remove: int = min(self.TAB_SIZE, len(text) - len(text.lstrip()))
                for _ in range(spaces_to_remove):
                    if text.startswith(" "):
                        cursor.deleteChar()
            return
        
        start: int = cursor.selectionStart()
        end: int = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        
        cursor.beginEditBlock()
        while cursor.position() <= end:
            block = cursor.block()
            text = block.text()
            if text.startswith("\t"):
                cursor.deleteChar()
                end -= 1
            elif text.startswith(" "):
                spaces_to_remove = min(self.TAB_SIZE, len(text) - len(text.lstrip()))
                for _ in range(spaces_to_remove):
                    if text.startswith(" "):
                        cursor.deleteChar()
                        end -= 1
            if not cursor.movePosition(QTextCursor.MoveOperation.NextBlock):
                break
        cursor.endEditBlock()
    
    def _format_code(self):
        """Format code with proper indentation and spacing (VS Code style)."""
        text = self.ui.codeEdit.toPlainText()
        if not text.strip():
            return
        
        # Confirm before formatting
        reply: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "Format Code",
            "Format the entire document?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        lines: list[str] = text.split("\n")
        formatted_lines: list[str] = []
        indent_level: int = 0
        indent_str: str = " " * self.TAB_SIZE if self.TAB_AS_SPACE else "\t"
        
        # Save cursor position
        cursor: QTextCursor = self.ui.codeEdit.textCursor()
        old_line: int = cursor.blockNumber()
        old_column: int = cursor.columnNumber()
        
        for i, line in enumerate(lines):
            stripped: str = line.strip()
            
            # Handle comments - preserve them but adjust indentation
            if stripped.startswith("//"):
                if stripped:
                    formatted_lines.append(indent_str * indent_level + stripped)
                else:
                    formatted_lines.append("")
                continue
            
            # Handle preprocessor directives - no indentation
            if stripped.startswith("#"):
                formatted_lines.append(stripped)
                continue
            
            # Handle empty lines - preserve them
            if not stripped:
                formatted_lines.append("")
                continue
            
            # Decrease indent for closing braces (before the line)
            if stripped.startswith("}"):
                indent_level = max(0, indent_level - 1)
            
            # Add line with proper indentation
            formatted_lines.append(indent_str * indent_level + stripped)
            
            # Increase indent for opening braces (after the line)
            # Count braces in the line
            indent_level += stripped.count("{") - stripped.count("}")
            indent_level = max(0, indent_level)
        
        formatted_text = "\n".join(formatted_lines)
        
        # Apply formatting
        self.ui.codeEdit.setPlainText(formatted_text)
        
        # Restore cursor position
        if old_line < len(formatted_lines):
            document: QTextDocument | None = self.ui.codeEdit.document()
            assert document is not None, "Document should not be None"
            block: QTextBlock = document.findBlockByLineNumber(old_line)
            new_cursor: QTextCursor = QTextCursor(block)
            # Try to restore column position
            line_text: str = formatted_lines[old_line]
            new_column: int = min(old_column, len(line_text))
            new_cursor.setPosition(block.position() + new_column)
            self.ui.codeEdit.setTextCursor(new_cursor)
            self.ui.codeEdit.centerCursor()
        
        self._log_to_output("Code formatted successfully")
    
    def _manage_snippets(self):
        """Open snippet management dialog (uses existing functionality)."""
        # The snippet management is already available via the snippets panel
        # Just ensure it's visible
        self.ui.snippetsDock.setVisible(True)
        self.ui.snippetsDock.raise_()
    
    def _find_in_files(self):
        """Find text in files dialog."""
        search_text, ok = QInputDialog.getText(
            self,
            "Find in Files",
            "Search for:",
            text="",
        )
        if not ok or not search_text:
            return
        
        # Ask for directory to search
        search_dir = QFileDialog.getExistingDirectory(
            self,
            "Select directory to search",
            str(self._filepath.parent) if self._filepath else str(Path.home()),
        )
        if not search_dir:
            return
        
        # Clear previous results
        self.ui.findResultsTree.clear()
        self._find_results = []
        
        # Search files
        self._search_in_directory(Path(search_dir), search_text)
        
        # Show results
        self._populate_find_results()
        self.ui.panelTabs.setCurrentWidget(self.ui.findResultsTab)
    
    def _search_in_directory(
        self,   
        directory: Path,
        search_text: str,
        find_results: list[dict[str, Any]],
    ) -> None:
        """Recursively search for text in .nss files."""
        if not directory.exists() or not directory.is_dir():
            return
        
        # Limit to .nss files to avoid performance issues
        for file_path in directory.rglob("*.nss"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    if search_text.lower() in line.lower():
                        self._find_results.append({
                            "file": str(file_path),
                            "line": line_num,
                            "content": line.strip()[:100],  # Limit content length
                        })
            except Exception:
                continue
    
    def _populate_find_results(self):
        """Populate the find results tree."""
        self.ui.findResultsTree.clear()
        
        # Group by file
        files_dict: dict[str, list[dict[str, Any]]] = {}
        for result in self._find_results:
            file_path = result["file"]
            if file_path not in files_dict:
                files_dict[file_path] = []
            files_dict[file_path].append(result)
        
        # Create tree items
        for file_path, results in files_dict.items():
            file_item = QTreeWidgetItem(self.ui.findResultsTree)
            file_item.setText(0, Path(file_path).name)
            file_item.setText(1, str(len(results)))
            file_item.setData(0, Qt.ItemDataRole.UserRole, file_path)
            
            for result in results:
                result_item = QTreeWidgetItem(file_item)
                result_item.setText(0, f"Line {result['line']}")
                result_item.setText(1, str(result['line']))
                result_item.setText(2, result['content'])
                result_item.setData(0, Qt.ItemDataRole.UserRole, result)
        
        # Connect double-click to open file
        self.ui.findResultsTree.itemDoubleClicked.connect(self._open_find_result)
    
    def _open_find_result(self, item: QTreeWidgetItem, column: int):
        """Open file from find results."""
        result_data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(result_data, dict) and "file" in result_data and "line" in result_data:
            file_path = result_data["file"]
            # Open file and go to line
            fileres = FileResource.from_path(Path(file_path))
            result = open_resource_editor(fileres)
            # open_resource_editor returns a tuple, get the editor
            editor: NSSEditor | None = None
            if isinstance(result, tuple):
                _, editor = cast(tuple[None, NSSEditor], result)
            else:
                editor = result
            ui = None if editor is None else editor.ui
            if ui is not None:
                # Try to go to the line
                document = ui.codeEdit.document()
                if document:
                    block = document.findBlockByLineNumber(result_data["line"] - 1)
                    cursor = QTextCursor(block)
                    ui.codeEdit.setTextCursor(cursor)
                    ui.codeEdit.centerCursor()
    
    def _setup_find_replace_widget(self):
        """Set up the VS Code-style inline find/replace widget."""
        # Create find/replace widget
        self._find_replace_widget = FindReplaceWidget(self)
        
        # Set it as a floating widget that appears above the editor
        # We'll position it dynamically when shown
        self._find_replace_widget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._find_replace_widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        
        # Make it look more like VS Code
        self._find_replace_widget.setStyleSheet("""
            FindReplaceWidget {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid palette(mid);
                border-radius: 3px;
                background-color: palette(base);
            }
            QPushButton {
                padding: 4px 8px;
                border: 1px solid palette(mid);
                border-radius: 3px;
                min-width: 60px;
                background-color: palette(button);
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QPushButton:disabled {
                color: palette(disabledText);
            }
            QCheckBox {
                spacing: 4px;
            }
        """)
        
        # Connect signals
        self._find_replace_widget.find_requested.connect(self._on_find_requested)
        self._find_replace_widget.find_next_requested.connect(self._on_find_next_requested)
        self._find_replace_widget.find_previous_requested.connect(self._on_find_previous_requested)
        self._find_replace_widget.replace_requested.connect(self._on_replace_requested)
        self._find_replace_widget.replace_all_requested.connect(self._on_replace_all_requested)
        self._find_replace_widget.close_requested.connect(self._on_find_replace_close)
        
        # Connect text changes to auto-find
        self._find_replace_widget.find_input.textChanged.connect(self._on_find_text_changed_in_widget)
        
        # Initially hidden
        self._find_replace_widget.hide()
    
    def _on_find_text_changed_in_widget(self):
        """Handle find text changes in widget - auto-search."""
        if self._find_replace_widget and self._find_replace_widget.isVisible():
            find_text = self._find_replace_widget.find_input.text()
            if find_text:
                # Update stored text and flags
                self._current_find_text = find_text
                self._current_find_flags = {
                    "case_sensitive": self._find_replace_widget.case_sensitive_check.isChecked(),
                    "whole_words": self._find_replace_widget.whole_words_check.isChecked(),
                    "regex": self._find_replace_widget.regex_check.isChecked()
                }
                # Auto-find first occurrence
                self.ui.codeEdit.find_next(
                    find_text,
                    self._current_find_flags.get("case_sensitive", False),
                    self._current_find_flags.get("whole_words", False),
                    self._current_find_flags.get("regex", False),
                    backward=False
                )
    
    def _show_find(self):
        """Show the find widget with selected text if any."""
        cursor = self.ui.codeEdit.textCursor()
        selected_text = cursor.selectedText() if cursor.hasSelection() else ""
        # Replace paragraph separator with newline
        if selected_text:
            selected_text = selected_text.replace('\u2029', '\n')
            # If multiline, just use first line
            if '\n' in selected_text:
                selected_text = selected_text.split('\n')[0]
        
        if self._find_replace_widget:
            self._find_replace_widget.show_find(selected_text if selected_text else None)
            # Position widget above the editor
            self._position_find_widget()
            # Store current find text
            if selected_text:
                self._current_find_text = selected_text
                self._find_replace_widget.find_input.setText(selected_text)
                self._find_replace_widget.find_input.selectAll()
    
    def _show_replace(self):
        """Show the replace widget with selected text if any."""
        cursor = self.ui.codeEdit.textCursor()
        selected_text = cursor.selectedText() if cursor.hasSelection() else ""
        # Replace paragraph separator with newline
        if selected_text:
            selected_text = selected_text.replace('\u2029', '\n')
            # If multiline, just use first line
            if '\n' in selected_text:
                selected_text = selected_text.split('\n')[0]
        
        if self._find_replace_widget:
            self._find_replace_widget.show_replace(selected_text if selected_text else None)
            # Position widget above the editor
            self._position_find_widget()
            # Store current find text
            if selected_text:
                self._current_find_text = selected_text
                self._find_replace_widget.find_input.setText(selected_text)
                self._find_replace_widget.find_input.selectAll()
    
    def _position_find_widget(self):
        """Position the find widget above the code editor (VS Code style)."""
        if not self._find_replace_widget or not self._find_replace_widget.isVisible():
            return
        
        # Get the code editor's position in global coordinates
        editor_global_pos = self.ui.codeEdit.mapToGlobal(self.ui.codeEdit.rect().topLeft())
        # Position widget at the top-right of the editor (VS Code style)
        widget_width = self._find_replace_widget.width()
        editor_width = self.ui.codeEdit.width()
        x_pos = editor_global_pos.x() + editor_width - widget_width - 20  # 20px margin
        y_pos = editor_global_pos.y() + 10  # 10px from top
        self._find_replace_widget.move(x_pos, y_pos)
        self._find_replace_widget.raise_()
        self._find_replace_widget.activateWindow()
        self._find_replace_widget.setFocus()
    
    def _on_find_requested(self, text: str, case_sensitive: bool, whole_words: bool, regex: bool):
        """Handle find request from widget."""
        self._current_find_text = text
        self._current_find_flags = {
            "case_sensitive": case_sensitive,
            "whole_words": whole_words,
            "regex": regex
        }
        # The actual find is done in find_next/previous handlers
    
    def _on_find_next_requested(self):
        """Handle find next."""
        # Get text from widget if available, otherwise use stored text
        if self._find_replace_widget and self._find_replace_widget.isVisible():
            find_text = self._find_replace_widget.find_input.text()
            if find_text:
                self._current_find_text = find_text
                self._current_find_flags = {
                    "case_sensitive": self._find_replace_widget.case_sensitive_check.isChecked(),
                    "whole_words": self._find_replace_widget.whole_words_check.isChecked(),
                    "regex": self._find_replace_widget.regex_check.isChecked()
                }
        
        if self._current_find_text:
            found = self.ui.codeEdit.find_next(
                self._current_find_text,
                self._current_find_flags.get("case_sensitive", False),
                self._current_find_flags.get("whole_words", False),
                self._current_find_flags.get("regex", False),
                backward=False
            )
            if not found:
                # Don't show message box, just log to output
                self._log_to_output("Find: No more occurrences found")
    
    def _on_find_previous_requested(self):
        """Handle find previous."""
        if self._current_find_text and self._find_replace_widget:
            found = self.ui.codeEdit.find_previous(
                self._current_find_text,
                self._current_find_flags.get("case_sensitive", False),
                self._current_find_flags.get("whole_words", False),
                self._current_find_flags.get("regex", False)
            )
            if not found:
                QMessageBox.information(self, "Find", "No more occurrences found")
    
    def _on_replace_requested(
        self,
        find_text: str,
        replace_text: str,
        case_sensitive: bool,
        whole_words: bool,
        regex: bool,
    ):
        """Handle replace request."""
        cursor = self.ui.codeEdit.textCursor()
        # If there's already a selection that matches, replace it
        if cursor.hasSelection():
            selected = cursor.selectedText()
            # Check if selection matches (considering flags)
            matches = False
            if regex:
                import re
                try:
                    pattern = re.compile(find_text, re.IGNORECASE if not case_sensitive else 0)
                    matches = bool(pattern.match(selected))
                except Exception:
                    matches = False
            elif whole_words:
                matches = (selected == find_text) or (not case_sensitive and selected.lower() == find_text.lower())
            else:
                matches = (selected == find_text) or (not case_sensitive and selected.lower() == find_text.lower())
            
            if matches:
                cursor.insertText(replace_text)
                # Find next occurrence
                self.ui.codeEdit.find_next(find_text, case_sensitive, whole_words, regex, backward=False)
                return
        
        # Otherwise, find next occurrence first
        found = self.ui.codeEdit.find_next(find_text, case_sensitive, whole_words, regex, backward=False)
        if found:
            # Replace the selected text
            self.ui.codeEdit.replace_current(find_text, replace_text)
            # Find next occurrence
            self.ui.codeEdit.find_next(find_text, case_sensitive, whole_words, regex, backward=False)
        else:
            self._log_to_output("Replace: No occurrences found to replace")
    
    def _on_replace_all_requested(
        self,
        find_text: str,
        replace_text: str,
        case_sensitive: bool,
        whole_words: bool,
        regex: bool,
    ):
        """Handle replace all request."""
        # Confirm before replacing all
        reply = QMessageBox.question(
            self,
            "Replace All",
            f"Replace all occurrences of '{find_text}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            count = self.ui.codeEdit.replace_all_occurrences(find_text, replace_text, case_sensitive, whole_words, regex)
            self._log_to_output(f"Replace All: Replaced {count} occurrence(s)")
            QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s)")
    
    def _on_find_replace_close(self):
        """Handle find/replace widget close."""
        # Return focus to editor
        self.ui.codeEdit.setFocus()
        # Clear selection highlight if any
        cursor = self.ui.codeEdit.textCursor()
        cursor.clearSelection()
        self.ui.codeEdit.setTextCursor(cursor)
    
    def _delete_line(self):
        """Delete current line(s) - VS Code Ctrl+Shift+K."""
        cursor = self.ui.codeEdit.textCursor()
        if cursor.hasSelection():
            # Delete selected lines
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        else:
            # Delete current line
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            # Include newline if not last line
            if not cursor.atEnd():
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self.ui.codeEdit.setTextCursor(cursor)
    
    def _analyze_code(self):
        """Analyze code for potential issues."""
        text = self.ui.codeEdit.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "Analyze Code", "No code to analyze.")
            return
        
        issues: list[str] = []
        lines: list[str] = text.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped: str = line.strip()
            # Check for common issues
            if stripped and not stripped.startswith('//'):
                # Check for missing semicolons (heuristic)
                if any(keyword in stripped for keyword in ['return', 'break', 'continue']):
                    if not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}'):
                        issues.append(f"Line {i}: Possible missing semicolon")
                # Check for empty if/while/for blocks
                if any(keyword in stripped for keyword in ['if', 'while', 'for']):
                    if stripped.endswith('{') and i < len(lines):
                        next_line = lines[i].strip() if i < len(lines) else ""
                        if next_line == '}':
                            issues.append(f"Line {i}: Empty block detected")
        
        if issues:
            message = "Code Analysis Results:\n\n" + "\n".join(issues[:20])  # Limit to 20 issues
            if len(issues) > 20:
                message += f"\n\n... and {len(issues) - 20} more issues"
            QMessageBox.information(self, "Code Analysis", message)
        else:
            QMessageBox.information(self, "Code Analysis", "No issues found!")
    
    def _show_documentation(self):
        """Show documentation."""
        QMessageBox.information(
            self,
            "Documentation",
            "NSS Script Editor Documentation\n\n"
            "This editor provides a VS Code-like experience for editing NSS scripts.\n\n"
            "Key Features:\n"
            "- Syntax highlighting\n"
            "- Auto-completion\n"
            "- Error diagnostics\n"
            "- Code formatting\n"
            "- Bookmarks and snippets\n"
            "- Find and replace\n"
            "- Outline view\n\n"
            "For more information, visit the PyKotor documentation."
        )
    
    def _show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
Keyboard Shortcuts:

File Operations:
  Ctrl+N          - New file
  Ctrl+O          - Open file
  Ctrl+S          - Save
  Ctrl+Shift+S    - Save As
  Ctrl+W          - Close
  Ctrl+Q          - Exit
  F5              - Compile

Edit Operations:
  Ctrl+Z          - Undo
  Ctrl+Shift+Z    - Redo
  Ctrl+X          - Cut
  Ctrl+C          - Copy
  Ctrl+V          - Paste
  Ctrl+F          - Find
  Ctrl+H          - Replace
  Ctrl+G          - Go to Line
  Ctrl+/          - Toggle Comment
  Ctrl+D          - Duplicate Line
  Ctrl+Shift+K    - Delete Line
  Alt+Up/Down     - Move Line
  Ctrl+]          - Indent
  Ctrl+[          - Unindent

View Operations:
  Ctrl+B          - Toggle File Explorer
  Ctrl+`          - Toggle Terminal Panel
  Ctrl+Shift+U    - Toggle Output Panel
  Ctrl+=          - Zoom In
  Ctrl+-          - Zoom Out
  Ctrl+0          - Reset Zoom
  Alt+Z           - Toggle Word Wrap

Code Operations:
  Shift+Alt+F     - Format Code
  Ctrl+Space      - Trigger Suggest
  F12             - Go to Definition
  Shift+F12       - Find All References
  Ctrl+K, Ctrl+B - Toggle Bookmark
  Ctrl+K, Ctrl+N  - Next Bookmark
  Ctrl+K, Ctrl+P  - Previous Bookmark
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About NSS Editor",
            "NSS Script Editor\n\n"
            "Part of Holocron Toolset\n"
            "A comprehensive editor for Knights of the Old Republic scripts.\n\n"
            "Features VS Code-like editing experience with syntax highlighting, "
            "auto-completion, error diagnostics, and more."
        )
    
    def _check_for_updates(self):
        """Check for updates."""
        QMessageBox.information(
            self,
            "Check for Updates",
            "Update checking is not yet implemented.\n\n"
            "Please check the PyKotor repository for updates."
        )
    
    def _start_debugging(self):
        """Start test run (dry-run testing with event simulation)."""
        try:
            # Get source code
            text = self.ui.codeEdit.toPlainText()
            if not text.strip():
                QMessageBox.warning(self, "Test Run", "Cannot test empty script.")
                return
            
            # Detect entry point
            entry_point = self._detect_entry_point(text)
            if entry_point == "unknown":
                QMessageBox.warning(
                    self,
                    "Test Run",
                    "Cannot detect entry point. Script must have either main() or StartingConditional() function."
                )
                return
            
            # Show test configuration dialog
            from qtpy.QtWidgets import QDialog
            config_dialog = TestConfigDialog(entry_point, self)
            if config_dialog.exec_() != QDialog.DialogCode.Accepted:
                return  # User cancelled
            
            test_config = config_dialog.get_test_config()
            
            # Try to compile
            from pykotor.common.misc import Game
            
            game = Game.K2 if self._is_tsl else Game.K1
            
            # Compile script
            try:
                ncs = ht_compile_script(text, self.library, self.functions, self.constants)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Compilation Error",
                    f"Cannot start test run: script has compilation errors.\n\n{universal_simplify_exception(e)}"
                )
                return
            
            # Create debugger/test runner
            from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter
            interpreter = Interpreter(ncs, game)
            
            # Set up mocks based on test configuration
            for func_name, mock_func in test_config["mocks"].items():
                try:
                    interpreter.set_mock(func_name, mock_func)
                except Exception as e:
                    # Mock may fail if function doesn't exist, log and continue
                    RobustLogger().debug(f"Failed to set mock for {func_name}: {e}")
            
            # Create debugger wrapper with pre-configured interpreter
            self._debugger = Debugger(ncs, game)
            
            # Set up debugger callbacks
            self._debugger.on_breakpoint = self._on_debugger_breakpoint
            self._debugger.on_step = self._on_debugger_step
            self._debugger.on_finished = self._on_debugger_finished
            self._debugger.on_error = self._on_debugger_error
            
            # Map breakpoints from source lines to instruction indices
            self._map_breakpoints_to_instructions()
            
            # Show test UI
            self._show_test_ui()
            
            # Start test run with configured interpreter (will pause at first instruction for step-through)
            self._debugger.start(interpreter)
            
            # Update UI
            if hasattr(self.ui, 'actionStart_Debugging'):
                self.ui.actionStart_Debugging.setEnabled(False)
            if hasattr(self.ui, 'actionStop_Debugging'):
                self.ui.actionStop_Debugging.setEnabled(True)
            if hasattr(self.ui, 'actionStep_Over'):
                self.ui.actionStep_Over.setEnabled(True)
            if hasattr(self.ui, 'actionStep_Into'):
                self.ui.actionStep_Into.setEnabled(True)
            if hasattr(self.ui, 'actionStep_Out'):
                self.ui.actionStep_Out.setEnabled(True)
            
            event_name = config_dialog.config_widget.event_combo.currentText()
            self._log_to_output(f"Test run started: {entry_point}() with event {event_name} (event number: {test_config['event_number']})")
            self._update_debug_visualization()
            self._update_debug_widgets()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test Run Error",
                f"Failed to start test run:\n\n{universal_simplify_exception(e)}"
            )
            RobustLogger().error("Failed to start test run", exc_info=True)
    
    def _stop_debugging(self):
        """Stop test run."""
        if self._debugger is None:
            return
        
        try:
            self._debugger.stop()
            self._debugger = None
            self._current_debug_line = None
            
            # Hide test UI
            self._hide_test_ui()
            
            # Update UI
            if hasattr(self.ui, 'actionStart_Debugging'):
                self.ui.actionStart_Debugging.setEnabled(True)
            if hasattr(self.ui, 'actionStop_Debugging'):
                self.ui.actionStop_Debugging.setEnabled(False)
            if hasattr(self.ui, 'actionStep_Over'):
                self.ui.actionStep_Over.setEnabled(False)
            if hasattr(self.ui, 'actionStep_Into'):
                self.ui.actionStep_Into.setEnabled(False)
            if hasattr(self.ui, 'actionStep_Out'):
                self.ui.actionStep_Out.setEnabled(False)
            
            self._log_to_output("Test run stopped")
            self._update_debug_visualization()
            
        except Exception as e:
            RobustLogger().error("Failed to stop test run", exc_info=True)
            QMessageBox.warning(self, "Test Run", f"Error stopping test run: {e}")
    
    def _toggle_breakpoint(self):
        """Toggle breakpoint at current line."""
        cursor: QTextCursor = self.ui.codeEdit.textCursor()
        line_number: int = cursor.blockNumber() + 1
        
        if line_number in self._breakpoint_lines:
            # Remove breakpoint
            self._breakpoint_lines.remove(line_number)
            self._log_to_output(f"Breakpoint removed at line {line_number}")
        else:
            # Add breakpoint
            self._breakpoint_lines.add(line_number)
            self._log_to_output(f"Breakpoint set at line {line_number}")
            
            # If debugger is running, update its breakpoints
            if self._debugger is not None:
                self._map_breakpoints_to_instructions()
        
        self._update_debug_visualization()
    
    def _clear_all_breakpoints(self):
        """Clear all breakpoints."""
        count = len(self._breakpoint_lines)
        self._breakpoint_lines.clear()
        
        if self._debugger is not None:
            self._debugger.clear_breakpoints()
        
        self._log_to_output(f"Cleared {count} breakpoint(s)")
        self._update_debug_visualization()
    
    def _map_breakpoints_to_instructions(self):
        """Map source line breakpoints to instruction indices.
        
        Uses the line_number field on NCSInstruction when available, otherwise falls back
        to a heuristic mapping.
        """
        if self._debugger is None or self._debugger._ncs is None:
            return
        
        # Clear existing breakpoints in debugger
        self._debugger.clear_breakpoints()
        
        # Build a mapping of line numbers to instruction indices
        # This uses the line_number field on instructions when available
        line_to_instructions: dict[int, list[int]] = {}
        for idx, instruction in enumerate(self._debugger._ncs.instructions):
            line_num = getattr(instruction, 'line_number', -1)
            if line_num >= 0:
                if line_num not in line_to_instructions:
                    line_to_instructions[line_num] = []
                line_to_instructions[line_num].append(idx)
        
        # Map breakpoints using the line number mapping
        for line_num in self._breakpoint_lines:
            if line_num in line_to_instructions:
                # Use the first instruction for this line
                instruction_index = line_to_instructions[line_num][0]
                self._debugger.add_breakpoint(instruction_index)
            else:
                # Fallback heuristic: assume roughly 1 instruction per line
                instruction_index = line_num - 1  # Convert to 0-indexed
                if 0 <= instruction_index < len(self._debugger._ncs.instructions):
                    self._debugger.add_breakpoint(instruction_index)
    
    def _on_debugger_breakpoint(self, instruction_index: int):
        """Handle breakpoint hit."""
        # Map instruction index back to source line using line_number field
        source_line = self._instruction_index_to_line(instruction_index)
        self._current_debug_line = source_line
        
        self._log_to_output(f"Breakpoint hit at instruction {instruction_index} (line {source_line})")
        self._update_debug_visualization()
        self._update_debug_widgets()
        
        # Scroll to breakpoint line
        self._goto_line(source_line)
    
    def _on_debugger_step(self, instruction_index: int):
        """Handle step completion."""
        # Map instruction index back to source line using line_number field
        source_line = self._instruction_index_to_line(instruction_index)
        self._current_debug_line = source_line
        
        self._log_to_output(f"Step completed at instruction {instruction_index} (line {source_line})")
        self._update_debug_visualization()
        self._update_debug_widgets()
        
        # Scroll to current line
        self._goto_line(source_line)
    
    def _instruction_index_to_line(self, instruction_index: int) -> int:
        """Map instruction index to source line number.
        
        Uses the line_number field on NCSInstruction when available,
        otherwise falls back to a heuristic.
        
        Args:
        ----
            instruction_index: int: Instruction index to map
            
        Returns:
        -------
            int: Source line number (1-indexed)
        """
        if self._debugger is None or self._debugger._ncs is None:
            return instruction_index + 1
        
        if 0 <= instruction_index < len(self._debugger._ncs.instructions):
            instruction = self._debugger._ncs.instructions[instruction_index]
            line_num = getattr(instruction, 'line_number', -1)
            if line_num >= 0:
                return line_num
        
        # Fallback heuristic: assume roughly 1 instruction per line
        return instruction_index + 1
    
    def _on_debugger_finished(self):
        """Handle debugger finished."""
        self._current_debug_line = None
        self._log_to_output("Debugging session finished")
        self._update_debug_visualization()
        
        # Re-enable start debugging
        if hasattr(self.ui, 'actionStart_Debugging'):
            self.ui.actionStart_Debugging.setEnabled(True)
        if hasattr(self.ui, 'actionStop_Debugging'):
            self.ui.actionStop_Debugging.setEnabled(False)
        if hasattr(self.ui, 'actionStep_Over'):
            self.ui.actionStep_Over.setEnabled(False)
        if hasattr(self.ui, 'actionStep_Into'):
            self.ui.actionStep_Into.setEnabled(False)
        if hasattr(self.ui, 'actionStep_Out'):
            self.ui.actionStep_Out.setEnabled(False)
    
    def _on_debugger_error(self, error: Exception):
        """Handle debugger error."""
        self._log_to_output(f"Debugger error: {universal_simplify_exception(error)}")
        QMessageBox.critical(
            self,
            "Debugger Error",
            f"An error occurred during debugging:\n\n{universal_simplify_exception(error)}"
        )
        self._stop_debugging()
    
    def _update_debug_visualization(self):
        """Update visual indicators for debugging (breakpoints, current line)."""
        # Update code editor with breakpoint and current line indicators
        assert self.ui.codeEdit is not None, "Code editor should not be None"
        self.ui.codeEdit.set_breakpoint_lines(self._breakpoint_lines)
        self.ui.codeEdit.set_current_debug_line(self._current_debug_line)
        
        # Trigger repaint
        self.ui.codeEdit.update()
    
    def _update_debug_widgets(self):
        """Update debug UI widgets with current debugger state."""
        if self._debugger is None:
            # Clear all widgets
            self._debug_variables_widget.clear()
            self._debug_callstack_widget.clear()
            # Don't clear watch widget - preserve watch expressions
            return
        
        # Update variables
        variables = self._debugger.get_variables()
        self._debug_variables_widget.update_variables(variables)
        
        # Update call stack
        call_stack = self._debugger.call_stack
        self._debug_callstack_widget.update_call_stack(call_stack)
        
        # Update watch expressions
        watch_expressions = self._debug_watch_widget.get_watch_expressions()
        watch_values = {}
        for expr in watch_expressions:
            try:
                value = self._debugger.evaluate_watch(expr)
                watch_values[expr] = str(value)
            except Exception:
                watch_values[expr] = "<error>"
        self._debug_watch_widget.update_watch_values(watch_values)
    
    def _step_over(self):
        """Step over current instruction."""
        if self._debugger is not None and self._debugger.state == DebuggerState.PAUSED:
            self._debugger.step_over()
    
    def _step_into(self):
        """Step into current instruction."""
        if self._debugger is not None and self._debugger.state == DebuggerState.PAUSED:
            self._debugger.step_into()
    
    def _step_out(self):
        """Step out of current function."""
        if self._debugger is not None and self._debugger.state == DebuggerState.PAUSED:
            self._debugger.step_out()
    
    def _continue_debugging(self):
        """Continue debugging execution."""
        if self._debugger is not None and self._debugger.state == DebuggerState.PAUSED:
            self._debugger.resume()
    
    def _toggle_bookmark_at_cursor(self):
        """Toggle bookmark at current cursor line."""
        cursor = self.ui.codeEdit.textCursor()
        line_number = cursor.blockNumber() + 1
        
        if self._has_bookmark_at_line(line_number):
            self._remove_bookmark_at_line(line_number)
        else:
            self.add_bookmark()
    
    def _find_all_references_at_cursor(self):
        """Find all references to the symbol at cursor."""
        cursor = self.ui.codeEdit.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip()
        if word:
            self._find_all_references(word)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    editor = NSSEditor()
    editor.show()
    sys.exit(app.exec())
