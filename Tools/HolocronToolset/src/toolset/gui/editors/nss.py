from __future__ import annotations

import json
import os

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from qtpy.QtCore import QDir, QEvent, QSettings, QSize, Qt
from qtpy.QtWidgets import (
    QApplication,
    QFileSystemModel,
    QInputDialog,
    QMenu,
    QPlainTextEdit,
    QSplitterHandle,
)

#from toolset.gui.dialogs.web_ide_selector import WebIDEManager
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.uic.qtpy.editors.nss import Ui_MainWindow
from utility.updater.github import download_github_file

if TYPE_CHECKING:
    from qtpy.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class NSSIDEFeatures:
    def __init__(self, editor: NSSEditor):
        self.editor = editor
        self.web_ide_manager = WebIDEManager(self.editor)
        self.settings = QSettings("PyKotor", "NSSEditor")

    def setup_ide_features(self):
        self._restore_editor_state()
        self._setup_code_folding()
        self._setup_advanced_search()
        self._setup_minimap()
        self.restore_ui_state()

    def _setup_code_folding(self):
        pass  # Implement code folding if available in your QPlainTextEdit

    def _setup_advanced_search(self):
        self.editor.ui.searchBar.textChanged.connect(self.editor.search)
        self.editor.ui.searchLineEdit.returnPressed.connect(self.editor.search)
        self.editor.ui.replaceLineEdit.returnPressed.connect(self.editor.replace)

    def _setup_minimap(self):
        pass  # Implement minimap if available in your QPlainTextEdit

    def toggle_web_ide(self):
        if self.editor.current_editor == self.editor.ui.nativeEditor:
            self._switch_to_web_ide()
        else:
            self._switch_to_native_ide()
        self._save_editor_state()

    def _switch_to_web_ide(self):
        content = self.editor.ui.nativeEditor.toPlainText()
        self.editor.ui.webEditor.load(self.web_ide_manager.get_selected_ide_url())
        self.editor.ui.editorStack.setCurrentWidget(self.editor.ui.webEditor)
        self.editor.current_editor = self.editor.ui.webEditor
        self.editor.ui.webEditor.page().runJavaScript(f"editor.setValue(`{content}`);")
        self.editor.ui.toggleEditorButton.setText("Switch to Native Editor")
        self.settings.setValue("CurrentEditor", "web")

    def _switch_to_native_ide(self):
        content = self.editor.ui.webEditor.get_content()
        self.editor.ui.editorStack.setCurrentWidget(self.editor.ui.nativeEditor)
        self.editor.current_editor = self.editor.ui.nativeEditor
        self.editor.ui.nativeEditor.setPlainText(content)
        self.editor.ui.toggleEditorButton.setText("Switch to Web Editor")
        self.settings.setValue("CurrentEditor", "native")

    def _save_editor_state(self):
        self.settings.setValue("EditorType", "web" if self.editor.current_editor == self.editor.ui.webEditor else "native")
        self.settings.setValue("EditorContent", self.editor.get_content())
        self.settings.setValue("EditorGeometry", self.editor.saveGeometry())
        self.settings.setValue("EditorState", self.editor.saveState())

    def _restore_editor_state(self):
        editor_type = self.settings.value("CurrentEditor", "native")
        content = self.settings.value("EditorContent", "")
        geometry = self.settings.value("EditorGeometry")
        state = self.settings.value("EditorState")

        if editor_type == "web":
            self._switch_to_web_ide()
        elif editor_type == "native":
            self._switch_to_native_ide()

        self.editor.set_content(content)

        if geometry:
            self.editor.restoreGeometry(geometry)
        if state:
            self.editor.restoreState(state)

    def update_ui_state(self):
        self.settings.setValue("MainSplitterState", self.editor.ui.mainSplitter.saveState())
        self.settings.setValue("RightSplitterState", self.editor.ui.rightSplitter.saveState())
        self.settings.setValue("FileExplorerVisible", int(self.editor.ui.fileExplorerTabs.isVisible()))

    def restore_ui_state(self):
        main_splitter_state = self.settings.value("MainSplitterState", type=bytes)
        right_splitter_state = self.settings.value("RightSplitterState", type=bytes)
        file_explorer_visible = self.settings.value("FileExplorerVisible", True, type=bool)

        if main_splitter_state:
            self.editor.ui.mainSplitter.restoreState(main_splitter_state)
        if right_splitter_state:
            self.editor.ui.rightSplitter.restoreState(right_splitter_state)
        self.editor.ui.fileExplorerTabs.setVisible(bool(file_explorer_visible))

    def save_last_directory(self, directory: str):
        self.settings.setValue("LastExploredDirectory", directory)

    def update_file_explorer(self):
        last_dir = self.settings.value("LastExploredDirectory", QDir.homePath())
        model = QFileSystemModel(self.editor.ui.fileExplorerTree)
        model.setRootPath(last_dir)
        model.setNameFilters(["*.nss", "*.ncs"])
        model.setNameFilterDisables(False)
        self.editor.ui.fileExplorerTree.setModel(model)
        self.editor.ui.fileExplorerTree.setRootIndex(model.index(last_dir))
        self.editor.ui.fileExplorerTree.setSortingEnabled(True)
        self.editor.ui.fileExplorerTree.setDragEnabled(True)
        self.editor.ui.fileExplorerTree.setAcceptDrops(True)

    def toggle_file_explorer(self):
        if self.editor.ui.fileExplorerTabs.isVisible():
            self.editor.ui.fileExplorerTabs.hide()
        else:
            self.editor.ui.fileExplorerTabs.show()

    def update_editor_settings(self):
        font = self.settings.value("EditorFont", self.editor.font())
        font_size = self.settings.value("EditorFontSize", 12)
        self.editor.ui.nativeEditor.setFont(font)
        self.editor.ui.nativeEditor.setFontPointSize(font_size)

    def get_selected_ide_url(self):
        return self.web_ide_manager.get_selected_ide_url()

    def eventFilter(self, obj, event):
        if isinstance(obj, QSplitterHandle):
            if event.type() == QEvent.MouseMove:
                QApplication.setOverrideCursor(Qt.SizeHorCursor if obj.orientation() == Qt.Horizontal else Qt.SizeVerCursor)
            elif event.type() == QEvent.Leave:
                QApplication.restoreOverrideCursor()
        return False

    def save_snippets(self, snippets):
        self.settings.setValue("Snippets", json.dumps(snippets))

    def load_snippets(self):
        snippets_json = self.settings.value("Snippets", "[]")
        return json.loads(snippets_json)

    def update_snippets_list(self):
        self.editor.ui.snippetList.clear()
        self.editor.ui.snippetList.addItems(self.load_snippets())


class NSSEditor(Editor):
    def __init__(self, parent: Optional[QWidget] = None, installation: Optional[HTInstallation] = None):
        """Initialize the script editor window.

        This method sets up the UI, connections, and various features of the NSSEditor.

        Args:
            parent: QWidget | None: The parent widget
            installation: HTInstallation | None: The installation object
        """
        super().__init__(parent, "Script Editor", "script", installation)

        self.setWindowTitle("Script Editor")

        self._is_tsl: bool = installation.tsl if installation else False
        self.bookmarks: list[tuple[int, str]] = []

        self.owner: str = "KOTORCommunityPatches"
        self.repo: str = "Vanilla_KOTOR_Script_Source"
        self.sourcerepo_url: str = f"https://github.com/{self.owner}/{self.repo}"
        self.sourcerepo_forks_url: str = f"{self.sourcerepo_url}/forks"

        self._length: int = 0
        self._is_decompiled: bool = False
        self._global_settings: GlobalSettings = GlobalSettings()

        self._setup_ui()
        self.ide_features = NSSIDEFeatures(self)
        self.snippets = self.ide_features.load_snippets()
        self.new()

    def _setup_ui(self):
        self.ui = Ui_MainWindow()
        self._setup_ui_connections()
        self._setup_actions()
        self.ide_features.update_file_explorer()
        self.ide_features.setup_ide_features()

    def _setup_actions(self):
        # Connect file explorer
        self.ui.fileExplorerTree.activated.connect(self._update_file_explorer_path)
        self.ui.fileExplorerTree.doubleClicked.connect(self._open_file_from_explorer)

        # Connect "Download from Vanilla Source Repo" button
        self.actionDownloadVanillaSource = self.ui.actionDownloadVanillaSource
        self.actionDownloadVanillaSource.triggered.connect(self._download_from_vanilla_source)
        self.ui.menuFile.addAction(self.actionDownloadVanillaSource)

        self.ui.toggleEditorButton.clicked.connect(self.ide_features.toggle_web_ide)
        # Connect other actions
        self.ui.actionToggleFileExplorer.triggered.connect(self.ide_features.toggle_file_explorer)
        self.ui.actionZoom_In.triggered.connect(lambda: self.current_editor.change_text_size(increase=True))
        self.ui.actionZoom_Out.triggered.connect(lambda: self.current_editor.change_text_size(increase=False))
        self.ui.actionReset_Zoom.triggered.connect(self.reset_zoom)
        self.ui.mainSplitter.splitterMoved.connect(self.ide_features.update_ui_state)
        self.ui.rightSplitter.splitterMoved.connect(self.ide_features.update_ui_state)

        # Setup drag and drop for splitters
        for splitter in [self.ui.mainSplitter, self.ui.rightSplitter]:
            for i in range(splitter.count()):
                handle = splitter.handle(i)
                handle.installEventFilter(self)

        # Setup snippets
        self.ui.snippetAddButton.clicked.connect(self.add_snippet)
        self.ui.snippetDelButton.clicked.connect(self.remove_snippet)
        self.ui.snippetReloadButton.clicked.connect(self.ide_features.update_snippets_list)
        self.ui.snippetList.itemDoubleClicked.connect(self.insert_snippet)
        self.ui.snippetSearchEdit.textChanged.connect(self.filter_snippets)
        self.ide_features.update_snippets_list()

    def _update_file_explorer_path(self, index):
        path = self.ui.fileExplorerTree.model().filePath(index)
        self.ui.fileExplorerPath.setText(path)

    def _download_from_vanilla_source(self):
        self._load_remote_script("path/to/default/script.nss")  # Replace with actual default path

    def _update_current_editor(self):
        current_widget = self.ui.editorStack.currentWidget()
        if isinstance(current_widget, QPlainTextEdit):
            self.current_editor = current_widget
            self.current_editor.cursorPositionChanged.connect(self._update_status_bar)
        self._update_outline()

    def _update_status_bar(self):
        cursor = self.current_editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.statusBar().showMessage(f"Line: {line}, Column: {column}")

    def _update_outline(self):
        # Implement outline update logic here
        pass

    def closeEvent(self, event):
        self.ide_features.update_ui_state()
        super().closeEvent(event)

    def get_content(self) -> str:
        if isinstance(self.current_editor, QPlainTextEdit):
            return self.current_editor.toPlainText()
        elif isinstance(self.current_editor, QWebEngineView):
            return self.current_editor.page().runJavaScript("editor.getValue();", lambda result: result)

    def set_content(self, content: str):
        if isinstance(self.current_editor, QPlainTextEdit):
            self.current_editor.setPlainText(content)
        elif isinstance(self.current_editor, QWebEngineView):
            self.current_editor.set_content(content)

    def _open_file_from_explorer(self, index):
        file_path = self.ui.fileExplorerTree.model().filePath(index)
        if os.path.isfile(file_path):
            self.open_file(file_path)

    def open_file(self, file_path: str):
        content = Path(file_path).read_text(encoding="utf-8")
        self.set_content(content)
        file_name = os.path.basename(file_path)
        self.setWindowTitle(f"Script Editor - {file_name}")
        self.ide_features.save_last_directory(os.path.dirname(file_path))

    def _load_remote_script(self, selected_path: str):
        content = self._download_and_load_remote_script(selected_path)
        self.set_content(content)
        file_name = f"{Path(selected_path).name} (Vanilla)"
        self.setWindowTitle(f"Script Editor - {file_name}")
        self.statusBar().showMessage(f"Loaded script from {self.sourcerepo_url}/{selected_path}")

    def search(self):
        search_text = self.ui.searchBar.text()
        current_editor = self.ui.editorStack.currentWidget()
        if search_text:
            cursor = current_editor.document().find(search_text)
            if not cursor.isNull():
                current_editor.setTextCursor(cursor)
            else:
                self.statusBar().showMessage(f"'{search_text}' not found", 3000)

    def replace(self):
        search_text = self.ui.searchLineEdit.text()
        replace_text = self.ui.replaceLineEdit.text()
        if search_text and replace_text:
            cursor = self.current_editor.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == search_text:
                cursor.insertText(replace_text)
            else:
                cursor = self.current_editor.document().find(search_text)
                if not cursor.isNull():
                    cursor.insertText(replace_text)
                    self.current_editor.setTextCursor(cursor)
                else:
                    self.statusBar().showMessage(f"'{search_text}' not found", 3000)

    def _download_and_load_remote_script(self, selected_path: str) -> str:
        content = download_github_file(self.owner, self.repo, selected_path)
        return content.decode("utf-8")

    def new(self):
        self.set_content("")
        self.setWindowTitle("Script Editor - Untitled")

    def save_file(self, file_path: str):
        content = self.get_content()
        Path(file_path).write_text(content, encoding="utf-8")
        self.setWindowTitle(f"Script Editor - {os.path.basename(file_path)}")

    def set_syntax_highlighter(self, highlighter):
        highlighter(self.current_editor.document())

    def change_text_size(self, increase: bool = True):
        if isinstance(self.current_editor, QPlainTextEdit):
            self.current_editor.change_text_size(increase)
        elif isinstance(self.current_editor, QWebEngineView):
            self.current_editor.page().runJavaScript(f"document.body.style.fontSize = '{12 + (1 if increase else -1)}px'")

    def reset_zoom(self):
        default_font = self.font()
        self.current_editor.setFont(default_font)
        self.ide_features.settings.setValue("EditorFont", default_font.toString())
        self.ide_features.settings.setValue("EditorFontSize", default_font.pointSize())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(".nss"):
                self.open_file(file_path)
                break

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ide_features.update_ui_state()

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            distance = (event.pos() - self._drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self.ide_features.update_ui_state()

    def eventFilter(self, obj, event):
        if isinstance(obj, QSplitterHandle):
            if event.type() == QEvent.MouseMove:
                QApplication.setOverrideCursor(Qt.SizeHorCursor if obj.orientation() == Qt.Horizontal else Qt.SizeVerCursor)
            elif event.type() == QEvent.Leave:
                QApplication.restoreOverrideCursor()
            elif event.type() == QEvent.MouseButtonRelease:
                self.ide_features.update_ui_state()
        return super().eventFilter(obj, event)

    def sizeHint(self) -> QSize:
        return QSize(1280, 720)

    def minimumSizeHint(self) -> QSize:
        return QSize(800, 600)

    def add_snippet(self):
        name, ok = QInputDialog.getText(self, "Add Snippet", "Enter snippet name:")
        if ok and name:
            content = self.current_editor.textCursor().selectedText()
            self.snippets.append({"name": name, "content": content})
            self.ide_features.save_snippets(self.snippets)
            self.ide_features.update_snippets_list()

    def remove_snippet(self):
        current_item = self.ui.snippetList.currentItem()
        if current_item:
            index = self.ui.snippetList.row(current_item)
            del self.snippets[index]
            self.ide_features.save_snippets(self.snippets)
            self.ide_features.update_snippets_list()

    def insert_snippet(self, item):
        index = self.ui.snippetList.row(item)
        content = self.snippets[index]["content"]
        self.current_editor.textCursor().insertText(content)

    def filter_snippets(self, text):
        for i in range(self.ui.snippetList.count()):
            item = self.ui.snippetList.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Add Snippet", self.add_snippet)
        menu.exec(event.globalPos())


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    editor = NSSEditor()
    editor.show()
    sys.exit(app.exec())
