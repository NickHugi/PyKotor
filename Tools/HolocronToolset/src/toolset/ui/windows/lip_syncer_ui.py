
################################################################################
## Form generated from reading UI file 'lip_syncer.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(260, 357)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.languageSelect = QComboBox(Dialog)
        self.languageSelect.addItem("")
        self.languageSelect.setObjectName("languageSelect")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.languageSelect)


        self.verticalLayout.addLayout(self.formLayout)

        self.audioList = QListWidget(Dialog)
        self.audioList.setObjectName("audioList")

        self.verticalLayout.addWidget(self.audioList)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.AddAudioButton = QPushButton(Dialog)
        self.AddAudioButton.setObjectName("AddAudioButton")

        self.horizontalLayout.addWidget(self.AddAudioButton)

        self.removeAudioButton = QPushButton(Dialog)
        self.removeAudioButton.setObjectName("removeAudioButton")

        self.horizontalLayout.addWidget(self.removeAudioButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", "LLanguage:", None))
        self.languageSelect.setItemText(0, QCoreApplication.translate("Dialog", "English", None))

        self.AddAudioButton.setText(QCoreApplication.translate("Dialog", "Load MP3s", None))
        self.removeAudioButton.setText(QCoreApplication.translate("Dialog", "Remove MP3", None))
    # retranslateUi

