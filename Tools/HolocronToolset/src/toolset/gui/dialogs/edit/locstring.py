from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QDialog

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class LocalizedStringDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, locstring: LocalizedString):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.locstring import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.locstring import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.locstring import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.locstring import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.stringrefNoneButton.setToolTip("Override the TLK with a custom entry.")
        self.ui.stringrefNewButton.setToolTip("Create a new entry in the TLK.")
        self.setWindowTitle(f"{installation.talktable().language().name.title()} - {installation.name} - Localized String Editor")

        self.ui.stringrefSpin.valueChanged.connect(self.stringrefChanged)
        self.ui.stringrefNewButton.clicked.connect(self.newTlkString)
        self.ui.stringrefNoneButton.clicked.connect(self.noTlkString)
        self.ui.maleRadio.clicked.connect(self.substringChanged)
        self.ui.femaleRadio.clicked.connect(self.substringChanged)
        self.ui.languageSelect.currentIndexChanged.connect(self.substringChanged)
        self.ui.stringEdit.textChanged.connect(self.stringEdited)

        self._installation = installation
        self.locstring = LocalizedString.from_dict(locstring.to_dict())
        self.ui.stringrefSpin.setValue(locstring.stringref)

    def accept(self):
        if self.locstring.stringref != -1:
            tlk_path = CaseAwarePath(self._installation.path(), "dialog.tlk")
            tlk = read_tlk(tlk_path)
            if len(tlk) <= self.locstring.stringref:
                tlk.resize(self.locstring.stringref + 1)
            tlk.get(self.locstring.stringref).text = self.ui.stringEdit.toPlainText()
            write_tlk(tlk, tlk_path)
        super().accept()

    def reject(self):
        super().reject()

    def stringrefChanged(self, stringref: int):
        self.ui.substringFrame.setVisible(stringref == -1)
        self.locstring.stringref = stringref

        if stringref == -1:
            self._update_text()
        else:
            self.ui.stringEdit.setPlainText(self._installation.talktable().string(stringref))

    def newTlkString(self):
        self.ui.stringrefSpin.setValue(self._installation.talktable().size())

    def noTlkString(self):
        self.ui.stringrefSpin.setValue(-1)

    def substringChanged(self):
        self._update_text()

    def _update_text(self):
        language = Language(self.ui.languageSelect.currentIndex())
        gender = Gender(int(self.ui.femaleRadio.isChecked()))
        text = self.locstring.get(language, gender) or ""
        self.ui.stringEdit.setPlainText(text)

    def stringEdited(self):
        if self.locstring.stringref == -1:
            language = Language(self.ui.languageSelect.currentIndex())
            gender = Gender(int(self.ui.femaleRadio.isChecked()))
            self.locstring.set_data(language, gender, self.ui.stringEdit.toPlainText())
