from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger
from qtpy import QtCore, QtWidgets
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QMessageBox

from utility.gui.base import UserCommunication

if TYPE_CHECKING:
    from qtpy import QtGui
    from qtpy.QtGui import QIcon, QPixmap
    from qtpy.QtWidgets import QStatusBar
    from typing_extensions import Self


class CustomQPushButton(QtWidgets.QPushButton):
    def __init__(self, enum_member: MessageBoxButton, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_member: MessageBoxButton = enum_member
        self.setProperty("standardButtonRole", enum_member.value)
        self.setText(enum_member.text())
        icon: QIcon = enum_member.icon()
        assert icon is not None
        self.setIcon(icon)

    def __repr__(self):
        return f"{self.enum_member!r}.as_qpushbutton()"

    def __eq__(self, other):
        if isinstance(other, CustomQPushButton):
            return self.enum_member == other.enum_member
        if isinstance(other, MessageBoxButton):
            return self.enum_member == other
        if isinstance(other, int):
            return int(self) == other
        if isinstance(other, QMessageBox.StandardButton):
            return int(self) == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.enum_member.value)

    def __int__(self) -> QMessageBox.StandardButton:
        return self.enum_member.value

    def as_standardbutton(self) -> QMessageBox.StandardButton:
        return self.enum_member.as_standardbutton()

    def as_messageboxbutton_enum(self) -> MessageBoxButton:
        return self.enum_member

    def as_int(self) -> int:
        return int(self)

    @classmethod
    def from_int(cls, value: int) -> Self:
        return cls(MessageBoxButton.from_int(value))

    @classmethod
    def from_standardbutton(cls, value: QMessageBox.StandardButton) -> Self:
        return cls(MessageBoxButton.from_standardbutton(value))

    @classmethod
    def from_messageboxbutton_enum(cls, value: MessageBoxButton) -> Self:
        return cls(value)

    def text(self) -> str:
        return self.enum_member.text()

    def icon(self) -> QIcon:
        return self.enum_member.icon()


class MessageBoxButton(IntEnum):
    NoButton = QMessageBox.StandardButton.NoButton  # 0
    Open = QMessageBox.StandardButton.Open  # 32
    Escape = QMessageBox.StandardButton.Escape  # 512
    Default = QMessageBox.StandardButton.Default  # 4096
    Ok = QMessageBox.StandardButton.Ok  # 1024
    Save = QMessageBox.StandardButton.Save  # 2048
    SaveAll = QMessageBox.StandardButton.SaveAll  # 8192
    Yes = QMessageBox.StandardButton.Yes  # 16384
    YesToAll = QMessageBox.StandardButton.YesToAll  # 32768
    No = QMessageBox.StandardButton.No  # 65536
    NoToAll = QMessageBox.StandardButton.NoToAll  # 131072
    Abort = QMessageBox.StandardButton.Abort  # 262144
    Retry = QMessageBox.StandardButton.Retry  # 524288
    Ignore = QMessageBox.StandardButton.Ignore  # 1048576
    Close = QMessageBox.StandardButton.Close  # 2097152
    Cancel = QMessageBox.StandardButton.Cancel  # 4194304
    Discard = QMessageBox.StandardButton.Discard  # 8388608
    Help = QMessageBox.StandardButton.Help  # 16777216
    Apply = QMessageBox.StandardButton.Apply  # 33554432
    Reset = QMessageBox.StandardButton.Reset  # 67108864
    RestoreDefaults = QMessageBox.StandardButton.RestoreDefaults  # 134217728
    LastButton = QMessageBox.StandardButton.LastButton  # 536870912
    YesAll = QMessageBox.StandardButton.YesAll  # 1073741824
    FlagMask = QMessageBox.StandardButton.FlagMask  # 1073741824
    NoAll = QMessageBox.StandardButton.NoAll  # 2147483648
    ButtonMask = QMessageBox.StandardButton.ButtonMask  # 4294967295  # A bitmask covering all values

    @classmethod
    def from_int(cls, value: int) -> MessageBoxButton:
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Cannot find QMessageBox.StandardButton with value '{value}'")

    def as_int(self) -> int:
        enum_button_map = {
            self.NoButton: 0,
            self.Default: 256,
            self.Escape: 512,
            self.Ok: 1024,
            self.Save: 2048,
            self.SaveAll: 4096,
            self.Open: 8192,
            self.Yes: 16384,
            self.YesToAll: 32768,
            self.No: 65536,
            self.NoToAll: 131072,
            self.Abort: 262144,
            self.Retry: 524288,
            self.Ignore: 1048576,
            self.Close: 2097152,
            self.Cancel: 4194304,
            self.Discard: 8388608,
            self.Help: 16777216,
            self.Apply: 33554432,
            self.Reset: 67108864,
            self.RestoreDefaults: 134217728,
            self.LastButton: 134217728,
            self.YesAll: 32768,
            self.NoAll: 131072,
            self.ButtonMask: -769  # A bitmask covering all values
        }
        return enum_button_map[self]

    def get(self) -> QMessageBox.StandardButton:
        """Returns the QMessageBox.StandardButton corresponding to the enum member."""
        standard_button_map = {
            0: QMessageBox.NoButton,
            256: QMessageBox.Default,
            512: QMessageBox.Escape,
            1024: QMessageBox.Ok,
            2048: QMessageBox.Save,
            4096: QMessageBox.SaveAll,
            8192: QMessageBox.Open,
            16384: QMessageBox.Yes,
            32768: QMessageBox.YesToAll,
            65536: QMessageBox.No,
            131072: QMessageBox.NoToAll,
            262144: QMessageBox.Abort,
            524288: QMessageBox.Retry,
            1048576: QMessageBox.Ignore,
            2097152: QMessageBox.Close,
            4194304: QMessageBox.Cancel,
            8388608: QMessageBox.Discard,
            16777216: QMessageBox.Help,
            33554432: QMessageBox.Apply,
            67108864: QMessageBox.Reset,
            134217728: QMessageBox.RestoreDefaults,
            -769: QMessageBox.ButtonMask  # A bitmask covering all values
        }
        return standard_button_map[self.value]


    def text(self) -> str:
        """Get the default text for a given MessageBoxButton."""
        button_texts: dict[MessageBoxButton, str] = {
            MessageBoxButton.NoButton: "No Button",
            MessageBoxButton.Ok: "OK",
            MessageBoxButton.Save: "Save",
            MessageBoxButton.SaveAll: "Save All",
            MessageBoxButton.Open: "Open",
            MessageBoxButton.Yes: "Yes",
            MessageBoxButton.YesToAll: "Yes to All",
            MessageBoxButton.No: "No",
            MessageBoxButton.NoToAll: "No to All",
            MessageBoxButton.Abort: "Abort",
            MessageBoxButton.Retry: "Retry",
            MessageBoxButton.Ignore: "Ignore",
            MessageBoxButton.Close: "Close",
            MessageBoxButton.Cancel: "Cancel",
            MessageBoxButton.Discard: "Discard",
            MessageBoxButton.Help: "Help",
            MessageBoxButton.Apply: "Apply",
            MessageBoxButton.Reset: "Reset",
            MessageBoxButton.RestoreDefaults: "Restore Defaults",
            MessageBoxButton.YesAll: "Yes All",
            MessageBoxButton.NoAll: "No All",
            MessageBoxButton.Default: "Default",
            MessageBoxButton.Escape: "Escape",
            MessageBoxButton.FlagMask: "Flag Mask",
            MessageBoxButton.ButtonMask: "Button Mask"
        }
        return button_texts.get(self.__class__(self.value), "Unknown Button")

    def is_real_button(self) -> bool:
        return (
            self is not MessageBoxButton.FlagMask
            and self is not MessageBoxButton.NoButton
            and self is not MessageBoxButton.ButtonMask
#            and self is not MessageBoxButton.FirstButton
            and self is not MessageBoxButton.LastButton
        )

    def as_qpushbutton(self) -> QtWidgets.QPushButton:
        """Convert the MessageBoxButton to a QPushButton."""
        if not self.is_real_button():
            raise ValueError(f"Not a real button: {self.text()} ({self.value})")
        return CustomQPushButton(self)

    @classmethod
    def from_qpushbutton(cls, qp_button: QtWidgets.QPushButton) -> Self:
        return cls(qp_button.property("standardButtonRole"))

    def as_standardbutton(self) -> QMessageBox.StandardButton:
        return self.value

    @classmethod
    def from_standardbutton(cls, button: QMessageBox.StandardButton) -> Self:
        for btn_enum in cls:
            if btn_enum.value == button:
                return btn_enum
        raise ValueError(f"Cannot find QMessageBox.StandardButton with value '{button}', do not pass multiple buttons.")

    @classmethod
    def standardbuttons_to_qpushbuttons(cls, buttons: QMessageBox.StandardButtons) -> list[QtWidgets.QPushButton]:
        """Convert QMessageBox.StandardButtons to a list of QPushButton."""
        qpushbuttons = []
        for button in cls:
            if not cls.is_real_button(button):
                RobustLogger().debug(f"Not a real button: {button.text()}")
                continue
            if buttons & QMessageBox.StandardButton(button.value):  # Ensure the bitmask is correctly applied
                RobustLogger().debug(f"Adding qpushbutton for '{button.text()}'")
                qpushbuttons.append(button.as_qpushbutton())
        print(f"Converted the following to standard buttons: {','.join(cls.from_qpushbutton(qb).text() for qb in qpushbuttons)}")
        return qpushbuttons

    def icon(self) -> QtGui.QIcon:
        """Get the default icon of a MessageBoxButton."""
        button_box = QMessageBox()
        button_box.addButton(self.get())
        return button_box.button(self.get()).icon()


class MultipleButtonsError(Exception):
    """Exception raised when multiple QMessageBox.StandardButtons are passed."""


ICON_MAP: dict[Any, QtWidgets.QStyle.StandardPixmap] = {
    QMessageBox.Information: QtWidgets.QStyle.SP_MessageBoxInformation,
    QMessageBox.Warning: QtWidgets.QStyle.SP_MessageBoxWarning,
    QMessageBox.Critical: QtWidgets.QStyle.SP_MessageBoxCritical,
    QMessageBox.Question: QtWidgets.QStyle.SP_MessageBoxQuestion,
}


class BetterMessageBox(QtWidgets.QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        *args,
        icon: QtWidgets.QStyle = QtWidgets.QStyle.SP_MessageBoxInformation,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.Ok,  # noqa: N803
        parent: QtWidgets.QWidget | QtWidgets.QMainWindow | None = None,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)

        self.setWindowTitle(title)
        self.icon: QtWidgets.QStyle.StandardPixmap = ICON_MAP.get(icon, icon)
        self.buttons: list[QtWidgets.QPushButton] = MessageBoxButton.standardbuttons_to_qpushbuttons(buttons)
        smb_default_button: QtWidgets.QPushButton = MessageBoxButton(defaultButton).as_qpushbutton()
        if smb_default_button not in self.buttons:
            self.buttons.append(smb_default_button)
        self.result_button: QMessageBox.StandardButton = MessageBoxButton(defaultButton).as_standardbutton()
        self.initUI(message.replace("<br>", "\n"))

    def initUI(self, message):
        layout = QtWidgets.QVBoxLayout(self)

        # Add icon
        icon_label = QtWidgets.QLabel(self)
        icon: QIcon = self.style().standardIcon(self.icon)
        self.setWindowIcon(icon)
        icon_pixmap: QPixmap = icon.pixmap(32, 32)  # Change the icon size to 32x32
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(QtCore.Qt.AlignLeft)
        layout.addWidget(icon_label)

        # Add spacing above the text
        layout.addSpacerItem(QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        # Add text label
        label = QtWidgets.QLabel(message, self)
        label.setWordWrap(True)  # Enable word wrap
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)

        # Add spacing below the text
        layout.addSpacerItem(QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        # Add buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)  # Add stretch to push buttons to the right
        self.addButtons(button_layout)
        button_layout.addStretch(1)  # Add stretch to push buttons to the left
        layout.addLayout(button_layout)

        self.adjustSizeToFitContent()
        self.applyStylesheet()

    def exec_(self):
        result = super().exec()
        for button in self.buttons:
            if button.isChecked():
                self.result_button = MessageBoxButton.from_qpushbutton(button).as_standardbutton()
        return self.result_button

    def addButtons(self, layout: QtWidgets.QHBoxLayout):
        """Add QPushButton instances to the layout and connect signals."""
        for button in self.buttons:
            s_button = button.property("standardButtonRole")
            e_button = MessageBoxButton(s_button)
            print(f"Adding button '{e_button.text()}'")
            layout.addWidget(button)
            button.clicked.connect(lambda *args, e_button=e_button: self.button_clicked(e_button))

    def button_clicked(self, e_button: MessageBoxButton):
        sButton: QMessageBox.StandardButton = e_button.as_standardbutton()
        print(f"User pressed button: {MessageBoxButton(sButton).text()}")
        self.result_button = sButton
        self.accept()  # Modify this as needed based on the button action

    def adjustSizeToFitContent(self):
        self.setMinimumSize(500, 300)  # Set the initial size.
        self.adjustSize()
        self.setMinimumSize(self.sizeHint())

    def applyStylesheet(self):
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                min-width: 80px;
                min-height: 30px;
                font-size: 14px;
            }
        """)


class QtUserCommunication(UserCommunication):
    widget: QtWidgets.QWidget | QtWidgets.QMainWindow | None = None

    def input(self, prompt: str) -> str:
        text, ok = QtWidgets.QInputDialog.getText(self.widget, "Input", prompt)
        return text if ok and text else ""

    def print(self, *args: str):
        BetterMessageBox("Print Message", "    ".join(args), parent=self.widget).exec()

    def messagebox(self, title: str, message: str):
        BetterMessageBox(title, message, parent=self.widget).exec()

    def askquestion(self, title: str, message: str) -> bool:
        response: QMessageBox.StandardButton = QMessageBox.question(
            self.widget,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
        )
        return response == QMessageBox.Yes

    def error(self, title: str, message: str):
        BetterMessageBox(title, message, icon=QMessageBox.Icon.Critical, parent=self.widget).exec()

    def update_response(
        self,
        text: str,
        color: str = "black",
        font_size: int = 14,
        font_family: str = "Comic Sans",
    ):
        if not isinstance(self.widget, QtWidgets.QMainWindow):
            return
        status_bar: QStatusBar | None = self.widget.statusBar()
        if status_bar is None:
            return
        if not hasattr(status_bar, "setText"):
            status_bar.showMessage(text)
        else:
            status_bar.setText(text)
        status_bar.setStyleSheet(f"color: {color}; font-size: {font_size}px; font-family: {font_family}; font-weight: bold;")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])


    buttons = QMessageBox.NoButton
    for button in MessageBoxButton:
        if not button.is_real_button():
            print(f"first test: Skipping nonreal button {button.text()}")
            continue
        print(f"first test: adding button {button.text()}")
        buttons |= button.get()
    result = QMessageBox(QMessageBox.Information, "Test title", "Test message", buttons).exec()
    print(f"first test: You pressed button '{MessageBoxButton(result).text()}'")



    some_window = QtWidgets.QMainWindow()
    comm = QtUserCommunication(some_window)
    comm.print(
        "This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. "
    )
    bmb = BetterMessageBox(
        "Test input dialog",
        (
            "this is a question I am asking you to get a result of the button press. Please choose one now."
            "Your result helps improve the overall utility of messagebox alternatives. This is a test of two newlines:\n\nthis text should be two lines lower.\n"
            "This is on a new line and a test of br newlines<br><br>this text should be two lines lower!"
        ),
        icon=QtWidgets.QStyle.SP_TrashIcon,
        buttons=QMessageBox.Ok | QMessageBox.Yes | QMessageBox.Cancel,
    )
    result = bmb.exec()

    # Retrieve the result button
    result_button = bmb.result_button
    if result_button == QMessageBox.Ok:
        comm.print("OK button pressed")
    elif result_button == QMessageBox.Yes:
        comm.print("Yes button pressed")
    elif result_button == QMessageBox.Cancel:
        comm.print("Cancel button pressed")
    else:
        comm.print(f"Unknown button pressed: '{result_button}'")
    test = comm.input("Input something")
    comm.messagebox("Your output was", test)
