
################################################################################
## Form generated from reading UI file 'save_to_module.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(174, 95)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.resrefEdit = QLineEdit(Dialog)
        self.resrefEdit.setObjectName("resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.resrefEdit)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.typeCombo = QComboBox(Dialog)
        self.typeCombo.setObjectName("typeCombo")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.typeCombo)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Save To Module", None))
        self.label.setText(QCoreApplication.translate("Dialog", "ResRef:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", "Type:", None))
    # retranslateUi

