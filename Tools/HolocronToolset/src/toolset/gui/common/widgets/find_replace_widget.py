"""VS Code-style inline find/replace widget for code editors."""

from __future__ import annotations

import qtpy
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from toolset.gui.common.localization import translate as tr

if qtpy.QT5:
    from qtpy.QtCore import QRegExp  # pyright: ignore[reportAttributeAccessIssue]
elif qtpy.QT6:
    from qtpy.QtCore import QRegularExpression  # pyright: ignore[reportAttributeAccessIssue]


class FindReplaceWidget(QWidget):
    """VS Code-style inline find/replace bar that appears above the editor."""

    find_requested = Signal(str, bool, bool, bool)  # text, case_sensitive, whole_words, regex
    replace_requested = Signal(str, str, bool, bool, bool)  # find, replace, case_sensitive, whole_words, regex
    replace_all_requested = Signal(str, str, bool, bool, bool)
    close_requested = Signal()
    find_next_requested = Signal()
    find_previous_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setup_ui()
        self.hide()

    def setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Find input
        find_label = QLabel(tr("Find:"))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText(tr("Find..."))
        self.find_input.setMinimumWidth(200)
        self.find_input.returnPressed.connect(self._on_find_next)
        self.find_input.textChanged.connect(self._on_find_text_changed)

        # Replace input (initially hidden)
        replace_label = QLabel(tr("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText(tr("Replace..."))
        self.replace_input.setMinimumWidth(200)
        self.replace_input.returnPressed.connect(self._on_replace_next)

        # Buttons
        self.prev_button = QPushButton("↑")
        self.prev_button.setToolTip(tr("Find Previous (Shift+F3)"))
        self.prev_button.setMaximumWidth(30)
        self.prev_button.clicked.connect(self._on_find_previous)

        self.next_button = QPushButton("↓")
        self.next_button.setToolTip(tr("Find Next (F3)"))
        self.next_button.setMaximumWidth(30)
        self.next_button.clicked.connect(self._on_find_next)

        self.replace_button = QPushButton(tr("Replace"))
        self.replace_button.clicked.connect(self._on_replace)
        self.replace_button.setEnabled(False)

        self.replace_all_button = QPushButton(tr("Replace All"))
        self.replace_all_button.clicked.connect(self._on_replace_all)
        self.replace_all_button.setEnabled(False)

        self.close_button = QPushButton("✕")
        self.close_button.setMaximumWidth(25)
        self.close_button.setToolTip(tr("Close (Escape)"))
        self.close_button.clicked.connect(self.hide)

        # Options
        self.case_sensitive_check = QCheckBox("Aa")
        self.case_sensitive_check.setToolTip(tr("Match Case"))
        self.case_sensitive_check.toggled.connect(self._on_options_changed)

        self.whole_words_check = QCheckBox("Ab")
        self.whole_words_check.setToolTip(tr("Match Whole Word"))
        self.whole_words_check.toggled.connect(self._on_options_changed)

        self.regex_check = QCheckBox(".*")
        self.regex_check.setToolTip(tr("Use Regular Expression"))
        self.regex_check.toggled.connect(self._on_options_changed)

        # Store replace label for show/hide
        self.replace_label = replace_label
        
        # Add to layout
        layout.addWidget(find_label)
        layout.addWidget(self.find_input)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        layout.addWidget(replace_label)
        layout.addWidget(self.replace_input)
        layout.addWidget(self.replace_button)
        layout.addWidget(self.replace_all_button)
        layout.addWidget(self.case_sensitive_check)
        layout.addWidget(self.whole_words_check)
        layout.addWidget(self.regex_check)
        layout.addWidget(self.close_button)
        
        # Initially hide replace components
        replace_label.hide()
        self.replace_input.hide()
        self.replace_button.hide()
        self.replace_all_button.hide()

        # Style
        self.setStyleSheet("""
            FindReplaceWidget {
                background-color: palette(window);
                border-bottom: 1px solid palette(mid);
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid palette(mid);
                border-radius: 3px;
            }
            QPushButton {
                padding: 4px 8px;
                border: 1px solid palette(mid);
                border-radius: 3px;
                min-width: 60px;
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

        self._show_replace = False

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.close_requested.emit()
        elif event.key() == Qt.Key.Key_F3:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._on_find_previous()
            else:
                self._on_find_next()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_H:
            self.toggle_replace()
        else:
            super().keyPressEvent(event)

    def show_find(self, text: str | None = None):
        """Show the find widget."""
        self._show_replace = False
        if hasattr(self, 'replace_label'):
            self.replace_label.hide()
        self.replace_input.hide()
        self.replace_button.hide()
        self.replace_all_button.hide()
        self.show()
        if text:
            self.find_input.setText(text)
            self.find_input.selectAll()
        else:
            # Try to get selected text from editor
            self.find_input.selectAll()
        self.find_input.setFocus()

    def show_replace(self, text: str | None = None):
        """Show the find and replace widget."""
        self._show_replace = True
        if hasattr(self, 'replace_label'):
            self.replace_label.show()
        self.replace_input.show()
        self.replace_button.show()
        self.replace_all_button.show()
        self.show()
        if text:
            self.find_input.setText(text)
            self.find_input.selectAll()
        else:
            self.find_input.selectAll()
        self.find_input.setFocus()

    def toggle_replace(self):
        """Toggle between find and replace modes."""
        if self._show_replace:
            self.show_find()
        else:
            self.show_replace()

    def _on_find_text_changed(self):
        """Handle find text changes."""
        has_text = bool(self.find_input.text())
        self.next_button.setEnabled(has_text)
        self.prev_button.setEnabled(has_text)
        self.replace_button.setEnabled(has_text)
        self.replace_all_button.setEnabled(has_text and bool(self.replace_input.text()))

        # Auto-search as user types
        if has_text:
            self._on_find_next()

    def _on_find_next(self):
        """Emit find next signal."""
        text = self.find_input.text()
        if text:
            self.find_requested.emit(
                text,
                self.case_sensitive_check.isChecked(),
                self.whole_words_check.isChecked(),
                self.regex_check.isChecked(),
            )
            self.find_next_requested.emit()

    def _on_find_previous(self):
        """Emit find previous signal."""
        text = self.find_input.text()
        if text:
            self.find_requested.emit(
                text,
                self.case_sensitive_check.isChecked(),
                self.whole_words_check.isChecked(),
                self.regex_check.isChecked(),
            )
            self.find_previous_requested.emit()

    def _on_replace(self):
        """Emit replace signal."""
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if find_text:
            self.replace_requested.emit(
                find_text,
                replace_text,
                self.case_sensitive_check.isChecked(),
                self.whole_words_check.isChecked(),
                self.regex_check.isChecked(),
            )

    def _on_replace_next(self):
        """Emit replace signal and then find next."""
        # First replace the current match
        self._on_replace()
        # Then find the next occurrence
        self._on_find_next()

    def _on_replace_all(self):
        """Emit replace all signal."""
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if find_text:
            self.replace_all_requested.emit(
                find_text,
                replace_text,
                self.case_sensitive_check.isChecked(),
                self.whole_words_check.isChecked(),
                self.regex_check.isChecked(),
            )

    def _on_options_changed(self):
        """Handle option checkbox changes."""
        if self.find_input.text():
            self._on_find_next()

