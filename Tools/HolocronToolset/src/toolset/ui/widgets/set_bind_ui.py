
################################################################################
## Form generated from reading UI file 'set_bind.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton


class Ui_Form:
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(354, 41)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.mouseCombo = QComboBox(Form)
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.setObjectName("mouseCombo")
        self.mouseCombo.setMinimumSize(QSize(80, 0))

        self.horizontalLayout.addWidget(self.mouseCombo)

        self.setKeysEdit = QLineEdit(Form)
        self.setKeysEdit.setObjectName("setKeysEdit")
        self.setKeysEdit.setReadOnly(True)

        self.horizontalLayout.addWidget(self.setKeysEdit)

        self.setButton = QPushButton(Form)
        self.setButton.setObjectName("setButton")
        self.setButton.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout.addWidget(self.setButton)

        self.clearButton = QPushButton(Form)
        self.clearButton.setObjectName("clearButton")
        self.clearButton.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout.addWidget(self.clearButton)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", "Form", None))
        self.mouseCombo.setItemText(0, QCoreApplication.translate("Form", "Left", None))
        self.mouseCombo.setItemText(1, QCoreApplication.translate("Form", "Middle", None))
        self.mouseCombo.setItemText(2, QCoreApplication.translate("Form", "Right", None))
        self.mouseCombo.setItemText(3, QCoreApplication.translate("Form", "Any", None))
        self.mouseCombo.setItemText(4, QCoreApplication.translate("Form", "None", None))

        self.setKeysEdit.setPlaceholderText(QCoreApplication.translate("Form", "none", None))
        self.setButton.setText(QCoreApplication.translate("Form", "Set", None))
        self.clearButton.setText(QCoreApplication.translate("Form", "Clear", None))
    # retranslateUi

