"""Native terminal widget for Holocron Toolset - VSCode-like experience."""

from __future__ import annotations

import os
import sys

from typing import TYPE_CHECKING

from qtpy.QtCore import QProcess, Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QColor, QFont, QKeyEvent, QPalette, QTextCursor  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    from qtpy.QtCore import QByteArray  # pyright: ignore[reportPrivateImportUsage]


class TerminalWidget(QWidget):
    """A native terminal widget that behaves like VSCode's integrated terminal."""

    command_executed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        """Initialize the terminal widget.

        Args:
        ----
            parent: QWidget | None: The parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        self._setup_process()
        self._command_history: list[str] = []
        self._history_index: int = -1
        self._current_command: str = ""
        self._prompt: str = self._get_prompt()
        self._output_buffer: str = ""

    def _setup_ui(self):
        """Set up the terminal UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create the text display
        self.terminal_output = QPlainTextEdit(self)
        self.terminal_output.setReadOnly(False)
        self.terminal_output.setUndoRedoEnabled(False)
        self.terminal_output.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.terminal_output.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.terminal_output.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Set terminal-like font
        font = QFont("Consolas" if sys.platform == "win32" else "Monaco", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal_output.setFont(font)

        # Apply terminal color scheme (VSCode dark theme style)
        self._apply_terminal_theme()

        # Override key press event (store original for chaining)
        self._original_key_press = self.terminal_output.keyPressEvent
        self.terminal_output.keyPressEvent = self._handle_key_press  # type: ignore[method-assign]

        layout.addWidget(self.terminal_output)
        self.setLayout(layout)

        # Show welcome message
        self._write_output("Holocron Toolset Terminal\n")
        self._write_output("Type 'help' for available commands.\n\n")
        self._write_prompt()

    def _apply_terminal_theme(self):
        """Apply VSCode-style dark terminal theme."""
        palette = self.terminal_output.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))  # Background
        palette.setColor(QPalette.ColorRole.Text, QColor(204, 204, 204))  # Foreground text
        self.terminal_output.setPalette(palette)

        self.terminal_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: none;
                padding: 8px;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 14px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _setup_process(self):
        """Set up the process for command execution."""
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)  # type: ignore[attr-defined]
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_process_finished)

    def _get_prompt(self) -> str:
        """Get the command prompt string."""
        cwd = os.getcwd()
        if sys.platform == "win32":
            return f"{cwd}> "
        return f"{cwd}$ "

    def _write_output(self, text: str):
        """Write text to the terminal output.

        Args:
        ----
            text: str: The text to write
        """
        # Move cursor to end before appending
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.terminal_output.setTextCursor(cursor)

        # Insert text with proper encoding handling
        try:
            # Handle different encoding scenarios
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            self.terminal_output.insertPlainText(text)
        except (UnicodeDecodeError, AttributeError):
            # Fallback to replace errors
            text_str = str(text)
            self.terminal_output.insertPlainText(text_str)

        # Ensure we scroll to the bottom
        self.terminal_output.ensureCursorVisible()

    def _write_prompt(self):
        """Write the command prompt."""
        self._prompt = self._get_prompt()
        self._write_output(self._prompt)
        self._mark_prompt_start()

    def _mark_prompt_start(self):
        """Mark the start position of user input."""
        self._prompt_start_pos = self.terminal_output.textCursor().position()

    def _get_current_command(self) -> str:
        """Get the current command text."""
        cursor = self.terminal_output.textCursor()
        cursor.setPosition(self._prompt_start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        return cursor.selectedText()

    def _clear_current_command(self):
        """Clear the current command line."""
        cursor = self.terminal_output.textCursor()
        cursor.setPosition(self._prompt_start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

    def _replace_current_command(self, text: str):
        """Replace the current command with new text."""
        self._clear_current_command()
        self.terminal_output.insertPlainText(text)

    def _handle_key_press(self, event: QKeyEvent):
        """Handle key press events in the terminal.

        Args:
        ----
            event: QKeyEvent: The key event
        """
        key = event.key()
        modifiers = event.modifiers()

        # Prevent editing before the prompt
        cursor_pos = self.terminal_output.textCursor().position()
        if cursor_pos < self._prompt_start_pos:
            if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Left, Qt.Key.Key_Delete):
                return
            # Move cursor to end if trying to type
            if not modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
                cursor = self.terminal_output.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.terminal_output.setTextCursor(cursor)

        # Handle Enter key - execute command
        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            command = self._get_current_command().strip()
            self._write_output("\n")

            if command:
                self._command_history.append(command)
                self._history_index = len(self._command_history)
                self._execute_command(command)
            else:
                self._write_prompt()
            return

        # Handle Up arrow - previous command
        elif key == Qt.Key.Key_Up:
            if self._command_history and self._history_index > 0:
                self._history_index -= 1
                self._replace_current_command(self._command_history[self._history_index])
            return

        # Handle Down arrow - next command
        elif key == Qt.Key.Key_Down:
            if self._command_history:
                if self._history_index < len(self._command_history) - 1:
                    self._history_index += 1
                    self._replace_current_command(self._command_history[self._history_index])
                elif self._history_index == len(self._command_history) - 1:
                    self._history_index = len(self._command_history)
                    self._clear_current_command()
            return

        # Handle Ctrl+C - cancel current command
        elif key == Qt.Key.Key_C and modifiers & Qt.KeyboardModifier.ControlModifier:
            if self.process.state() == QProcess.ProcessState.Running:
                self.process.kill()
                self._write_output("\n^C\n")
                self._write_prompt()
            else:
                self._write_output("^C\n")
                self._write_prompt()
            return

        # Handle Ctrl+L - clear screen
        elif key == Qt.Key.Key_L and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.clear()
            return

        # Handle Backspace - don't delete prompt
        elif key == Qt.Key.Key_Backspace:
            if cursor_pos <= self._prompt_start_pos:
                return

        # Allow default handling for other keys
        QPlainTextEdit.keyPressEvent(self.terminal_output, event)

    def _execute_command(self, command: str):
        """Execute a command in the terminal.

        Args:
        ----
            command: str: The command to execute
        """
        self.command_executed.emit(command)

        # Handle built-in commands
        if command == "clear" or command == "cls":
            self.clear()
            return
        elif command == "help":
            self._show_help()
            return
        elif command.startswith("cd "):
            self._change_directory(command[3:].strip())
            return

        # Execute external command
        if sys.platform == "win32":
            # Use PowerShell or cmd for Windows
            shell = os.environ.get('COMSPEC', 'cmd.exe')
            self.process.start(shell, ['/c', command])
        else:
            # Use bash for Unix-like systems
            self.process.start('/bin/bash', ['-c', command])

        if not self.process.waitForStarted(3000):
            self._write_output("Error: Failed to start process\n")
            self._write_prompt()

    def _handle_stdout(self):
        """Handle stdout from the process."""
        data: QByteArray = self.process.readAllStandardOutput()
        try:
            # Try UTF-8 first, then fall back to system encoding
            text = bytes(data).decode('utf-8', errors='replace')
        except (UnicodeDecodeError, AttributeError):
            try:
                text = bytes(data).decode(sys.getdefaultencoding(), errors='replace')
            except (UnicodeDecodeError, AttributeError):
                text = str(data)

        self._write_output(text)

    def _handle_stderr(self):
        """Handle stderr from the process."""
        data: QByteArray = self.process.readAllStandardError()
        try:
            # Try UTF-8 first, then fall back to system encoding
            text = bytes(data).decode('utf-8', errors='replace')
        except (UnicodeDecodeError, AttributeError):
            try:
                text = bytes(data).decode(sys.getdefaultencoding(), errors='replace')
            except (UnicodeDecodeError, AttributeError):
                text = str(data)

        # Write errors in red (ANSI color code simulation)
        self._write_output(text)

    def _handle_process_finished(self, exit_code: int, exit_status):
        """Handle process finishing.

        Args:
        ----
            exit_code: int: The process exit code
            exit_status: The exit status
        """
        if exit_code != 0:
            self._write_output(f"\nProcess exited with code {exit_code}\n")
        self._write_prompt()

    def _change_directory(self, path: str):
        """Change the working directory.

        Args:
        ----
            path: str: The path to change to
        """
        try:
            # Expand user home directory
            if path.startswith("~"):
                path = os.path.expanduser(path)

            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)

            # Normalize the path
            path = os.path.normpath(path)

            if os.path.isdir(path):
                os.chdir(path)
                self._write_output(f"Changed directory to: {path}\n")
            else:
                self._write_output(f"Error: Directory not found: {path}\n")
        except Exception as e:
            self._write_output(f"Error changing directory: {e}\n")

        self._write_prompt()

    def _show_help(self):
        """Show help information."""
        help_text = """
Available built-in commands:
  clear/cls  - Clear the terminal screen
  cd <path>  - Change the current directory
  help       - Show this help message
  
Keyboard shortcuts:
  Ctrl+C     - Cancel current command
  Ctrl+L     - Clear screen
  Up Arrow   - Previous command
  Down Arrow - Next command

You can also run any system command directly.
"""
        self._write_output(help_text)
        self._write_prompt()

    def clear(self):
        """Clear the terminal."""
        self.terminal_output.clear()
        self._write_output("Holocron Toolset Terminal\n\n")
        self._write_prompt()

    def write_message(self, message: str, color: str | None = None):
        """Write a message to the terminal.

        Args:
        ----
            message: str: The message to write
            color: str | None: Optional color name
        """
        self._write_output(f"\n{message}\n")

    def execute_command_silently(self, command: str):
        """Execute a command without showing it in the terminal.

        Args:
        ----
            command: str: The command to execute
        """
        self._execute_command(command)

