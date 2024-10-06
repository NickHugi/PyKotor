
################################################################################
## Form generated from reading UI file 'locstring_edit.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton


class Ui_Form:
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(233, 23)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.locstringText = QLineEdit(Form)
        self.locstringText.setObjectName("locstringText")
        self.locstringText.setReadOnly(True)

        self.horizontalLayout.addWidget(self.locstringText)

        self.editButton = QPushButton(Form)
        self.editButton.setObjectName("editButton")
        self.editButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout.addWidget(self.editButton)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", "Form", None))
        self.editButton.setText(QCoreApplication.translate("Form", "...", None))
    # retranslateUi

