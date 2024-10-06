
################################################################################
## Form generated from reading UI file 'select_module.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QListWidget, QPushButton, QVBoxLayout


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(336, 373)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filterEdit = QLineEdit(Dialog)
        self.filterEdit.setObjectName("filterEdit")

        self.verticalLayout.addWidget(self.filterEdit)

        self.moduleList = QListWidget(Dialog)
        self.moduleList.setObjectName("moduleList")

        self.verticalLayout.addWidget(self.moduleList)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cancelButton = QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)

        self.browseButton = QPushButton(Dialog)
        self.browseButton.setObjectName("browseButton")

        self.horizontalLayout.addWidget(self.browseButton)

        self.openButton = QPushButton(Dialog)
        self.openButton.setObjectName("openButton")
        self.openButton.setEnabled(False)

        self.horizontalLayout.addWidget(self.openButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Open Module", None))
        self.filterEdit.setPlaceholderText(QCoreApplication.translate("Dialog", "filter...", None))
        self.cancelButton.setText(QCoreApplication.translate("Dialog", "Cancel", None))
        self.browseButton.setText(QCoreApplication.translate("Dialog", "Browse", None))
        self.openButton.setText(QCoreApplication.translate("Dialog", "Open", None))
    # retranslateUi

