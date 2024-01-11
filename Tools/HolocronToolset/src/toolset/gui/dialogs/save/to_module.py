from pykotor.resource.type import ResourceType
from PyQt5.QtWidgets import QDialog


class SaveToModuleDialog(QDialog):
    """SaveToModuleDialog lets the user specify a ResRef and a resource type when saving to a module."""

    def __init__(self, resref, restype, supported):
        super().__init__()

        from toolset.uic.dialogs.save_to_module import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.resrefEdit.setText(resref)
        self.ui.typeCombo.addItems([restype.extension.upper() for restype in supported])
        self.ui.typeCombo.setCurrentIndex(supported.index(restype))

    def resname(self) -> str:  # resref filename stem
        return self.ui.resrefEdit.text()

    def restype(self) -> ResourceType:
        return ResourceType.from_extension(self.ui.typeCombo.currentText().lower())
