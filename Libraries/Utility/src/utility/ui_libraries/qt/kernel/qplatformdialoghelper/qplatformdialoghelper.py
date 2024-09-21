from __future__ import annotations

import sys

from abc import ABC, abstractmethod
from enum import Flag
from typing import TYPE_CHECKING, Self

from qtpy.QtCore import QObject, Signal
from qtpy.QtGui import QColor, QFont
from qtpy.QtWidgets import QFileDialog as QFileDialog, QMessageBox, QStyle

if TYPE_CHECKING:
    from qtpy.QtCore import Qt


class QPlatformDialogHelper(QObject, ABC):
    accept: Signal = Signal()
    reject: Signal = Signal()

    StyleHint = QStyle.StyleHint
    DialogCode = QFileDialog.DialogCode

    def __new__(cls, *args, **kwargs) -> Self:
        new_cls: type[Self] = cls
        if cls is QPlatformDialogHelper:
            if sys.platform == ("win32", "cygwin"):
                from utility.ui_libraries.qt.kernel.qplatformdialoghelper.qwindowsdialoghelpers import QWindowsDialogHelper
                new_cls = QWindowsDialogHelper
            elif sys.platform == "linux":
                from utility.ui_libraries.qt.kernel.qplatformdialoghelper.qlinuxdialoghelpers import LinuxFileDialogHelper
                new_cls = LinuxFileDialogHelper
            elif sys.platform == "darwin":
                from utility.ui_libraries.qt.kernel.qplatformdialoghelper.qmacdialoghelpers import QMacDialogHelper
                new_cls = QMacDialogHelper
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


class QPlatformFileDialogHelper(QPlatformDialogHelper):
    FileMode = QFileDialog.FileMode
    AcceptMode = QFileDialog.AcceptMode
    Option = QFileDialog.Option

    Options = int

    fileSelected = Signal(str)
    filesSelected = Signal(list)
    currentChanged = Signal(str)
    directoryEntered = Signal(str)
    filterSelected = Signal(str)

    @abstractmethod
    def setDirectory(self, directory: str):
        ...

    @abstractmethod
    def directory(self) -> str:
        ...

    @abstractmethod
    def selectFile(self, filename: str):
        ...

    @abstractmethod
    def selectedFiles(self) -> list[str]:
        ...

    @abstractmethod
    def setFilter(self):
        ...

    @abstractmethod
    def selectNameFilter(self, filter: str):  # noqa: A002
        ...

    @abstractmethod
    def selectedNameFilter(self) -> str:
        ...

    @abstractmethod
    def selectMimeTypeFilter(self, filter: str):  # noqa: A002
        ...

    @abstractmethod
    def selectedMimeTypeFilter(self) -> str:
        ...

    @abstractmethod
    def defaultNameFilterString(self) -> str:
        ...

    @abstractmethod
    def isSupportedUrl(self, url: str) -> bool:
        ...


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

    StandardButton = QMessageBox.StandardButton
    StandardButtons = int

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
    def setButtons(self, buttons: StandardButtons):
        """Set the standard buttons to be displayed in the dialog.

        :param buttons: A combination of StandardButtons flags
        """
        ...

    @abstractmethod
    def buttons(self) -> StandardButtons:
        """Get the current standard buttons set for the dialog.

        :return: The current StandardButtons flags
        """
        ...

    @abstractmethod
    def setButtonText(self, button: StandardButton, text: str):
        """Set custom text for a standard button.

        :param button: The StandardButton to modify
        :param text: The new text for the button
        """
        ...

    @abstractmethod
    def buttonText(self, button: StandardButton) -> str:
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
