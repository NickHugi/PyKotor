from copy import deepcopy

from PyQt5.QtWidgets import QDialog, QWidget

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.tools.path import CaseAwarePath
from toolset.data.installation import HTInstallation


class LocalizedStringDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, locstring: LocalizedString):
        super().__init__(parent)

        from toolset.uic.dialogs.locstring import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(f"{installation.talktable().language().name.title()} - {installation.name} - Localized String Editor")

        self.ui.stringrefSpin.valueChanged.connect(self.stringrefChanged)
        self.ui.stringrefNewButton.clicked.connect(self.newTlkString)
        self.ui.stringrefNoneButton.clicked.connect(self.noTlkString)
        self.ui.maleRadio.clicked.connect(self.substringChanged)
        self.ui.femaleRadio.clicked.connect(self.substringChanged)
        self.ui.languageSelect.currentIndexChanged.connect(self.substringChanged)
        self.ui.stringEdit.textChanged.connect(self.stringEdited)

        self._installation = installation
        self.locstring = deepcopy(locstring)
        self.ui.stringrefSpin.setValue(locstring.stringref)

    def accept(self) -> None:
        if self.locstring.stringref != -1:
            tlk_path = CaseAwarePath(self._installation.path(), "dialog.tlk")
            tlk = read_tlk(tlk_path)
            if len(tlk) <= self.locstring.stringref:
                tlk.resize(self.locstring.stringref + 1)
            tlk.get(self.locstring.stringref).text = self.ui.stringEdit.toPlainText()
            write_tlk(tlk, tlk_path)
        super().accept()

    def reject(self) -> None:
        super().reject()

    def stringrefChanged(self, stringref: int) -> None:
        self.ui.substringFrame.setVisible(stringref == -1)
        self.locstring.stringref = stringref

        if stringref == -1:
            self._update_text()
        else:
            self.ui.stringEdit.setPlainText(self._installation.talktable().string(stringref))

    def newTlkString(self):
        self.ui.stringrefSpin.setValue(self._installation.talktable().size())

    def noTlkString(self) -> None:
        self.ui.stringrefSpin.setValue(-1)

    def substringChanged(self) -> None:
        self._update_text()

    def _update_text(self):
        language = Language(self.ui.languageSelect.currentIndex())
        gender = Gender(int(self.ui.femaleRadio.isChecked()))
        text = (
            self.locstring.get(language, gender)
            if self.locstring.get(language, gender) is not None
            else ""
        )
        self.ui.stringEdit.setPlainText(text)

    def stringEdited(self) -> None:
        if self.locstring.stringref == -1:
            language = Language(self.ui.languageSelect.currentIndex())
            gender = Gender(int(self.ui.femaleRadio.isChecked()))
            self.locstring.set_data(language, gender, self.ui.stringEdit.toPlainText())
