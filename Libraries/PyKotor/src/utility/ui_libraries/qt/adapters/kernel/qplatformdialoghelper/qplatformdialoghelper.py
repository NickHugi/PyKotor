from __future__ import annotations

import os
import re
import sys

from abc import abstractmethod
from enum import Flag
from typing import TYPE_CHECKING

from qtpy.QtCore import (
    QObject,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QFont
from qtpy.QtWidgets import QFileDialog, QMessageBox, QStyle

if TYPE_CHECKING:
    from qtpy.QtCore import QUrl, Qt
    from typing_extensions import Self


class QPlatformDialogHelper(QObject):
    accept: Signal = Signal()
    reject: Signal = Signal()

    StyleHint = QStyle.StyleHint
    DialogCode = QFileDialog.DialogCode

    def __new__(cls, *args, **kwargs) -> Self:
        new_cls: type[Self] = cls
        if cls is QPlatformDialogHelper:
            if sys.platform in ("win32", "cygwin"):
                from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qwindowsdialoghelpers import QWindowsDialogHelper
                new_cls = QWindowsDialogHelper  # type: ignore[misc]
            elif sys.platform == "linux":
                from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qlinuxdialoghelpers import LinuxFileDialogHelper
                new_cls = LinuxFileDialogHelper  # type: ignore[misc]
            elif sys.platform == "darwin":
                from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qmacdialoghelpers import QMacDialogHelper
                new_cls = QMacDialogHelper  # type: ignore[misc]
            raise NotImplementedError(f"No dialog helper implemented for {sys.platform}")
        return super().__new__(new_cls)

    @abstractmethod
    def exec(self) -> DialogCode:
        ...

    @abstractmethod
    def show(self, window_flags: QObject, window_state: Qt.WindowState, parent: QObject | None):
        ...

    @abstractmethod
    def hide(self):
        ...

    def selectMimeTypeFilter(self, filter: str) -> None:
        """TODO: Platform specific implementation."""
    def selectedMimeTypeFilter(self) -> str:
        """TODO: Platform specific implementation."""

    def isSupportedUrl(self, url: QUrl) -> bool:
        return url.isLocalFile()

    def setOptions(self, options: QFileDialog.Option) -> None:
        self._private.options = options
    def testOption(self, option: QFileDialog.Option) -> bool:
        return self._private.options & option

    def defaultStyleHint(self) -> StyleHint:
        return self.StyleHint(0)

    def styleHint(self) -> StyleHint:
        return self.defaultStyleHint()


class QPlatformColorDialogHelper(QPlatformDialogHelper):
    currentColorChanged: Signal = Signal(QColor)

    @abstractmethod
    def setCurrentColor(self, color: QColor):
        ...

    @abstractmethod
    def currentColor(self) -> QColor:
        ...


class QPlatformFileDialogHelper(QPlatformDialogHelper if TYPE_CHECKING else QObject):
    """Abstract base class for platform-specific file dialog helpers.
    This class defines the interface for creating and managing file dialogs across different platforms.

    This is a massive TODO as it would be an enormous amount of work to implement this for all platforms.
    Therefore, this class is currently a stub and will be implemented in the future.
    """
    filterRegExp = r"^(.+)\s*\((.*)\)$"

    def __init__(self, options: int):
        super().__init__()
        self._options: int = options
        self._directory: str = ""
        self._selectedFiles: list[str] = []
        self._selectedNameFilter: str = ""
        self._selectedMimeTypeFilter: str = ""

    @staticmethod
    def cleanFilterList(filter: str) -> list[str]:
        """
        Mirror Qt's QPlatformFileDialogHelper::cleanFilterList behaviour.

        The incoming string can contain an optional human readable label followed by
        one or more glob patterns enclosed in parentheses, e.g. "Images (*.png *.jpg)".
        """

        if not filter:
            return []

        filter = filter.strip()
        match = re.match(QPlatformFileDialogHelper.filterRegExp, filter)
        if not match:
            # No parenthesised pattern list – treat the entire string as a pattern.
            return [filter]

        pattern_section: str = match.group(2).strip()
        if not pattern_section:
            return []

        # Patterns are separated by whitespace in Qt's implementation.
        return [pattern for pattern in pattern_section.split() if pattern]

    FileMode = QFileDialog.FileMode.AnyFile
    AcceptMode = QFileDialog.AcceptMode.AcceptOpen
    Option = QFileDialog.Option.ReadOnly & ~QFileDialog.Option.ReadOnly

    fileSelected = Signal(str)
    filesSelected = Signal(list)
    currentChanged = Signal(str)
    directoryEntered = Signal(str)
    filterSelected = Signal(str)

    def isSupportedUrl(self, url: QUrl) -> bool:
        return os.path.exists(url.toLocalFile())  # noqa: PTH110

    def setDirectory(self, directory: str) -> None:
        self._directory = directory

    def directory(self) -> str:
        return self._directory

    def selectFile(self, filename: QUrl) -> None:
        self._selectedFiles = [filename.toString()]

    def selectedFiles(self) -> list[str]:
        return self._selectedFiles

    def setFilter(self) -> None:
        pass

    def selectMimeTypeFilter(self, filter: str) -> None:  # noqa: A002
        self._selectedMimeTypeFilter = filter

    def selectedMimeTypeFilter(self) -> str:
        return self._selectedMimeTypeFilter

    def selectNameFilter(self, filter: str) -> None:  # noqa: A002
        self._selectedNameFilter = filter

    def selectedNameFilter(self) -> str:
        return self._selectedNameFilter


class QPlatformFontDialogHelper(QPlatformDialogHelper):
    currentFontChanged = Signal(QFont)

    @abstractmethod
    def setCurrentFont(self, font: QFont):
        ...

    @abstractmethod
    def currentFont(self) -> QFont:
        ...


class QPlatformMessageDialogHelper(QPlatformDialogHelper):
    """Abstract base class for platform-specific message dialog helpers.
    This class defines the interface for creating and managing message dialogs across different platforms.
    """

    StandardButton: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok
    StandardButtons = QMessageBox.StandardButton(0)

    class ButtonRole(Flag):
        """Enum defining the roles of buttons in a message dialog.
        These roles determine the semantic meaning and behavior of buttons.
        """
        InvalidRole = -1  # Invalid button role
        AcceptRole = 0    # Accepting or "OK" role
        RejectRole = 1    # Rejecting or "Cancel" role
        DestructiveRole = 2  # Destructive or dangerous action role
        ActionRole = 3    # Action button role
        HelpRole = 4      # Help button role
        YesRole = 5       # "Yes" button role
        NoRole = 6        # "No" button role
        ResetRole = 7     # Reset to default values role
        ApplyRole = 8     # Apply changes role

    class Icon(Flag):
        """Enum defining the standard icons that can be displayed in a message dialog."""
        NoIcon = 0        # No icon
        Information = 1   # Information icon
        Warning = 2       # Warning icon
        Critical = 3      # Critical or error icon
        Question = 4      # Question icon

    clickedButton = Signal(int)  # Signal emitted when a button is clicked, passing the button's ID

    @abstractmethod
    def setButtons(self, buttons: QMessageBox.StandardButton):
        """Set the standard buttons to be displayed in the dialog.

        :param buttons: A combination of StandardButtons flags
        """
        ...

    @abstractmethod
    def buttons(self) -> QMessageBox.StandardButton:
        """Get the current standard buttons set for the dialog.

        :return: The current StandardButtons flags
        """
        ...

    @abstractmethod
    def setButtonText(self, button: QMessageBox.StandardButton, text: str):
        """Set custom text for a standard button.

        :param button: The StandardButton to modify
        :param text: The new text for the button
        """
        ...

    @abstractmethod
    def buttonText(self, button: QMessageBox.StandardButton) -> str:
        """Get the current text of a standard button.

        :param button: The StandardButton to query
        :return: The current text of the button
        """
        ...

    @abstractmethod
    def setIcon(self, icon: Icon):
        """Set the icon to be displayed in the dialog.

        :param icon: The Icon enum value to set
        """
        ...

    @abstractmethod
    def icon(self) -> Icon:
        """Get the current icon set for the dialog.

        :return: The current Icon enum value
        """
        ...

    @abstractmethod
    def setText(self, text: str):
        """Set the main text of the message dialog.

        :param text: The main message text
        """
        ...

    @abstractmethod
    def text(self) -> str:
        """Get the current main text of the message dialog.

        :return: The current main message text
        """
        ...

    @abstractmethod
    def setInformativeText(self, text: str):
        """Set additional informative text for the dialog.

        :param text: The informative text to set
        """
        ...

    @abstractmethod
    def informativeText(self) -> str:
        """Get the current informative text of the dialog.

        :return: The current informative text
        """
        ...

    @abstractmethod
    def setDetailedText(self, text: str):
        """Set detailed text for the dialog, typically shown in an expandable section.

        :param text: The detailed text to set
        """
        ...

    @abstractmethod
    def detailedText(self) -> str:
        """Get the current detailed text of the dialog.

        :return: The current detailed text
        """
        ...
