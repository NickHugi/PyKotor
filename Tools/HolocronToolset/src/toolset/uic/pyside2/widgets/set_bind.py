# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'set_bind.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(354, 41)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.mouseCombo = QComboBox(Form)
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.addItem("")
        self.mouseCombo.setObjectName(u"mouseCombo")
        self.mouseCombo.setMinimumSize(QSize(80, 0))

        self.horizontalLayout.addWidget(self.mouseCombo)

        self.setKeysEdit = QLineEdit(Form)
        self.setKeysEdit.setObjectName(u"setKeysEdit")
        self.setKeysEdit.setReadOnly(True)

        self.horizontalLayout.addWidget(self.setKeysEdit)

        self.setButton = QPushButton(Form)
        self.setButton.setObjectName(u"setButton")
        self.setButton.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout.addWidget(self.setButton)

        self.clearButton = QPushButton(Form)
        self.clearButton.setObjectName(u"clearButton")
        self.clearButton.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout.addWidget(self.clearButton)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.mouseCombo.setItemText(0, QCoreApplication.translate("Form", u"Left", None))
        self.mouseCombo.setItemText(1, QCoreApplication.translate("Form", u"Middle", None))
        self.mouseCombo.setItemText(2, QCoreApplication.translate("Form", u"Right", None))
        self.mouseCombo.setItemText(3, QCoreApplication.translate("Form", u"Any", None))
        self.mouseCombo.setItemText(4, QCoreApplication.translate("Form", u"None", None))

        self.setKeysEdit.setPlaceholderText(QCoreApplication.translate("Form", u"none", None))
        self.setButton.setText(QCoreApplication.translate("Form", u"Set", None))
        self.clearButton.setText(QCoreApplication.translate("Form", u"Clear", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
