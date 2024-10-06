
################################################################################
## Form generated from reading UI file 'search_result.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(303, 401)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.resultList = QListWidget(Dialog)
        self.resultList.setObjectName("resultList")

        self.verticalLayout.addWidget(self.resultList)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.openButton = QPushButton(Dialog)
        self.openButton.setObjectName("openButton")

        self.horizontalLayout.addWidget(self.openButton)

        self.okButton = QPushButton(Dialog)
        self.okButton.setObjectName("okButton")

        self.horizontalLayout.addWidget(self.okButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Search Results", None))
        self.openButton.setText(QCoreApplication.translate("Dialog", "Open", None))
        self.okButton.setText(QCoreApplication.translate("Dialog", "OK", None))
    # retranslateUi

