from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import markdown

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.error_handling import universal_simplify_exception
from utility.system.os_helper import is_frozen

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


def get_wiki_path() -> Path:
    """Get the path to the wiki directory.
    
    Returns:
        Path to wiki directory, checking both frozen and development locations.
    """
    if is_frozen():
        # When frozen, wiki should be bundled in the same directory as the executable
        import sys
        exe_path = Path(sys.executable).parent
        wiki_path = exe_path / "wiki"
        if wiki_path.exists():
            return wiki_path
    
    # Development mode: check toolset/wiki first, then root wiki
    toolset_wiki = Path(__file__).parent.parent.parent.parent.parent / "wiki"
    if toolset_wiki.exists():
        return toolset_wiki
    
    root_wiki = Path(__file__).parent.parent.parent.parent.parent.parent / "wiki"
    if root_wiki.exists():
        return root_wiki
    
    # Fallback
    return Path("./wiki")


class EditorHelpDialog(QDialog):
    """Non-blocking dialog for displaying editor help documentation from wiki markdown files."""
    
    def __init__(self, parent: QWidget | None, wiki_filename: str):
        """Initialize the help dialog.
        
        Args:
            parent: Parent widget
            wiki_filename: Name of the markdown file in the wiki directory (e.g., "GFF-File-Format.md")
        """
        super().__init__(parent)
        from toolset.gui.common.localization import translate as tr, trf
        self.setWindowTitle(trf("Help - {filename}", filename=wiki_filename))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.resize(900, 700)
        
        # Setup UI
        layout = QVBoxLayout(self)
        self.text_browser = QTextBrowser(self)
        layout.addWidget(self.text_browser)
        
        # Set search paths for relative links
        wiki_path = get_wiki_path()
        self.text_browser.setSearchPaths([str(wiki_path)])
        
        # Load and display the markdown file
        self.load_wiki_file(wiki_filename)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
    
    def load_wiki_file(self, wiki_filename: str) -> None:
        """Load and render a markdown file from the wiki directory.
        
        Args:
            wiki_filename: Name of the markdown file (e.g., "GFF-File-Format.md")
        """
        wiki_path = get_wiki_path()
        file_path = wiki_path / wiki_filename
        
        if not file_path.exists():
            from toolset.gui.common.localization import translate as tr, trf
            error_html = f"""
            <html>
            <body>
            <h1>{tr("Help File Not Found")}</h1>
            <p>{trf("Could not find help file: <code>{filename}</code>", filename=wiki_filename)}</p>
            <p>{trf("Expected location: <code>{path}</code>", path=str(file_path))}</p>
            <p>{trf("Wiki path: <code>{path}</code>", path=str(wiki_path))}</p>
            </body>
            </html>
            """
            self.text_browser.setHtml(error_html)
            return
        
        try:
            text: str = decode_bytes_with_fallbacks(file_path.read_bytes())
            html: str = markdown.markdown(
                text,
                extensions=["tables", "fenced_code", "codehilite", "toc"]
            )
            self.text_browser.setHtml(html)
        except Exception as e:
            error_html = f"""
            <html>
            <body>
            <h1>Error Loading Help File</h1>
            <p>Could not load help file: <code>{wiki_filename}</code></p>
            <p>Error: {universal_simplify_exception(e)}</p>
            </body>
            </html>
            """
            self.text_browser.setHtml(error_html)

