# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'locstring_edit.ui'
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
        Form.resize(233, 23)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.locstringText = QLineEdit(Form)
        self.locstringText.setObjectName(u"locstringText")
        self.locstringText.setReadOnly(True)

        self.horizontalLayout.addWidget(self.locstringText)

        self.editButton = QPushButton(Form)
        self.editButton.setObjectName(u"editButton")
        self.editButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout.addWidget(self.editButton)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.editButton.setText(QCoreApplication.translate("Form", u"...", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
