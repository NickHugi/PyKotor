from pykotor.common.misc import ResRef
from pykotor.resource.generics.git import GITModuleLink, GITTrigger
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QWidget
from toolset.data.installation import HTInstallation


class TriggerDialog(QDialog):
    def __init__(self, parent: QWidget, trigger: GITTrigger, installation: HTInstallation):
        super().__init__(parent)

        from toolset.uic.dialogs.instance.trigger import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.transNameEdit.setInstallation(installation)

        self.setWindowTitle("Edit Trigger")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/trigger.png")))

        self.ui.resrefEdit.setText(str(trigger.resref))
        self.ui.tagEdit.setText(trigger.tag)
        self.ui.xPosSpin.setValue(trigger.position.x)
        self.ui.yPosSpin.setValue(trigger.position.y)
        self.ui.zPosSpin.setValue(trigger.position.z)
        self.ui.linkToTagEdit.setText(trigger.linked_to)
        self.ui.linkToModuleEdit.setText(str(trigger.linked_to_module))
        self.ui.noTransCheck.setChecked(trigger.linked_to_flags == 0)
        self.ui.toDoorCheck.setChecked(trigger.linked_to_flags == 1)
        self.ui.toWaypointCheck.setChecked(trigger.linked_to_flags == 2)
        self.ui.transNameEdit.setLocstring(trigger.transition_destination)

        self.trigger: GITTrigger = trigger

    def accept(self) -> None:
        super().accept()
        self.trigger.resref = ResRef(self.ui.resrefEdit.text())
        self.trigger.tag = self.ui.tagEdit.text()
        self.trigger.position.x = self.ui.xPosSpin.value()
        self.trigger.position.y = self.ui.yPosSpin.value()
        self.trigger.position.z = self.ui.zPosSpin.value()
        self.trigger.linked_to = self.ui.linkToTagEdit.text()
        self.trigger.linked_to_module = ResRef(self.ui.linkToModuleEdit.text())
        self.trigger.linked_to_flags = GITModuleLink(
            0 if self.ui.noTransCheck.isChecked() else 1 if self.ui.toDoorCheck.isChecked() else 2,
        )
        self.trigger.transition_destination = self.ui.transNameEdit.locstring()
