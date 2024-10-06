
################################################################################
## Form generated from reading UI file 'edit_animation.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit

from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(400, 70)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.animationSelect = ComboBox2DA(Dialog)
        self.animationSelect.setObjectName("animationSelect")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.animationSelect)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.participantEdit = QLineEdit(Dialog)
        self.participantEdit.setObjectName("participantEdit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.participantEdit)


        self.horizontalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Edit Animation", None))
        self.label.setText(QCoreApplication.translate("Dialog", "Animation:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", "Participant:", None))
    # retranslateUi

