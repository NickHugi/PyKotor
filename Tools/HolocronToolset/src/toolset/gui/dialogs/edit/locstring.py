from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
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
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        from toolset.uic.qtpy.dialogs.locstring import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.stringrefNoneButton.setToolTip("Override the TLK with a custom entry.")
        self.ui.stringrefNewButton.setToolTip("Create a new entry in the TLK.")
        self.setWindowTitle(f"{installation.talktable().language().name.title()} - {installation.name} - Localized String Editor")

        self.ui.stringrefSpin.valueChanged.connect(self.stringref_changed)
        self.ui.stringrefNewButton.clicked.connect(self.new_tlk_string)
        self.ui.stringrefNoneButton.clicked.connect(self.no_tlk_string)
        self.ui.maleRadio.clicked.connect(self.substring_changed)
        self.ui.femaleRadio.clicked.connect(self.substring_changed)
        self.ui.languageSelect.currentIndexChanged.connect(self.substring_changed)
        self.ui.stringEdit.textChanged.connect(self.string_edited)

        self._installation = installation
        self.locstring = LocalizedString.from_dict(locstring.to_dict())  # Deepcopy the object, we don't trust the `deepcopy` function though.
        self.ui.stringrefSpin.setValue(locstring.stringref)

    def accept(self):
        if self.locstring.stringref != -1:
            tlk_path = CaseAwarePath(self._installation.path(), "dialog.tlk")
            tlk = read_tlk(tlk_path)
            if len(tlk) <= self.locstring.stringref:
                tlk.resize(self.locstring.stringref + 1)
            tlk[self.locstring.stringref].text = self.ui.stringEdit.toPlainText()
            write_tlk(tlk, tlk_path)
        super().accept()

    def reject(self):
        super().reject()

    def stringref_changed(self, stringref: int):
        self.ui.substringFrame.setVisible(stringref == -1)
        self.locstring.stringref = stringref

        if stringref == -1:
            self._update_text()
        else:
            self.ui.stringEdit.setPlainText(self._installation.talktable().string(stringref))

    def new_tlk_string(self):
        self.ui.stringrefSpin.setValue(self._installation.talktable().size())

    def no_tlk_string(self):
        self.ui.stringrefSpin.setValue(-1)

    def substring_changed(self):
        self._update_text()

    def _update_text(self):
        language = Language(self.ui.languageSelect.currentIndex())
        gender = Gender(int(self.ui.femaleRadio.isChecked()))
        text = self.locstring.get(language, gender) or ""
        self.ui.stringEdit.setPlainText(text)

    def string_edited(self):
        if self.locstring.stringref == -1:
            language = Language(self.ui.languageSelect.currentIndex())
            gender = Gender(int(self.ui.femaleRadio.isChecked()))
            self.locstring.set_data(language, gender, self.ui.stringEdit.toPlainText())
