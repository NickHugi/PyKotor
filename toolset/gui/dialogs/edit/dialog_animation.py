from toolset.data.installation import HTInstallation
from PyQt5.QtWidgets import QDialog, QWidget

from pykotor.resource.generics.dlg import DLGAnimation


class EditAnimationDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, animation: DLGAnimation = DLGAnimation()):
        super().__init__(parent)

        from toolset.uic.dialogs.edit_animation import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        animations_list = installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
        self.ui.animationSelect.setItems(animations_list.get_column("name"), sortAlphabetically=True, cleanupStrings=True, ignoreBlanks=True)

        self.ui.animationSelect.setCurrentIndex(animation.animation_id)
        self.ui.participantEdit.setText(animation.participant)

    def animation(self) -> DLGAnimation:
        animation = DLGAnimation()
        animation.animation_id = self.ui.animationSelect.currentIndex()
        animation.participant = self.ui.participantEdit.text()
        return animation
