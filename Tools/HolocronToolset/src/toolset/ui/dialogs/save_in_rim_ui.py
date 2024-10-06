
################################################################################
## Form generated from reading UI file 'save_in_rim.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(271, 77)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cancelButton = QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)

        self.overrideSaveButton = QPushButton(Dialog)
        self.overrideSaveButton.setObjectName("overrideSaveButton")

        self.horizontalLayout.addWidget(self.overrideSaveButton)

        self.modSaveButton = QPushButton(Dialog)
        self.modSaveButton.setObjectName("modSaveButton")

        self.horizontalLayout.addWidget(self.modSaveButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Cannot save to RIM", None))
        self.label.setText(QCoreApplication.translate("Dialog", "Saving to RIM files is disabled. You can choose\n"
"to save it to the Override or .MOD file instead.", None))
        self.cancelButton.setText(QCoreApplication.translate("Dialog", "Cancel", None))
        self.overrideSaveButton.setText(QCoreApplication.translate("Dialog", "Save to Override", None))
        self.modSaveButton.setText(QCoreApplication.translate("Dialog", "Save to .MOD", None))
    # retranslateUi

