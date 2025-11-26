from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.tools.path import CaseAwarePath
from toolset.data.installation import HTInstallation

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.resource_auto import TLK
    from toolset.data.installation import HTInstallation


class LocalizedStringDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        locstring: LocalizedString,
    ):
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
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        from toolset.gui.common.localization import translate as tr, trf
        self.ui.stringrefNoneButton.setToolTip(tr("Override the TLK with a custom entry."))
        self.ui.stringrefNewButton.setToolTip(tr("Create a new entry in the TLK."))
        self.setWindowTitle(trf("{language} - {name} - Localized String Editor", language=installation.talktable().language().name.title(), name=installation.name))

        self.ui.stringrefSpin.valueChanged.connect(self.stringref_changed)
        self.ui.stringrefNewButton.clicked.connect(self.new_tlk_string)
        self.ui.stringrefNoneButton.clicked.connect(self.no_tlk_string)
        self.ui.maleRadio.clicked.connect(self.substring_changed)
        self.ui.femaleRadio.clicked.connect(self.substring_changed)
        self.ui.languageSelect.currentIndexChanged.connect(self.substring_changed)
        self.ui.stringEdit.textChanged.connect(self.string_edited)

        self._installation: HTInstallation = installation
        self.locstring: LocalizedString = LocalizedString.from_dict(locstring.to_dict())  # Deepcopy the object, we don't trust the `deepcopy` function though.
        self.ui.stringrefSpin.setValue(locstring.stringref)

    def accept(self):
        if self.locstring.stringref != -1:
            tlk_path: CaseAwarePath = CaseAwarePath(self._installation.path(), "dialog.tlk")
            tlk: TLK = read_tlk(tlk_path)
            if len(tlk) <= self.locstring.stringref:
                tlk.resize(self.locstring.stringref + 1)
            tlk[self.locstring.stringref].text = self.ui.stringEdit.toPlainText()
            write_tlk(tlk, tlk_path)
        super().accept()

    def reject(self):
        super().reject()

    def stringref_changed(
        self,
        stringref: int,
    ):
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
        language: Language = Language(self.ui.languageSelect.currentIndex())
        gender: Gender = Gender(int(self.ui.femaleRadio.isChecked()))
        text: str = self.locstring.get(language, gender) or ""
        self.ui.stringEdit.setPlainText(text)

    def string_edited(self):
        if self.locstring.stringref == -1:
            language: Language = Language(self.ui.languageSelect.currentIndex())
            gender: Gender = Gender(int(self.ui.femaleRadio.isChecked()))
            self.locstring.set_data(language, gender, self.ui.stringEdit.toPlainText())
